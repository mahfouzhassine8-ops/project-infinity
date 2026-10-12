#!/usr/bin/env python3
"""Preserve/reconstruct the full locked native parent, then compile the exact three-file delta."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FOUNDATION = ROOT / 'repairs/android-checkpoint-shutdown'
OUT = ROOT / 'checkpoint-build'
PARENT_APK = '160adfccc775f83c640354778e54f6f33164084413401f9c348ebe9ea41fb3e4'
PARENT_ENGINE = '5d42d0d8ef6a90a5678fd7a24cc4e3b01e2375c213c590a92c178d7a34cc1113'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def foundation():
    sys.path.insert(0, str(FOUNDATION))
    spec = importlib.util.spec_from_file_location('unchanged_checkpoint_native', FOUNDATION / 'native_ci.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(parent):
    assert digest(parent.read_bytes()) == PARENT_APK, 'Incorrect locked APK 2103374'
    with zipfile.ZipFile(parent) as archive:
        assert digest(archive.read('lib/arm64-v8a/libkodi.so')) == PARENT_ENGINE
    module = foundation()
    # Every inherited source, persistence, provider and shutdown suite runs unchanged.
    module.prepare()
    original = json.loads((FOUNDATION / 'runtime/native/manifest.json').read_text())
    module.runtime_delta.verify(Path('kodi'), original['after'])
    before = original['after']
    delta = json.loads((HERE / 'native-delta.json').read_text())
    assert len(delta['files']) == 3
    for entry in delta['files']:
        name = entry['file']
        source = HERE / 'native' / name
        assert digest(source.read_bytes()) == entry['after'], name
        assert before.get(name) == entry['before'], 'Parent input differs: ' + name
        if entry['before'] is None:
            assert not (Path('kodi') / name).exists(), 'Unexpected pre-existing file: ' + name
    unresolved = json.loads((HERE / 'native-parent-unmapped.json').read_text())
    assert all(before[name] == expected for name, expected in unresolved.items())
    with tarfile.open(OUT / 'exact-parent-unmapped-sources.tar.gz', 'w:gz') as archive:
        for name in sorted(unresolved):
            archive.add(Path('kodi') / name, arcname=name, recursive=False)
    after = dict(before)
    for entry in delta['files']:
        destination = Path('kodi') / entry['file']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / 'native' / entry['file'], destination)
        after[entry['file']] = entry['after']
    module.runtime_delta.verify(Path('kodi'), after)
    changed = [name for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]
    assert changed == sorted(entry['file'] for entry in delta['files'])
    candidate = dict(original)
    candidate['after'] = after
    candidate['changed'] = sorted(set(original['changed']) | set(changed))
    candidate['added'] = sorted(set(original['added']) | (after.keys() - before.keys()))
    candidate['preview_parent_sha256'] = PARENT_ENGINE
    guard = ROOT / '.zip-preview-compile/runtime/native/manifest.json'
    write(guard, candidate)
    write(OUT / 'FILE-PREVIEW-NATIVE-PRESERVATION.json', {
        'parent_version': 2103374, 'parent_native_sha256': PARENT_ENGINE,
        'source_commit': os.environ.get('GITHUB_SHA'), 'before': before, 'after': after,
        'changed': changed, 'unrelated_reviewed_inputs_preserved': len(before) - 2,
        'previously_unmapped_parent_inputs_resolved': len(unresolved),
        'original_foundation_suites_unchanged': True, 'physical_device_verified': False})
    shutil.copyfile(HERE / 'native-delta.json', OUT / 'FILE-PREVIEW-NATIVE-DELTA.json')
    subprocess.run([sys.executable, str(HERE / 'test_native_preview.py')], check=True)


def compile_engine():
    module = foundation()
    # The unchanged compiler recipe receives a strict candidate manifest in a scratch
    # namespace. Original repository manifests and all inherited tests remain untouched.
    module.HERE = ROOT / '.zip-preview-compile'
    module.compile_engine(True)
    binary = (OUT / 'libkodi.so').read_bytes()
    assert digest(binary) != PARENT_ENGINE, 'Native hook not present in output'
    for token in [b'Infinity.FilePreview.Path', b'Infinity.FilePreview.AcceptNonce',
                  b'Infinity.FilePreview.NativeVersion', b'special://skin/resources/lib/infinity_file_preview.py']:
        assert token in binary, 'Compiled preview bridge is missing: ' + repr(token)
    proof = json.loads((OUT / 'ENGINE-PROOF.json').read_text())
    proof.update(purpose='isolated ZIP file-preview native candidate 2103375',
                 immediate_parent_apk=2103374, immediate_parent_native_sha256=PARENT_ENGINE,
                 preview_delta=json.loads((HERE / 'native-delta.json').read_text())['files'],
                 original_foundation_tests_unchanged=True, device_accepted=False, locked=False)
    write(OUT / 'ENGINE-PROOF.json', proof)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'compile'])
    parser.add_argument('--parent', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert args.parent is not None
        prepare(args.parent)
    else:
        compile_engine()
