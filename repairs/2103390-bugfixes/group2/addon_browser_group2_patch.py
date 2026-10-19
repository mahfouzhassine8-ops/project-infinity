#!/usr/bin/env python3
"""Infinity Group #2 Add-on Browser: signed 2103390 skin-only candidate.

EXACT SCOPE: the original 14 skin.infinity.diggz layouts, and only their
AddonBrowser.xml, Includes_InfinityBrowser223.xml and FileBrowser.xml.

No native Kodi changes, no other skin screens, no third-party addons,
no installed addon state changes, no package/build/signing changes.

This script only computes/stages asset bytes in a separate output directory.
The original signed APK remains immutable. Reject unfamiliar APKs.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SIGNED_BASE_SHA256 = '778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'
SKIN_PREFIX = 'assets/addons/skin.infinity.diggz/'
FILES = ('AddonBrowser.xml', 'Includes_InfinityBrowser223.xml', 'FileBrowser.xml')
ORIGINAL_MEMBER_COUNT = 7430
EXPECTED_LAYOUTS = {
    '16x9', '20x9', '5x6', '6x5', 'fallback', 'portrait', 'unified',
    'responsive/base', 'responsive/landscape', 'responsive/portrait',
    'responsive/square', 'responsive/tall', 'responsive/ultrawide',
    'responsive/wide',
}

HEADER_ARC = (b'<control type="image"><right>0</right><top>0</top><width>62%</width><height>160</height>'
              b'<texture colordiffuse="$VAR[InfinityPaletteAccent]">infinity_browser/header_arc.png'
              b'</texture></control>')
WRONG_HELP = 'Select “Install from zip file” here to enter Kodi’s native file picker.'.encode('utf8')
CONTEXT_HELP = b'$VAR[InfinityAddonBrowserHint]'
OLD_FOCUS = b'<onleft>50</onleft>\n      <onright>50</onright>'
NEW_FOCUS = b'<onleft>50</onleft>\n      <onright>9096</onright>'

# Actual Kodi Omega CAddonsDirectory paths. Use existing native directory,
# keyboard and installer (not new handlers). A dynamic fallback covers nested
# repository categories and paths from add-ons we do not control.
NEW_INCLUDE = '''  <variable name="InfinityAddonBrowserHint">
    <value condition="String.StartsWith(Container.FolderPath,addons://user/)">My add-ons: select an installed add-on to review its available actions.</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://outdated/)">Available updates: review the selected add-on before choosing an update.</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://recently_updated/)">Recently updated: browse add-ons and open one for its details.</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://repos/)">Install from repository: choose a repository to browse its add-ons.</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://search/)">Search: Kodi provides the original search keyboard and add-on results.</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://install/)">Install from zip file: Kodi opens its native ZIP file picker.</value>
    <value condition="String.IsEqual(Container.FolderPath,addons://)">Choose a category to browse add-ons, updates, repositories or search.</value>
    <value>Browse this Kodi add-on section and select an item for its next action.</value>
  </variable>
  <variable name="InfinityAddonBrowserFooter">
    <value condition="String.StartsWith(Container.FolderPath,addons://user/)">My add-ons | Enable and Disable are different from hiding an item</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://outdated/)">Available updates | Review before installing updates</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://recently_updated/)">Recently updated | View installed add-on details</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://repos/)">Repositories | Browse available add-ons</value>
    <value condition="String.StartsWith(Container.FolderPath,addons://search/)">Search | Kodi's original input and results</value>
    <value condition="String.IsEqual(Container.FolderPath,addons://)">Kodi Add-on Browser | Select an item • BACK returns</value>
    <value>Kodi Add-on Browser | Select an item • BACK returns</value>
  </variable>
'''.encode('utf8')

# Existing footer art remains. Only the four false, non-functional navigation
# labels and their decorative separators become one truthful status label.
FOOTER_RE = re.compile(
    rb'(?P<background><control type="image"><left>2\.5%</left><right>2\.5%</right>'
    rb'<(?P<position>top|bottom)>[^<>]+</(?P=position)><height>78</height>'
    rb'<texture colordiffuse="\$VAR\[InfinityBrowserFooter\]" border="18">'
    rb'infinity_browser/footer\.png</texture></control>)'
    rb'(?P<old>.*?)(?=</controls>\s*</window>)', re.DOTALL)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _replace_once(data: bytes, old: bytes, new: bytes, message: str) -> bytes:
    if data.count(old) != 1:
        raise ValueError(f'{message}: expected exactly one preimage, got {data.count(old)}')
    if new and new in data:
        raise ValueError(f'{message}: already changed')
    return data.replace(old, new, 1)


def patch_addon_browser(data: bytes) -> bytes:
    # Preserve original Infinity logo, BACK, content control id50, artwork and
    # native six categories exactly; no fake tappable controls are introduced.
    data = _replace_once(data, HEADER_ARC, b'', 'blue-slash header art')
    data = _replace_once(data, WRONG_HELP, CONTEXT_HELP, 'out-of-context ZIP-only instruction')
    data = _replace_once(data, OLD_FOCUS, NEW_FOCUS, 'right navigation to existing BACK control')
    matches = list(FOOTER_RE.finditer(data))
    if len(matches) != 1:
        raise ValueError('Unexpected native Add-on Browser footer layout')
    match = matches[0]
    original = match.group('old')
    expected = (b'<label>INSTALL ZIP</label>', b'<label>REPOSITORIES</label>',
                b'<label>UPDATES</label>', b'<label>DEPENDENCIES</label>')
    if any(original.count(label) != 1 for label in expected):
        raise ValueError('Unexpected four original misleading footer labels')
    if original.count(b'<control type="label">') != 4 or original.count(b'<control type="image">') != 3:
        raise ValueError('Footer has additional controls; refuse broad removal')
    if b'<onclick' in original or b'<visible' in original or b' id=' in original:
        raise ValueError('Footer contains real interaction, cannot replace')
    position = match.group('position')
    offset = b'26' if position == b'bottom' else b'94.05%'
    replacement = (b'<control type="label"><left>5%</left><width>90%</width><'
                   + position + b'>' + offset + b'</' + position + b'>'
                   + b'<height>44</height><align>center</align><aligny>center</aligny>'
                   + b'<font>InfinityTiny</font><textcolor>$VAR[InfinityDiggzSecondaryText]</textcolor>'
                   + b'<label>$VAR[InfinityAddonBrowserFooter]</label></control>')
    data = data[:match.start('old')] + replacement + data[match.end('old'):]
    root = ET.fromstring(data)
    controls = root.find('controls')
    if controls is None: raise ValueError('No original control tree')
    original_list = root.find('.//control[@id="50"]')
    back = root.find('.//control[@id="9096"]')
    if original_list is None or original_list.get('type') != 'panel' or back is None:
        raise ValueError('Lost original Kodi add-on browser focus/control')
    if original_list.findtext('onright') != '9096' or back.findtext('onleft') != '50':
        raise ValueError('Back navigation focus contract changed')
    if len(root.findall('.//control[@id="50"]')) != 1:
        raise ValueError('Duplicate native Add-on Browser panel')
    if root.find('.//control[@id="9096"]/onclick') is None or back.findtext('onclick') != 'PreviousMenu':
        raise ValueError('Original Back activation changed')
    return data


def patch_includes(data: bytes) -> bytes:
    if b'InfinityAddonBrowserHint' in data or b'InfinityAddonBrowserFooter' in data:
        raise ValueError('Already patched or conflicting browser variables')
    data = _replace_once(data, b'</includes>', NEW_INCLUDE + b'</includes>', 'browser include footer')
    parsed = ET.fromstring(data)
    for name in ('InfinityAddonBrowserHint', 'InfinityAddonBrowserFooter'):
        var = parsed.find("./variable[@name='"+name+"']")
        if var is None or not var.findall('value'):
            raise ValueError('Missing contextual browser variable')
    return data


def patch_file_browser(data: bytes) -> bytes:
    # The ZIP list->right action was routing via scrollbar 61. When scrollbar
    # is not focusable on a one-page list, right-side buttons are unreachable
    # until the selection opens. Use existing native OK button 413 directly.
    for control_id in ('450', '451'):
        opening = f'<control type="list" id="{control_id}">'.encode()
        if data.count(opening) != 1: raise ValueError('Expected native picker list '+control_id)
        a = data.index(opening)
        b = data.index(b'<itemlayout', a)
        before = data[a:b]
        fixed = _replace_once(before, b'<onright>61</onright>', b'<onright>413</onright>', 'native ZIP list right focus '+control_id)
        data = data[:a] + fixed + data[b:]
    root = ET.fromstring(data)
    for control_id in ('450', '451'):
        control = root.find(f".//control[@id='{control_id}']")
        if control is None or control.findtext('onright') != '413':
            raise ValueError('ZIP picker existing side action not reachable')
    ok = root.find(".//control[@id='413']")
    if ok is None or ok.get('type') != 'button':
        raise ValueError('Original ZIP picker OK button disappeared')
    if root.find(".//control[@id='9410']") is None:
        raise ValueError('Original compact native preview button disappeared')
    return data

PATCHERS = {'AddonBrowser.xml': patch_addon_browser,
            'Includes_InfinityBrowser223.xml': patch_includes,
            'FileBrowser.xml': patch_file_browser}


def candidate_map(original_apk: Path) -> dict[str, bytes]:
    original_apk = Path(original_apk)
    if sha(original_apk.read_bytes()) != SIGNED_BASE_SHA256:
        raise ValueError('Protected original 2103390 APK SHA does not match')
    staged: dict[str, bytes] = {}
    with ZipFile(original_apk) as apk:
        names=apk.namelist()
        if len(names) != ORIGINAL_MEMBER_COUNT or len(set(names)) != ORIGINAL_MEMBER_COUNT:
            raise ValueError('Original signed APK member inventory is different')
        selected=[name for name in names if name.startswith(SKIN_PREFIX)
                  and any(name.endswith('/'+f) for f in FILES)]
        found_layouts={n[len(SKIN_PREFIX):].rsplit('/', 1)[0] for n in selected}
        if found_layouts != EXPECTED_LAYOUTS or len(selected) != 42:
            raise ValueError('Unknown original Infinity Browser layout inventory')
        for n in selected:
            which=n.rsplit('/',1)[-1]
            original=apk.read(n)
            modified=PATCHERS[which](original)
            if original==modified: raise ValueError('Missing expected browser correction in '+n)
            staged[n]=modified
    if len(staged) != 42: raise ValueError('Unexpected file count')
    return staged


def staged_inventory(original_apk: Path) -> dict:
    staged=candidate_map(original_apk)
    with ZipFile(original_apk) as z:
        allnames=z.namelist()
        changed=[{'path':p,'before_sha256':sha(z.read(p)),'after_sha256':sha(data)}
                 for p,data in sorted(staged.items())]
        if any(x['before_sha256']==x['after_sha256'] for x in changed):
            raise ValueError('Unchanged asset on intended changed list')
        return {'source_apk_sha256':SIGNED_BASE_SHA256,'base_members':len(allnames),
                'proposed_changed_members':len(changed),
                'unchanged_original_members':len(allnames)-len(changed),
                'changed':changed,'source_only':True,'signed_apk_built':False,
                'physical_fold_verified':False}


def stage(original_apk: Path, destination_dir: Path) -> dict:
    original_apk=Path(original_apk).resolve()
    destination_dir=Path(destination_dir).resolve()
    if str(destination_dir)==str(original_apk.parent) or original_apk.is_relative_to(destination_dir):
        raise ValueError('Refusing to write next to/over protected signed original')
    data=candidate_map(original_apk)
    for rel,content in data.items():
        path=destination_dir/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
    return staged_inventory(original_apk)


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser()
    parser.add_argument('signed_original_apk',type=Path)
    parser.add_argument('--stage-to',type=Path,default=None)
    args=parser.parse_args()
    receipt=(stage(args.signed_original_apk,args.stage_to)
             if args.stage_to else staged_inventory(args.signed_original_apk))
    print(json.dumps(receipt,indent=2))
