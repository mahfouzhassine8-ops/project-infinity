#!/usr/bin/env python3
"""Compile the saved 2103377 native-entry wrapper over exact locked 2103376.

Native-only validation. No APK creation, signing, release, or shutdown-fix claim.
The saved 274-test Java candidate must be paired with this rebuilt native engine.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'checkpoint-build'
SCRATCH = ROOT / '.close-lifecycle-compile'
SOURCE = ROOT / 'kodi'
MAIN = 'xbmc/platform/android/activity/android_main.cpp'
HEADER = 'xbmc/platform/android/activity/InfinityNativeActivityEntry.h'
PARENT_MAP_SHA = 'df5b66fbad0bb5c9b693a72904bcd7b4a683aa64375e44900bf45870c4b85081'
PARENT_MAIN_SHA = '41c8c0fc88ab335229f330d95e58ba0daf7fe05c4a0beb6d9190ffcfc8c6dd8a'
WRAPPER_SHA = '0a60dccc271f5d2a80e9f6aebaf60278e6e33c86379d5d0228ea710abb3da69e'
SYMBOL = 'InfinityNativeActivity_onCreate'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def load_parent_driver():
    spec = importlib.util.spec_from_file_location(
        'locked_2103376_native_driver', ROOT / 'repairs/critical-preview-2103376/native_candidate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pin_parent(manifest):
    encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    require(len(manifest) == 9391 and hashlib.sha256(encoded).hexdigest() == PARENT_MAP_SHA,
            'Not the complete exact locked 2103376 native manifest')
    require(manifest[MAIN] == PARENT_MAIN_SHA, 'Unapproved native entry preimage')


def prepare(args):
    # Reuse the successful parent reconstruction and unchanged inherited gates.
    # Do not substitute upstream Kodi or an approximate source snapshot.
    parent = load_parent_driver()
    parent.prepare(args.locked, args.previous)
    original = json.loads((ROOT / '.critical-preview-compile/runtime/native/manifest.json').read_text())
    before = original['after']
    pin_parent(before)
    published = json.loads((args.parent_proof / 'CRITICAL-PREVIEW-NATIVE-PRESERVATION.json').read_text())
    require(published['after'] == before, 'Reconstruction differs from green 2103376 native evidence')
    foundation = parent.previous().foundation()
    foundation.runtime_delta.verify(SOURCE, before)
    approved = json.loads((ROOT / 'docs/verification/Infinity-2103377-Local-Android-274-20261013.json').read_text())
    android = approved['android_verification']
    require(android['totals'] == dict(tests=274, failures=0, errors=0, skipped=0),
            'Accepted 274-test checkpoint missing')
    for key in ('previous_234_case_names_preserved', 'previous_234_test_sources_unchanged',
                'runtime_source_matches_candidate', 'compiled_java_inputs_match_candidate'):
        require(android[key] is True, 'Android preservation receipt missing: ' + key)
    recorded = approved['provenance']['candidate_files'][
        'repairs/shutdown-recents-2103377/lifecycle/InfinityNativeActivityEntry.h']
    require(recorded == WRAPPER_SHA == digest(HERE / 'InfinityNativeActivityEntry.h'),
            'Wrapper does not match the accepted lifecycle candidate')
    require(digest(SOURCE / MAIN) == PARENT_MAIN_SHA and not (SOURCE / HEADER).exists(),
            'Native entry changed before staging')
    text = (SOURCE / MAIN).read_text()
    anchor = '#include "InfinityShutdownTrace.h"\n'
    require(text.count(anchor) == 1, 'Native include anchor missing or ambiguous')
    (SOURCE / MAIN).write_text(text.replace(anchor, anchor + '#include "InfinityNativeActivityEntry.h"\n', 1))
    shutil.copyfile(HERE / 'InfinityNativeActivityEntry.h', SOURCE / HEADER)
    after = dict(before)
    after[MAIN] = digest(SOURCE / MAIN)
    after[HEADER] = WRAPPER_SHA
    foundation.runtime_delta.verify(SOURCE, after)
    candidate = dict(original, after=after,
                     changed=sorted(set(original['changed']) | {MAIN}),
                     added=sorted(set(original['added']) | {HEADER}))
    write(SCRATCH / 'runtime/native/manifest.json', candidate)
    write(OUT / 'LIFECYCLE-NATIVE-PRESERVATION.json', {
        'source_commit': os.environ['GITHUB_SHA'], 'parent_version': 2103376,
        'parent_manifest_sha256': PARENT_MAP_SHA, 'before': before, 'after': after,
        'changed': [MAIN], 'added': [HEADER], 'unchanged_parent_inputs': len(before) - 1,
        'wrapper_matches_274_test_checkpoint': True, 'shutdown_corrected': False,
        'apk_packaged_or_signed': False, 'physical_device_verified': False})
    # A reproducible source delta, not a replacement for the complete source map.
    shutil.copyfile(SOURCE / MAIN, OUT / 'lifecycle-android_main.cpp')
    shutil.copyfile(SOURCE / HEADER, OUT / Path(HEADER).name)
    print('STAGED: exact 9391-file parent, one include plus saved native-entry wrapper; no APK.')


def compile_engine():
    parent = load_parent_driver()
    foundation = parent.previous().foundation()
    foundation.HERE = SCRATCH
    foundation.compile_engine(True)
    binary = OUT / 'libkodi.so'
    symbols = subprocess.check_output(['readelf', '--dyn-syms', '--wide', str(binary)], text=True)
    (OUT / 'lifecycle-dynamic-symbols.txt').write_text(symbols)
    for name in (SYMBOL, 'ANativeActivity_onCreate', 'JNI_OnLoad'):
        rows = [row.split() for row in symbols.splitlines() if row.split() and row.split()[-1] == name]
        require(any(len(row) >= 8 and row[3:6] == ['FUNC', 'GLOBAL', 'DEFAULT']
                    and row[6] != 'UND' for row in rows), 'Missing defined public native entry: ' + name)
    require(b'infinityPrepareNativeTask' in binary.read_bytes(), 'Missing Java admission callback')
    proof_path = OUT / 'ENGINE-PROOF.json'
    proof = json.loads(proof_path.read_text())
    proof.update(purpose='Native-only lifecycle compilation for unfinished 2103377',
                 immediate_parent_apk=2103376, wrapper_sha256=WRAPPER_SHA,
                 required_native_entry=SYMBOL, defined_native_entry_verified=True,
                 matched_java_checkpoint='12220187e6de5819651f7429bfdec43fcbaf3591',
                 complete_native_engine_compiled=True, shutdown_corrected=False,
                 apk_packaged_or_signed=False, physical_device_verified=False,
                 device_accepted=False, locked=False)
    write(proof_path, proof)
    print('PASS: full native engine linked and native entry exports verified. Shutdown/APK gates remain open.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'compile'])
    parser.add_argument('--locked', type=Path)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--parent-proof', type=Path)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.mode == 'prepare':
        require(all((args.locked, args.previous, args.parent_proof)), 'Missing pinned parent inputs')
        prepare(args)
    else:
        compile_engine()
