#!/usr/bin/env python3
"""Materialize missing Infinity palette variables on a fresh-engine presentation.

The 1.0.3 transformer only updated pre-existing palette variables. On a fresh
1.0.6 engine some referenced colors (including the player blue/white pair) were
never defined. Fill missing definitions without weakening any release checks.
This does not by itself adapt Xenon or isolate the native player's resource loader.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from infinity_1_0_3_reference_ui import LIGHT_VALUES, DARK_VALUES

VARIABLES = 'assets/addons/skin.estuary/xml/Variables.xml'
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', re.I)


def materialize_variables(data):
    root = ET.fromstring(data)
    counts = {}
    for variable in root.findall('variable'):
        name = variable.get('name')
        counts[name] = counts.get(name, 0) + 1
    for color in LIGHT_VALUES:
        name = 'InfinityColor_' + color
        if counts.get(name, 0) > 1:
            raise ValueError('Duplicate palette variable: ' + name)
        if name in counts:
            continue
        variable = ET.SubElement(root, 'variable', {'name': name})
        ET.SubElement(variable, 'value', {'condition': '$EXP[Infinity.ThemeLight]'}).text = LIGHT_VALUES[color]
        ET.SubElement(variable, 'value', {'condition': '$EXP[Infinity.ThemeDark]'}).text = DARK_VALUES[color]
        ET.SubElement(variable, 'value').text = DARK_VALUES[color]
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Keep the input APK and any previous output unchanged')
    with zipfile.ZipFile(source) as src:
        if len(src.namelist()) != len(set(src.namelist())):
            raise ValueError('Duplicate input APK members')
        variables = materialize_variables(src.read(VARIABLES))
        with zipfile.ZipFile(output, 'w', allowZip64=True) as dst:
            for entry in src.infolist():
                if SIGNATURE.fullmatch(entry.filename):
                    continue
                dst.writestr(entry, variables if entry.filename == VARIABLES else src.read(entry.filename))
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output) as dst:
        for name in src.namelist():
            if name != VARIABLES and not SIGNATURE.fullmatch(name) and src.read(name) != dst.read(name):
                raise ValueError('Changed a protected APK member: ' + name)
    return {'schema': 1, 'signed': False, 'crash_fixed': False,
            'native_or_dex_changed': False, 'runtime_player_protection': False,
            'changed_non_signing_member': VARIABLES,
            'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    a.receipt.write_text(json.dumps(build(a.source, a.output), indent=2) + '\n')
