"""Deterministic standard Kodi script ZIP; no signer or APK workflow."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ADDON = HERE / 'addon/script.infinity.readonlyinventory'


def build(out):
    metadata = ET.parse(ADDON / 'addon.xml').getroot()
    assert metadata.attrib['id'] == ADDON.name and metadata.attrib['version'] == '1.0.0'
    assert [(x.get('point'), x.get('library')) for x in metadata.findall('extension')] == [('xbmc.python.script', 'default.py'), ('xbmc.addon.metadata', None)]
    assert [(x.get('addon'), x.get('version')) for x in metadata.findall('requires/import')] == [('xbmc.python', '3.0.1')]
    paths = [ADDON / n for n in ('addon.xml', 'collector.py', 'default.py', 'resources/identity-pins.json')]
    for p in paths:
        assert p.is_file() and not p.is_symlink()
        if p.suffix == '.py':
            ast.parse(p.read_text())
    out.mkdir(parents=True, exist_ok=True)
    target = out / 'script.infinity.readonlyinventory-1.0.0.zip'
    assert not target.exists(), 'New output only'
    hashes = {}
    with ZipFile(target, 'x', compression=ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(paths):
            name = ADDON.name + '/' + p.relative_to(ADDON).as_posix()
            raw = p.read_bytes()
            i = ZipInfo(name, date_time=(2026, 11, 8, 0, 0, 0));i.compress_type=ZIP_DEFLATED;i.external_attr=0o100644 << 16
            z.writestr(i, raw)
            hashes[name] = hashlib.sha256(raw).hexdigest()
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (out / 'SHA256SUMS').write_text(digest + '  ' + target.name + '\n')
    report = dict(status='BUILT_STANDALONE_READONLY_DIAGNOSTIC_NOT_INFINITY_FIX', addon=ADDON.name, version='1.0.0', sha256=digest, bytes=target.stat().st_size, files=hashes, APK_build=False, signing_keys_accessed=False, Fold_execution='NOT_RUN', Infinity_release_clearance=False)
    (out / 'BUILD-REPORT.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--out', type=Path, required=True)
    build(parser.parse_args().out)
