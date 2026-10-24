"""Selected popup/metadata host checks. No Android or shutdown acceptance."""
import ast
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
CC = HERE / 'overlay/script.infinity.commandcenter'
BASE = HERE.parent / 'tracking/final-eight/overlay/script.infinity.commandcenter'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Item:
    def __init__(self, **kwargs):
        self.path = kwargs.get('path', '')
        self.properties = {}
        self.info = {}
    def setInfo(self, kind, value): self.info.update(value)
    def setProperty(self, key, value): self.properties[key] = value
    def getProperty(self, key): return self.properties.get(key, '')
    def setUniqueIDs(self, values): self.ids = values
    def setArt(self, values): self.art = values
    def addContextMenuItems(self, values): self.menu = values


class QuickActions(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.calls = []; self.writers = 0; self.depth = 0
        self.choice = ''; self.modal_action = ''; self.modal_calls = []; self.available = True
        self.props = {}; self.selection_mutation = None; self.modal_mutation = None
        @contextmanager
        def scope():
            self.writers += 1; self.depth += 1
            try: yield
            finally: self.depth -= 1
        def read(path, default):
            try: return json.loads(Path(path).read_text())
            except (OSError, ValueError): return default
        def write(path, data): Path(path).write_text(json.dumps(data, sort_keys=True))
        def choose(title, rows):
            if self.selection_mutation: self.selection_mutation()
            return rows.index(self.choice) if self.choice else -1
        def modal(item, entry, **kwargs):
            self.assertEqual(self.depth, 0)
            self.modal_calls.append((item, entry, kwargs))
            if self.modal_mutation: self.modal_mutation()
            return self.modal_action
        modules = {name: types.ModuleType(name) for name in
                   ('xbmc', 'xbmcgui', 'xbmcplugin', 'common', 'experience',
                    'persistence_participant', 'infinity_settings', 'information', 'provider_inventory')}
        xbmc = modules['xbmc']; xbmc.getSkinDir = lambda: 'skin.infinity.diggz'
        xbmc.getCondVisibility = lambda *a: self.available
        xbmc.getInfoLabel = lambda *a: 'plugin://different-provider/'
        xbmc.log = lambda *a: None; xbmc.LOGINFO = 1
        xbmc.executebuiltin = lambda *a: self.calls.append(('builtin', a))
        xbmc.executeJSONRPC = lambda *a: json.dumps({'result': {'favourites': []}})
        xbmc.Player = lambda: types.SimpleNamespace(play=lambda *a: self.calls.append(('play', a)))
        xbmc.Monitor = lambda: types.SimpleNamespace(abortRequested=lambda: False)
        gui = modules['xbmcgui']; gui.ListItem = Item; gui.getCurrentWindowId = lambda: 10025
        gui.Window = lambda *a: types.SimpleNamespace(getProperty=lambda k: self.props.get(k, ''),
                setProperty=self.props.__setitem__, clearProperty=lambda k: self.props.pop(k, None))
        gui.Dialog = lambda: types.SimpleNamespace(input=lambda *a: 'Weekend')
        common = modules['common']; common.addon_profile = lambda: self.root
        common.setting_bool = lambda *a: True; common.read_json = read
        common.atomic_json = write; common.persistence_scope = scope
        exp = modules['experience']; exp.artwork = lambda *a: a[0]; exp.commands = lambda *a: []
        exp.stable_route = lambda v: v; exp.number = lambda v, default=0: float(v or default)
        exp.verified_source = lambda entry, route: route or ''
        modules['persistence_participant'].AdmissionClosed = RuntimeError
        modules['infinity_settings'].choose = choose
        modules['information'].show_information = modal
        modules['provider_inventory'].eligible = lambda *a, **kw: ([], [])
        patcher = patch.dict(sys.modules, modules); patcher.start(); self.addCleanup(patcher.stop)
        self.hub = load('resume_hub', CC / 'resume_hub.py')
        self.hub.publish_home = lambda data: None; self.hub.flush_kodi_sync = lambda *a, **kw: None
        self.metadata = load('title_metadata', CC / 'title_metadata.py')
        self.selection = load('selection_contract', CC / 'selection_contract.py')
        with patch.object(sys, 'argv', ['plugin.py', '1', '']):
            self.plugin = load('universal_popup', CC / 'plugin.py')
        self.plugin._favourite = lambda *a: (None, None)
        self.plugin.navigation_target = lambda entry, *a, **kw: entry.get('source') or ''
        self.path = self.root / self.hub.CONTINUE_FILE
        self.data = dict(schema=2, revision=7, items={}, watched={}, watchlist={}, collection={},
                         later={}, lists={}, sources={'f' * 64: {'route': 'original'}},
                         navigation_recovery={'keep': {'success_verified': True, 'route': 'remembered'}},
                         extension={'keep': [1, 2]})
        self.write()
    def write(self): self.path.write_text(json.dumps(self.data))
    def saved(self): return json.loads(self.path.read_text())
    def movie(self, ident='603', **kwargs):
        identity = self.hub.media_identity('movie', {'tmdb': ident})
        return dict(key=self.hub.identity_key(identity), identity=identity, media='movie',
                    title='Same label', label='Same label', source='plugin://plugin.video.umbrella/?tmdb=' + ident,
                    **kwargs)
    def popup(self, entry, bucket=''):
        return self.plugin.show_item_menu(entry['key'], bucket=bucket, incoming=entry if not bucket else None)

    def test_explicit_save_and_remove_from_unsaved_title_preserve_other_owners(self):
        entry = self.movie(information={'plot': 'Complete original.\nFinal sentence.'})
        original = deepcopy(self.data)
        self.choice = 'Save for Later'; self.assertTrue(self.popup(entry))
        after = self.saved(); self.assertEqual(after['later'][entry['key']]['source'], entry['source'])
        self.assertEqual(after['later'][entry['key']]['information'], entry['information'])
        self.assertEqual(after['items'], {})
        self.choice = 'Remove from Save for Later'; self.assertTrue(self.popup(entry))
        after = self.saved(); self.assertEqual(after['later'], {})
        for key in ('items', 'watched', 'watchlist', 'collection', 'sources', 'navigation_recovery', 'extension'):
            self.assertEqual(after[key], original[key])

    def test_save_uses_exact_selected_saved_bucket_not_another_buckets_route(self):
        old = self.movie(); selected = dict(old, source='plugin://plugin.video.seren/?exact=603')
        self.data['items'][old['key']] = old
        self.data['watchlist'][old['key']] = selected; self.write()
        self.choice = 'Save for Later'; self.assertTrue(self.popup(selected, 'watchlist'))
        after = self.saved(); self.assertEqual(after['later'][old['key']]['source'], selected['source'])
        self.assertEqual(after['items'][old['key']], old)

    def test_saved_later_removal_uses_verified_identity_across_sections(self):
        entry = self.movie(); alias = dict(entry, key='a' * 64, source='original-saved-route')
        unrelated = self.movie('604')
        self.data['later'] = {alias['key']: alias, unrelated['key']: unrelated}; self.write()
        rows = self.plugin._menu_rows(entry, self.data)
        self.assertIn(('Remove from Save for Later', 'remove-later', ''), rows)
        self.assertNotIn(('Save for Later', 'save-later', ''), rows)
        self.choice = 'Remove from Save for Later'; self.assertTrue(self.popup(entry))
        self.assertEqual(self.saved()['later'], {unrelated['key']: unrelated})

    def test_conflicting_ids_cannot_remove_or_overwrite_saved_title(self):
        entry = self.movie(); old = dict(entry, identity=self.hub.media_identity('movie', {'tmdb': '604'}))
        self.data['later'][entry['key']] = old; self.write(); before = self.path.read_bytes()
        self.choice = 'Save for Later'; self.assertFalse(self.popup(entry))
        self.assertEqual(self.path.read_bytes(), before)

    def test_cancel_preserves_view_and_does_not_enter_writer(self):
        before = self.path.read_bytes(); self.assertFalse(self.popup(self.movie()))
        self.assertEqual(self.path.read_bytes(), before); self.assertEqual(self.calls, [])
        self.assertEqual(self.writers, 0)

    def test_info_keeps_entire_synopsis_and_uses_no_progress_writer(self):
        plot = '  Original\n' + ('A complete unshortened sentence. ' * 4000) + '\nFINAL END.  '
        tag = types.SimpleNamespace(getPlot=lambda: plot, getDuration=lambda: 6035,
                                    getYear=lambda: 2024, getCast=lambda: 'Real Actor as Role')
        entry = self.movie(information=self.metadata.capture(types.SimpleNamespace(getVideoInfoTag=lambda: tag)))
        self.choice = 'Information'; before = self.path.read_bytes()
        self.assertFalse(self.popup(entry))
        item, shown, options = self.modal_calls[0]
        self.assertEqual(item.info['plot'], plot); self.assertEqual(item.info['duration'], 6035)
        self.assertEqual(item.info['year'], 2024); self.assertEqual(shown['information']['cast'], 'Real Actor as Role')
        self.assertEqual(self.path.read_bytes(), before); self.assertEqual(self.writers, 0)
        self.assertEqual(self.calls, [])

    def test_information_play_reuses_latest_verified_resume_and_original_route(self):
        entry = self.movie(position=110, duration=6000)
        self.data['items'][entry['key']] = entry; self.write()
        self.choice = 'Information'; self.modal_action = 'play'
        def update():
            self.data['items'][entry['key']]['position'] = 222; self.write()
        self.modal_mutation = update
        self.assertTrue(self.popup(entry, 'continue'))
        name, args = self.calls[-1]; self.assertEqual(name, 'play'); self.assertEqual(args[0], entry['source'])
        self.assertEqual(args[1].properties['ResumeTime'], '222.0'); self.assertEqual(self.writers, 0)

    def test_trailer_never_executes_builtin_or_guessed_title(self):
        for invalid in ('RunPlugin(plugin://unverified/)', 'javascript:evil()', 'https://a/\nRunScript(x)'):
            self.assertEqual(self.metadata.trailer_route(invalid), '')
        entry = self.movie(information={'trailer': 'https://example.invalid/exact-original-trailer.mp4'})
        self.choice = 'Information'; self.modal_action = 'trailer'
        self.assertTrue(self.popup(entry)); self.assertEqual(self.calls[-1], ('play', (entry['information']['trailer'],)))
        self.assertEqual(self.writers, 0)

    def test_disabled_trailer_provider_is_not_dispatched(self):
        entry = self.movie(information={'trailer': 'plugin://plugin.video.youtube/?video_id=original'})
        self.choice = 'Information'; self.modal_action = 'trailer'; self.available = False
        self.assertFalse(self.popup(entry)); self.assertEqual(self.calls, [])

    def test_stale_popup_does_not_reverse_new_list_membership(self):
        entry = self.movie(); self.choice = 'Save for Later'
        def save_elsewhere():
            self.data['later'][entry['key']] = dict(entry, source='other-verified-selected-route'); self.write()
        self.selection_mutation = save_elsewhere
        self.assertFalse(self.popup(entry))
        self.assertEqual(self.saved()['later'][entry['key']]['source'], 'other-verified-selected-route')

    def test_trackit_functions_are_ast_identical(self):
        before = ast.parse((BASE / 'plugin.py').read_text()); after = ast.parse((CC / 'plugin.py').read_text())
        for name in ('_target', 'navigation_target', 'recover_entry', 'play_saved'):
            old = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == name)
            new = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertEqual(ast.dump(old), ast.dump(new), name)

    def test_actual_playback_capture_has_one_rpc_and_retains_original_fallback(self):
        tree = ast.parse((CC / 'service.py').read_text())
        method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_continue_player_item')
        calls = []; item = {'type': 'movie', 'title': 'Exact', 'uniqueid': {'tmdb': '603'}, 'plot': 'Last sentence.'}
        def rpc(method, params):
            calls.append((method, params)); return {'result': {'item': item}}
        env = {'jsonrpc': rpc}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'actual-start-capture', 'exec'), env)
        self.assertEqual(env['_continue_player_item'](7), item)
        self.assertEqual(len(calls), 1); self.assertIn('plot', calls[0][1]['properties'])
        self.assertIn('uniqueid', calls[0][1]['properties'])
        calls.clear()
        def fallback(method, params):
            calls.append((method, params))
            return {'error': 'unsupported descriptive property'} if len(calls) == 1 else {'result': {'item': item}}
        env['jsonrpc'] = fallback
        self.assertEqual(env['_continue_player_item'](7), item)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][1]['properties'], ['title', 'showtitle', 'season', 'episode', 'file', 'thumbnail', 'art', 'uniqueid'])

    def test_actual_identity_capture_and_progress_preserve_full_description_without_route_change(self):
        item = dict(type='movie', title='Original title', file='plugin://original/?movie=603',
                    uniqueid={'tmdb': '603'}, plot='  Full original synopsis. Final sentence.  ',
                    year=2024, runtime=6035, cast=[{'name': 'Actor', 'role': 'Role'}])
        results = []
        for path in (BASE / 'service.py', CC / 'service.py'):
            tree = ast.parse(path.read_text())
            method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_continue_identity')
            env = dict(hub=self.hub, xbmc=sys.modules['xbmc'], setting_bool=lambda *a: True,
                       source_identity=lambda *a: None)
            exec(compile(ast.Module(body=[method], type_ignores=[]), 'actual-identity-capture', 'exec'), env)
            results.append(env['_continue_identity'](item))
        original, captured = results
        self.assertEqual({k: v for k, v in captured.items() if k != 'information'}, original)
        self.assertEqual(captured['information']['plot'], item['plot'])
        self.assertEqual(captured['information']['cast'], 'Actor as Role')
        captured.update(position=35, duration=6050, updated=100)
        data, key = self.hub.record_progress(self.data, captured)
        original_route = data['items'][key]['source']
        data, key = self.hub.record_progress(data, dict(captured, source='other-provider', information={'year': 2025}, updated=200))
        self.assertEqual(data['items'][key]['information']['plot'], item['plot'])
        self.assertEqual(data['items'][key]['source'], original_route)
        self.assertEqual(data['navigation_recovery'], self.data['navigation_recovery'])
        self.assertEqual(self.metadata.from_entry(data['items'][key])['duration'], 6050)

    def test_non_infinity_skin_cannot_open_popup_or_touch_records(self):
        sys.modules['xbmc'].getSkinDir = lambda: 'skin.other'
        self.choice = 'Save for Later'; before = self.path.read_bytes()
        self.assertFalse(self.popup(self.movie()))
        self.assertEqual(self.path.read_bytes(), before); self.assertEqual(self.writers, 0)
        self.assertEqual(self.calls, []); self.assertEqual(self.modal_calls, [])

    def test_single_provider_handler_passes_exact_selection_and_always_ends_directory(self):
        calls = []; self.plugin.PARAMS = dict(action='search-provider', media='tv', query='Original query', provider='plugin.video.seren')
        sys.modules['xbmcplugin'].endOfDirectory = lambda *a, **kw: calls.append(('end', a, kw))
        with patch.dict(sys.modules, {'infinity_search': types.SimpleNamespace(search_provider=lambda *a: calls.append(('search', a)))}):
            self.plugin.main()
        self.assertEqual(calls[0], ('search', (1, 'tv', 'Original query', 'plugin.video.seren')))
        self.assertEqual(calls[1][0], 'end')


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(QuickActions))
    (HERE / 'QUICK-ACTIONS-HOST.json').write_text(json.dumps(dict(
        host='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
        scope='Quick actions/metadata actual Python with mocked Kodi APIs',
        android17='NOT RUN', physical_fold='NOT RUN', shutdown='NOT RUN'), indent=2) + '\n')
    sys.exit(not result.wasSuccessful())
