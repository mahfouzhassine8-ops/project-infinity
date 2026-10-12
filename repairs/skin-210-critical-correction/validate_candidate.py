#!/usr/bin/env python3
"""Independent route, membership and semantic preservation gates for skin 210."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile
from lxml import etree as E

HERE = Path(__file__).resolve().parent
PARENT = '544279a735b2e2a4a7d1d77ac94a101dfd112f5f538deca1968f341d0ab6bb08'
PROVIDER = 'plugin.video.playlistbrowser'


def archive(path):
    with zipfile.ZipFile(path) as data:
        assert data.testzip() is None and len(data.namelist()) == len(set(data.namelist()))
        return {name.removeprefix('skin.infinity.diggz/'): data.read(name) for name in data.namelist() if not name.endswith('/')}


def canonical(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(),
            tuple(canonical(child) for child in node if isinstance(child.tag, str)))


def evaluate(node, section='tvshows', submenu='tvshows', ready=True, installed=True, tv='tv', sports='sports'):
    states = {'System.HasAddon(' + PROVIDER + ')': installed,
              'String.IsEqual(Window(Home).Property(Infinity.Playlist.Ready),v1)': ready,
              '!String.IsEmpty(Window(Home).Property(Infinity.Playlist.TVPath))': bool(tv),
              '!String.IsEmpty(Window(Home).Property(Infinity.Playlist.SportsPath))': bool(sports),
              'String.IsEqual(Container(9000).ListItem.Property(section),tvguide)': section == 'tvguide',
              'String.IsEqual(Container(9000).ListItem.Property(section),sports)': section == 'sports',
              'String.IsEqual(Container(9000).ListItem.Property(submenuVisibility),num-4)': submenu == 'num-4',
              'String.IsEqual(Container(9000).ListItem.Property(submenuVisibility),sports)': submenu == 'sports'}
    for value in node.findall('value'):
        condition = value.get('condition')
        if not condition or all(states[part] for part in condition.split(' + ')):
            return value.text or ''
    raise AssertionError('Variable has no fallback')


def condition_value(expression, atoms):
    """Evaluate the shipped bracket/AND/OR expression, with controlled GUI info atoms."""
    for atom in sorted(atoms, key=len, reverse=True):
        expression = expression.replace(atom, '1' if atoms[atom] else '0')
    tokens = list(''.join(expression.split()))
    assert set(tokens) <= set('01![]+|'), expression
    position = 0
    def primary():
        nonlocal position
        token = tokens[position]; position += 1
        if token == '!': return not primary()
        if token == '[':
            value = either()
            assert tokens[position] == ']'; position += 1
            return value
        assert token in '01'; return token == '1'
    def both():
        nonlocal position
        value = primary()
        while position < len(tokens) and tokens[position] == '+':
            position += 1; right = primary(); value = value and right
        return value
    def either():
        nonlocal position
        value = both()
        while position < len(tokens) and tokens[position] == '|':
            position += 1; right = both(); value = value or right
        return value
    result = either(); assert position == len(tokens)
    return result


class CandidateTests(unittest.TestCase):
    def test_exact_package_delta_and_no_removals(self):
        self.assertEqual(hashlib.sha256(self.parent.read_bytes()).hexdigest(), PARENT)
        self.assertEqual(sorted(n for n in self.before if self.before[n] != self.after.get(n)), self.inventory['modified'])
        self.assertEqual(sorted(set(self.after) - set(self.before)), self.inventory['added'])
        self.assertFalse(set(self.before) - set(self.after))
        self.assertEqual(self.inventory['added'], ['resources/lib/infinity_playlist_registry.py', 'resources/lib/infinity_playlist_routes.py'])
        self.assertEqual(len(self.inventory['modified']), 50)
        for name, digest in self.inventory['delta_sha256'].items():
            self.assertEqual(hashlib.sha256(self.after[name]).hexdigest(), digest, name)
        self.assertFalse(any('fixtures/' in name or 'provider-2.' in name for name in self.after))

    def test_all_bundled_invalid_presets_replaced_and_variables_resolve(self):
        edits = 0
        for name, root in self.xml.items():
            self.assertNotIn(b'channels_by_group&amp;src=100', self.after[name], name)
            self.assertNotIn(b'$VAR[Infinity209SportsPath', self.after[name], name)
            for node in root.iter():
                text = node.text or ''
                if '$VAR[Infinity210Playlist' in text:
                    for variable in re.findall(r'\$VAR\[(Infinity210Playlist[0-9a-f]+)\]', text):
                        self.assertIn(variable, self.variables, name)
                        self.assertIn(node.tag, ('content', 'onclick'))
                        edits += 1
        self.assertEqual(edits, 244)
        self.metrics['corrected_widget_and_browse_expressions'] = edits
        self.assertEqual(len(self.variables), 8)

    def test_widgets_do_not_request_channels_on_tvshows_or_before_resolution(self):
        widgets = [node for node in self.variables.values() if len(node.findall('value')) == 2]
        self.assertEqual(len(widgets), 6)
        for node in widgets:
            self.assertEqual(evaluate(node), '')
            self.assertEqual(evaluate(node, section='tvguide', submenu='num-4', ready=False), '')
            self.assertEqual(evaluate(node, section='sports', submenu='sports', installed=False), '')
            self.assertEqual(evaluate(node, section='tvguide', submenu='num-4', tv='', sports=''), '')
            self.assertEqual(evaluate(node, section='sports', submenu='sports', tv='', sports=''), '')
            route = evaluate(node, section='tvguide', submenu='num-4') or evaluate(node, section='sports', submenu='sports')
            self.assertIn('Window(Home).Property(Infinity.Playlist.', route)
            self.assertIn('&reload=', route)
        old = E.fromstring(self.before['unified/Home.xml'])
        self.assertGreater(sum('channels_by_group' in (node.text or '') and 'group=TV' in (node.text or '')
                               for node in old.findall('.//content')), 0, 'Old TV Shows background failure must be represented')
        self.metrics['widget_variables_guarded'] = 6

    def test_explicit_browsing_recovers_without_guessing_a_source(self):
        browsers = [node for node in self.variables.values() if len(node.findall('value')) == 3]
        self.assertEqual(len(browsers), 2)
        for node in browsers:
            self.assertEqual(evaluate(node, ready=False), 'plugin://' + PROVIDER + '/')
            self.assertEqual(evaluate(node, tv='', sports=''), 'plugin://' + PROVIDER + '/')
            self.assertEqual(evaluate(node, installed=False), 'addons://sources/video/')
            self.assertIn('Path)]&reload=', evaluate(node))

    def test_only_enumerated_route_and_lifecycle_semantics_change(self):
        checked = 0
        for name in self.inventory['modified']:
            if not name.endswith('.xml'):
                self.assertEqual(name, 'resources/lib/infinity_file_preview.py')
                continue
            old = E.fromstring(self.before[name]); new = copy.deepcopy(self.xml[name])
            if name == 'addon.xml':
                self.assertEqual(new.get('version'), '1.0.5.210')
                new.set('version', old.get('version'))
                new.find("extension[@point='xbmc.addon.metadata']/description").text = old.find("extension[@point='xbmc.addon.metadata']/description").text
            elif name.endswith('/Includes_InfinityPreview.xml'):
                for node in list(old.findall('variable')):
                    if node.get('name', '').startswith('Infinity209SportsPath'): old.remove(node)
                for node in list(new.findall('variable')):
                    if node.get('name', '').startswith('Infinity210Playlist'): new.remove(node)
            else:
                if name.endswith('/Home.xml'):
                    for text in ('ClearProperty(Infinity.Playlist.Ready,Home)', 'RunScript(special://skin/resources/lib/infinity_playlist_routes.py)'):
                        nodes = new.xpath('./onload[text()=$value]', value=text)
                        self.assertEqual(len(nodes), 1, name)
                        self.assertFalse(nodes[0].attrib)
                        new.remove(nodes[0])
                    old_visible = old.find(".//control[@id='8898']/visible")
                    new_visible = new.find(".//control[@id='8898']/visible")
                    guard = '!String.IsEqual(Window(Home).Property(Infinity.WidgetPrimaryReady),false)'
                    recovery = ('[String.IsEqual(Window(Home).Property(Infinity.Playlist.Ready),v1) + '
                                '[[String.IsEqual(Container(9000).ListItem.Property(section),tvguide) + String.IsEmpty(Window(Home).Property(Infinity.Playlist.TVPath))] | '
                                '[String.IsEqual(Container(9000).ListItem.Property(section),sports) + String.IsEmpty(Window(Home).Property(Infinity.Playlist.SportsPath))]]]')
                    self.assertEqual(new_visible.text, old_visible.text.replace(guard, guard + ' | ' + recovery), name)
                    new_visible.text = old_visible.text
                if name.endswith('/FileBrowser.xml'):
                    nodes = new.xpath('./onload[text()="SetProperty(Infinity.FilePreview.OptIn,v1)"]')
                    self.assertEqual(len(nodes), 1, name)
                    self.assertEqual(dict(nodes[0].attrib), {'condition': '!String.IsEqual(Window.Property(Infinity.FilePreview.RouteRevision),2103376)'})
                    nodes[0].attrib.clear()
                old_nodes, new_nodes = list(old.iter()), list(new.iter())
                self.assertEqual(len(old_nodes), len(new_nodes), name)
                for before, after in zip(old_nodes, new_nodes):
                    left, right = (before.text or '').strip(), (after.text or '').strip()
                    if left == right:
                        continue
                    self.assertEqual(before.tag, after.tag)
                    self.assertIn(before.tag, ('content', 'onclick'))
                    if left.startswith('$VAR[Infinity209SportsPath'):
                        original = self.old_variables[left[5:-1]]
                    else:
                        original = left
                    self.assertIn('plugin://' + PROVIDER + '/?action=channels_by_group&src=100&group=', original)
                    match = re.search(r'\$VAR\[(Infinity210Playlist[0-9a-f]+)\]', right)
                    self.assertIsNotNone(match)
                    variable = self.variables[match[1]]
                    kind = 'TV' if 'group=TV' in original else 'Sports'
                    self.assertIn('Infinity.Playlist.' + kind + 'Path', variable.findtext('value'))
                    old_reload = original.split('&reload=', 1)[1].removesuffix(',Home)')
                    self.assertEqual(variable.findtext('value').split('&reload=', 1)[1], old_reload)
                    if before.tag == 'onclick':
                        self.assertEqual(right, 'SetProperty(Infinity.BrowsePath,' + match[0] + ',Home)')
                    else:
                        self.assertEqual(right, match[0])
                    after.text = before.text
                    checked += 1
            self.assertEqual(canonical(old), canonical(new), name + ': unrelated semantic change')
        self.assertEqual(checked, 244)
        self.metrics['independently_checked_xml_route_edits'] = checked

    def test_compact_recovery_is_reachable_only_for_missing_tv_or_sports_route(self):
        homes = [name for name in self.xml if name.endswith('/Home.xml')]
        self.assertEqual(len(homes), 14)
        for name in homes:
            visible = self.xml[name].find(".//control[@id='8898']/visible").text
            original = E.fromstring(self.before[name]).find(".//control[@id='8898']/visible").text
            for section, ready, tv, sports, expected in [('tvguide', True, '', '', True),
                    ('sports', True, '', '', True), ('tvguide', False, '', '', False),
                    ('movies', True, '', '', False), ('tvshows', True, '', '', False),
                    ('tvguide', True, 'valid', '', False), ('sports', True, '', 'valid', False)]:
                atoms = {'String.IsEqual(Window(Home).Property(Infinity.EffectiveViewMode),compact)': True,
                         'String.IsEmpty(Window(Home).Property(Infinity.EffectiveViewMode))': False,
                         'String.IsEqual(Skin.String(Infinity.HomeView),compact)': True,
                         'String.IsEqual(Container(9000).ListItem.Property(section),infinity)': section == 'infinity',
                         'String.IsEqual(Window(Home).Property(Infinity.WidgetPrimaryReady),false)': True,
                         'String.IsEqual(Window(Home).Property(Infinity.Playlist.Ready),v1)': ready,
                         'String.IsEqual(Container(9000).ListItem.Property(section),tvguide)': section == 'tvguide',
                         'String.IsEqual(Container(9000).ListItem.Property(section),sports)': section == 'sports',
                         'String.IsEmpty(Window(Home).Property(Infinity.Playlist.TVPath))': not tv,
                         'String.IsEmpty(Window(Home).Property(Infinity.Playlist.SportsPath))': not sports}
                self.assertFalse(condition_value(original, atoms), 'Parent hides recovery behind the widget-ready gate')
                self.assertEqual(condition_value(visible, atoms), expected, name + ' ' + section)
        self.metrics['compact_browse_recovery_controls'] = len(homes)

    def test_protected_layouts_resources_and_services_are_exact(self):
        protected = 0
        for name, data in self.before.items():
            if name not in self.inventory['modified']:
                self.assertEqual(data, self.after[name], name)
                protected += 1
        for name in ('infinity_zip_metadata.py', 'infinity_preview_state.py', 'infinity_continuity.py', 'infinity_native_ambient.py'):
            self.assertEqual(self.before['resources/lib/' + name], self.after['resources/lib/' + name])
        previews = [name for name in self.before if name.endswith('/InfinityFilePreview.xml')]
        self.assertEqual(len(previews), 14)
        for name in previews:
            self.assertEqual(self.before[name], self.after[name], name)
        self.metrics['unchanged_payloads'] = protected
        self.metrics['unchanged_preview_layouts'] = len(previews)
        self.metrics['xml_documents_parsed'] = len(self.xml)


def main():
    parser = argparse.ArgumentParser()
    for name in ('parent', 'candidate', 'out'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    cls = CandidateTests; cls.parent = args.parent; cls.before = archive(args.parent); cls.after = archive(args.candidate)
    cls.inventory = json.loads((HERE / 'change-inventory.json').read_text())
    cls.xml = {n: E.fromstring(data) for n, data in cls.after.items() if n.endswith('.xml')}
    cls.variables, cls.old_variables, cls.metrics = {}, {}, {}
    for name, root in cls.xml.items():
        if name.endswith('/Includes_InfinityPreview.xml'):
            names = [v.get('name') for v in root.findall('variable')]
            assert len(names) == len(set(names)), name
            for node in root.findall('variable'):
                if node.get('name', '').startswith('Infinity210Playlist'):
                    cls.variables[node.get('name')] = node
            for node in E.fromstring(cls.before[name]).findall('variable'):
                if node.get('name', '').startswith('Infinity209SportsPath'):
                    cls.old_variables[node.get('name')] = node.findtext('value')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    receipt = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
               'metrics': cls.metrics, 'physical_device_verified': False,
               'condition_validation': 'Controlled evaluation of emitted expressions; actual Kodi GUI evaluation remains a device check.'}
    (args.out / 'SKIN-210-VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)


if __name__ == '__main__':
    main()
