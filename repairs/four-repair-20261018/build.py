"""Hash-pinned forward builds; untouched skin members retain identical bytes."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT_SHA = '8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235'
SKIN = 'skin.infinity.diggz/'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj

rotate = module('approved_rotate_226', HERE.parent / 'full-system-20261017/player_rotate_226.py')
Edit = module('preserved_skin_editor_225', HERE.parent / 'skin-phase-d-225/build.py').Edit

def sha(raw): return hashlib.sha256(raw).hexdigest()

def remove_display(data):
    e = Edit(data)
    rows = [c for c in e.root.iter('control') if c.findtext('label') == 'Display Mode' and
            c.findtext('onclick') == 'ActivateWindow(1197)']
    if len(rows) > 1: raise ValueError('Unexpected duplicate Display Mode row')
    for row in rows:
        start, _, _, end = e.spans[row]
        e.replace(start, end, '', 'remove only standalone Display Mode from Playback')
    return e.done(), bool(rows)

def browse_patch(data):
    e = Edit(data)
    grid = e.control('50')
    content = grid.find('content')
    assert content.text == '$INFO[Window(Home).Property(Infinity.BrowsePath)]'
    condition = '[String.IsEqual(Window(Home).Property(Infinity.BrowsePath),addons://sources/video) | String.IsEqual(Window(Home).Property(Infinity.BrowsePath),addons://sources/video/)] + System.AddonIsEnabled(script.infinity.uirepair)'
    e.attr(content, 'condition', '![' + condition + ']', 'retain all other browse routes')
    a, b, c, d = e.spans[content]
    e.replace(d, d, '\n<content target="videos" condition="' + condition + '">plugin://script.infinity.uirepair/?action=sources&amp;rev=$INFO[Window(Home).Property(Infinity.UI.GridRevision)]</content>', 'Video Sources only')
    # An explicit action uses the selected installed ID; original D-pad opens
    # directly. The new native tap path decides selection versus activation.
    start, opening, _, _ = e.spans[grid]
    e.replace(opening, opening, '\n<onclick condition="String.IsEqual(ListItem.Property(Infinity.UI.Kind),addon)">RunScript(script.infinity.uirepair,open,$INFO[ListItem.Property(Addon.ID)])</onclick>', 'installed add-on activation')
    # Separate persistent recovery control. It is not an extra top-level item
    # in the approved per-add-on menu and can never itself be hidden.
    footer = next(c for c in e.root.findall('./controls/control') if c.get('type') == 'label' and
                  c.findtext('label') == 'INFINITY BROWSE • PICK UP WHERE YOU LEFT OFF')
    a, _, _, d = e.spans[footer]
    e.replace(a, d, '''<control type="button" id="13">
      <left>10.1852%</left><bottom>8</bottom><width>87.4074%</width><height>56</height>
      <label>Restore Hidden Video Sources</label><font>InfinityTiny</font>
      <textcolor>$VAR[InfinityLegacySecondary]</textcolor><focusedcolor>$VAR[InfinityLegacyText]</focusedcolor>
      <texturefocus border="12" colordiffuse="$VAR[InfinityLegacyAccent]">infinity_glass/focus.png</texturefocus>
      <texturenofocus border="12" colordiffuse="$VAR[InfinityLegacyField]">infinity_glass/field.png</texturenofocus>
      <onclick>RunScript(script.infinity.uirepair,restore)</onclick><onup>50</onup><onleft>12</onleft><onright>50</onright>
      <visible>''' + condition + '''</visible>
    </control>''', 'reversible hide recovery')
    e.set(grid, 'ondown', '13', 'reachable recovery control')
    return e.done()

def continue_patch(data):
    e = Edit(data)
    for name in ('InfinityCompactContinueMoviesPath', 'InfinityCompactContinueTVPath'):
        var = e.root.find("variable[@name='" + name + "']")
        if var is None: continue
        value = var.find('value')
        assert 'plugin://script.infinity.commandcenter/?action=continue' in value.text
        a, opening, _, _ = e.spans[var]
        new = value.text.replace('plugin://script.infinity.commandcenter/', 'plugin://script.infinity.uirepair/').replace('&', '&amp;')
        e.replace(opening, opening, '<value condition="System.AddonIsEnabled(script.infinity.uirepair)">' + new + '</value>', 'same controller items with explicit context routing')
    return e.done()

def build(parent, out, coordinated=False):
    assert sha(parent.read_bytes()) == PARENT_SHA, 'Unverified .225 full skin'
    out.mkdir(parents=True, exist_ok=True)
    version = '1.0.5.227' if coordinated else '1.0.5.226'
    changes, removed = {}, []
    with zipfile.ZipFile(parent) as src:
        assert src.testzip() is None and len(src.namelist()) == len(set(src.namelist()))
        for name in src.namelist():
            raw = src.read(name); updated = raw
            if name == SKIN + 'unified/VideoOSD.xml':
                updated = rotate.patch_osd(updated)
                # Cyan is an explicit rotation state, independent of the theme accent.
                e = Edit(updated)
                for image in e.root.findall('.//control[@type="image"]'):
                    if image.findtext('visible') == 'Skin.HasSetting(Infinity.PlayerRotationUnlocked)':
                        e.attr(image.find('texture'), 'colordiffuse', 'FF00D9FF', 'approved cyan orientation state')
                updated = e.done()
            if name.endswith('/VideoOSD.xml'):
                updated, changed = remove_display(updated)
                if changed: removed.append(name)
            if coordinated and name.endswith('/Custom_1193_InfinityBrowse.xml'):
                # The sole active .225 layout is unified. Fallback copies remain
                # untouched, and do not acquire dependencies on a native candidate.
                if name == SKIN + 'unified/Custom_1193_InfinityBrowse.xml': updated = browse_patch(updated)
            if coordinated and name == SKIN + 'unified/Includes_InfinityHomeUnified.xml':
                updated = continue_patch(updated)
            if updated != raw: changes[name] = updated
        assert SKIN + 'unified/VideoOSD.xml' in removed
        addon = src.read(SKIN + 'addon.xml').replace(b'version="1.0.5.225"', ('version="' + version + '"').encode(), 1)
        if coordinated:
            addon = addon.replace(b'  </requires>', b'    <import addon="script.infinity.uirepair" version="0.1.0" />\n  </requires>', 1)
            changes[SKIN + 'unified/InfinityItemOptions.xml'] = (HERE / 'InfinityItemOptions.xml').read_bytes()
        changes[SKIN + 'addon.xml'] = addon
        manifest = json.loads(src.read(SKIN + 'Infinity-Protected-Manifest.json'))
        manifest.update(candidate=int(version.split('.')[-1]), candidate_version=version, skin_version=version,
                        candidate_locked=False, four_repair=dict(parent_sha256=PARENT_SHA,
                        native_required=coordinated, physical_fold_verified=False, crash_fixed=False,
                        unchanged_userdata=True))
        for name, raw in changes.items(): manifest['protected_files'][name[len(SKIN):]] = sha(raw)
        changes[SKIN + 'Infinity-Protected-Manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
        target = out / ('skin.infinity.diggz-' + version + ('-Coordinated-TEST.zip' if coordinated else '-Rotate-Playback-TEST.zip'))
        with zipfile.ZipFile(target, 'w') as dst:
            for info in src.infolist(): dst.writestr(copy.copy(info), changes.get(info.filename, src.read(info)))
            for name in sorted(set(changes) - set(src.namelist())):
                dst.writestr(name, changes[name], compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(target) as dst:
            assert dst.testzip() is None
            for name in src.namelist():
                if name not in changes: assert src.read(name) == dst.read(name), name
            for name in dst.namelist():
                if name.endswith('.xml'): ET.fromstring(dst.read(name))
            assert b'PlayerControl(Repeat)' in dst.read(SKIN + 'unified/PlayerControls.xml')
    report = dict(version=version, sha256=sha(target.read_bytes()), artifact=target.name,
                  changed_files=sorted(changes), display_rows_removed=removed,
                  untouched_members_byte_identical=True, physical_fold_verified=False, crash_fixed=False)
    (out / ('BUILD-' + version + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    if coordinated:
        helper = out / 'script.infinity.uirepair-0.1.0-TEST.zip'
        with zipfile.ZipFile(helper, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted((HERE / 'addon').rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts:
                    if p.suffix == '.py': compile(p.read_bytes(), str(p), 'exec')
                    z.write(p, 'script.infinity.uirepair/' + p.relative_to(HERE / 'addon').as_posix())
            z.write(HERE / 'InfinityItemOptions.xml', 'script.infinity.uirepair/resources/skins/Default/1080i/InfinityItemOptions.xml')
    print(json.dumps(report, indent=2))
    return target

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--parent', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--coordinated', action='store_true')
    a = p.parse_args(); build(a.parent, a.out, a.coordinated)
