#!/usr/bin/env python3
"""Resolve selected Fold ANR PCs only against the exact locked TEST4 code bytes.

No user diagnostics, runtime edits, APK packaging or baseline changes occur.
The PC values are the non-sensitive offsets from the supplied physical trace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

EXPECTED_TEXT_SHA256 = "eb95501280431e17ff4b2b74e52fb98e3fc59b776ba0a20a1ed97534a14ed298"
EXPECTED_TEXT_SIZE = 47118804
PACKAGED_TEXT_RVA = 0x143c000
LOCKED_APK_SHA256 = "bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286"
NATIVE_COMMIT = "f5e3d9434d8a8c0918d1f4cc6758cf3704eb873c"
PCS = (
    0x14adfb8, 0x15a65a8, 0x15e88d8, 0x16475d8, 0x164dca0,
    0x164de68, 0x164def8, 0x167cba8, 0x168cf34, 0x168e190,
    0x17a6bc8, 0x1a4eec0, 0x1a4f1ac, 0x1a638a0, 0x1a68360,
    0x1a6fe7c, 0x1b1cd48, 0x1b20d0c, 0x1b21214, 0x1b39964,
    0x1bb59a8, 0x23ade18, 0x23c9434, 0x23ca78c, 0x23ca9b8,
    0x23dcad4, 0x23dcb94, 0x23e1c10, 0x2800f60, 0x2808e40,
)


def elf_sections(data: bytes) -> dict[str, tuple[int, ...]]:
    if len(data) < 64 or data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("Expected little-endian ELF64 native library")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", data)
    if header[2] != 183:
        raise ValueError("Expected AArch64 library")
    offset, entry_size, count, strings_index = header[6], header[11], header[12], header[13]
    if entry_size != 64 or not 0 < strings_index < count or offset + count * entry_size > len(data):
        raise ValueError("Invalid ELF section table")
    headers = [struct.unpack_from("<IIQQQQIIQQ", data, offset + i * entry_size)
               for i in range(count)]
    strings_header = headers[strings_index]
    start, size = strings_header[4:6]
    if start + size > len(data):
        raise ValueError("Invalid ELF string table")
    names = data[start:start + size]
    result = {}
    for section in headers:
        if section[0] >= len(names):
            raise ValueError("Invalid ELF section name")
        name = names[section[0]:].split(b"\0", 1)[0].decode("ascii")
        if section[1] != 8 and section[4] + section[5] > len(data):
            raise ValueError("ELF section is outside the file")
        result[name] = section
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.library.read_bytes()
    sections = elf_sections(data)
    text = sections[".text"]
    digest = hashlib.sha256(data[text[4]:text[4] + text[5]]).hexdigest()
    if digest != EXPECTED_TEXT_SHA256 or text[5] != EXPECTED_TEXT_SIZE:
        raise ValueError("Native .text does not match the locked TEST4 APK; refusing attribution")
    tool = shutil.which("llvm-addr2line") or shutil.which("addr2line")
    if tool is None:
        raise ValueError("No addr2line tool available")
    results = []
    for pc in PCS:
        # Stripping can change ELF section/file layout. Align identical code
        # sections explicitly rather than assuming matching virtual addresses.
        symbol_pc = pc + text[3] - PACKAGED_TEXT_RVA
        lookup = subprocess.check_output(
            [tool, "-a", "-C", "-f", "-i", "-e", str(args.library), hex(symbol_pc), hex(symbol_pc - 4)],
            text=True,
        )
        results.append({"pc": hex(pc), "symbol_pc": hex(symbol_pc),
                        "return_callsite": hex(symbol_pc - 4), "lookup": lookup})
    report = {
        "schema": 1,
        "scope": "READ_ONLY_EXACT_TEST4_SYMBOLIZATION",
        "locked_apk_sha256": LOCKED_APK_SHA256,
        "native_source_commit": NATIVE_COMMIT,
        "native_artifact_run": 38975950035,
        "native_library_sha256": hashlib.sha256(data).hexdigest(),
        "locked_text_sha256": digest,
        "locked_text_size": text[5],
        "packaged_text_rva": hex(PACKAGED_TEXT_RVA),
        "symbol_text_rva": hex(text[3]),
        "symbol_text_file_offset": hex(text[4]),
        "has_full_symbols": ".symtab" in sections,
        "has_debug_info": ".debug_info" in sections,
        "addresses": results,
        "root_cause_proven": False,
        "runtime_changed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
