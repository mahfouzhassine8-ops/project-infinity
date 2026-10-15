#!/usr/bin/env python3
"""Reconstruct one candidate from the exact owned baseline ZIP into a NEW folder.

This is a source preparation tool, NOT an installer. It never changes the baseline
archive, installed add-ons, settings, credentials or userdata. No fuzzy patching.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import xml.etree.ElementTree as ET
import zipfile


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if '\\' in value or ':' in value or path.is_absolute() or any(p in ('..', '') for p in path.parts):
        raise ValueError('Unsafe archive/delta path')
    return path


def reconstruct(baseline: Path, delta: Path, component: str, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise ValueError('Output must be a new directory; no existing files are overwritten')
    document = json.loads(delta.read_text(encoding='utf-8'))
    if document.get('schema') != 1 or component not in document.get('components', {}):
        raise ValueError('Unknown delta schema or component')
    info = document['components'][component]
    if sha(baseline.read_bytes()) != info['baseline_zip_sha256']:
        raise ValueError('Wrong baseline ZIP. Exact preserved bytes are required')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='infinity-review-', dir=output.parent))
    try:
        with zipfile.ZipFile(baseline) as archive:
            members = archive.infolist()
            if len(members) > 10000 or sum(m.file_size for m in members) > 512 * 1024 * 1024:
                raise ValueError('Archive exceeds review limits')
            seen = set()
            for member in members:
                path = safe_path(member.filename)
                if not path.parts or path.parts[0] != component:
                    raise ValueError('Archive contains an unexpected component')
                if path.as_posix() in seen:
                    raise ValueError('Duplicate archive path')
                seen.add(path.as_posix())
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise ValueError('Archive symlinks are not supported')
                if member.is_dir():
                    continue
                if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo'):
                    continue
                target = staging.joinpath(*path.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open('xb') as sink:
                    shutil.copyfileobj(source, sink, 64 * 1024)
        for relative, change in info['files'].items():
            path = safe_path(relative)
            target = staging / component / path
            before = change['before_sha256']
            if before is None:
                if target.exists():
                    raise ValueError('New source unexpectedly exists')
                after = change['new_text'].encode('utf-8')
            else:
                original = target.read_bytes()
                if sha(original) != before:
                    raise ValueError('Pre-patch source hash mismatch: '+relative)
                lines = original.decode('utf-8').splitlines(keepends=True)
                amended = []
                cursor = 0
                for start, end, replacements in change['operations']:
                    if not isinstance(start, int) or not isinstance(end, int) or not (cursor <= start <= end <= len(lines)):
                        raise ValueError('Invalid or overlapping delta operations')
                    if not isinstance(replacements, list) or any(not isinstance(s, str) for s in replacements):
                        raise ValueError('Invalid replacement text')
                    amended.extend(lines[cursor:start]); amended.extend(replacements); cursor = end
                amended.extend(lines[cursor:]); after = ''.join(amended).encode('utf-8')
            if len(after) != change['after_bytes'] or sha(after) != change['after_sha256']:
                raise ValueError('Post-patch source hash mismatch: '+relative)
            if target.suffix == '.py':
                compile(after, relative, 'exec')
            elif target.suffix == '.xml':
                ET.fromstring(after)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(after)
        manifest = ET.parse(staging/component/'addon.xml').getroot()
        if manifest.get('id') != component or manifest.get('version') != info['target_version']:
            raise ValueError('Candidate identity mismatch')
        output.mkdir(exist_ok=False)
        try:
            shutil.copytree(staging/component, output/component)
        except Exception:
            shutil.rmtree(output, ignore_errors=True)
            raise
        receipt = {'component': component, 'version': info['target_version'],
                   'baseline_sha256': info['baseline_zip_sha256'], 'changed_files': len(info['files']),
                   'installed': False, 'device_verified': False, 'settings_changed': False}
        (output/'RECONSTRUCTION-RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
        return receipt
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--deltas', type=Path, required=True)
    parser.add_argument('--component', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(reconstruct(args.baseline, args.deltas, args.component, args.output), indent=2))
