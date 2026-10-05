#!/usr/bin/env python3
"""Create an exact-197 skin overlay and exact-420 saver controller candidate."""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
SKIN_ID = 'skin.infinity.diggz'
SAVER_ID = 'screensaver.arctic.mirage'
SKIN_VERSION = '1.0.5.198'
SAVER_VERSION = '421'
SKIN_SHA = 'ba1b5639dbbf81136a075d41f81c8a092f7b8afcfe25e71732545a67b21f948e'
SAVER_SHA = '1682f01d2f0098f2e3d96d25cfd62ef9cb2cf747f7f4618ff0a25f282632c4f3'
XML_NAME = 'screensaver-arctic-mirage-addon.xml'
FALLBACK_XML = 'resources/skins/Default/1080i/' + XML_NAME
SKIN_METADATA = {'addon.xml', 'infinity-skin.json', 'Infinity-Protected-Manifest.json'}
SAVER_CHANGED = {'addon.xml', 'default.py', 'resources/lib/screensaver.py', FALLBACK_XML}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def dump(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def read_zip(path, root):
    result = {}
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None, 'Archive CRC failure')
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            require(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename, 'Unsafe path')
            require(p.parts and p.parts[0] == root, 'Wrong root')
            require(not stat.S_ISLNK(info.external_attr >> 16), 'Symlink member')
            if info.is_dir():
                continue
            name = str(PurePosixPath(*p.parts[1:]))
            require(name not in result, 'Duplicate member')
            result[name] = z.read(info)
    return result


