#!/usr/bin/env python3
"""Read-only publisher ELF/source binding, never installed-image attribution.

Analysis dependencies: capstone==5.0.6, pyelftools==0.32.
This is static inspection, not an Android lifecycle or durability test.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

LIB_SHA = 'c4a8a8d1e046cab6a42934b8fba31246efb21a002a90beb2bffa555623a383a9'
SOURCE_SHA = '69273756ac1dcab82c0c4de3de5cf4e2571b618e1e2f02eef06a3d2618817d4e'
PUBLISHER = '6d38cce274bb45e2b658a63dd44a01e94c8ae990'
HEADERS = [
    'xbmc/interfaces/python/InfinityPythonPersistence.h',
    'xbmc/platform/android/activity/InfinityScriptPersistence.h',
    'xbmc/platform/android/activity/InfinityProtectedWrites.h',
]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect(a):
    library = a.reference / 'libadulthideout_core.so'
    source = a.reference / 'publisher-service-1.0.1.py'
    assert sha(library) == LIB_SHA and sha(source) == SOURCE_SHA
    manifest = json.loads((a.reference / 'publisher-manifest-1.0.1.json').read_text())
    entry = next(e for e in manifest['platforms']['android-arm64-v8a']
                 if e['name'] == library.name)
    assert manifest['version'] == '1.0.1'
    assert entry['sha256'] == LIB_SHA and entry['size'] == library.stat().st_size
    # Use only the current source map, not the older maps retained in the ZIP.
    assert sha(a.native_artifact) == '74ce5dfc29243db69e41b9108b00e9c826bfee893d1fdd6d1567b62fbe66a036'
    with ZipFile(a.native_artifact) as archive:
        native_map = json.loads(archive.read('NATIVE-SOURCE-MAP.json'))
    bound = {}
    for name in HEADERS:
        digest = sha(a.runtime / name)
        assert native_map[name] == digest, 'NOT_SIGNED83_HEADER:' + name
        bound[name] = digest
    exports = {}
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    with library.open('rb') as stream:
        elf = ELFFile(stream)
        assert elf['e_machine'] == 'EM_AARCH64'
        symbols = elf.get_section_by_name('.dynsym')
        for name in ('start_core_service', 'stop_core_service', 'is_core_service_running'):
            symbol = symbols.get_symbol_by_name(name)[0]
            section = elf.get_section(symbol['st_shndx'])
            start, size = symbol['st_value'], symbol['st_size']
            code = section.data()[start-section['sh_addr']:start-section['sh_addr']+size]
            rows = list(decoder.disasm(code, start))
            exports[name] = dict(address=hex(start), size=size,
                                 machine_code_sha256=hashlib.sha256(code).hexdigest(),
                                 instructions=[dict(address=hex(i.address), mnemonic=i.mnemonic,
                                                    operands=i.op_str) for i in rows])
        imports = sorted(s.name for s in symbols.iter_symbols()
                         if s['st_shndx'] == 'SHN_UNDEF' and s.name)
    # Pin the exact observed flag accesses. A new image requires a fresh review.
    running = exports['is_core_service_running']['instructions']
    stopping = exports['stop_core_service']['instructions']
    assert [(i['mnemonic'], i['operands']) for i in running[:3]] == [
        ('adrp', 'x8, #0x35a000'), ('add', 'x8, x8, #0x1c0'), ('ldarb', 'w8, [x8]')]
    suffix = [i for i in stopping if 0x16b850 <= int(i['address'], 16) <= 0x16b86c]
    assert [(i['mnemonic'], i['operands']) for i in suffix[:4]] == [
        ('adrp', 'x8, #0x35a000'), ('add', 'x8, x8, #0x1c0'),
        ('mov', 'w0, #1'), ('stlrb', 'wzr, [x8]')]
    return dict(
        status='STATIC_REFERENCE_INSPECTION_COMPLETED_NO_COMPLETION_CONTRACT_PROVEN',
        native_build_run=43040415571, native_build_attempt=2,
        signed83_source_bound_headers=bound,
        publisher_commit=PUBLISHER, publisher_core_version=manifest['version'],
        publisher_library_sha256=LIB_SHA, publisher_library_bytes=library.stat().st_size,
        publisher_service_git_blob='eb680f261bd5aa9b683263f2d835ead317800a1e',
        publisher_service_sha256=SOURCE_SHA, exports=exports,
        imports_relevant_to_scope=[s for s in imports if s in (
            'open', 'close', 'write', 'writev', 'fwrite', 'fsync', 'fdatasync',
            'pthread_create', 'pthread_join', 'pthread_detach')],
        interpretation=[
            'The running export reads the byte at0x35a1c0; the stop export directly clears that same byte on its return path and returns1.',
            'A false running flag or return1 alone therefore supplies no separately observed worker-join or protected-resource durability receipt.',
            'This does not prove a worker survives stop, or that the image modifies protected data. Imported I/O/thread functions alone cannot establish either claim.',
            'A safe adapter still needs a verified effect/retirement contract for the actual installed image; none is claimed by this static inspection.'
        ],
        installed_Fold_image_identified=False, native_Core_executed=False,
        metadata_targets_and_results_available=False,
        November11_191812='Owner-supplied summary only; original newer diagnostic not accessible here',
        source_modifications=False, shutdown_accepted=False,
        retained_old_tests='Reuse existing audit ratio and fail-closed ledger results; no repeated suites',
    )


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--native-artifact', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = inspect(args)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'exports'}, indent=2))
