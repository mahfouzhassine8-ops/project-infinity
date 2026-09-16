#!/usr/bin/env python3
"""Stage a presentation-only correction on the exact shipped 1.0.5 APK.

This is NOT an APK builder or a native splash fix. It exports an XML overlay and
an audit receipt. No signing, engine/DEX edits, font edits, profile writes, polling,
or skin reloads. The existing v4 hook remains the producer of window/theme facts.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

SOURCE_APK_SHA256 = '611eb282b2b095acc0341af3ee46fdedd9a97b104b449a8f41df480bd9d8c683'
SKIN = 'assets/addons/skin.estuary/'
XML_FILES = tuple(SKIN + 'xml/' + n for n in
                  ('Home.xml', 'Includes.xml', 'Includes_Home.xml', 'Variables.xml'))
LIGHT_OLD = ('String.IsEqual(Skin.String(Infinity.ThemePolicy),light) | '
             '[[String.IsEmpty(Skin.String(Infinity.ThemePolicy)) | '
             'String.IsEqual(Skin.String(Infinity.ThemePolicy),system)] + '
             'String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light)]')
DARK_OLD = '![' + LIGHT_OLD + ']'
MOBILE_OLD = 'String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)'
PORTRAIT_OLD = 'Integer.IsLess(System.ScreenWidth,System.ScreenHeight) + ' + MOBILE_OLD
LANDSCAPE_OLD = 'Integer.IsGreater(System.ScreenWidth,System.ScreenHeight) + ' + MOBILE_OLD
EXP = lambda key: '$EXP[Infinity.' + key + ']'
# Actual System.ScreenWidth/Height reflect the GUI geometry committed by v4.
# Do not prefer CommittedWidth/Height properties: v4's equal-size fast path does
# not republish those properties, so they can be absent/stale.
EXPRESSIONS = {
    'ThemeLight': '[' + LIGHT_OLD + ']',
    'ThemeDark': '!' + EXP('ThemeLight'),
    'Mobile': MOBILE_OLD,
    'Portrait': EXP('Mobile') + ' + Integer.IsLess(System.ScreenWidth,System.ScreenHeight)',
    'Landscape': EXP('Mobile') + ' + !Integer.IsLess(System.ScreenWidth,System.ScreenHeight)',
    'NonMobile': '!' + EXP('Mobile'),
}
# Paired colors live on mutually exclusive groups driven by the same hook fact.
# The common dark row is made slightly deeper to keep white text legible.
PALETTES = {
    'light': {'bg': 'FFE1F1FF', 'fg': 'FF0755A5', 'text': 'FF111821', 'icon': 'FF13202C', 'accent': 'FF0877E8'},
    'dark': {'bg': 'FF096DCF', 'fg': 'FFFFFFFF', 'text': 'FFF5F7FA', 'icon': 'FF19BFFF', 'accent': 'FF19BFFF'},
}


def set_text(node: ET.Element, tag: str, value: str) -> ET.Element:
    child = node.find(tag)
    if child is None:
        child = ET.SubElement(node, tag)
    child.text = value
    return child


def condition(text: str) -> str:
    # Longest expressions first. Replacing the complete light expression, not
    # one arm, prevents a manual light override from bypassing layout conditions.
    replacements = ((DARK_OLD, EXP('ThemeDark')), (LIGHT_OLD, EXP('ThemeLight')),
                    ('![' + LANDSCAPE_OLD + ']', '!' + EXP('Landscape')),
                    ('![' + PORTRAIT_OLD + ']', '!' + EXP('Portrait')),
                    (PORTRAIT_OLD, EXP('Portrait')), (LANDSCAPE_OLD, EXP('Landscape')),
                    ('![' + MOBILE_OLD + ']', EXP('NonMobile')), (MOBILE_OLD, EXP('Mobile')))
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def normalize_conditions(root: ET.Element) -> None:
    for node in root.iter():
        if node.tag == 'visible' and node.text:
            node.text = condition(node.text)
        if 'condition' in node.attrib:
            node.set('condition', condition(node.attrib['condition']))
        # All white.png references introduced by the presentation scripts are
        # missing in this APK. colors/white.png exists in its XBTF texture pack.
        if node.tag == 'texture' and node.text == 'white.png':
            node.text = 'colors/white.png'


def paired_menu(root: ET.Element) -> None:
    menu = root.find(".//control[@id='9000']")
    if menu is None:
        raise ValueError('Expected Home fixedlist 9000 not found')
    for layout_name in ('focusedlayout', 'itemlayout'):
        layout = menu.find(layout_name)
        if layout is None:
            raise ValueError('Missing ' + layout_name)
        children = list(layout.findall('control'))
        # Idempotence: an already paired layout is not duplicated a second time.
        if any(c.findtext('description') == 'Infinity palette light' for c in children):
            continue
        for c in children:
            layout.remove(c)
        for theme, palette in PALETTES.items():
            group = ET.SubElement(layout, 'control', {'type': 'group'})
            set_text(group, 'description', 'Infinity palette ' + theme)
            set_text(group, 'visible', EXP('ThemeLight' if theme == 'light' else 'ThemeDark'))
            for c in children:
                group.append(copy.deepcopy(c))
            focused = layout_name == 'focusedlayout'
            for c in group.iter('control'):
                if c.get('type') == 'label':
                    color = palette['fg' if focused else 'text']
                    for tag in ('textcolor', 'focusedcolor', 'selectedcolor'):
                        set_text(c, tag, color)
                    set_text(c, 'shadowcolor', '00FFFFFF')
                texture = c.find('texture')
                if texture is None:
                    continue
                filename = texture.text or ''
                if filename == 'lists/focus.png':
                    # Original focus texture is grey, not white, so tinting it
                    # cannot reproduce the requested light palette exactly.
                    texture.text = 'colors/white.png'
                    texture.set('colordiffuse', palette['bg'])
                elif 'ListItem.Art(thumb)' in filename:
                    texture.set('colordiffuse', palette['fg' if focused else 'icon'])
                elif filename == 'colors/white.png' and c.findtext('width') == '7':
                    texture.set('colordiffuse', palette['accent'])


def center_hero_text(root: ET.Element) -> None:
    definition = root.find("include[@name='ImageWidget']/definition")
    if definition is None:
        raise ValueError('Missing ImageWidget definition')
    gl = next((c for c in definition.iter('control')
               if c.get('type') == 'grouplist' and c.get('id', '').endswith('577')), None)
    if gl is None:
        raise ValueError('Missing hero grouplist')
    # Critical: Kodi grouplist otherwise resets every child to (0,0), defeating
    # centerleft even when the XML anchor appears correct in a text audit.
    set_text(gl, 'usecontrolcoords', 'true')
    widths = {'InfinityBodyHero': '760', 'InfinityBodyHeroCompact': '930',
              'InfinityBodyHeroPortrait': '790'}
    textboxes = [c for c in gl.findall('control') if c.get('type') == 'textbox']
    if len(textboxes) != 3:
        raise ValueError('Unexpected hero body variants; manual reconciliation required')
    for c in textboxes:
        font = c.findtext('font')
        if font not in widths:
            raise ValueError('Unexpected hero font: ' + str(font))
        for tag in ('left', 'right', 'aligny'):
            for old in list(c.findall(tag)):
                c.remove(old)
        set_text(c, 'centerleft', '50%')
        set_text(c, 'top', '0')
        set_text(c, 'width', widths[font])
        set_text(c, 'align', 'center')
        height = set_text(c, 'height', 'auto')
        height.attrib.clear()
        height.set('min', '0')
        height.set('max', '550')
    # The logo assets, image dimensions, fonts and button actions stay untouched.


def transform(files: dict[str, bytes]) -> dict[str, bytes]:
    if set(files) != set(XML_FILES):
        raise ValueError('Exactly the four audited XML files are required')
    roots = {name: ET.fromstring(data) for name, data in files.items()}
    for root in roots.values():
        normalize_conditions(root)
    includes = roots[SKIN + 'xml/Includes.xml']
    for key, value in EXPRESSIONS.items():
        name = 'Infinity.' + key
        node = next((n for n in includes.findall('expression') if n.get('name') == name), None)
        if node is None:
            node = ET.SubElement(includes, 'expression', {'name': name})
        node.text = value
    # Color facts use the same centralized policy; preserve all non-menu palette values.
    variables = roots[SKIN + 'xml/Variables.xml']
    for var in variables.findall('variable'):
        if not var.get('name', '').startswith('InfinityColor_'):
            continue
        values = var.findall('value')
        if len(values) >= 2:
            values[0].set('condition', EXP('ThemeLight'))
            values[1].set('condition', EXP('ThemeDark'))
    paired_menu(roots[SKIN + 'xml/Home.xml'])
    center_hero_text(roots[SKIN + 'xml/Includes_Home.xml'])
    return {name: ET.tostring(root, encoding='utf-8', xml_declaration=True)
            for name, root in roots.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('overlay', type=Path)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args()
    if args.apk.resolve() in (args.overlay.resolve(), args.receipt.resolve()):
        parser.error('Output must not overwrite the input APK')
    digest = hashlib.sha256(args.apk.read_bytes()).hexdigest()
    if digest != SOURCE_APK_SHA256:
        raise ValueError('APK does not match the audited 1.0.5 artifact; reconcile before applying')
    with zipfile.ZipFile(args.apk) as apk:
        if len(apk.namelist()) != len(set(apk.namelist())):
            raise ValueError('Duplicate APK entries')
        files = {name: apk.read(name) for name in XML_FILES}
    corrected = transform(files)
    args.overlay.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.overlay, 'w', zipfile.ZIP_DEFLATED) as out:
        for name, data in corrected.items():
            out.writestr(name, data)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({
        'status': 'staged-xml-overlay-not-an-installable-apk',
        'source_apk_sha256': digest,
        'changed_files': list(corrected), 'fonts_or_artwork_changed': False,
        'new_native_or_dex_code': False, 'native_splash_fixed': False,
        'device_tested': False,
        'hook_policy': 'Existing v4 facts; named skin expressions; no polling or reload'
    }, indent=2) + '\n')

if __name__ == '__main__':
    main()
