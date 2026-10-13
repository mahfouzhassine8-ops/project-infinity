#!/usr/bin/env python3
"""Materialize render-only source copies from the same production layout/runtime.

Uses a hash-verified exact parent FileBrowser from the checked-in fixture.
Does not package a skin or assert full-parent preservation.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
RECIPE = HERE.parent
sys.path.insert(0, str(RECIPE))
from layout import preview_xml, build_assets
from generate import OLD_ARM, NEW_ARM


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / 'fixture-manifest.json').read_text())
    blob = base64.b64decode(''.join(p.read_text() for p in sorted(HERE.glob('fixture-*.b64'))), validate=True)
    assert hashlib.sha256(blob).hexdigest() == manifest['fixture_sha256']
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        browser = archive.read('unified/FileBrowser.xml')
    assert browser.count(OLD_ARM) == 1
    xml = preview_xml()
    if isinstance(xml, str):
        xml = xml.encode('utf-8')
    payloads = {'unified/FileBrowser.xml': browser.replace(OLD_ARM, NEW_ARM),
                'unified/InfinityFilePreview.xml': xml}
    for path in (RECIPE / 'runtime').glob('*.py'):
        payloads['resources/lib/' + path.name] = path.read_bytes()
    payloads.update(build_assets())
    receipt = {}
    for name, data in sorted(payloads.items()):
        path = args.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        receipt[name] = hashlib.sha256(data).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    (args.out.parent / 'render-overlay-sha256.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
