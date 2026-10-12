import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import types
import unittest
from unittest.mock import patch
import urllib
import urllib.parse
from datetime import datetime, timezone
import warnings

warnings.filterwarnings('ignore', category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent / 'runtime'
sys.path.insert(0, str(RUNTIME))
import infinity_playlist_registry as registry


class Source:
    def __init__(self, number, name, m3u, js, epg):
        self.idx, self.name, self.m3u, self.js, self.epg = number, name, m3u, js, epg
        self.progs = {}
        self.channels = [{'name': 'TV channel', 'group': 'TV', 'url': 'plugin://active.provider/play/one', 'logo': ''},
                         {'name': 'Sports channel', 'group': 'Live Events', 'url': 'pvr://channels/tv/all/one', 'logo': ''}]
    def load_epg(self):
        pass
    def match_epg_key(self, channel):
        return None


class ListItem:
    def __init__(self, **kwargs):
        self.values = kwargs
    def setLabel2(self, value): pass
    def setInfo(self, *args): pass
    def setProperty(self, *args): pass
    def addContextMenuItems(self, *args, **kwargs): pass


def provider(version='2.7.3', data=None):
    code = (HERE / 'fixtures' / ('provider-' + version + '.py')).read_text()
    raw = data if data is not None else json.loads((HERE / 'fixtures' / ('registry-' + version + '.json')).read_text())
    dialogs, entries, endings, roots = [], [], [], []
    class InstanceSource(Source):
        pass
    env = {'Source': InstanceSource, 'os': os, 'json': json, 'urllib': urllib,
           'datetime': datetime, 'timezone': timezone, 'ADDON_PATH': '/provider', 'HANDLE': 73,
           'read_text': lambda path: json.dumps(raw), 'log': lambda *args: None,
           'get_string_setting': lambda name, default: default,
           'xbmcgui': types.SimpleNamespace(Dialog=lambda: types.SimpleNamespace(ok=lambda *args: dialogs.append(args)), ListItem=ListItem),
           'xbmcplugin': types.SimpleNamespace(endOfDirectory=lambda handle: endings.append(handle), setContent=lambda *args: None,
                                              addDirectoryItem=lambda handle, url, item, isFolder: entries.append(url)),
           '_apply_color': lambda text, key: text, 'set_art': lambda *args: None, 'channel_logo': lambda *args: '',
           'build_url': lambda params: registry.ROOT + '?' + urllib.parse.urlencode(params),
           'list_root': lambda: roots.append(True)}
    exec(compile(code, 'pinned-provider-routing-fixture', 'exec'), env)
    InstanceSource.load_channels = env['load_channels']
    return types.SimpleNamespace(env=env, code=code, raw=json.dumps(raw), dialogs=dialogs,
                                 entries=entries, endings=endings, roots=roots)


class RegistryTests(unittest.TestCase):
    def test_original_route_reproduces_exact_physical_error(self):
        fixture = provider()
        fixture.env['router']('?action=channels_by_group&src=100&group=TV')
        self.assertEqual(fixture.dialogs, [('Channels', 'Source not found.')])
        self.assertEqual(fixture.entries, [])
        self.assertEqual(fixture.endings, [73])

    def test_repaired_routes_execute_real_registry_router_and_alias_filter(self):
        fixture = provider()
        routes = registry.resolve(fixture.code, fixture.raw)
        self.assertEqual(routes['status'], 'resolved')
        self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlsplit(routes['tv']).query)['src'], ['105'])
        self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlsplit(routes['sports']).query)['src'], ['101'])
        for kind in ('tv', 'sports'):
            fixture.env['router']('?' + urllib.parse.urlsplit(routes[kind]).query)
        self.assertEqual(fixture.dialogs, [])
        urls = [urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['url'][0] for url in fixture.entries]
        self.assertEqual(urls, ['plugin://active.provider/play/one', 'pvr://channels/tv/all/one'])
        self.assertEqual(fixture.endings, [73, 73])

    def test_valid_older_source_100_is_preserved(self):
        fixture = provider('2.6.8')
        self.assertEqual(fixture.env['load_sources']()[0].name, 'TV APP')
        routes = registry.resolve(fixture.code, fixture.raw)
        self.assertEqual(routes['status'], 'legacy-valid')
        for kind in ('tv', 'sports'):
            self.assertIn('&src=100&', routes[kind])
            fixture.env['router']('?' + urllib.parse.urlsplit(routes[kind]).query)
        self.assertFalse(fixture.dialogs)

    def test_registry_reorder_and_alias_renumber_do_not_guess_fixed_ids(self):
        fixture = provider(); data = json.loads(fixture.raw)
        data.reverse()
        for item in data:
            item['source_id'] += 400
        routes = registry.resolve(fixture.code, json.dumps(data))
        self.assertIn('&src=505&', routes['tv'])
        self.assertIn('&src=501&', routes['sports'])

    def test_missing_and_ambiguous_aliases_require_explicit_browsing(self):
        fixture = provider(); data = json.loads(fixture.raw)
        without = [item for item in data if item['name'] != 'Doms List']
        result = registry.resolve(fixture.code, json.dumps(without))
        self.assertEqual((result['tv'], result['sports'], result['status']), ('', '', 'browse-required'))
        ambiguous = dict(next(item for item in data if item['source_id'] == 105), source_id=200, name='For TV Widget 9')
        result = registry.resolve(fixture.code, json.dumps(data + [ambiguous]))
        self.assertEqual(result['tv'], '')
        self.assertTrue(result['sports'])

    def test_unknown_code_is_not_imported_or_executed(self):
        fixture = provider()
        code = fixture.code.replace('sources = []', 'sources = ["changed contract"]')
        with patch('builtins.exec', side_effect=AssertionError('Runtime resolver must not execute provider code')):
            result = registry.resolve(code, fixture.raw)
        self.assertEqual((result['tv'], result['sports'], result['status']), ('', '', 'unsupported'))

    def test_bad_or_oversized_registry_never_emits_a_source_id(self):
        fixture = provider()
        for raw in ('{bad', '{}', json.dumps([{}] * 513), ' ' * (256 * 1024 + 1)):
            result = registry.resolve(fixture.code, raw)
            self.assertEqual((result['tv'], result['sports']), ('', ''))

    def test_portable_fingerprint_ignores_comments_and_empty_python312_type_params(self):
        fixture = provider()
        self.assertEqual(registry.contract(fixture.code), registry.contract('# comment\n' + fixture.code))
        node = registry.ast.parse(fixture.code).body[0]
        before = registry.canonical(node)
        if not hasattr(node, 'type_params'):
            node._fields += ('type_params',)
        node.type_params = []
        self.assertEqual(before, registry.canonical(node))

    def test_allocator_matches_actual_provider_on_reserved_duplicate_and_invalid_ids(self):
        randomizer = random.Random(210)
        base = [{'name': 'one', 'm3u': 'local.m3u'}, {'name': 'two', 'json': 'local.json', 'source_id': 103},
                {'name': 'alias', 'alias_source': 'one', 'alias_group': 'TV', 'source_id': 110},
                {'name': 'bad', 'source_id': 101}, {'m3u': 'local', 'source_id': 'bad'},
                None, {'m3u': 'local', 'source_id': 103}, {'m3u': 'local', 'source_id': 99},
                {'m3u': 'local', 'source_id': float('inf')}, {'m3u': 'local', 'source_id': None}]
        for version, mode in [('2.7.3', 'stable'), ('2.6.8', 'sequential')]:
            for _ in range(160):
                data = randomizer.choices(base, k=randomizer.randrange(0, 24))
                fixture = provider(version, data)
                actual = [{'id': value.idx, 'name': value.name, 'alias': getattr(value, 'alias_source', ''),
                           'group': getattr(value, 'alias_group', '')} for value in fixture.env['load_sources']()]
                self.assertEqual(registry.registry(data, mode), actual)


