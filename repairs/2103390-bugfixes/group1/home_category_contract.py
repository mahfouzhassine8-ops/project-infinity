#!/usr/bin/env python3
"""Group #1/#19: read-only audit of the *signed* 2103390 Home navigation.

The distinction matters: moving the focused Home category within control 9000
and ACTIVATING a static item are not equivalent. Activation enters Videos and
may close/reopen Home. Never 'fix' this by dropping the original video navigator,
changing Cobra, inventing a cache, or patching shared native directory code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

BASE_SHA256 = '778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'
PREFIX = 'assets/addons/skin.infinity.diggz/'
EXPECTED_CONTROLS = {'8101': ('movies', 'plugin.video.umbrella'),
                     '8102': ('tvshows', 'plugin.video.umbrella'),
                     '8830': ('movies', 'InfinityCompactContinueMoviesPath'),
                     '8831': ('tvshows', 'InfinityCompactContinueTVPath')}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audited_homes(original: bytes) -> dict:
    """Validate signed original and return counts only, without user data."""
    if sha256(original) != BASE_SHA256:
        raise ValueError('Unknown or modified 2103390 signed APK')
    from io import BytesIO
    with ZipFile(BytesIO(original)) as apk:
        homes = sorted(n for n in apk.namelist()
                       if n.startswith(PREFIX) and n.endswith('/Home.xml'))
        if len(homes) != 14:
            raise ValueError('Expected exactly 14 original Home XML variants')
        entries = []
        for path in homes:
            root = ET.fromstring(apk.read(path))
            navbar = root.find('.//control[@id="9000"]')
            if navbar is None or navbar.get('type') != 'wraplist':
                raise ValueError('Original Home category control changed: ' + path)
            categories = {}
            for item in navbar.findall('./content/item'):
                section = item.find('./property[@name="section"]')
                name = section.text if section is not None else ''
                if name in ('movies', 'tvshows'):
                    if name in categories:
                        raise ValueError('Duplicate Home category '+ name)
                    commands = [x.text or '' for x in item.findall('onclick')]
                    if len(commands) != 1 or not commands[0].startswith('ActivateWindow(Videos,'):
                        raise ValueError('Unexpected Home click action '+path+' '+name)
                    categories[name] = commands[0]
            if set(categories) != {'movies', 'tvshows'}:
                raise ValueError('Missing Home category action: '+path)
            controls = {}
            for control_id, (section, source) in EXPECTED_CONTROLS.items():
                c = root.find('.//control[@id="'+control_id+'"]')
                if c is None or c.get('type') != 'panel' or c.findtext('orientation') != 'horizontal':
                    raise ValueError('Home widget orientation changed: '+path+' '+control_id)
                if 'Property(section),'+section+')' not in (c.findtext('visible') or ''):
                    raise ValueError('Unexpected visibility condition: '+path+' '+control_id)
                content = c.findtext('content') or ''
                if source not in content:
                    raise ValueError('Unrecognized media source: '+path+' '+control_id)
                controls[control_id] = {'section': section, 'source_owner': source}
            entries.append({'variant': path[len(PREFIX):],
                            'selected_section_is_visibility_gate': True,
                            'activate_category_leaves_home_for_videos': True,
                            'controls': controls})
        return {'homes': len(entries), 'all_home_variants': entries,
                'owner_split': {'top_movies_tv': 'plugin.video.umbrella',
                                'continue_watching': 'Command Center via existing Infinity variables'},
                'note': 'Static proof of two DIFFERENT navigation paths; no proof which was used in actual Fold recording or which invalidation cause fired.'}


def from_signed_apk(path: Path) -> dict:
    return audited_homes(path.read_bytes())


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('original_apk', type=Path)
    args = parser.parse_args()
    data = from_signed_apk(args.original_apk)
    print(json.dumps({'homes': data['homes'], 'owner_split': data['owner_split'],
                      'external_navigation': sum(x['activate_category_leaves_home_for_videos'] for x in data['all_home_variants']),
                      'note': data['note']}, indent=2))