def write_zip(path, root, files):
    require(not path.exists(), 'Refusing to overwrite ' + str(path))
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(root + '/' + name, (2026, 10, 5, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=9)
    require(read_zip(path, root) == files, 'Exact archive round-trip failed')


def layout(skin_owned=True):
    """Percentage coordinates resolve against the actual owning skin canvas."""
    font_title, font_body, font_hint = ('InfinityTitle', 'InfinityBody', 'InfinitySmall') if skin_owned else ('Mirage_Title', 'Mirage_Body', 'Mirage_Small')
    black = 'special://home/addons/skin.infinity.diggz/media/infinity_ui/contract_white.png'
    motion = '!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)'
    image_controls = ''
    for art, visible in [
        ('fanart', ''),
        ('thumb', 'String.IsEmpty(Container(1297).ListItem.Art(fanart))'),
        ('poster', 'String.IsEmpty(Container(1297).ListItem.Art(fanart)) + String.IsEmpty(Container(1297).ListItem.Art(thumb))'),
    ]:
        image_controls += f'''
        <control type="image">
            <left>0%</left><top>0%</top><width>100%</width><height>100%</height>
            {('<visible>' + visible + '</visible>') if visible else ''}
            <aspectratio scalediffuse="false">scale</aspectratio>
            <fadetime>400</fadetime>
            <texture background="true">$INFO[Container(1297).ListItem.Art({art})]</texture>
            <animation effect="zoom" start="100" end="106" center="auto" time="15000" tween="sine" easing="inout" pulse="true" condition="{motion}">Conditional</animation>
        </control>'''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<window type="dialog">
    <defaultcontrol always="true">1297</defaultcontrol>
    <backgroundcolor>FF000000</backgroundcolor>
    <coordinates><system>1</system><left>0</left><top>0</top></coordinates>
    <controls>
        <!-- Opaque viewport-sized base: the Home page must not bleed through. -->
        <control type="image">
            <left>0%</left><top>0%</top><width>100%</width><height>100%</height>
            <texture colordiffuse="FF000000">{black}</texture>
        </control>
        <control type="list" id="1297">
            <left>-1000</left><top>-1000</top><width>1</width><height>1</height>
            <content sortby="random">$INFO[Skin.String(screensaver.arctic.mirage.path)]</content>
            <autoscroll time="20000">true</autoscroll>
            <orientation>horizontal</orientation><itemlayout/><focusedlayout/>
        </control>
        {image_controls}
        <control type="image" id="1298">
            <left>-1000</left><top>-1000</top><width>1</width><height>1</height><texture/>
        </control>
        <control type="group">
            <left>0%</left><top>60%</top><width>100%</width><height>40%</height>
        <control type="image">
            <left>0%</left><top>0%</top><width>100%</width><height>100%</height>
            <aspectratio>stretch</aspectratio>
            <texture>special://home/addons/screensaver.arctic.mirage/resources/media/plot-shadow.png</texture>
        </control>
        <control type="image">
            <left>5%</left><top>7.5%</top><width>74%</width><height>35%</height>
            <visible>!String.IsEmpty(Container(1297).ListItem.Art(clearlogo))</visible>
            <aspectratio align="left" aligny="center">keep</aspectratio>
            <texture background="true">$INFO[Container(1297).ListItem.Art(clearlogo)]</texture>
        </control>
        <control type="image">
            <left>5%</left><top>7.5%</top><width>74%</width><height>35%</height>
            <visible>String.IsEmpty(Container(1297).ListItem.Art(clearlogo)) + !String.IsEmpty(Container(1297).ListItem.Art(tvshow.clearlogo))</visible>
            <aspectratio align="left" aligny="center">keep</aspectratio>
            <texture background="true">$INFO[Container(1297).ListItem.Art(tvshow.clearlogo)]</texture>
        </control>
        <control type="textbox">
            <left>5%</left><top>7.5%</top><width>90%</width><height>35%</height>
            <visible>String.IsEmpty(Container(1297).ListItem.Art(clearlogo)) + String.IsEmpty(Container(1297).ListItem.Art(tvshow.clearlogo))</visible>
            <font>{font_title}</font><textcolor>FFFFFFFF</textcolor><shadowcolor>FF000000</shadowcolor>
            <label>$INFO[Container(1297).ListItem.Title]</label>
        </control>
        <control type="textbox">
            <left>5%</left><top>47.5%</top><width>90%</width><bottom>160</bottom>
            <visible>!String.IsEqual(Window.Property(screensaver.arctic.mirage.compact),true)</visible>
            <font>{font_body}</font><textcolor>FFFFFFFF</textcolor><shadowcolor>FF000000</shadowcolor>
            <scrolltime>200</scrolltime>
            <autoscroll delay="6000" time="1800" repeat="10000">{motion}</autoscroll>
            <label>$INFO[Container(1297).ListItem.Plot]</label>
        </control>
        <control type="button" id="1299">
            <left>5%</left><bottom>24</bottom><width>90%</width><height>120</height>
            <visible>String.IsEqual(Window.Property(screensaver.arctic.mirage.info_enabled),true) + !String.IsEmpty(Container(1297).ListItem.FileNameAndPath)</visible>
            <label>Details</label><font>{font_hint}</font>
            <textcolor>FFFFFFFF</textcolor><focusedcolor>FF51C9FF</focusedcolor><shadowcolor>FF000000</shadowcolor>
            <texturefocus border="18">special://home/addons/skin.infinity.diggz/media/infinity_polish/focus_rim.png</texturefocus>
            <texturenofocus/>
            <align>left</align><aligny>center</aligny>
            <onup>1297</onup><ondown>1297</ondown><onleft>1297</onleft><onright>1297</onright>
        </control>
        </control>
    </controls>
</window>
'''.encode()


def repair_saver(original):
    result = dict(original)
    src = original['resources/lib/screensaver.py'].decode()
    prefix = src[:src.index('class Screensaver(')].replace('import threading', 'import time')
    getters = src[src.index('    def _get_container_label('):src.index('    def should_restore_paused_video_osd_after_close(')]
    info = src[src.index('    def _make_info_listitem('):src.index('    def close_screensaver(')]
    result['resources/lib/screensaver.py'] = (prefix + (HERE/'controller_head.py.txt').read_text() + getters + info).encode()
    result['default.py'] = (HERE/'default.py.txt').read_bytes()
    result[FALLBACK_XML] = layout(False)
    addon = ET.fromstring(original['addon.xml'])
    addon.set('version', SAVER_VERSION)
    news = addon.find('./extension[@point="xbmc.addon.metadata"]/news')
    news.text = '421 - Infinity responsive screensaver candidate: controlled callback/wake loop; same-session paused OSD restore; no automatic wake-info popup; owned dialog resize recovery.[CR]' + (news.text or '')
    result['addon.xml'] = ET.tostring(addon, encoding='utf-8', xml_declaration=True)
    require({n for n in original if original[n] != result[n]} == SAVER_CHANGED, 'Unexpected saver change')
    require(set(original) == set(result), 'Unexpected saver file addition')
    return result


def repair_skin(original):
    result = dict(original)
    identity = ET.fromstring(original['addon.xml'])
    require(identity.get('id') == SKIN_ID and identity.get('version') == '1.0.5.197', 'Wrong skin identity')
    release = dict(version=SKIN_VERSION, title='Arctic Mirage Integration RC1', baseline='exact skin 1.0.5.197 Browser Focus RC1',
                   requires_apk=2103305, screensaver_id=SAVER_ID, screensaver_candidate=SAVER_VERSION,
                   status='source/package verified; device acceptance pending', physical_device_verified=False,
                   scope=['responsive add-on screensaver override', 'existing Infinity fonts', 'opaque full-window saver backdrop'])
    identity.set('version', SKIN_VERSION)
    description = identity.find('./extension[@point="xbmc.addon.metadata"]/description')
    description.text = 'Infinity 1.0.5.198 Arctic Mirage Integration RC1. Exact 197 skin plus additive responsive screensaver XML. Pair with Diggz Arctic Mirage 421. APK 2103305 compatible. Device acceptance pending.'
    result['addon.xml'] = ET.tostring(identity, encoding='utf-8', xml_declaration=True)
    meta = json.loads(original['infinity-skin.json'])
    meta['delivery_198_previous_release'] = deepcopy(meta['current_release'])
    meta.update(candidate=198, candidate_name=release['title'], skin_version=SKIN_VERSION, version=SKIN_VERSION,
                release=release['title'], current_release=release, candidate_locked=False, physical_device_verified=False)
    result['infinity-skin.json'] = dump(meta)
    manifest = json.loads(original['Infinity-Protected-Manifest.json'])
    for name, digest in manifest['protected_files'].items():
        require(sha(original[name]) == digest, 'Stale protected preimage: ' + name)
    manifest['delivery_198_previous_release'] = deepcopy(manifest['current_release'])
    manifest.update(candidate=198, candidate_version=SKIN_VERSION, skin_version=SKIN_VERSION,
                    current_release=release, candidate_locked=False)
    # Additive resources across every retained Home profile; no profile flags change.
    folders = {str(PurePosixPath(n).parent) for n in original if n.endswith('/Home.xml')}
    require('unified' in folders, 'Missing canonical profile')
    additions = {p + '/' + XML_NAME for p in folders}
    for name in additions:
        require(name not in original, 'Unexpected existing saver override')
        result[name] = layout(True)
        manifest['protected_files'][name] = sha(result[name])
    for name in manifest['protected_files']:
        require(name != 'Infinity-Protected-Manifest.json', 'Self-referential manifest')
        manifest['protected_files'][name] = sha(result[name])
    result['Infinity-Protected-Manifest.json'] = dump(manifest)
    require({n for n in original if original[n] != result[n]} == SKIN_METADATA, 'Unexpected skin preimage edit')
    require(set(result) - set(original) == additions, 'Unexpected skin additions')
    require(ET.tostring(identity.find('./extension[@point="xbmc.gui.skin"]')) ==
            ET.tostring(ET.fromstring(original['addon.xml']).find('./extension[@point="xbmc.gui.skin"]')), 'Resolution architecture changed')
    return result, additions


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skin', type=Path, required=True)
    p.add_argument('--saver', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(sha(a.skin.read_bytes()) == SKIN_SHA, 'Not the authenticated 197 ZIP')
    require(sha(a.saver.read_bytes()) == SAVER_SHA, 'Not the installed 420 ZIP')
    skin_old, saver_old = read_zip(a.skin, SKIN_ID), read_zip(a.saver, SAVER_ID)
    require(ET.fromstring(saver_old['addon.xml']).get('version') == '420', 'Wrong saver version')
    skin, additions = repair_skin(skin_old)
    saver = repair_saver(saver_old)
    for files in (skin, saver):
        for name, data in files.items():
            if name.endswith('.xml'):
                ET.fromstring(data)
            if name.endswith('.py'):
                ast.parse(data.decode(), filename=name)
    a.output.mkdir(parents=True, exist_ok=True)
    skin_path = a.output/(SKIN_ID + '-' + SKIN_VERSION + '-Arctic-Mirage-RC1.zip')
    saver_path = a.output/(SAVER_ID + '-' + SAVER_VERSION + '-Infinity-Responsive-RC1.zip')
    write_zip(skin_path, SKIN_ID, skin)
    write_zip(saver_path, SAVER_ID, saver)
    proof = dict(schema=1, base_skin_sha256=SKIN_SHA, base_saver_sha256=SAVER_SHA,
                 skin_file=skin_path.name, skin_sha256=sha(skin_path.read_bytes()),
                 screensaver_file=saver_path.name, screensaver_sha256=sha(saver_path.read_bytes()),
                 skin_existing_edits=sorted(SKIN_METADATA), skin_additions=sorted(additions),
                 skin_existing_files_identical=len(skin_old)-len(SKIN_METADATA),
                 saver_edits=sorted(SAVER_CHANGED), saver_existing_files_identical=len(saver_old)-len(SAVER_CHANGED),
                 parent_browser_focus_identical=True, home_player_drawer_weather_providers_identical=True,
                 apk_modified=False, native_modified=False, physical_device_verified=False,
                 all_xml_parsed=True, all_python_ast_parsed=True, exact_archive_roundtrip=True)
    (a.output/'package-proof.json').write_bytes(dump(proof))
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