class Home:
    def __init__(self):
        self.props = {'Infinity.Playlist.TVPath': 'stale', 'Infinity.Playlist.SportsPath': 'stale', 'Other': 'keep'}
        self.writes = []
    def setProperty(self, name, value):
        self.props[name] = value; self.writes.append((name, value))
    def clearProperty(self, name):
        self.props.pop(name, None); self.writes.append((name, ''))
    def getProperty(self, name):
        return self.props.get(name, '')


class RefreshTests(unittest.TestCase):
    def run_refresh(self, installed=True, unknown=False, missing=False, superseded=False):
        fixture = provider(); home = Home(); calls = []
        addon = types.SimpleNamespace(getAddonInfo=lambda key: {'path': '/installed/provider', 'version': '2.7.3'}[key])
        mocks = {'xbmc': types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz', LOGINFO=1,
                                             getCondVisibility=lambda query: installed, log=lambda *args: calls.append(args)),
                 'xbmcaddon': types.SimpleNamespace(Addon=lambda addon_id: addon),
                 'xbmcgui': types.SimpleNamespace(Window=lambda owner: home),
                 'xbmcvfs': types.SimpleNamespace(translatePath=lambda path: path)}
        spec = importlib.util.spec_from_file_location('route_refresh_test', RUNTIME / 'infinity_playlist_routes.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, mocks):
            spec.loader.exec_module(module)
            def read(path, limit):
                if missing: raise FileNotFoundError()
                if superseded: home.setProperty('Infinity.Playlist.Request', 'newer-refresh')
                if path.endswith('main.py'): return '' if unknown else fixture.code
                return fixture.raw
            with patch.object(module, 'read_local', side_effect=read), patch('builtins.open', side_effect=AssertionError('No extra file writes')):
                module.main()
        self.assertEqual(home.props['Other'], 'keep')
        self.assertTrue(all(name.startswith('Infinity.Playlist.') for name, value in home.writes))
        return home, calls

    def test_refresh_publishes_readiness_last(self):
        home, _ = self.run_refresh()
        self.assertEqual(home.writes[-1], ('Infinity.Playlist.Ready', 'v1'))
        self.assertEqual(home.props['Infinity.Playlist.Status'], 'resolved')
        self.assertIn('&src=105&', home.props['Infinity.Playlist.TVPath'])

    def test_missing_provider_clears_stale_widgets_and_keeps_addon_browser(self):
        home, _ = self.run_refresh(installed=False)
        self.assertEqual(home.props['Infinity.Playlist.TVPath'], '')
        self.assertEqual(home.props['Infinity.Playlist.TVBrowse'], 'addons://sources/video/')

    def test_unknown_and_missing_registry_keep_provider_root(self):
        for options in ({'unknown': True}, {'missing': True}):
            home, _ = self.run_refresh(**options)
            self.assertEqual(home.props['Infinity.Playlist.TVPath'], '')
            self.assertEqual(home.props['Infinity.Playlist.TVBrowse'], registry.ROOT)

    def test_superseded_refresh_cannot_restore_stale_routes(self):
        home, logs = self.run_refresh(superseded=True)
        self.assertNotIn('Infinity.Playlist.Ready', home.props)
        self.assertNotIn('Infinity.Playlist.TVPath', home.props)
        self.assertFalse(logs)


if __name__ == '__main__':
    unittest.main(verbosity=2, warnings='ignore')
