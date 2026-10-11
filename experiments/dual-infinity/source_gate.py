#!/usr/bin/env python3
"""Recover exact compiled preimages; refuse compilation of an incomplete tree.

This is a G0 source gate, not an Android isolation or playback certificate.
An upstream/older export is accepted only for individual byte-identical files.
All expected inputs remain mandatory, including generated branding assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]


def sha(path):
    with path.open('rb') as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
        return digest.hexdigest()


def relative_path(name):
    path = Path(name)
    if path.is_absolute() or not path.parts or '..' in path.parts:
        raise ValueError('Unsafe source manifest path: ' + name)
    return path


def compiled_manifest(group):
    parent = json.loads((HERE / 'PARENT.json').read_text())
    path = REPOSITORY / 'repairs/android-checkpoint-shutdown/runtime' / group / 'manifest.json'
    if sha(path) != parent[group + '_manifest_sha256']:
        raise ValueError('Compiled parent manifest changed: ' + group)
    expected = json.loads(path.read_text())['after']
    for name in expected:
        relative_path(name)
    return expected, parent


def select_exact(expected, candidates):
    selected, missing = {}, []
    for name, digest in sorted(expected.items()):
        for root in candidates:
            path = root / relative_path(name)
            # Do not allow exported symlinks to escape an explicitly selected root.
            if not path.resolve().is_relative_to(root.resolve()):
                continue
            if path.is_file() and sha(path) == digest:
                selected[name] = path
                break
        else:
            missing.append(name)
    return selected, missing


def recover(expected, candidates, destination):
    if destination.exists():
        raise ValueError('Recovery requires a fresh destination; no overwrite allowed')
    target = destination.resolve()
    for source in candidates:
        root = source.resolve()
        if target.is_relative_to(root) or root.is_relative_to(target):
            raise ValueError('Recovery destination overlaps a source root')
    selected, missing = select_exact(expected, candidates)
    # The selected payload is verified again after copying. Incomplete recovery
    # is useful evidence, but it never permits compilation or installation.
    destination.mkdir(parents=True)
    for name, source in selected.items():
        output = destination / relative_path(name)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output)
        if sha(output) != expected[name]:
            raise ValueError('Recovered source readback mismatch: ' + name)
    return missing


def inspect(expected, root):
    return [name for name, digest in sorted(expected.items())
            if not (root / relative_path(name)).is_file()
            or not (root / relative_path(name)).resolve().is_relative_to(root.resolve())
            or sha(root / relative_path(name)) != digest]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('recover', 'verify'))
    parser.add_argument('--group', choices=('native', 'android'), required=True)
    parser.add_argument('--source', action='append', type=Path, required=True)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    expected, parent = compiled_manifest(args.group)
    if args.operation == 'recover':
        if args.destination is None:
            parser.error('recover requires --destination')
        missing = recover(expected, args.source, args.destination)
    else:
        if len(args.source) != 1 or args.destination is not None:
            parser.error('verify requires exactly one source and no destination')
        missing = inspect(expected, args.source[0])
    result = {
        'schema': 1, 'gate': 'G0-source-only', 'group': args.group,
        'compiled_parent_commit': parent['compiled_parent_commit'],
        'expected_files': len(expected), 'verified_files': len(expected) - len(missing),
        'missing_or_mismatched': missing, 'complete': not missing,
        'source_prerequisite_passed': not missing,
        'compilation_authorized_by_this_report': False,
        'installation_safety_verified': False, 'physical_device_pass': False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'group': args.group, 'verified': result['verified_files'],
                      'expected': len(expected), 'source_pass': not missing}))
    return 0 if not missing else 2


if __name__ == '__main__':
    sys.exit(main())
