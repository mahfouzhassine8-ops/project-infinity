#!/usr/bin/env python3
"""Continue the verified 375 source checkpoint; reuse completed dependencies."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT / 'repairs/zip-preview-2103375'
OUT = ROOT / 'checkpoint-build'
PARENT_APK = '283478929b949bde7690905366e9cd2ee2e0cabc3150cd811cba722b10f18072'
PARENT_ENGINE = '0829366dd65fc2104716c2b76c4f84dbc2edb578f65a53ed94e555e91e484ec3'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def previous():
    spec = importlib.util.spec_from_file_location('verified_preview_375', PREVIOUS / 'native_candidate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(locked, parent):
    assert sha(parent.read_bytes()) == PARENT_APK, 'Wrong immediate parent APK 2103375'
    with zipfile.ZipFile(parent) as archive:
        assert sha(archive.read('lib/arm64-v8a/libkodi.so')) == PARENT_ENGINE
    old = previous()
    old.prepare(locked)
    original = json.loads((ROOT / '.zip-preview-compile/runtime/native/manifest.json').read_text())
    before = original['after']
    delta = json.loads((HERE / 'native-delta.json').read_text())['files']
    assert len(delta) == 3
    after = dict(before)
    for entry in delta:
        name = entry['file']
        assert before[name] == entry['before'], '375 source checkpoint mismatch: ' + name
        assert sha((HERE / 'native' / name).read_bytes()) == entry['after'], name
        assert sha((Path('kodi') / name).read_bytes()) == entry['before'], name
        shutil.copyfile(HERE / 'native' / name, Path('kodi') / name)
        after[name] = entry['after']
    module = old.foundation()
    module.runtime_delta.verify(Path('kodi'), after)
    changed = sorted(name for name in before if before[name] != after[name])
    assert changed == sorted(entry['file'] for entry in delta)
    candidate = dict(original, after=after, changed=sorted(set(original['changed']) | set(changed)))
    write(ROOT / '.critical-preview-compile/runtime/native/manifest.json', candidate)
    write(OUT / 'CRITICAL-PREVIEW-NATIVE-PRESERVATION.json', {
        'parent_version': 2103375, 'parent_native_sha256': PARENT_ENGINE,
        'source_commit': os.environ.get('GITHUB_SHA'), 'before': before, 'after': after,
        'changed': changed, 'unrelated_reviewed_inputs_preserved': len(before) - len(changed),
        'original_foundation_suites_unchanged': True, 'physical_device_verified': False})
    shutil.copyfile(HERE / 'native-delta.json', OUT / 'CRITICAL-PREVIEW-NATIVE-DELTA.json')
    subprocess.run([sys.executable, str(HERE / 'tests/test_input_dispatch.py'),
                    '--kodi', 'kodi', '--report', str(OUT / 'CRITICAL-PREVIEW-TESTS.json')], check=True)


def compile_engine():
    module = previous().foundation()
    module.HERE = ROOT / '.critical-preview-compile'
    module.compile_engine(True)
    binary = (OUT / 'libkodi.so').read_bytes()
    assert sha(binary) != PARENT_ENGINE
    for token in (b'Infinity ZIP preview: raw hold owner=', b'Infinity.FilePreview.RouteRevision',
                  b'Infinity.FilePreview.AcceptNonce', b'special://skin/resources/lib/infinity_file_preview.py'):
        assert token in binary, repr(token)
    proof = json.loads((OUT / 'ENGINE-PROOF.json').read_text())
    proof.update(purpose='ZIP preview input/instance correction 2103376',
                 immediate_parent_apk=2103375, immediate_parent_native_sha256=PARENT_ENGINE,
                 preview_delta=json.loads((HERE / 'native-delta.json').read_text())['files'],
                 original_foundation_tests_unchanged=True, device_accepted=False, locked=False)
    write(OUT / 'ENGINE-PROOF.json', proof)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'compile'])
    parser.add_argument('--locked', type=Path)
    parser.add_argument('--parent', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert args.locked and args.parent
        prepare(args.locked, args.parent)
    else:
        compile_engine()
