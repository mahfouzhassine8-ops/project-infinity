#!/usr/bin/env python3
"""Repair crash-recorder SIGABRT ownership without altering Kodi executable code.

NARROW SCOPE: stage ONLY the reviewed libinfinitycrash signal-source change.
Android's debuggerd should see the *original* FORTIFY abort stack, rather
than only infinitycrash.restore_and_reraise. This is a diagnostics integrity
repair, NOT a claim that a native destroyed-mutex failure has been fixed.

The original signed 2103405 libinfinitycrash.so stays the rollback reference.
Any install-over APK must independently match exact C source and native build ID.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

SOURCE_REL = "repairs/infinity-2103402-final/native-overlay/infinity_crash_recorder.c"
ORIGINAL_GIT_BLOB_SHA1 = "fc7be4f72c7e19606b718d4ef04487756a17a901"
BEFORE = "static const int g_signals[] = { SIGSEGV, SIGABRT, SIGBUS, SIGILL, SIGFPE };"
AFTER = "static const int g_signals[] = { SIGSEGV, SIGBUS, SIGILL, SIGFPE };"

def git_blob_sha1(contents: bytes) -> str:
    header = ("blob " + str(len(contents)) + "\x00").encode("ascii")
    return hashlib.sha1(header + contents).hexdigest()

def apply(source: bytes) -> bytes:
    if git_blob_sha1(source) != ORIGINAL_GIT_BLOB_SHA1:
        raise RuntimeError("Recorder source does not match audited baseline Git object")
    old, new = BEFORE.encode("ascii"), AFTER.encode("ascii")
    if source.count(old) != 1:
        raise RuntimeError("SIGABRT source anchor is not unique")
    modified = source.replace(old, new, 1)
    if modified.replace(new, old, 1) != source:
        raise RuntimeError("Unexpected recorder source modification")
    if b"SIGABRT" not in source or b"SIGABRT" in modified.split(b"static const int g_signals[]",1)[1].split(b";",1)[0]:
        raise RuntimeError("SIGABRT interception was not disabled")
    for token in (
        b"static void crash_handler(int sig, siginfo_t* info, void* opaque)",
        b"static void forward_original_signal(int sig, pid_t tid, siginfo_t* info, void* opaque)",
        b"static void rearm_sigsegv_if_needed(void)",
        b"native-crash-last.txt",
        b"native-maps-%d.txt",
    ):
        if token not in modified:
            raise RuntimeError("Existing signal/memory-map diagnostic owner disappeared")
    return modified

# The signed 2103405 binary may have been compiled from the archived source
# rather than the later diagnostic source revision. This alternate entrypoint
# can be used ONLY after the exact archive Git blob and rebuilt binary SHA
# are independently matched to the signed 2103405 inputs.
ARCHIVED_SOURCE_B64_GIT_SHA1 = "0ab710a2102f1cc143119068502dfbc0df82f8f6"
INSTALLED_RECORDER_BINARY_SHA256 = "bc7aab86fc97844e02e25c96fc73f269bc85f5f8ce5528e132a78841aa130bca"

MATCHED_BINARY_MASKED_BUILD_ID_SHA256 = "192d0a41f6678301c27756112dd627a2e38973ce3fd923fd0279b34ea728ce7d"

def normalized_elf_build_id(binary: bytes) -> bytes:
    """Ignore exactly the 20-byte non-runtime GNU Build ID, nothing else."""
    if (binary[:4] != b"\x7fELF" or binary[4:6] != b"\x02\x01" or
            binary[18:20] != b"\xb7\x00"):
        raise RuntimeError("Expected ELF64 ARM64 recorder")
    value=bytearray(binary)
    shoff=struct.unpack_from("<Q",value,0x28)[0]
    entsize,count,strings=struct.unpack_from("<HHH",value,0x3a)
    if entsize != 64 or not (0 <= strings < count) or shoff+entsize*count>len(value):
        raise RuntimeError("Invalid ELF section-header inventory")
    headers=[struct.unpack_from("<IIQQQQIIQQ",value,shoff+i*entsize) for i in range(count)]
    stringsec=headers[strings]
    names=value[stringsec[4]:stringsec[4]+stringsec[5]]
    matches=[]
    for section in headers:
        if section[0] >= len(names):continue
        label=names[section[0]:names.find(b"\x00",section[0])]
        if label == b".note.gnu.build-id":
            at, length=section[4],section[5]
            if length != 36 or at+36>len(value):
                raise RuntimeError("Unexpected Build ID note format")
            if struct.unpack_from("<III",value,at)!=(4,20,3) or value[at+12:at+16]!=b"GNU\x00":
                raise RuntimeError("Build ID note is not a canonical GNU SHA-1 note")
            matches.append((at+16,at+36))
    if len(matches)!=1:
        raise RuntimeError("Expected exactly one canonical Build ID note")
    start,end=matches[0]
    value[start:end]=b"\x00"*20
    return bytes(value)

def apply_reproduced_archived_source(source: bytes, archive_git_sha: str,
                                   recompiled_binary: bytes) -> bytes:
    if archive_git_sha != ARCHIVED_SOURCE_B64_GIT_SHA1:
        raise RuntimeError("Archived recorder input is not the reviewed original source archive")
    if hashlib.sha256(normalized_elf_build_id(recompiled_binary)).hexdigest() != MATCHED_BINARY_MASKED_BUILD_ID_SHA256:
        raise RuntimeError("Original archived source did not reproduce signed 2103405 recorder")
    old, new = BEFORE.encode("ascii"), AFTER.encode("ascii")
    if source.count(old) != 1:
        raise RuntimeError("Compiled archived source must expose exactly one signal ownership list")
    modified = source.replace(old, new, 1)
    if modified.replace(new, old, 1) != source:
        raise RuntimeError("Archived recorder patch was not exactly reversible")
    signal_list = modified.split(b"static const int g_signals[]",1)[1].split(b";",1)[0]
    if b"SIGABRT" in signal_list:
        raise RuntimeError("SIGABRT still registered")
    if not all(x in signal_list for x in (b"SIGSEGV",b"SIGBUS",b"SIGILL",b"SIGFPE")):
        raise RuntimeError("Existing other fatal signal owners changed")
    return modified


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    before = args.source.read_bytes()
    after = apply(before)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    if args.destination.exists():
        raise RuntimeError("Refusing to overwrite an existing candidate")
    args.destination.write_bytes(after)
    print("PATCHED_DIAGNOSTIC_SOURCE_SHA256="+hashlib.sha256(after).hexdigest())
    print("WHAT_CHANGED: SIGABRT interception disabled, nothing else")
    print("NOT_A_SEARCH_CRASH_FIX: native object lifetime is still under investigation")

if __name__ == "__main__":
    main()
