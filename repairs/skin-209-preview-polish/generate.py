#!/usr/bin/env python3
"""Targeted 209 delta from every exact locked 208 payload; no reconstruction of the parent."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
from lxml import etree as E

HERE = Path(__file__).resolve().parent
PARENT = 'a6d496f6bd576676d060a31b572e3930c7ac6a3625b8eaf5dcdd04433f172408'
SCRIPT = 'script.infinity.live'
PVR = 'pvr://channels/tv/*/'
TV_PATTERN = re.compile(r"plugin://plugin\.video\.playlistbrowser/\?action=channels_by_group&src=100&group=TV(?=&|[\"',)]|$)(?:&reload=(?:\$INFO\[[^\]]+\])*)?(?![a-zA-Z])")


def settext(parent, tag, value):
    node = parent.find(tag)
    if node is None:
        node = E.SubElement(parent, tag)
    node.text = str(value)
    return node


def button(parent, control_id, label):
    result = copy.deepcopy(parent.find("control[@id='414']"))
    assert result is not None
    result.set('id', str(control_id))
    settext(result, 'label', label)
    return result


def footer(group):
    originals = list(group)
    # Keep native buttons/IDs and navigation. A fixed footer owns its own icon/text
    # rectangles instead of placing a percentage-height image into native flow.
    elements = [n for n in originals if n.tag == 'control' and n.get('type') != 'button']
    for node in elements:
        group.remove(node)
    flow = E.SubElement(group, 'control', type='group', id='9413')
    settext(flow, 'width', '100%')
    settext(flow, 'height', 244)
    icon = E.SubElement(flow, 'control', type='image')
    for tag, value in [('left', '0'), ('top', '4'), ('width', '100%'), ('height', '96'), ('aspectratio', 'keep')]:
        settext(icon, tag, value)
    texture = E.SubElement(icon, 'texture', fallback='DefaultFolder.png', colordiffuse='$VAR[InfinityPolishIcon0Tint]')
    texture.text = '$VAR[InfinityPolishIcon0]'
    count = E.SubElement(flow, 'control', type='label')
    for tag, value in [('left', 0), ('top', 110), ('width', '100%'), ('height', 38), ('font', 'InfinityTiny'),
                       ('textcolor', '$VAR[InfinityDiggzSecondaryText]'), ('align', 'center'), ('aligny', 'center'),
                       ('label', '$INFO[Container(450).NumItems] items  •  $INFO[Container(450).CurrentPage]/$INFO[Container(450).NumPages]')]:
        settext(count, tag, value)
    helptext = E.SubElement(flow, 'control', type='textbox')
    for tag, value in [('left', 0), ('top', 158), ('width', '100%'), ('height', 82), ('font', 'InfinityTiny'),
                       ('textcolor', '$VAR[InfinityDiggzSecondaryText]'), ('align', 'center'),
                       ('text', 'Select a ZIP to install. Long press or choose Preview for file information. Back returns safely.')]:
        settext(helptext, tag, value)


def filebrowser(tree):
    root = tree.getroot()
    assert not root.xpath(".//control[@id='9410' or @id='9413']")
    load = E.Element('onload')
    load.text = 'SetProperty(Infinity.FilePreview.OptIn,v1)'
    root.insert(1, load)
    controls = root.find('controls')
    direct = controls.findall('control')
    title = next(n for n in direct if n.get('type') == 'label' and n.get('id') is None)
    subtitle = controls.find("control[@id='411']")
    path = controls.find("control[@id='412']")
    back = controls.find("control[@id='419']")
    logo = next(n for n in direct if n.get('type') == 'image' and n.findtext('aspectratio') == 'keep')
    # The approved two-column presentation is retained; only chrome becomes bounded.
    for node in (title, subtitle):
        settext(node, 'left', '16%')
        settext(node, 'width', '62%')
    for node, top, height in ((title, 6, 44), (subtitle, 52, 28), (path, 86, 28)):
        settext(node, 'top', top)
        settext(node, 'height', height)
    settext(logo, 'top', 12)
    settext(logo, 'height', 66)
    settext(back, 'top', 12)
    settext(back, 'height', 68)
    images = [n for n in direct if n.get('type') == 'image']
    assert len(images) == 5
    settext(images[1], 'height', 116)
    for node in images[-2:]:
        settext(node, 'top', 128)
        node.remove(node.find('height'))
        settext(node, 'bottom', 24)
    for node in controls.findall("control[@type='list']") + [controls.find("control[@id='61']")]:
        settext(node, 'top', 146)
        node.remove(node.find('height'))
        settext(node, 'bottom', 42)
    side = controls.find("control[@id='90']")
    settext(side, 'top', 146)
    side.remove(side.find('height'))
    settext(side, 'bottom', 42)
    settext(side, 'width', '25.5556%')
    preview = button(side, 9410, 'Preview')
    settext(preview, 'height', 84)
    settext(preview, 'visible', 'String.IsEqual(Window.Property(Infinity.FilePreview.NativeVersion),v1)')
    side.insert(list(side).index(side.find("control[@id='415']")) + 1, preview)
    footer(side)
    return tree


def addonbrowser(tree):
    root = tree.getroot()
    controls = root.find('controls')
    title = next(n for n in controls.findall('control') if n.get('type') == 'label')
    if title.findtext('left') == '12.8704%':
        settext(title, 'left', '16%')
        settext(title, 'width', '62%')
    return tree


def retired_routes(tree, relative, records):
    root = tree.getroot()
    for action in list(root.xpath("//*[text()='RunAddon(script.infinity.live)']")):
        if action.getparent() is None:
            continue
        parent = action.getparent()
        if parent.get('id') == '1700' and parent.getparent().get('id') == '17':
            group = parent.getparent()
            scope = group.getparent()
            while scope.getparent() is not None and not (scope.tag == 'include' and scope.get('name')):
                scope = scope.getparent()
            for link in scope.xpath('.//onup[text()="17"] | .//ondown[text()="17"] | .//onleft[text()="17"] | .//onright[text()="17"]'):
                link.text = '14' if link.tag in ('onup', 'onleft') else '15'
            group.getparent().remove(group)
            records.append({'file': relative, 'removed': 'Dedicated Infinity Live power-menu group 17 / button 1700'})
        elif parent.get('id') == '19522':
            for node in list(parent.findall('onclick')):
                parent.remove(node)
            settext(parent, 'onclick', 'ClearProperty(Infinity.CinemaDrawerLevel,home)')
            E.SubElement(parent, 'onclick').text = 'ActivateWindow(TVGuide)'
            records.append({'file': relative, 'replaced': 'Cinema legacy launcher', 'route': 'Existing native TVGuide'})
        else:
            for node in list(parent.findall('onclick')):
                if SCRIPT in (node.text or '') or SCRIPT in node.get('condition', ''):
                    parent.remove(node)
            E.SubElement(parent, 'onclick').text = 'ActivateWindow(TVGuide)'
            records.append({'file': relative, 'replaced': 'Legacy launcher', 'route': 'Existing native TVGuide'})
    for node in root.iter():
        if node.text:
            before = node.text
            node.text, count = TV_PATTERN.subn(PVR, before)
            if count:
                records.append({'file': relative, 'owner': node.tag, 'retired_tv_preset_routes': count, 'new_path': PVR})
        if (node.tag == 'property' and node.get('name') == 'widgetName' and node.text == 'Diggz Pick' and
                node.getparent().findtext("property[@name='section']") == 'tvguide'):
            node.text = 'Live channels'
    return tree


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    args = parser.parse_args()
    root = args.parent
    out = HERE / 'delta'
    for source in (HERE / 'resources' / 'lib').glob('*.py'):
        destination = out / 'resources' / 'lib' / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    expected = json.loads((HERE / 'parent-files.json').read_text())
    assert before == expected, 'Wrong/incomplete exact skin 208 source'
    records = []
    changed = {}
    helper = {}
    for source in sorted(root.rglob('*.xml')):
        relative = source.relative_to(root).as_posix()
        tree = E.parse(str(source))
        serialized_before = E.tostring(tree)
        if source.name == 'FileBrowser.xml':
            filebrowser(tree)
        if source.name == 'AddonBrowser.xml':
            addonbrowser(tree)
        retired_routes(tree, relative, records)
        if source.name == 'Home.xml':
            variables = E.Element('includes')
            for content in tree.findall('.//content'):
                value = content.text or ''
                if 'plugin.video.playlistbrowser' in value and 'src=100' in value and 'group=Live+Events' in value:
                    name = 'Infinity209SportsPath' + hashlib.sha256((relative + value).encode()).hexdigest()[:12]
                    variable = E.SubElement(variables, 'variable', name=name)
                    E.SubElement(variable, 'value', condition='String.IsEqual(Container(9000).ListItem.Property(section),sports)').text = value
                    E.SubElement(variable, 'value').text = ''
                    content.text = '$VAR[' + name + ']'
                    records.append({'file': relative, 'guarded_sports_widget': name, 'retained_active_uri': value})
            helper[source.parent] = variables
        if source.name == 'addon.xml' and source.parent == root:
            addon = tree.getroot()
            assert addon.get('version') == '1.0.5.208' and addon.get('id') == 'skin.infinity.diggz'
            addon.set('version', '1.0.5.209')
            requires = addon.find('requires')
            for node in list(requires):
                if node.get('addon') == SCRIPT:
                    requires.remove(node)
            if requires.find("import[@addon='xbmc.python']") is None:
                E.SubElement(requires, 'import', addon='xbmc.python', version='3.0.0')
            addon.find("extension[@point='xbmc.addon.metadata']/description").text = 'Infinity 1.0.5.209 File Preview, Live TV Navigation Cleanup & UI Polish RC1. Built directly from locked 1.0.5.208. Paired Infinity APK 2103375 supplies the ZIP preview bridge; all original playback, provider, PVR and shutdown functionality is preserved. Physical Fold acceptance pending.'
        if E.tostring(tree) != serialized_before:
            changed[relative] = tree
    all_variables = [copy.deepcopy(node) for variables in helper.values() for node in variables]
    for directory in sorted(set(helper) | {path.parent for path in root.rglob('FileBrowser.xml')}):
        changed[(directory.relative_to(root) / 'InfinityFilePreview.xml').as_posix()] = E.parse(str(HERE / 'InfinityFilePreview.xml'))
        include_relative = (directory.relative_to(root) / 'Includes.xml').as_posix()
        if not (root / include_relative).exists():
            # Partial historical folders inherit the globally loaded include universe.
            # Every complete universe below receives all route variables, including fallback references.
            continue
        legacy_path = directory / 'Includes_InfinityLegacy.xml'
        if not legacy_path.exists():
            legacy_path = root / 'unified/Includes_InfinityLegacy.xml'
        legacy = E.parse(str(legacy_path)).getroot()
        surface = copy.deepcopy(legacy.find("variable[@name='InfinityLegacySurface']"))
        assert surface is not None
        surface.set('name', 'InfinityPreviewSurface')
        for value in surface.findall('value'):
            assert re.fullmatch('[A-Fa-f0-9]{8}', value.text)
            value.text = 'FF' + value.text[2:]
        variables = E.Element('includes')
        variables.append(surface)
        variables.extend(copy.deepcopy(all_variables))
        relative = (directory.relative_to(root) / 'Includes_InfinityPreview.xml').as_posix()
        changed[relative] = E.ElementTree(variables)
        tree = changed.get(include_relative) or E.parse(str(root / include_relative))
        node = E.Element('include', file='Includes_InfinityPreview.xml')
        tree.getroot().insert(0, node)
        changed[include_relative] = tree
    for relative, tree in changed.items():
        destination = out / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        E.indent(tree, space='  ')
        tree.write(str(destination), encoding='utf-8', xml_declaration=True)
    current = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    (HERE / 'change-inventory.json').write_text(json.dumps({'parent_sha256': PARENT, 'new_version': '1.0.5.209', 'modified': sorted(set(current) & set(before)), 'added': sorted(set(current) - set(before)), 'removed': [], 'delta_sha256': current, 'retired_and_guarded_routes': records}, indent=2) + '\n')
    print(json.dumps({'modified': len(set(current) & set(before)), 'added': len(set(current) - set(before)), 'route_records': len(records)}))


if __name__ == '__main__':
    main()
