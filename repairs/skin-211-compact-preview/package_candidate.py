#!/usr/bin/env python3
"""Overlay new entries while preserving every unrelated compressed ZIP entry."""
import argparse
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

PARENT = '8febf697772ece72c9a445d0b5b6fd2650f97889a00e1e311dc0588199596bb3'
PREFIX = 'skin.infinity.diggz/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compressed(path, info):
    with path.open('rb') as stream:
        stream.seek(info.header_offset)
        header = stream.read(30)
        assert header[:4] == b'PK\x03\x04'
        name, extra = struct.unpack_from('<HH', header, 26)
        stream.seek(name + extra, 1)
        return stream.read(info.compress_size)


def build(parent, delta, out):
    assert sha(parent.read_bytes()) == PARENT
    inventory = json.loads((delta.parent / 'change-inventory.json').read_text())
    files = {p.relative_to(delta).as_posix(): p.read_bytes() for p in delta.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    assert {n: sha(d) for n, d in files.items()} == inventory['delta_sha256']
    assert not inventory['removed']
    out.mkdir(parents=True, exist_ok=True)
    candidate = out / 'skin.infinity.diggz-1.0.5.211-Compact-ZIP-Preview-RC1.zip'
    shutil.copyfile(parent, candidate)
    with tempfile.TemporaryDirectory(prefix='infinity-skin-211-') as directory:
        directory = Path(directory)
        for name, data in files.items():
            path = directory / PREFIX / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o644)
            os.utime(path, (1791849600, 1791849600))
        subprocess.run(['zip', '-q', '-X', '-9', str(candidate.resolve()), *[PREFIX + n for n in sorted(files)]],
                       cwd=directory, env=dict(os.environ, TZ='UTC'), check=True)
    complete = []
    with zipfile.ZipFile(parent) as before, zipfile.ZipFile(candidate) as after:
        for archive in (before, after):
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(before.namelist()) <= set(after.namelist())
        actual = {n[len(PREFIX):] for n in after.namelist() if n not in before.namelist() or after.read(n) != before.read(n)}
        assert actual == set(files), 'Unenumerated package change'
        for name in sorted(after.namelist()):
            relative = name[len(PREFIX):]
            new = after.read(name)
            old = before.read(name) if name in before.namelist() else None
            new_comp = compressed(candidate, after.getinfo(name))
            old_comp = compressed(parent, before.getinfo(name)) if old is not None else None
            status = 'added' if old is None else ('modified' if new != old else 'unchanged')
            if relative not in files:
                assert status == 'unchanged' and old_comp == new_comp, name
            complete.append({'file': name, 'status': status, 'before_sha256': sha(old) if old is not None else None,
                             'after_sha256': sha(new), 'before_compressed_sha256': sha(old_comp) if old_comp is not None else None,
                             'after_compressed_sha256': sha(new_comp), 'before_bytes': len(old) if old is not None else None,
                             'after_bytes': len(new), 'reason': inventory['reasons'].get(relative, 'Preserved byte-for-byte.')})
        for name in after.namelist():
            if name.endswith('.xml'):
                ET.fromstring(after.read(name))
        a = ET.fromstring(after.read(PREFIX + 'addon.xml'))
        assert (a.get('id'), a.get('version')) == ('skin.infinity.diggz', '1.0.5.211')
        b = ET.fromstring(before.read(PREFIX + 'addon.xml'))
        assert ET.tostring(a.find('requires')) == ET.tostring(b.find('requires'))
        assert ET.tostring(a.find("extension[@point='xbmc.gui.skin']")) == ET.tostring(b.find("extension[@point='xbmc.gui.skin']"))
    receipt = {'file': candidate.name, 'sha256': sha(candidate.read_bytes()), 'bytes': candidate.stat().st_size,
               'parent_sha256': PARENT, 'parent_bytes': parent.stat().st_size, 'source_commit': os.environ.get('GITHUB_SHA'),
               'modified': inventory['modified'], 'added': inventory['added'], 'removed': [],
               'unchanged_payload_entries': sum(x['status'] == 'unchanged' for x in complete),
               'unchanged_compressed_entries': sum(x['status'] == 'unchanged' for x in complete),
               'apk_rebuilt': False, 'apk_pair': 2103376, 'physical_device_accepted': False, 'locked': False, 'promoted': False}
    (out / 'SKIN-211-PRESERVATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (out / 'SKIN-211-COMPLETE-FILE-HASHES.json').write_text(json.dumps(complete, indent=2) + '\n')
    (out / 'SKIN-211-CHANGED-FILES.json').write_text(json.dumps([x for x in complete if x['status'] != 'unchanged'], indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('file', 'sha256', 'bytes', 'unchanged_payload_entries', 'unchanged_compressed_entries')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--delta', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.parent, args.delta, args.out)
