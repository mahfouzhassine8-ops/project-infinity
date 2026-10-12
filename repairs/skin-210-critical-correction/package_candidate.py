#!/usr/bin/env python3
"""Overlay the reviewed 210 delta while retaining every unrelated compressed 209 entry."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
PARENT = '544279a735b2e2a4a7d1d77ac94a101dfd112f5f538deca1968f341d0ab6bb08'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compressed(path, info):
    with path.open('rb') as file:
        file.seek(info.header_offset)
        header = file.read(30)
        assert header[:4] == b'PK\x03\x04'
        name, extra = struct.unpack_from('<HH', header, 26)
        file.seek(name + extra, 1)
        return file.read(info.compress_size)


def build(parent, out):
    assert sha(parent.read_bytes()) == PARENT, 'Incorrect failed skin 209'
    inventory = json.loads((HERE / 'change-inventory.json').read_text())
    delta = HERE / 'delta'
    files = {p.relative_to(delta).as_posix(): p.read_bytes() for p in delta.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    assert {name: sha(data) for name, data in files.items()} == inventory['delta_sha256'], 'Unreviewed delta'
    assert not inventory['removed'], 'This candidate removes navigation fragments, not package files'
    out.mkdir(parents=True, exist_ok=True)
    candidate = out / 'skin.infinity.diggz-1.0.5.210-Critical-Correction-RC1.zip'
    shutil.copyfile(parent, candidate)
    with tempfile.TemporaryDirectory(prefix='infinity-skin-210-') as directory:
        directory = Path(directory)
        names = []
        for name, data in files.items():
            relative = 'skin.infinity.diggz/' + name
            destination = directory / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination.chmod(0o644)
            os.utime(destination, (1791763200, 1791763200))
            names.append(relative)
        subprocess.run(['zip', '-q', '-X', '-9', str(candidate.resolve()), *sorted(names)],
                       cwd=directory, env=dict(os.environ, TZ='UTC'), check=True)
    with zipfile.ZipFile(parent) as before, zipfile.ZipFile(candidate) as after:
        for archive in (before, after):
            assert archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist()))
        changes = sorted(name.removeprefix('skin.infinity.diggz/') for name in after.namelist()
                         if name not in before.namelist() or after.read(name) != before.read(name))
        assert changes == sorted(files)
        assert not (set(before.namelist()) - set(after.namelist()))
        preserved = [name for name in before.namelist() if name.removeprefix('skin.infinity.diggz/') not in files]
        for name in preserved:
            assert before.read(name) == after.read(name), name
            assert compressed(parent, before.getinfo(name)) == compressed(candidate, after.getinfo(name)), name
        addon = ET.fromstring(after.read('skin.infinity.diggz/addon.xml'))
        assert addon.get('id') == 'skin.infinity.diggz' and addon.get('version') == '1.0.5.210'
        xml = 0
        for name in after.namelist():
            if name.endswith('.xml'):
                ET.fromstring(after.read(name))
                xml += 1
        patches = []
        for name in inventory['modified']:
            patches.extend(difflib.unified_diff(before.read('skin.infinity.diggz/' + name).decode().splitlines(True),
                                               files[name].decode().splitlines(True), '209/' + name, '210/' + name))
        (out / 'skin-210-source.patch').write_text(''.join(patches))
        payloads = {name: sha(after.read(name)) for name in after.namelist() if not name.endswith('/')}
    receipt = {'file': candidate.name, 'sha256': sha(candidate.read_bytes()), 'bytes': candidate.stat().st_size,
               'parent_file': parent.name, 'parent_sha256': PARENT, 'parent_bytes': parent.stat().st_size,
               'version': '1.0.5.210', 'addon_id': 'skin.infinity.diggz', 'changed': inventory['modified'],
               'added': inventory['added'], 'removed_package_files': [],
               'preserved_payload_entries': len(preserved), 'preserved_compressed_entries': len(preserved),
               'xml_documents_parsed': xml, 'bytes_saved': parent.stat().st_size - candidate.stat().st_size,
               'preview_native_pair': 2103376, 'protected_rollback': 'Exact locked skin 1.0.5.208', 'immediate_parent': 'Failed skin 1.0.5.209', 'source_commit': os.environ.get('GITHUB_SHA'),
               'device_verified': False, 'locked': False, 'production_promoted': False}
    (out / 'SKIN-210-PRESERVATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (out / 'SKIN-210-FILES.json').write_text(json.dumps(payloads, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ('file', 'sha256', 'bytes', 'bytes_saved', 'xml_documents_parsed')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.parent, args.out)
