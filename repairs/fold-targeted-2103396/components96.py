"""Exact-source corrective overlay over signed 2103395; no profile mutations."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'fold-critical-2103395'))
import components95 as prior
from native94 import require, once

PARENT = '89545ab1b5a3898b98509e3377ab07602e102056a6c3e4bc757248916bac543e'
COMMIT = 'f1d32c1bc74c61d4166780eec34f59c349204dc9'
CC, UI, WB, SKIN, HEALTH = prior.CC, prior.UI, prior.WB, prior.SKIN, prior.HEALTH
PACKAGES = [(CC, '0.3.5.25', '0.3.5.26'), (UI, '0.1.7', '0.1.8'),
            (WB, '1.0.6', '1.0.7'), (SKIN, '1.0.5.232', '1.0.5.233'),
            (HEALTH, '2.5.22', '2.5.23'), ('script.infinity.rails', '0.2.7', '0.2.7')]
sha = prior.sha
digest = prior.digest
evidence_manifest = prior.evidence_manifest


def read_parent(apk):
    require(digest(apk) == PARENT, 'exact permanently signed 2103395 APK required')
    with ZipFile(apk) as z:
        require(len(z.namelist()) == len(set(z.namelist())) and z.testzip() is None,
                'duplicate or damaged parent APK')
        return {n[14:]: z.read(n) for n in z.namelist()
                if n.startswith('assets/addons/') and not n.endswith('/') and
                n.split('/')[2] in {a for a, _, _ in PACKAGES}}


def xml_bytes(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def popup_xml(raw):
    root = ET.fromstring(raw)
    card = root.find('.//control[@id="100"]')
    require(card is not None, 'original Option B card absent')
    # Python owns all geometry. Remove the old center/right/bottom constraints,
    # which otherwise keep competing with setPosition/setWidth/setHeight.
    for ctrl in (card, *card.findall('control')):
        for name in ('centerleft', 'centertop', 'right', 'bottom'):
            for node in ctrl.findall(name):
                ctrl.remove(node)
    close = root.find('.//control[@id="9"]')
    close.find('label').text = '×'
    for name in ('texturefocus', 'texturenofocus'):
        close.find(name).text = 'infinity_glass/field.png'
        close.find(name).set('border', '16')
    for tag, value in [('font', 'InfinityBodyBold'), ('align', 'center'),
                       ('aligny', 'center'), ('textcolor', '$VAR[InfinityLegacyText]')]:
        node = close.find(tag)
        if node is None:
            node = ET.SubElement(close, tag)
        node.text = value
    for ident in (101, 102, 103, 104):
        root.find('.//control[@id="%d"]/font' % ident).text = 'InfinitySmall'
    return xml_bytes(root)


def popup_runtime(raw):
    start = raw.index(b'def geometry(')
    end = raw.index(b'\ndef _rpc(', start)
    raw = raw[:start] + (HERE / 'popup_geometry.py').read_bytes() + b'\n\n' + raw[end:]
    raw = once(raw,
        b"            bounds=geometry(background.getWidth(),background.getHeight())",
        b"            bounds=geometry(background.getWidth(),background.getHeight(),\n"
        b"                xbmc.getInfoLabel('System.ScreenWidth'), xbmc.getInfoLabel('System.ScreenHeight'))")
    raw = once(raw, b"            for ident,coords in zip((101,102,103,104),bounds['buttons']):",
        b"            for ident,key in ((110,'surface'),(111,'surface'),(9,'close')):\n"
        b"                ctrl=self.getControl(ident)\n"
        b"                xx,yy,ww,hh=bounds[key]\n"
        b"                ctrl.setPosition(xx,yy);ctrl.setWidth(ww);ctrl.setHeight(hh)\n"
        b"            for ident,coords in zip((101,102,103,104),bounds['buttons']):")
    return raw


# Keep the existing explicit preference and effective theme contract. Extend
# only Infinity surface tokens; cyan focus, artwork and text are untouched.
OLED_SURFACES = prior.old.OLED_SURFACES | {
    'InfinityBoardPanel', 'InfinityBoardPanelSoft', 'InfinityBoardSurface',
    'InfinityDirectorySurface', 'InfinityDirectorySurfaceSoft',
    'InfinityDrawerQuietRow', 'InfinityToastSurface', 'InfinityGlassSurface',
    'InfinityGlassSurfaceSoft', 'InfinityGlassSurfaceStrong',
    'InfinityBrowserSurface', 'InfinityBrowserCard', 'InfinityBrowserBackground',
    'InfinityDialogBackground', 'InfinityDialogPanel', 'InfinityMenuSurface',
}


def oled(raw):
    root = ET.fromstring(raw)
    changed = False
    for node in root.findall('variable'):
        if node.get('name') in OLED_SURFACES:
            matching = [n for n in node.findall('value')
                        if n.get('condition') == prior.old.OLED_CONDITION]
            if matching:
                require(len(matching) == 1, 'ambiguous OLED condition')
                matching[0].text = 'FF000000'
            else:
                child = ET.Element('value', {'condition': prior.old.OLED_CONDITION})
                child.text = 'FF000000'
                node.insert(0, child)
            changed = True
    return xml_bytes(root) if changed else raw


def ambient_experience(raw):
    # Home's active featured panels have their own selected ListItem. Global
    # ListItem follows the navigation/add-on row and frequently has no fanart.
    # Use existing displayed artwork only; no resolver, cache or network task.
    raw = once(raw, b"            sig = (focus, route, title, self.label('ListItem.Art(fanart)'), tier, ambient)",
        b"            art = self.label('ListItem.Art(fanart)')\n"
        b"            section = self.label('Container(9000).ListItem.Property(section)')\n"
        b"            panels = {'movies': (8101, 8801), 'tvshows': (8102, 8802)}\n"
        b"            if not art:\n"
        b"                for panel in panels.get(section, ()):\n"
        b"                    if self.xbmc.getCondVisibility('Control.IsVisible(%d)' % panel):\n"
        b"                        art = self.label('Container(%d).ListItem.Art(fanart)' % panel)\n"
        b"                        if not art:\n"
        b"                            art = self.label('Container(%d).ListItem.Art(poster)' % panel)\n"
        b"                        if art:\n"
        b"                            break\n"
        b"            sig = (focus, route, title, art, tier, ambient)")
    raw = once(raw, b"                self.publish('AmbientHome.Art', artwork(sig[3], tier, True) if ambient != 'off' else '')",
        b"                submitted = artwork(sig[3], tier, True) if ambient != 'off' else ''\n"
        b"                self.publish('AmbientHome.Art', submitted)\n"
        b"                self.publish('AmbientHome.SubmittedMode', ambient if submitted else 'off')")
    raw = once(raw, b"for name in ('AmbientHome.Art', 'Preload.One', 'Preload.Two'):",
        b"for name in ('AmbientHome.Art', 'AmbientHome.SubmittedMode', 'Preload.One', 'Preload.Two'):")
    return raw


def ambient_worker(raw):
    # Native BeginAndroidCheckpoint already sends this worker the normal
    # cooperative abort latch. Its writes are the temp lock and memfd textures.
    # Publish lifecycle facts, and clear them only after the existing cleanup.
    raw = once(raw, b"    monitor, observer = xbmc.Monitor(), Observer()",
        b"    monitor, observer = xbmc.Monitor(), Observer()\n"
        b"    home.setProperty(PREFIX+'WriterLifecycle', 'running-optional')")
    raw = once(raw, b"    finally:\n        DialogMirror.clear()",
        b"    finally:\n        home.setProperty(PREFIX+'WriterLifecycle', 'stopping-optional')\n"
        b"        DialogMirror.clear()")
    raw = once(raw, b"        lock.close()\n\n\n", b"        lock.close()\n"
        b"        home.setProperty(PREFIX+'Status', 'stopped')\n"
        b"        home.setProperty(PREFIX+'WriterLifecycle', 'stopped')\n\n\n")
    return raw


def health_ambient(raw):
    marker = b'    return result\n\n\ndef native_roots()'
    require(raw.count(marker) == 1, 'Health environment boundary differs')
    extra = b'''    # Setting readback is not evidence that pixels were rendered.
    try:
        home = xbmcgui.Window(10000)
        saved = xbmcaddon.Addon('script.infinity.commandcenter').getSetting('ambient_home')
        result['ambient_home'] = {
            'saved_mode': saved,
            'published_mode': home.getProperty('Infinity.AmbientHome.Mode'),
            'artwork_submitted_mode': home.getProperty('Infinity.AmbientHome.SubmittedMode'),
            'artwork_backdrop_visible': bool(xbmc.getCondVisibility('Control.IsVisible(29860)')),
            'artwork_available': bool(home.getProperty('Infinity.AmbientHome.Art')),
            'native_renderer_status': home.getProperty('Infinity.NativeAmbient.Status'),
            'native_renderer_active': home.getProperty('Infinity.NativeAmbient.Active'),
            'optional_writer_lifecycle': home.getProperty('Infinity.NativeAmbient.WriterLifecycle'),
            'renderer_applied_mode': 'unverified',
            'physical_visual_verified': False,
            'healthy_from_setting_equality': False,
        }
    except (RuntimeError, TypeError):
        result['ambient_home'] = {'renderer_applied_mode': 'unavailable',
                                  'physical_visual_verified': False}
'''
    return once(raw, marker, extra + marker)


def components(original):
    final = dict(original)
    # Proven in both signed bytes and the failing Fold session log. Installer
    # version receipts are not resident participant registration receipts.
    final[CC + '/checkpoint_runtime.py'] = once(original[CC + '/checkpoint_runtime.py'],
        b'ADDON_VERSION = "0.3.5.23"', b'ADDON_VERSION = "0.3.5.26"')
    final[CC + '/experience.py'] = ambient_experience(original[CC + '/experience.py'])
    key = SKIN + '/resources/lib/infinity_native_ambient.py'
    final[key] = ambient_worker(original[key])
    final[HEALTH + '/khc_kodi.py'] = health_ambient(original[HEALTH + '/khc_kodi.py'])
    final[UI + '/home_option_b.py'] = popup_runtime(original[UI + '/home_option_b.py'])
    name = UI + '/resources/skins/Default/1080i/InfinityHomeOptionB.xml'
    popup = popup_xml(original[name])
    final[name] = popup
    # Resolve from the active Infinity skin's actual canvas, rather than an
    # add-on's forced 1920x1080 fallback stretched over a portrait window.
    final[SKIN + '/unified/InfinityHomeOptionB.xml'] = popup
    for name, raw in original.items():
        if name.startswith(SKIN + '/') and name.endswith('.xml') and b'<variable ' in raw:
            final[name] = oled(raw)
    for addon, old, version in PACKAGES:
        if old != version:
            key = addon + '/addon.xml'
            final[key] = once(final[key], ('version="' + old + '"').encode(),
                              ('version="' + version + '"').encode())
    final[WB + '/controller.py'] = once(final[WB + '/controller.py'],
        b'"0.3.5.25"', b'"0.3.5.26"')
    pins = {n.split('/', 1)[1]: sha(b) for n, b in final.items()
            if n.startswith(CC + '/') and (n.endswith('.py') or
                n.endswith('/addon.xml') or n == CC + '/resources/settings.xml')}
    for addon in (UI, WB):
        final[addon + '/CONTROLLER-PREIMAGES.json'] = (
            json.dumps(pins, sort_keys=True, indent=2) + '\n').encode()
    for leaf in ('infinity-skin.json', 'Infinity-Protected-Manifest.json'):
        key = SKIN + '/' + leaf
        data = json.loads(final[key])
        data.update(candidate=233, skin_version='1.0.5.233', candidate_locked=False)
        for field in ('version', 'candidate_version'):
            if field in data:
                data[field] = '1.0.5.233'
        if 'protected_files' in data:
            data['protected_files'] = {p: sha(final[SKIN + '/' + p]) for p in data['protected_files']}
        final[key] = (json.dumps(data, sort_keys=True, indent=2) + '\n').encode()
    for name, raw in list(final.items()):
        if name.startswith(HEALTH + '/') and name.endswith('.py'):
            final[name] = raw.replace(b'2.5.22', b'2.5.23')
        if name.endswith('.py'):
            ast.parse(final[name].decode(), filename=name)
        if name.endswith('.xml'):
            ET.fromstring(final[name])
    return final


def ledger(before, after):
    return dict(parent_apk_sha256=PARENT, parent_source_commit=COMMIT,
        versions={a: v for a, _, v in PACKAGES},
        changed={n: dict(before=sha(before[n]) if n in before else None, after=sha(after[n]))
                 for n in sorted(after) if before.get(n) != after[n]},
        removed=sorted(set(before) - set(after)), physical_fold_verified=False, final_lock=False)


def stage(apk, out):
    before = read_parent(apk)
    after = components(before)
    require(not out.exists(), 'refusing existing stage')
    for name, body in after.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return ledger(before, after)


if __name__ == '__main__':
    print(json.dumps(stage(Path(sys.argv[1]), Path(sys.argv[2])), indent=2, sort_keys=True))
