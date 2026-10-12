#!/usr/bin/env python3
"""Verify the clean approved Cobra runtime and retained transport before edits."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in root.rglob('*') if p.is_file()}


def check(args):
    identity = json.loads(args.identity.read_text())
    approved = snapshot(args.approved)
    transport = snapshot(args.transport)
    expected = json.loads(args.approved_receipt.read_text())['after']
    assert approved == expected, 'Approved 2103324 runtime differs from build receipt'
    with tarfile.open(args.transport_archive) as archive:
        archived = {m.name.removeprefix('shell-kodi/'): digest(archive.extractfile(m).read())
                    for m in archive.getmembers() if m.isfile()}
    assert transport == archived, 'Retained 2103369 source differs from its compiled source archive'
    cobra = identity['cobra_source_hashes']
    assert len(cobra) == 24
    for name, value in cobra.items():
        assert approved.get(name) == transport.get(name) == value, name
    assert digest(args.cobra_apk.read_bytes()) == identity['cobra_apk_sha256']
    assert digest(args.transport_apk.read_bytes()) == identity['retained_transport_sha256']
    with zipfile.ZipFile(args.transport_apk) as apk:
        assert apk.testzip() is None
        native = [n for n in apk.namelist() if n.endswith('/libkodi.so')]
        assert len(native) == 1
        assert digest(apk.read(native[0])) == identity['retained_native_sha256']
    tree = json.loads(args.git_tree.read_text())
    assert tree['sha'] == '023339cebbfd08bb877466f12b9c68588459f1a2'
    mismatched = []
    checked = 0
    for entry in tree['tree']:
        if entry['type'] != 'blob':
            continue
        path = args.repo / entry['path']
        if not path.is_file():
            mismatched.append({'path': entry['path'], 'reason': 'missing'})
            continue
        data = path.read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != entry['sha']:
            mismatched.append({'path': entry['path'], 'reason': 'git blob mismatch'})
        checked += 1
    assert not mismatched, json.dumps(mismatched)
    assert not (args.repo / 'repairs/cobra-six-2103370').exists()
    result = {
        'gate': 'A', 'result': 'PASS', 'identity': identity,
        'approved_runtime_files': len(approved), 'transport_runtime_files': len(transport),
        'cobra_files_byte_identical': len(cobra), 'transport_git_blobs_verified': checked,
        'approved_runtime_hashes': approved, 'transport_runtime_hashes': transport,
        'approved_archive_sha256': digest(args.approved_receipt.with_name('repaired-shell-source.tar.gz').read_bytes()),
        'transport_archive_sha256': digest(args.transport_archive.read_bytes()),
        'transport_git_tree': tree['sha'],
        'rejected_2103370_product_changes_in_baseline': False,
        'native_recompile_authorized': False, 'physical_device_acceptance': False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('gate', 'result', 'approved_runtime_files',
          'transport_runtime_files', 'cobra_files_byte_identical', 'transport_git_blobs_verified')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('identity', 'approved', 'transport', 'approved-receipt', 'transport-archive',
                 'cobra-apk', 'transport-apk', 'git-tree', 'repo', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    check(parser.parse_args())
