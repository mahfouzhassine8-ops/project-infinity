#!/usr/bin/env python3
"""Forward-only full .226 skin ZIP, correcting the unified OSD Rotate->Repeat regression.

Requires the exact tested .225 full skin ZIP, never a clean install.
Android activity actions and white/cyan state are taken from the already
approved 16x9/VideoOSD implementation. No native, resume data or add-ons change.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PARENT = "8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235"
ROOT = "skin.infinity.diggz/"
OSD = ROOT + "unified/VideoOSD.xml"
UUID = "1.0.5.226"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def patch_osd(data):
    s = data.decode("utf-8")
    assert s.count('<control type="button" id="265">') == 1, "Not the approved unified Repeat regression"
    assert s.count("PlayerControl(Repeat)") == 1
    assert s.count("InfinityPlayerRepeatLabel") == 2
    assert s.count(">265<") == 2
    at = s.index('<control type="button" id="265">')
    start = s.rfind('        <control type="group">\n', 0, at)
    end = s.index('        <control type="group">\n', at + 1)
    assert start >= 0 and end > start
    group = s[start:end]
    buttons = re.findall(r'<control type="button".*?</control>', group, re.S)
    images = re.findall(r'<control type="image">.*?</control>', group, re.S)
    assert len(buttons) == 1 and len(images) == 3
    button = buttons[0].replace('id="265"', 'id="263"')
    button = button.replace('$VAR[InfinityPlayerRepeatLabel]',
                            'Player rotation policy: Follow Device / Infinity-controlled')
    button = button.replace('<enable>!Skin.HasSetting(Infinity.PlayerDrawerOpen)</enable>',
                            '<enable>System.Platform.Android + Player.HasVideo + !Skin.HasSetting(Infinity.PlayerDrawerOpen)</enable>')
    actions = (
        '<onclick condition="System.Platform.Android + Player.HasVideo + !Skin.HasSetting(Infinity.PlayerDrawerOpen) + !Skin.HasSetting(Infinity.PlayerRotationUnlocked)">StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED)</onclick>\n'
        '            <onclick condition="System.Platform.Android + Player.HasVideo + !Skin.HasSetting(Infinity.PlayerDrawerOpen) + Skin.HasSetting(Infinity.PlayerRotationUnlocked)">StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_FOLLOW_DEVICE)</onclick>\n'
        '            <onclick condition="System.Platform.Android + Player.HasVideo + !Skin.HasSetting(Infinity.PlayerDrawerOpen)">Skin.ToggleSetting(Infinity.PlayerRotationUnlocked)</onclick>'
    )
    assert button.count('<onclick>PlayerControl(Repeat)</onclick>') == 1
    button = button.replace('<onclick>PlayerControl(Repeat)</onclick>', actions)
    first = images[0].replace('osd_modern/osdrepeat.png','infinity_reference/rotate.png')
    first = first.replace('$VAR[InfinityGlassTextSecondary]','FFFFFFFF')
    first = first.replace('!Playlist.IsRepeatOne + !Playlist.IsRepeat',
                          '!Skin.HasSetting(Infinity.PlayerRotationUnlocked)')
    second = images[1].replace('osd_modern/osdrepeatone.png','infinity_reference/rotate.png')
    second = second.replace('$VAR[InfinityGlassFocus]','$VAR[InfinityPaletteFocus]')
    second = second.replace('Playlist.IsRepeatOne','Skin.HasSetting(Infinity.PlayerRotationUnlocked)')
    group = group.replace(buttons[0],button,1).replace(images[0],first,1)
    group = group.replace(images[1],second,1).replace(images[2],'',1)
    s = s[:start] + group + s[end:]
    s = s.replace('<onright>265</onright>', '<onright>263</onright>')
    s = s.replace('<onleft>265</onleft>', '<onleft>263</onleft>')
    s = s.replace('<label>$VAR[InfinityPlayerRepeatLabel]</label>',
                  '<label>Rotation</label>')
    s = s.replace('<visible>Control.HasFocus(265)</visible>',
                  '<visible>Control.HasFocus(263)</visible>')
    assert 'InfinityPlayerRepeatLabel' not in s and '>265<' not in s
    assert 'PlayerControl(Repeat)' not in s
    root = ET.fromstring(s)
    selected = [n for n in root.iter('control') if n.get('id') == '263']
    assert len(selected) == 1
    clicks = [a.text or '' for a in selected[0].findall('onclick')]
    assert len(clicks) == 3 and clicks[0].endswith('PLAYER_ROTATION_UNLOCKED)')
    assert clicks[1].endswith('PLAYER_ROTATION_FOLLOW_DEVICE)')
    assert clicks[2] == 'Skin.ToggleSetting(Infinity.PlayerRotationUnlocked)'
    return s.encode()

def build(parent, output):
    assert sha(parent.read_bytes()) == PARENT, "Unverified skin parent: refusing"
    with zipfile.ZipFile(parent) as src:
        assert src.testzip() is None
        names = src.namelist()
        assert len(names) == len(set(names))
        before = src.read(OSD)
        edited = patch_osd(before)
        addon_path = ROOT + 'addon.xml'
        addon = src.read(addon_path)
        assert addon.count(b'version="1.0.5.225"') == 1
        addon = addon.replace(b'version="1.0.5.225"',b'version="1.0.5.226"',1)
        manifest_path=ROOT+'Infinity-Protected-Manifest.json'
        manifest=json.loads(src.read(manifest_path))
        assert manifest['candidate']==225
        manifest.update(candidate=226,candidate_version=UUID,skin_version=UUID,
                        candidate_locked=False,
                        rotate_correction_226={
                            'parent_sha256':PARENT,'physical_fold_verified':False,
                            'source':'original approved 16x9 Rotate actions, not Repeat',
                            'native_or_userdata_changes':False})
        manifest['protected_files']['unified/VideoOSD.xml']=sha(edited)
        manifest['protected_files']['addon.xml']=sha(addon)
        changes={OSD:edited,addon_path:addon,
                 manifest_path:(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()}
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w',allowZip64=True) as out:
            for item in src.infolist():
                out.writestr(item,changes.get(item.filename,src.read(item)))
    with zipfile.ZipFile(parent) as original, zipfile.ZipFile(output) as built:
        assert original.namelist()==built.namelist() and built.testzip() is None
        for name in original.namelist():
            if name not in changes: assert original.read(name)==built.read(name),name
        assert b'PlayerControl(Repeat)' in built.read(ROOT+'unified/PlayerControls.xml')
        assert ET.fromstring(built.read(addon_path)).attrib['version']==UUID
    print(json.dumps({'version':UUID,'sha256':sha(output.read_bytes()),
        'files_modified':sorted(changes),'previous_skin_preserved':True,
        'physical_fold_verified':False},indent=2))
if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    build(a.parent,a.output)
