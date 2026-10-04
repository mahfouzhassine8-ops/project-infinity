#!/usr/bin/env python3
"""Guarded CI transforms. Verify every inherited source, not only edited files."""
import argparse
import hashlib
import json
from pathlib import Path
from native_patch import PATH, BASE_SHA, transform

HERE = Path(__file__).resolve().parent
ANDROID_FILES = ['tools/android/packaging/xbmc/src/' + n for n in
                 ['InfinityAndroidKeyboard.java.in', 'InfinityGlassOptions.java.in']]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root, expected):
    bad = [name for name, sha in expected.items()
           if not (root / name).is_file() or digest(root / name) != sha]
    if bad:
        raise RuntimeError('Source preservation failure: ' + repr(bad))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['android', 'native', 'verify'])
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--parent-proof', type=Path)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    if a.command == 'verify':
        data = json.loads(a.receipt.read_text())
        verify(a.source, data['after'])
        print('PASS preserved source manifest:', len(data['after']), 'files')
        return
    proof = json.loads(a.parent_proof.read_text())
    if a.command == 'android':
        assert proof['source_commit'] == '0a8d8a13efff44cc8be0c99416a1d239b3066e8c'
        before = proof['files']
        assert len(before) == 250
        replacements = {name: (HERE / Path(name).name).read_bytes() for name in ANDROID_FILES}
    else:
        before = proof['after']
        assert before[PATH] == BASE_SHA
        replacements = {PATH: transform((a.source / PATH).read_text()).encode()}
    verify(a.source, before)
    after = dict(before)
    for name, content in replacements.items():
        assert name in before
        (a.source / name).write_bytes(content)
        after[name] = hashlib.sha256(content).hexdigest()
    changed = sorted(n for n in before if before[n] != after[n])
    assert changed == sorted(replacements)
    verify(a.source, after)
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.write_text(json.dumps({
        'schema': 1, 'baseline_apk': 2103303, 'baseline_skin': '1.0.5.194',
        'before': before, 'after': after, 'changed': changed,
        'physical_device_verified': False, 'historical_crash_owner_proven': False
    }, indent=2) + '\n')
    print('PASS:', len(changed), 'declared edits;', len(before)-len(changed), 'sources unchanged')

if __name__ == '__main__':
    main()
