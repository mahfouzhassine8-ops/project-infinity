#!/usr/bin/env python3
"""Narrow follow-up to Work's approved #1 Rotate/Playback repair.

Forward-only from exact Work 1.0.5.227. The unified Rotate state is already
explicit cyan; 13 alternate OSD layouts still use theme-derived focus color.
Change only those image colors and unavoidable skin candidate metadata. No
Kodi engine, Cobra, Command Center, helper, or other skin controls are touched.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET

PREFIX = 'skin.infinity.diggz/'
PARENT_SHA256 = 'cc07fe41ccef2b9eca52b8b273ac5ad9a6c1f498a008d64ac0526a7e62dbe699'
VERSION = '1.0.5.228'
ADDON = PREFIX + 'addon.xml'
MANIFEST = PREFIX + 'Infinity-Protected-Manifest.json'
IMAGE = re.compile(rb'<control type="image">.*?</control>', re.DOTALL)
TEXTURE = b'<texture colordiffuse="$VAR[InfinityPaletteFocus]">infinity_reference/rotate.png</texture>'
CYAN = b'<texture colordiffuse="FF00D9FF">infinity_reference/rotate.png</texture>'
ACTIVE = b'<visible>Skin.HasSetting(Infinity.PlayerRotationUnlocked)</visible>'
OSD_WHITE = 'FFFFFFFF'
OSD_CYAN = 'FF00D9FF'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def osd_state(xml: bytes, path: str, cyan_required: bool) -> None:
    root = ET.fromstring(xml)
    matches = [c for c in root.iter('control') if c.get('id') == '263']
    if len(matches) != 1:
        raise ValueError('missing/duplicate approved Rotate slot: ' + path)
    clicks = [c.text for c in matches[0].findall('onclick')]
    if clicks != [
        'StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED)',
        'StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_FOLLOW_DEVICE)',
        'Skin.ToggleSetting(Infinity.PlayerRotationUnlocked)',
    ]:
        raise ValueError('Rotate action semantics differ from approved Work repair: ' + path)
    states = {}
    for node in root.findall('.//control[@type="image"]'):
        image = node.find('texture')
        if image is not None and image.text == 'infinity_reference/rotate.png':
            states[node.findtext('visible')] = image.get('colordiffuse')
    expected = {
        '!Skin.HasSetting(Infinity.PlayerRotationUnlocked)': OSD_WHITE,
        'Skin.HasSetting(Infinity.PlayerRotationUnlocked)': OSD_CYAN if cyan_required else '$VAR[InfinityPaletteFocus]',
    }
    if states != expected:
        raise ValueError('unexpected Rotate icon or state: ' + path + ' ' + repr(states))
    if b'PlayerControl(Repeat)' in xml or b'<label>Display Mode</label>' in xml:
        raise ValueError('regressed Rotate-vs-Repeat or duplicate Playback row: ' + path)


def patch_layout(raw: bytes, path: str) -> bytes:
    osd_state(raw, path, cyan_required=False)
    changed = 0

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal changed
        block = match.group()
        if ACTIVE in block and TEXTURE in block:
            if block.count(TEXTURE) != 1:
                raise ValueError('ambiguous Rotate texture: ' + path)
            changed += 1
            return block.replace(TEXTURE, CYAN, 1)
        return block

    updated = IMAGE.sub(replace, raw)
    if changed != 1:
        raise ValueError('Rotate state did not have exactly one intended image: ' + path)
    osd_state(updated, path, cyan_required=True)
    return updated


def build(parent: Path, target: Path) -> dict:
    if digest(parent.read_bytes()) != PARENT_SHA256:
        raise ValueError('Unapproved skin parent: refusing any modification')
    target.parent.mkdir(parents=True, exist_ok=True)
    replacements: dict[str, bytes] = {}
    with zipfile.ZipFile(parent) as before:
        names = before.namelist()
        if before.testzip() is not None or len(names) != len(set(names)):
            raise ValueError('Corrupt or ambiguous parent skin ZIP')
        osds = sorted(n for n in names if n.endswith('/VideoOSD.xml'))
        if len(osds) != 14 or PREFIX + 'unified/VideoOSD.xml' not in osds:
            raise ValueError('Unexpected active/alternate OSD inventory')
        for name in osds:
            raw = before.read(name)
            if name == PREFIX + 'unified/VideoOSD.xml':
                osd_state(raw, name, cyan_required=True)
            else:
                replacements[name] = patch_layout(raw, name)
        addon = before.read(ADDON)
        old = b'version="1.0.5.227"'
        if addon.count(old) != 1:
            raise ValueError('Unexpected skin add-on manifest version')
        replacements[ADDON] = addon.replace(old, b'version="1.0.5.228"', 1)
        original = json.loads(before.read(MANIFEST))
        if any(original.get(k) != v for k, v in (
            ('candidate', 227), ('candidate_version', '1.0.5.227'),
            ('skin_version', '1.0.5.227'), ('candidate_locked', False))):
            raise ValueError('Unexpected pinned protected manifest version')
        manifest = copy.deepcopy(original)
        manifest.update(candidate=228, candidate_version=VERSION, skin_version=VERSION,
                        candidate_locked=False,
                        item1_rotate_cyan_228=dict(parent_sha256=PARENT_SHA256,
                            changed_osd_count=13, cobra_changed=False,
                            physical_fold_verified=False, final_lock=False))
        for name, body in replacements.items():
            manifest['protected_files'][name[len(PREFIX):]] = digest(body)
        replacements[MANIFEST] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
        if len(replacements) != 15:
            raise ValueError('Unexpected out-of-scope skin changes')
        with zipfile.ZipFile(target, 'w', allowZip64=True) as after:
            for info in before.infolist():
                after.writestr(copy.copy(info), replacements.get(info.filename, before.read(info)))

    with zipfile.ZipFile(parent) as before, zipfile.ZipFile(target) as after:
        if before.namelist() != after.namelist() or after.testzip() is not None:
            raise ValueError('Lost/corrupted protected skin entry')
        different = [n for n in before.namelist() if before.read(n) != after.read(n)]
        if sorted(different) != sorted(replacements):
            raise ValueError('Out-of-scope payload diff: ' + repr(different))
        for name in names:
            if 'cobra' in name.casefold() and before.read(name) != after.read(name):
                raise ValueError('Cobra protection violation')
        for name in osds:
            osd_state(after.read(name), name, cyan_required=True)
    receipt = dict(item=1, implemented=True, version=VERSION,
                   parent_sha256=PARENT_SHA256, candidate_sha256=digest(target.read_bytes()),
                   changed_payloads=sorted(replacements), unchanged_entries=3072-len(replacements),
                   cobra_payload_diff=[], native_or_apk_modified=False,
                   physical_fold_verified=False, integrated_apk_qualified=False)
    target.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.parent, args.out), indent=2))


if __name__ == '__main__':
    main()
