#!/usr/bin/env python3
"""Generate a strictly enumerated correction over the exact failed skin 209."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile
from lxml import etree as E

HERE = Path(__file__).resolve().parent
PARENT = '544279a735b2e2a4a7d1d77ac94a101dfd112f5f538deca1968f341d0ab6bb08'
PREFIX = 'skin.infinity.diggz/'
PROVIDER = 'plugin.video.playlistbrowser'
PATH = re.compile(r'plugin://plugin\.video\.playlistbrowser/\?action=channels_by_group&src=100&group=(TV|Live\+Events)(&reload=.*)?$')
PRIMARY_READY = '!String.IsEqual(Window(Home).Property(Infinity.WidgetPrimaryReady),false)'
RECOVERY = ('[String.IsEqual(Window(Home).Property(Infinity.Playlist.Ready),v1) + '
            '[[String.IsEqual(Container(9000).ListItem.Property(section),tvguide) + String.IsEmpty(Window(Home).Property(Infinity.Playlist.TVPath))] | '
            '[String.IsEqual(Container(9000).ListItem.Property(section),sports) + String.IsEmpty(Window(Home).Property(Infinity.Playlist.SportsPath))]]]')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def generate(parent):
    assert sha(parent.read_bytes()) == PARENT
    with zipfile.ZipFile(parent) as archive:
        assert archive.testzip() is None
        before = {n.removeprefix(PREFIX): archive.read(n) for n in archive.namelist() if not n.endswith('/')}
    roots = {n: E.fromstring(data) for n, data in before.items() if n.endswith('.xml')}
    variables, previous, edits = {}, {}, []
    for name, root in roots.items():
        if name.endswith('/Includes_InfinityPreview.xml'):
            for variable in root.findall('variable'):
                if variable.get('name', '').startswith('Infinity209SportsPath'):
                    old = previous.setdefault(variable.get('name'), variable.findtext('value'))
                    assert old == variable.findtext('value')

    def variable(path, context, browse=False):
        match = PATH.fullmatch(path)
        assert match, path
        key = 'TV' if match[1] == 'TV' else 'Sports'
        reload = match[2] or ''
        route = '$INFO[Window(Home).Property(Infinity.Playlist.' + key + 'Path)]' + reload
        ready = ('System.HasAddon(' + PROVIDER + ') + String.IsEqual(Window(Home).Property(Infinity.Playlist.Ready),v1)'
                 ' + !String.IsEmpty(Window(Home).Property(Infinity.Playlist.' + key + 'Path))')
        condition = ready + (' + ' + context if context else '')
        identity = sha((condition + route + str(browse)).encode())[:12]
        name = 'Infinity210Playlist' + identity
        node = E.Element('variable', name=name)
        E.SubElement(node, 'value', condition=condition).text = route
        if browse:
            E.SubElement(node, 'value', condition='System.HasAddon(' + PROVIDER + ')').text = 'plugin://' + PROVIDER + '/'
            E.SubElement(node, 'value').text = 'addons://sources/video/'
        else:
            E.SubElement(node, 'value').text = ''
        if name in variables:
            assert E.tostring(variables[name]) == E.tostring(node)
        else:
            variables[name] = node
        return '$VAR[' + name + ']'

    for name, root in roots.items():
        if name.endswith('/Home.xml'):
            clear = E.Element('onload'); clear.text = 'ClearProperty(Infinity.Playlist.Ready,Home)'
            run = E.Element('onload'); run.text = 'RunScript(special://skin/resources/lib/infinity_playlist_routes.py)'
            root.insert(0, clear); root.insert(1, run)
            button = root.find(".//control[@id='8898']")
            assert button is not None
            visible = button.find('visible')
            assert visible is not None and visible.text.count(PRIMARY_READY) == 1
            visible.text = visible.text.replace(PRIMARY_READY, PRIMARY_READY + ' | ' + RECOVERY)
        if name.endswith('/FileBrowser.xml'):
            nodes = root.xpath('./onload[text()="SetProperty(Infinity.FilePreview.OptIn,v1)"]')
            assert len(nodes) == 1
            # 375 compatibility is retained; 376 owns the exact dialog instance.
            nodes[0].set('condition', '!String.IsEqual(Window.Property(Infinity.FilePreview.RouteRevision),2103376)')
        for node in root.iter():
            old = node.text or ''
            text = old
            if old.startswith('$VAR[Infinity209SportsPath'):
                text = previous[old[5:-1]]
            if node.tag == 'content' and PATH.fullmatch(text):
                section = 'tvguide' if 'group=TV' in text else 'sports'
                if name.endswith('/Home.xml'):
                    context = 'String.IsEqual(Container(9000).ListItem.Property(section),' + section + ')'
                else:
                    assert name.endswith('/script-skinshortcuts-includes.xml'), name
                    submenu = 'num-4' if section == 'tvguide' else 'sports'
                    context = 'String.IsEqual(Container(9000).ListItem.Property(submenuVisibility),' + submenu + ')'
                    assert any(context == parent.findtext('visible') for parent in node.iterancestors()), name
                node.text = variable(text, context)
            elif node.tag == 'onclick' and text.startswith('SetProperty(Infinity.BrowsePath,plugin://' + PROVIDER):
                assert text.endswith(',Home)') and name.endswith('/Home.xml')
                path = text[len('SetProperty(Infinity.BrowsePath,'):-len(',Home)')]
                node.text = 'SetProperty(Infinity.BrowsePath,' + variable(path, '', browse=True) + ',Home)'
            if old != (node.text or ''):
                edits.append({'file': name, 'xpath': root.getroottree().getpath(node), 'old': old, 'new': node.text})
    for name, root in roots.items():
        if name.endswith('/Includes_InfinityPreview.xml'):
            for node in list(root.findall('variable')):
                if node.get('name', '').startswith('Infinity209SportsPath'):
                    root.remove(node)
            for key in sorted(variables):
                root.append(E.fromstring(E.tostring(variables[key])))
    addon = roots['addon.xml']
    addon.set('version', '1.0.5.210')
    addon.find("extension[@point='xbmc.addon.metadata']/description").text = (
        'Infinity 1.0.5.210 Critical Preview and Channels Correction RC1. Continues skin 209; '
        'paired APK 2103376 corrects ZIP input dispatch. Provider presets resolve the installed '
        'registry without changing provider files or user data. Galaxy Fold acceptance pending.')
    owned = {name for name in roots if name == 'addon.xml' or name.endswith(('/Home.xml', '/FileBrowser.xml',
              '/Includes_InfinityPreview.xml', '/script-skinshortcuts-includes.xml'))}
    delta = {}
    for name in sorted(owned):
        data = E.tostring(roots[name], encoding='UTF-8', xml_declaration=True, pretty_print=True)
        # Do not reserialize a family file if it has no reviewed semantic edit.
        if E.tostring(E.fromstring(before[name])) != E.tostring(roots[name]):
            delta[name] = data
    for path in sorted((HERE / 'runtime').glob('*.py')):
        delta['resources/lib/' + path.name] = path.read_bytes()
    output = HERE / 'delta'
    if output.exists():
        shutil.rmtree(output)  # Only this recipe's generated scratch overlay.
    for name, data in delta.items():
        path = output / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    inventory = {'parent_sha256': PARENT, 'parent_version': '1.0.5.209', 'version': '1.0.5.210',
                 'modified': sorted(set(delta) & set(before)), 'added': sorted(set(delta) - set(before)),
                 'removed': [], 'delta_sha256': {n: sha(d) for n, d in delta.items()},
                 'route_edit_count': len(edits), 'variables': sorted(variables),
                 'all_provider_and_user_data_files_untouched': True}
    (HERE / 'change-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    (HERE / 'route-evidence.json').write_text(json.dumps(edits, indent=2) + '\n')
    print(json.dumps({'modified': len(inventory['modified']), 'added': len(inventory['added']),
                      'route_edits': len(edits), 'new_variables': len(variables)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--parent', type=Path, required=True)
    generate(parser.parse_args().parent)
