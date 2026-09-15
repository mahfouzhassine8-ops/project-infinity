#!/usr/bin/env python3
"""Inject the clean-core Infinity Compatibility Guard into an unsigned candidate APK."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'addons/service.infinity.compat'
PREFIX = 'assets/addons/service.infinity.compat/'
SIGNING = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', re.I)


def files():
    out = {}
    for path in sorted(ADDON.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            out[PREFIX + path.relative_to(ADDON).as_posix()] = path.read_bytes()
    return out


def build(source: Path, output: Path, receipt: Path):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Keep input and previous output unchanged')
    addon = files()
    required = {
        PREFIX + 'addon.xml',
        PREFIX + 'runtime_service.py',
        PREFIX + 'compat_runtime.py',
        PREFIX + 'layout_service.py',
        PREFIX + 'theme_contract.py',
    }
    missing = sorted(required - set(addon))
    if missing:
        raise ValueError('Compatibility Guard package is incomplete: ' + ', '.join(missing))
    if PREFIX + 'service.py' in addon:
        raise ValueError('Legacy Compatibility Guard mutation service must not be packaged')

    manifest = ET.fromstring(addon[PREFIX + 'addon.xml'])
    services = [
        node for node in manifest.findall('extension')
        if node.attrib.get('point') == 'xbmc.service'
    ]
    if len(services) != 1 or services[0].attrib.get('library') != 'runtime_service.py':
        raise ValueError('Compatibility Guard must declare exactly one clean-core runtime service')

    for name, data in addon.items():
        if name.endswith('.xml'):
            ET.fromstring(data)
    with zipfile.ZipFile(source) as src:
        names = src.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate APK members')
        if any(name in names for name in addon):
            raise ValueError('Compatibility Guard already exists in input')
        with zipfile.ZipFile(output, 'w', allowZip64=True) as dst:
            for item in src.infolist():
                if SIGNING.fullmatch(item.filename):
                    continue
                dst.writestr(item, src.read(item.filename))
            for name, data in addon.items():
                dst.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output) as dst:
        for name in src.namelist():
            if not SIGNING.fullmatch(name) and src.read(name) != dst.read(name):
                raise ValueError('Protected APK member changed: ' + name)
        for name, data in addon.items():
            if dst.read(name) != data:
                raise ValueError('Injected add-on member mismatch: ' + name)
    data = {
        'schema': 2,
        'release': 'Infinity Stability Candidate',
        'signed': False,
        'clean_core_contract': True,
        'single_startup_service': True,
        'supported_skin_ids': ['skin.infinity.diggz', 'skin.infinity'],
        'player_file_mutation': False,
        'skin_file_mutation': False,
        'foreign_skin_reassertion': False,
        'existing_apk_members_preserved': True,
        'device_tested': False,
        'addon_files': {k: hashlib.sha256(v).hexdigest() for k, v in addon.items()},
        'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    print('Injected clean-core Infinity Compatibility Guard without changing existing APK members.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    build(a.source, a.output, a.receipt)
