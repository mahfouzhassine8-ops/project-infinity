#!/usr/bin/env python3
"""Create a DISPOSABLE Kodi render profile; never updates a shipped skin ZIP.

The tested preview XML/controller/assets are byte-identical source copies.
Test-only addon dependencies, resolution, Home and startup are adapted to run a
desktop binary without activating any provider/service. See harness-receipt.json.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(args):
    profile = args.profile.resolve()
    assert not profile.exists(), 'Disposable profile must be new'
    manifest = json.loads((HERE / 'fixture-manifest.json').read_text())
    blob = base64.b64decode(''.join(p.read_text() for p in sorted(HERE.glob('fixture-*.b64'))), validate=True)
    assert sha(blob) == manifest['fixture_sha256']
    skin = profile / 'addons/skin.infinity.diggz'
    with zipfile.ZipFile(io.BytesIO(blob)) as source:
        assert set(source.namelist()) == set(manifest['files'])
        for name, digest in manifest['files'].items():
            data = source.read(name)
            assert sha(data) == digest, name
            dest = skin / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    overlaid = {}
    if args.overlay:
        overlay = args.overlay.resolve()
        assert overlay.is_dir()
        for path in overlay.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                rel = path.relative_to(overlay)
                dest = skin / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                data = path.read_bytes()
                dest.write_bytes(data)
                overlaid[rel.as_posix()] = sha(data)
    userdata = profile / 'userdata'
    userdata.mkdir(parents=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    chosen = profile / 'selected-files/infinity-render-fixture.zip'
    chosen.parent.mkdir()
    with zipfile.ZipFile(chosen, 'w', compression=zipfile.ZIP_DEFLATED) as target:
        target.writestr('plugin.video.infinity.render.fixture/addon.xml',
            '<addon id="plugin.video.infinity.render.fixture" name="Infinity Preview Test" '
            'version="6.2.4" provider-name="Infinity renderer fixture">'
            '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
            '<extension point="xbmc.python.pluginsource" library="main.py"><provides>video</provides></extension>'
            '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Real ZIP metadata fixture</summary>'
            '<description lang="en_GB">Desktop renderer test archive; no code is executed.</description>'
            '<platform>all</platform></extension></addon>')
        target.writestr('plugin.video.infinity.render.fixture/main.py', '# Never executed or installed by this harness.\n')
    # Record all source copies before modifying ONLY test infrastructure.
    selected = {p.relative_to(skin).as_posix(): sha(p.read_bytes()) for p in skin.rglob('*') if p.is_file()}
    addon = ET.fromstring((skin / 'addon.xml').read_bytes())
    requires = addon.find('requires')
    requires.clear()
    ET.SubElement(requires, 'import', {'addon': 'xbmc.gui', 'version': '5.17.0'})
    ET.SubElement(requires, 'import', {'addon': 'xbmc.python', 'version': '3.0.0'})
    extension = addon.find("extension[@point='xbmc.gui.skin']")
    extension.clear()
    extension.set('point', 'xbmc.gui.skin')
    ET.SubElement(extension, 'res', {'width': str(args.width), 'height': str(args.height),
                 'aspect': str(args.width) + ':' + str(args.height), 'default': 'true', 'folder': 'unified'})
    ET.ElementTree(addon).write(skin / 'addon.xml', encoding='UTF-8', xml_declaration=True)
    (skin / 'unified/Home.xml').write_text('''<window><defaultcontrol>1</defaultcontrol>
<onload condition="!Window(Home).Property(RenderHarnessStarted)">RunScript(special://profile/render_probe.py)</onload>
<controls><control type="image"><left>0</left><top>0</top><width>100%</width><height>100%</height>
<texture colordiffuse="FF101923">infinity_ui/contract_white.png</texture></control>
<control type="button" id="1"><left>10</left><top>10</top><width>400</width><height>42</height>
<label>Kodi desktop renderer — disposable fixture</label><font>InfinityTiny</font></control></controls></window>''')
    # The stock native browser supplies controls; its standard skin layout remains
    # the exact candidate FileBrowser XML from the fixture/overlay.
    (userdata / 'guisettings.xml').write_text('''<settings version="2">
<setting id="lookandfeel.skin">skin.infinity.diggz</setting>
<setting id="lookandfeel.font">Default</setting>
<setting id="lookandfeel.skinzoom">0</setting>
<setting id="videoscreen.screenmode">DESKTOP</setting>
<setting id="screensaver.mode"></setting>
<setting id="services.zeroconf">false</setting>
<setting id="services.upnpserver">false</setting>
<setting id="services.upnprenderer">false</setting>
<setting id="locale.language">resource.language.en_gb</setting>
<setting id="eventlog.enabled">false</setting>
<!-- Kodi21.3 requires a resolutions element; without it the entire GUI settings
     file is rejected and Kodi silently switches to Estuary, preventing this
     isolated Infinity renderer probe from ever starting. -->
<resolutions />
<viewstates />
</settings>''')
    (userdata / 'advancedsettings.xml').write_text('<advancedsettings><loglevel hide="true">1</loglevel><splash>false</splash></advancedsettings>')
    config = {'theme': args.theme, 'width': args.width, 'height': args.height,
              'dp_width': args.dp_width, 'dp_height': args.dp_height,
              'output': str(output), 'selected_zip': str(chosen), 'label': args.label,
              'skin': str(skin), 'controller_sha256': selected['resources/lib/infinity_file_preview.py'],
              'preview_xml_sha256': selected['unified/InfinityFilePreview.xml']}
    (userdata / 'render-config.json').write_text(json.dumps(config, indent=2))
    shutil.copyfile(HERE / 'probe.py', userdata / 'render_probe.py')
    receipt = {'kind': 'Actual Kodi desktop WindowXMLDialog renderer, simulated native request',
               'physical_device_verified': False, 'android_dispatch_verified': False,
               'fixture_parent_sha256': manifest['parent_sha256'], 'test_only_modified_files': ['addon.xml', 'unified/Home.xml'],
               'source_file_sha256': selected, 'overlaid_sha256': overlaid, 'config': config,
               'notes': ['Kodi21.3 Linux does not contain Infinity Android adaptive-native patches.',
                         'Logical canvas and dp metrics are explicitly supplied test inputs.',
                         'Real FileBrowser window; preview request properties are injected, not generated by a touch gesture.',
                         'No archive content is executed and no Install action is sent.']}
    (output / 'harness-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(profile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--overlay', type=Path)
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--height', type=int, default=2400)
    parser.add_argument('--dp-width', type=int, default=360)
    parser.add_argument('--dp-height', type=int, default=800)
    parser.add_argument('--theme', choices=['dark', 'light', 'OLED', 'cinema'], default='dark')
    parser.add_argument('--label', default='before-210')
    prepare(parser.parse_args())
