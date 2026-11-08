"""Read-only direct-call inspection of the already-built, pinned ARM64 engine.

Not an Android execution, concurrency, crash-prevention or deadlock test.
"""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import struct

EXPECTED = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
ROOT_SYMBOL = '_ZN9XBMCAddon4xbmc12getInfoLabelEPKc'


def inspect(library):
    with library.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == EXPECTED, 'Only the preserved run42453405536 engine is selected'
    with library.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        assert raw[:6] == b'\x7fELF\x02\x01'
        assert struct.unpack_from('<H', raw, 18)[0] == 183  # AArch64
        shoff = struct.unpack_from('<Q', raw, 40)[0]
        shsize, shnum = struct.unpack_from('<HH', raw, 58)
        sections = [struct.unpack_from('<IIQQQQIIQQ', raw, shoff + i * shsize)
                    for i in range(shnum)]
        functions = {}
        for section in sections:
            if section[1] not in (2, 11):  # SHT_SYMTAB / SHT_DYNSYM
                continue
            strings = sections[section[6]]
            base = strings[4]
            for at in range(section[4], section[4] + section[5], section[9]):
                name, info, _, index, address, size = struct.unpack_from('<IBBHQQ', raw, at)
                if info & 15 != 2 or index == 0 or size == 0:
                    continue
                name = raw[base + name:raw.find(b'\0', base + name)].decode()
                entry = functions.setdefault(address, dict(names=[], size=size, section=index))
                if name not in entry['names']:
                    entry['names'].append(name)

        def edges(address):
            function = functions[address]
            section = sections[function['section']]
            offset = section[4] + address - section[3]
            result = []
            for i in range(0, function['size'] - 3, 4):
                word = struct.unpack_from('<I', raw, offset + i)[0]
                if word & 0xfc000000 not in (0x94000000, 0x14000000):
                    continue  # BL / B immediate, including tail calls
                immediate = word & 0x03ffffff
                if immediate & 0x02000000:
                    immediate -= 0x04000000
                target = address + i + immediate * 4
                if target in functions and not address <= target < address + function['size']:
                    result.append((address + i, target))
            return result

        root = next(a for a, f in functions.items() if ROOT_SYMBOL in f['names'])
        visited, paths = set(), []

        def walk(address, trail):
            if address in visited or len(trail) > 12:
                return
            visited.add(address)
            for pc, target in edges(address):
                names = functions[target]['names']
                if not any('optional' in n or 'GuiLock' in n for n in names):
                    continue
                route = trail + [dict(from_function=functions[address]['names'][0],
                                      call_pc=hex(pc), target_function=names[0], target=hex(target))]
                if any('_ZN14XBMCAddonUtils7GuiLockC' in n or
                       '_ZN14XBMCAddonUtils7GuiLockD' in n for n in names):
                    paths.append(route)
                else:
                    walk(target, route)

        walk(root, [])
        assert any('GuiLockC' in p[-1]['target_function'] for p in paths), 'Constructor link missing'
        assert any('GuiLockD' in p[-1]['target_function'] for p in paths), 'Destructor link missing'
    return dict(status='PASS_LINKED_AARCH64_DIRECT_BRANCH_PATHS_TO_EXISTING_GUI_LOCK',
                library_sha256=digest, source_run=42453405536, root=ROOT_SYMBOL, paths=paths,
                method='Read-only ELF64 symbol table and AArch64 BL/B immediate decode; no execution or source changes',
                deadlock_or_crash_prevention='NOT_PROVEN_BY_STATIC_LINKAGE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(inspect(args.library), indent=2) + '\n')
    print('PASS linked guard constructor/destructor paths; Android stability NOT RUN')
