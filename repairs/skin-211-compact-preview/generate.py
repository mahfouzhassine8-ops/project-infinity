#!/usr/bin/env python3
"""Build only the reviewed preview overlay over the exact Skin 210 package."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from layout import preview_xml, build_assets

HERE = Path(__file__).resolve().parent
PARENT = '8febf697772ece72c9a445d0b5b6fd2650f97889a00e1e311dc0588199596bb3'
PREFIX = 'skin.infinity.diggz/'
OLD_ARM = b'<onload condition="!String.IsEqual(Window.Property(Infinity.FilePreview.RouteRevision),2103376)">SetProperty(Infinity.FilePreview.OptIn,v1)</onload>'
NEW_ARM = b'<onload>SetProperty(Infinity.FilePreview.OptIn,v1)</onload>'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def generate(parent, output):
    assert sha(parent.read_bytes()) == PARENT, 'Skin 210 input hash mismatch'
    with zipfile.ZipFile(parent) as archive:
        assert archive.testzip() is None
        before = {n[len(PREFIX):]: archive.read(n) for n in archive.namelist() if not n.endswith('/')}
    browser = sorted(n for n in before if n.endswith('/FileBrowser.xml'))
    preview = sorted(n for n in before if n.endswith('/InfinityFilePreview.xml'))
    assert len(browser) == len(preview) == 14
    delta, reasons = {}, {}
    for name in browser:
        assert before[name].count(OLD_ARM) == 1, name
        delta[name] = before[name].replace(OLD_ARM, NEW_ARM)
        reasons[name] = 'Restore the synchronous opt-in removed in 210; native 376 initializes the layout before assigning ZIP context.'
    xml = preview_xml()
    if isinstance(xml, str):
        xml = xml.encode('utf-8')
    for name in preview:
        delta[name] = xml
        reasons[name] = 'Replace the oversized preview only with the approved compact card; preserve all other window XML.'
    for source in sorted((HERE / 'runtime').glob('*.py')):
        name = 'resources/lib/' + source.name
        delta[name] = source.read_bytes()
        reasons[name] = ('Preview-only bounds-to-dp geometry and resize transforms.' if source.name == 'infinity_preview_geometry.py'
                         else 'Bind real metadata to the compact rows and scale the preview in its existing worker; retain nonce/install/cleanup safeguards.')
    for name, data in build_assets().items():
        assert name not in before, 'Existing textures must not be overwritten: ' + name
        delta[name] = data
        reasons[name] = 'New compact-preview-only texture matching the approved ZIP/card/button design; no existing asset changed.'
    addon = before['addon.xml']
    assert addon.count(b'version="1.0.5.210"') == 1
    addon = addon.replace(b'version="1.0.5.210"', b'version="1.0.5.211"', 1)
    addon, count = re.subn(rb'(<description[^>]*>).*?(</description>)',
                         rb'\g<1>Infinity 1.0.5.211 Compact ZIP Preview Correction RC1. Continues exact Skin 210 with its Channels correction preserved. Use unchanged APK 2103376. Galaxy Fold acceptance pending.\g<2>', addon, count=1, flags=re.S)
    assert count == 1
    delta['addon.xml'] = addon
    reasons['addon.xml'] = 'Candidate version and description only; add-on ID, imports and resolution declaration unchanged.'
    output.mkdir(parents=True, exist_ok=True)
    for name, data in delta.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    inventory = {'parent_sha256': PARENT, 'parent_version': '1.0.5.210', 'version': '1.0.5.211',
                 'modified': sorted(set(delta) & set(before)), 'added': sorted(set(delta) - set(before)), 'removed': [],
                 'delta_sha256': {n: sha(d) for n, d in sorted(delta.items())}, 'reasons': reasons}
    (output.parent / 'change-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps({'modified': len(inventory['modified']), 'added': len(inventory['added']), 'removed': 0}))
    return inventory


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    generate(args.parent, args.out)
