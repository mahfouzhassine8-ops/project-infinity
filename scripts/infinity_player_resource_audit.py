#!/usr/bin/env python3
"""Audit the player resource dependency boundary before native isolation is enabled.

This is a preparation/verification tool, not an activated player restriction.
Never claim that redirecting VideoOSD.xml alone isolates a Kodi player skin.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

SKIN = 'assets/addons/skin.estuary/'
PLAYER_WINDOWS = ('VideoOSD.xml', 'VideoFullScreen.xml', 'DialogSeekBar.xml',
                  'Custom_1199_InfinityVideoLock.xml')
TOKENS = re.compile(r'\$(VAR|ESCVAR|EXP)\[([^\],]+)')


def audit(apk):
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate APK members')
        xml = {n[len(SKIN + 'xml/'):]: ET.fromstring(archive.read(n)) for n in names
               if n.startswith(SKIN + 'xml/') and n.endswith('.xml')}
        for name in PLAYER_WINDOWS:
            if name not in xml:
                raise ValueError('Missing approved player window: ' + name)
        definitions = {'include': {}, 'variable': {}, 'expression': {}}
        owners = {}
        for name, tree in xml.items():
            for kind in definitions:
                for node in tree.findall(kind):
                    key = node.get('name')
                    if key:
                        # Definition order is noted, not used to simulate Kodi's runtime.
                        definitions[kind].setdefault(key, node)
                        owners.setdefault((kind, key), name)
        queue = [(name, xml[name]) for name in PLAYER_WINDOWS]
        if 'Defaults.xml' in xml:
            queue.append(('Defaults.xml', xml['Defaults.xml']))
        visited = set()
        resources = set(PLAYER_WINDOWS)
        references = set()
        unresolved = set()
        skin_state = set()
        fonts = set()
        while queue:
            owner, tree = queue.pop()
            resources.add(owner)
            for include in tree.iter('include'):
                name = include.get('content') or (include.text or '').strip()
                if name and '$PARAM[' not in name:
                    references.add(('include', name))
            serialized = ET.tostring(tree, encoding='unicode')
            for kind, name in TOKENS.findall(serialized):
                references.add(('expression' if kind == 'EXP' else 'variable', name))
            for node in tree.iter('font'):
                if node.text and node.text.strip():
                    fonts.add(node.text.strip())
            skin_state.update(re.findall(r'Skin\.(?:String|HasSetting)\(([^)]+)\)', serialized))
            for kind, name in list(references):
                if (kind, name) in visited:
                    continue
                visited.add((kind, name))
                if name in definitions[kind]:
                    queue.append((owners[kind, name], definitions[kind][name]))
                else:
                    unresolved.add((kind, name))
        protected_paths = sorted(SKIN + 'xml/' + n for n in resources)
        # Font and packed-texture files must be independently resolved too.
        asset_paths = sorted(n for n in names if n.startswith(SKIN + 'fonts/') or
                             n.startswith(SKIN + 'media/'))
        inventory = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in protected_paths + asset_paths}
        engine_inventory = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in names if
                            n.endswith('.so') or re.fullmatch(r'classes\d*\.dex', n)}
        return {
            'schema': 1, 'input_sha256': hashlib.sha256(Path(apk).read_bytes()).hexdigest(),
            'player_windows': list(PLAYER_WINDOWS),
            'home_window_redirected': False,
            'dependency_definitions': [kind + ':' + name for kind, name in sorted(visited)],
            'unresolved_definitions': [kind + ':' + name for kind, name in sorted(unresolved)],
            'player_font_references': sorted(fonts),
            'skin_state_dependencies': sorted(skin_state),
            'resource_sha256': inventory, 'engine_and_dex_sha256': engine_inventory,
            'runtime_protection_implemented': False,
            'ready_for_release': False,
            'required_before_activation': [
                'Private player includes/defaults, variables, expressions, colors and font namespace.',
                'Private packed-texture lookup, localization and custom-dialog IDs.',
                'Native window routing and reload/lifetime tests; no switch of the global active skin.',
                'Exact Xenon home XML/color adapter that preserves widgets and artwork.',
                'Global theme policy independent of active-skin preferences.',
                'Stop/resume, audio, subtitle, lock, folding, light/dark and device tests.'
            ]
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('apk', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.write_text(json.dumps(audit(a.apk), indent=2) + '\n')


if __name__ == '__main__':
    main()
