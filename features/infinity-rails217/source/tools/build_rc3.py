#!/usr/bin/env python3
"""Reproducible complete .217 ZIP, exact .215 + reconciled RC2 + Rails-only RC3."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

WORK = Path(__file__).resolve().parents[1]
BASE = WORK.parent / 'baseline/skin.infinity.diggz-1.0.5.215-CommandCenter-Settings-Readability-RC1-TEST.zip'
RC2 = WORK.parent / 'helper-before/resources/skin216'
SKIN = WORK / 'skin/skin.infinity.diggz'
HELPER = WORK / 'addons/script.infinity.rails'
OUT = WORK.parent / 'delivery'
BASE_SHA = '486aa86c8f8dcda31d80c6d058f4b96154dcb2b3f1a18cfa464c65e280ec7e70'
PROFILES = ['16x9', '20x9', '5x6', '6x5', 'fallback', 'portrait', 'unified'] + ['responsive/' + p for p in ['base', 'landscape', 'portrait', 'square', 'tall', 'ultrawide', 'wide']]
CONTROLS = (9200, 8820, 8720, 19600)
ROUTE = 'System.AddonIsEnabled(script.infinity.rails) + Window.IsActive(home) + [' + ' | '.join(
    '[String.IsEqual(Window(Home).Property(Infinity.Rails.Focused),' + str(c) + ') + String.IsEqual(Container(' + str(c) + ').ListItem.Property(Infinity.Rails.Item),true)]' for c in CONTROLS) + ']'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def variables():
    light = '[String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light) | [String.IsEmpty(Window(Home).Property(Infinity.SystemTheme)) + String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),light)]]'
    oled = 'String.IsEqual(Window(Home).Property(Infinity.SystemTheme),OLED)'
    colors = {'Surface': ('FAF8FCFF', 'FF000000', 'F20A111A'),
              'Text': ('FF102237', 'FFFFFFFF', 'FFF2F6FB'),
              'Secondary': ('FF445F75', 'FFBECAD6', 'FFBACDDD'),
              'Field': ('FFEAF3F8', 'FF000000', 'F0131D29'),
              'Focus': ('FFD1EDFF', 'FF07304D', 'FF103D58'),
              'Border': ('FFB8C9D8', 'FF223A50', 'FF29445C'),
              'Accent': ('FF006DCB', 'FF24A8FF', 'FF24A8FF')}
    nodes = []
    for key, (lc, oc, dc) in colors.items():
        v = ET.Element('variable', {'name': 'InfinityRails' + key})
        ET.SubElement(v, 'value', {'condition': oled}).text = oc
        ET.SubElement(v, 'value', {'condition': light}).text = lc
        ET.SubElement(v, 'value').text = dc
        nodes.append(ET.tostring(v, encoding='unicode'))
    return '\n'.join(nodes)


def dialog_xml():
    root = ET.Element('window', {'type': 'dialog'})
    ET.SubElement(root, 'defaultcontrol', {'always': 'true'}).text = '200'
    ET.SubElement(root, 'depth').text = 'DepthDialog+'
    motion = '!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)'
    for name, start, end, duration in [('WindowOpen', '0', '100', '180'), ('WindowClose', '100', '0', '140')]:
        ET.SubElement(root, 'animation', {'effect': 'fade', 'start': start, 'end': end, 'time': duration, 'condition': motion}).text = name
    controls = ET.SubElement(root, 'controls')
    group = ET.SubElement(controls, 'control', {'type': 'group', 'id': '1'})
    ET.SubElement(group, 'visible').text = 'String.IsEqual(Window.Property(Rails.LayoutReady),true)'
    def control(kind, cid, x, y, w, h):
        c = ET.SubElement(group, 'control', {'type': kind, 'id': str(cid)})
        for k, v in [('left', x), ('top', y), ('width', w), ('height', h)]:
            ET.SubElement(c, k).text = str(v)
        return c
    def tag(c, name, value, **attrs):
        ET.SubElement(c, name, attrs).text = value
    surface = control('image', 2, 0, 0, 760, 680)
    tag(surface, 'texture', 'infinity_glass/surface.png', border='24', colordiffuse='$VAR[InfinityRailsSurface]')
    tag(surface, 'bordertexture', 'infinity_glass/rim.png', border='24', colordiffuse='$VAR[InfinityRailsBorder]')
    tag(surface, 'bordersize', '2')
    icon = control('image', 5, 28, 54, 72, 72)
    tag(icon, 'texture', '')
    tag(icon, 'aspectratio', 'keep')
    for cid, y, font, label, color in [(6, 24, 'InfinityBodyBold', '$INFO[Window.Property(Rails.Title)]', 'Text'),
                                       (7, 78, 'InfinitySmall', '$INFO[Window.Property(Rails.Subtitle)]', 'Secondary')]:
        c = control('label', cid, 120, y, 530, 52)
        for n, value in [('font', font), ('label', label), ('textcolor', '$VAR[InfinityRails' + color + ']'), ('aligny', 'center'), ('scroll', 'true')]:
            tag(c, n, value)
    close = control('button', 9, 674, 24, 64, 64)
    tag(close, 'label', '')
    tag(close, 'texturefocus', 'infinity_legacy/close_focus.png', colordiffuse='$VAR[InfinityRailsAccent]')
    tag(close, 'texturenofocus', 'infinity_legacy/close.png', colordiffuse='$VAR[InfinityRailsText]')
    for d in ['onleft', 'onright', 'onup', 'ondown']:
        tag(close, d, '200')
    for i in range(5):
        c = control('button', 200 + i, 24, 160 + i * 100, 712, 96)
        for n, value in [('label', ''), ('font', 'InfinityBody'), ('align', 'left'), ('aligny', 'center'), ('textoffsetx', '24'), ('textcolor', '$VAR[InfinityRailsText]'), ('focusedcolor', '$VAR[InfinityRailsText]'), ('disabledcolor', '$VAR[InfinityRailsSecondary]'), ('scroll', 'true')]:
            tag(c, n, value)
        tag(c, 'texturefocus', 'infinity_glass/focus.png', border='16', colordiffuse='$VAR[InfinityRailsAccent]')
        tag(c, 'texturenofocus', 'infinity_glass/field.png', border='16', colordiffuse='$VAR[InfinityRailsField]')
        tag(c, 'onup', str(9 if i == 0 else 199 + i))
        tag(c, 'ondown', str(9 if i == 4 else 201 + i))
        tag(c, 'onleft', '9'); tag(c, 'onright', '9')
    for cid, x, label in [(210, 24, 'Previous'), (211, 556, 'Next')]:
        c = control('button', cid, x, 660, 180, 88)
        for n, value in [('label', label), ('font', 'InfinitySmall'), ('textcolor', '$VAR[InfinityRailsText]'), ('focusedcolor', '$VAR[InfinityRailsText]'), ('disabledcolor', '$VAR[InfinityRailsSecondary]'), ('onup', '200'), ('ondown', '9')]:
            tag(c, n, value)
        tag(c, 'texturefocus', 'infinity_glass/focus.png', border='16', colordiffuse='$VAR[InfinityRailsAccent]')
        tag(c, 'texturenofocus', 'infinity_glass/field.png', border='16', colordiffuse='$VAR[InfinityRailsField]')
        tag(c, 'onleft', '9' if cid == 210 else '210'); tag(c, 'onright', '211' if cid == 210 else '9')
    c = control('label', 212, 208, 660, 344, 88)
    for n, value in [('label', ''), ('font', 'InfinitySmall'), ('textcolor', '$VAR[InfinityRailsSecondary]'), ('align', 'center'), ('aligny', 'center')]:
        tag(c, n, value)
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def patch_home(raw):
    text = raw.decode('utf-8')
    text = text.replace('<window>', '<window>\n  <onload>ClearProperty(Infinity.Rails.Focused,home)</onload>', 1)
    for cid in CONTROLS:
        marker = re.compile(r'(<control type="(?:panel|fixedlist)" id="' + str(cid) + r'">)')
        if len(marker.findall(text)) != 1:
            raise ValueError('Unexpected rail control: ' + str(cid))
        hooks = '\n        <onfocus>SetProperty(Infinity.Rails.Focused,' + str(cid) + ',home)</onfocus>\n        <onunfocus>ClearProperty(Infinity.Rails.Focused,home)</onunfocus>'
        text = marker.sub(lambda m: m[1] + hooks, text)
    # No gesture thresholds/keymaps/onclick/geometry are replaced.
    return text.encode()


def patch_context(raw):
    text = raw.decode('utf-8')
    # Leave all original controls/labels/textures intact for unrelated contexts.
    # Core still owns long-press detection. Only a selected Rails item is routed.
    text = text.replace('<window>', '<window>\n  <onload condition="' + ROUTE + '">RunScript(script.infinity.rails,context)</onload>', 1)
    if text.count('<controls>') != 1:
        raise ValueError('Unexpected context owner.')
    text = text.replace('<controls>', '<controls>\n    <control type="group">\n      <visible>![' + ROUTE + ']</visible>', 1)
    text = text.replace('</controls>', '    </control>\n  </controls>', 1)
    ET.fromstring(text)
    return text.encode()


def zip_tree(root, target):
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc', '.pyo'):
                continue
            item = ZipInfo(root.name + '/' + p.relative_to(root).as_posix(), date_time=(2026, 10, 14, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, p.read_bytes())


def build():
    assert sha(BASE.read_bytes()) == BASE_SHA, 'Refused unknown baseline'
    with ZipFile(BASE) as z:
        before = {n[len('skin.infinity.diggz/'):]: z.read(n) for n in z.namelist() if n.startswith('skin.infinity.diggz/') and not n.endswith('/')}
    assert ET.fromstring(before['addon.xml']).get('version') == '1.0.5.215'
    after = dict(before)
    m = json.loads((RC2 / 'manifest.json').read_text())
    assert m['base_package_sha256'] == BASE_SHA
    for name, record in m['files'].items():
        assert record['before'] == (sha(before[name]) if name in before else None)
        raw = (RC2 / 'objects' / record['after']).read_bytes()
        assert sha(raw) == record['after']
        after[name] = raw
    for profile in PROFILES:
        name = profile + '/Home.xml'
        after[name] = patch_home(after[name])
        inc = profile + '/Includes_InfinityRails.xml'
        text = after[inc].decode().replace('Infinity.Rails.Revision', 'Infinity.Rails.movies.Revision', 1)
        text = text.replace('Infinity.Rails.Revision', 'Infinity.Rails.tvshows.Revision', 1)
        after[inc] = text.replace('</includes>', variables() + '\n</includes>').encode()
        ctx = profile + '/DialogContextMenu.xml'
        after[ctx] = patch_context(after[ctx])
        after[profile + '/DialogInfinityRails.xml'] = dialog_xml()
    xml = after['addon.xml'].decode().replace('version="1.0.5.216"', 'version="1.0.5.217"', 1)
    xml = xml.replace('</requires>', '    <import addon="script.infinity.rails" version="0.1.2"/>\n  </requires>', 1)
    xml = re.sub(r'<description lang="en_GB">.*?</description>', '<description lang="en_GB">Infinity 1.0.5.217 Custom Rails RC3 TEST. Full skin update from exact .215 with RC2 rails preserved. Dedicated long-press menu, all four modes, atomic saved choices. Physical-device acceptance pending. NOT LOCKED.</description>', xml, count=1, flags=re.S)
    after['addon.xml'] = xml.encode()
    for name in ['infinity-skin.json', 'Infinity-Protected-Manifest.json']:
        data = json.loads(after[name])
        data['skin_version'], data['candidate'], data['candidate_locked'] = '1.0.5.217', 217, False
        for key in ['version', 'candidate_version']:
            if key in data:
                data[key] = '1.0.5.217'
        if 'candidate_name' in data:
            data['candidate_name'] = 'Custom Rails RC3 TEST'
        data['custom_addon_rails_217'] = dict(base_version='1.0.5.215', base_sha256=BASE_SHA,
            baseline_record_commit='85b1305ef7a220dd23aaeb40c7d38150b8da4a92',
            rc2_record_commit='faae58d7594b8be1e423e119ddd1e1c9839767fd',
            helper_version='0.1.2', full_skin=True, device_verified=False, locked=False,
            native_changed=False, user_data_migrated=False)
        for path in data.get('protected_files', {}):
            if path in after and path not in ['infinity-skin.json', 'Infinity-Protected-Manifest.json']:
                data['protected_files'][path] = sha(after[path])
        after[name] = (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()
    if SKIN.exists():
        shutil.rmtree(SKIN)
    for name, raw in after.items():
        target = SKIN / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    fallback = HELPER / 'resources/skins/Default/1080i/DialogInfinityRails.xml'
    fallback.parent.mkdir(parents=True, exist_ok=True)
    fallback.write_bytes(dialog_xml())
    OUT.mkdir(parents=True, exist_ok=True)
    full = OUT / 'skin.infinity.diggz-1.0.5.217-Custom-Rails-RC3-TEST.zip'
    helper = OUT / 'script.infinity.rails-0.1.2-RC3-TEST.zip'
    zip_tree(SKIN, full); zip_tree(HELPER, helper)
    changed = [n for n in before if after[n] != before[n]]
    added = sorted(set(after) - set(before))
    record = dict(baseline_version='1.0.5.215', baseline_sha256=BASE_SHA,
                  baseline_record_commit='85b1305ef7a220dd23aaeb40c7d38150b8da4a92',
                  rc2_record_commit='faae58d7594b8be1e423e119ddd1e1c9839767fd',
                  candidate_version='1.0.5.217', helper_version='0.1.2',
                  original_files=len(before), changed_existing=len(changed),
                  unchanged_original=len(before)-len(changed), deleted=[], new_files=added,
                  changed_files=sorted(changed), profiles=PROFILES, native_changed=False,
                  physical_device_verified=False, live_kodi_verified=False, locked=False,
                  packages={p.name:dict(sha256=sha(p.read_bytes()), bytes=p.stat().st_size) for p in [full, helper]})
    (OUT / 'preservation.json').write_text(json.dumps(record, indent=2) + '\n')
    (OUT / 'skin-file-sha256.json').write_text(json.dumps({n:sha(b) for n,b in after.items()}, sort_keys=True, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    build()
