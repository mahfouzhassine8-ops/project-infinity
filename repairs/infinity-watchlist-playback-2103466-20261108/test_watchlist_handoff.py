"""New missing Watchlist launch/AV integration cases; mocked Kodi, real code."""
import ast
import copy
import importlib
import json
import shutil
from pathlib import Path
import sys
import time
import types
import unittest
import tempfile
from urllib.parse import urlencode

from test_watchlist_progress import load_hub, BASE, OVERLAY


class Item:
    def __init__(self, **kwargs): self.properties = {}; self.path = kwargs.get('path', '')
    def setProperty(self, name, value): self.properties[name] = value
    def getProperty(self, name): return self.properties.get(name, '')
    def setPath(self, value): self.path = value
    def setInfo(self, *args): pass
    def setUniqueIDs(self, *args): pass
    def setArt(self, *args): pass
    def addContextMenuItems(self, *args): pass


class Home(Item):
    def clearProperty(self, name): self.properties.pop(name, None)


class Handoff(unittest.TestCase):
    def setUp(self):
        self.hub = load_hub()
        self.home = Home()
        self.plays = []
        xbmc = sys.modules['xbmc']
        xbmc.Player = lambda: types.SimpleNamespace(play=lambda route, item: self.plays.append((route, item)))
        sys.modules['xbmcgui'].Window = lambda ident: self.home
        sys.modules['xbmcgui'].ListItem = Item
        self.helper = importlib.import_module('saved_playback')
        self.verify_source = self.helper.verified_producer
        self.helper.verified_producer = lambda provider: provider in self.helper.PRODUCERS
        sys.modules.pop('selection_contract', None)
        self.selection = importlib.import_module('selection_contract')
        self.data = {'schema': 2, 'items': {}, 'watched': {}, 'watchlist': {}, 'resume_hidden': {}}
        self.hub.load_view = lambda profile: copy.deepcopy(self.data)
        self.route = 'plugin://plugin.video.umbrella/?action=play_Item&tmdb=603'
        identity = self.hub.media_identity('movie', {'tmdb': '603'})
        self.saved = {'key': self.hub.identity_key(identity), 'media': 'movie', 'identity': identity,
                      'title': 'Same title', 'source': self.route, 'stable_source': self.route,
                      'season': -1, 'episode': -1, 'position': 0}
        self.data['watchlist'][self.saved['key']] = self.saved
        self.env = self.plugin_functions()

    def plugin_functions(self):
        sys.modules['title_metadata'] = types.SimpleNamespace(from_entry=lambda entry: {})
        names = ('_watchlist_target', 'play_watchlist', '_list_item', '_apply_identity')
        nodes = [n for n in ast.parse((OVERLAY / 'plugin.py').read_text()).body
                 if isinstance(n, ast.FunctionDef) and n.name in names]
        env = {'hub': self.hub, 'PROFILE': Path('/testprofile/addon_data/script.infinity.commandcenter'),
               'xbmc': sys.modules['xbmc'], 'xbmcgui': sys.modules['xbmcgui'],
               'navigation_target': lambda entry, *args: entry['source'], 'number': lambda value: float(value or 0),
               'artwork': lambda value, *args: value, '_context': lambda *args: [],
               '_url': lambda **params: 'plugin://script.infinity.commandcenter/?' + urlencode(params),
               'recover_entry': lambda *args, **kwargs: None}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'actual-plugin-handoff', 'exec'), env)
        return env

    def progress(self, position=120):
        row = dict(self.saved, position=position, duration=1200, percentage=position / 12,
                   updated=100, resume_revision=10, playback_occurrence='1' * 32)
        self.data['items'][row['key']] = row
        return row

    def native_selected(self):
        token = 'a' * 32
        value = dict(schema=1, token=token, key=self.saved['key'], profile='/testprofile',
                     selection=self.selection.snapshot(self.saved, 'watchlist'), destination=self.route,
                     epoch_ms=int(time.time() * 1000))
        self.home.setProperty('Infinity.Watchlist.Selected', json.dumps(value))
        return token

    def origin(self, saved=None, route=None):
        saved = saved or self.saved
        return dict(schema=1, token='b' * 32, key=saved['key'], profile='/testprofile',
                    selection=self.selection.snapshot(saved, 'watchlist'), destination=route or self.route,
                    epoch_ms=int(time.time() * 1000), resume=0, resume_revision=0)

    def actual(self, origin=True):
        row = dict(type='movie', uniqueid={'tmdb': '603'}, file='https://stream/item', season=-1, episode=-1)
        if origin: row['infinity_watchlist_origin'] = self.origin()
        return row

    def test_direct_click_rechecks_offset_after_render_and_binds_exact_item(self):
        row = self.progress(120)
        _, rendered = self.env['_list_item'](self.saved, self.data, 'watchlist', render={'tier': 'standard'})
        self.assertEqual(rendered.getProperty('StartOffset'), '120.0')
        token = self.native_selected()
        row.update(position=345, resume_revision=11)
        self.assertTrue(self.env['play_watchlist'](self.saved['key'], token))
        route, item = self.plays[-1]
        self.assertEqual(route, self.route)
        self.assertEqual(item.path, self.route)
        self.assertEqual(item.getProperty('StartOffset'), '345.0')
        self.assertEqual(item.getProperty('Infinity.Watchlist.Launch'), self.home.getProperty('Infinity.Watchlist.Launch'))
        launch = json.loads(item.getProperty('Infinity.Watchlist.Launch'))
        self.assertEqual(launch['resume'], 345)
        self.assertEqual(launch['resume_revision'], 11)
        self.assertEqual(launch['selected_token'], token)
        self.assertEqual(self.saved['position'], 0)

    def test_url_without_native_selection_or_changed_snapshot_cannot_dispatch(self):
        self.assertFalse(self.env['play_watchlist'](self.saved['key']))
        token = self.native_selected()
        self.saved['source'] += '&changed=true'
        self.assertFalse(self.env['play_watchlist'](self.saved['key'], token))
        self.assertEqual(self.plays, [])

    def test_confirmed_popup_play_has_fresh_oneuse_descriptor_not_render_authority(self):
        self.progress(240)
        expected = self.selection.token(self.saved, 'watchlist')
        self.assertTrue(self.env['play_watchlist'](self.saved['key'], expected_selection=expected))
        first = json.loads(self.plays[-1][1].getProperty('Infinity.Watchlist.Launch'))
        self.assertNotIn('selected_token', first)
        self.assertTrue(self.env['play_watchlist'](self.saved['key'], expected_selection=expected))
        second = json.loads(self.plays[-1][1].getProperty('Infinity.Watchlist.Launch'))
        self.assertNotEqual(first['token'], second['token'])

    def test_actual_receipt_admits_route_but_same_title_ordinary_play_is_unchanged(self):
        entry = dict(self.saved, source='https://stream/item')
        ordinary = self.helper.admit(Path('/unused'), self.actual(False), entry)
        self.assertIs(ordinary, entry)
        admitted = self.helper.admit(Path('/unused'), self.actual(), entry)
        self.assertEqual(admitted['stable_source'], self.route)
        self.assertEqual(admitted['identity'], entry['identity'])
        self.assertIn('_watchlist_origin', admitted)

    def test_stale_profile_source_mismatch_and_conflicting_id_withhold_admission(self):
        entry = dict(self.saved)
        for alteration in ('profile', 'epoch', 'id', 'route'):
            with self.subTest(alteration=alteration):
                actual = self.actual()
                if alteration == 'profile': actual['infinity_watchlist_origin']['profile'] = '/other'
                if alteration == 'epoch': actual['infinity_watchlist_origin']['epoch_ms'] = 1
                if alteration == 'id': actual['uniqueid']['tmdb'] = '604'
                if alteration == 'route': actual['infinity_watchlist_origin']['destination'] += '&tmdb=604'
                self.assertIs(self.helper.admit(Path('/unused'), actual, entry), entry)

    def test_folder_episode_parent_proof_preserves_raw_identity_and_exact_season(self):
        identity = self.hub.show_identity('season', {'tmdb': '100'}, 2)
        anchor = dict(self.saved, key=self.hub.identity_key(identity), media='tv', identity=identity,
                      source='plugin://plugin.video.umbrella/?action=episodes&tmdb=100&season=2',
                      stable_source='', season=2, episode=-1)
        self.data['watchlist'] = {anchor['key']: anchor}
        route = 'plugin://plugin.video.umbrella/?action=play_Item&tmdb=100&season=2&episode=3'
        actual = dict(type='episode', uniqueid={'tmdb': '100'}, season=2, episode=3,
                      file='https://stream/episode', infinity_watchlist_origin=self.origin(anchor, route))
        raw = dict(media='tv', season=2, episode=3, identity=self.hub.media_identity('tv', {'tmdb': '100'}, 2, 3))
        admitted = self.helper.admit(Path('/unused'), actual, raw)
        self.assertTrue(admitted['show_ids_verified'])
        self.assertEqual(admitted['show_tmdb'], '100')
        self.assertEqual(admitted['identity'], raw['identity'])
        self.assertNotIn('verified_next', admitted)
        actual['season'] = 1
        self.assertIs(self.helper.admit(Path('/unused'), actual, raw), raw)

    def resume_method(self, actual, row):
        node = next(n for cls in ast.parse((OVERLAY / 'service.py').read_text()).body
                    if isinstance(cls, ast.ClassDef) and cls.name == 'InfinityPlayer'
                    for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_resume_watchlist')
        current = [copy.deepcopy(actual)]
        seeks = []
        env = {'setting_bool': lambda *args: True, 'hub': self.hub, 'xbmc': sys.modules['xbmc'],
               '_continue_player_item': lambda player_id: current[0]}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-scoped-resume', 'exec'), env)
        state = types.SimpleNamespace(profile=Path('/unused'), cw_item=row, isPlayingVideo=lambda: True,
                                      getTotalTime=lambda: 1200, getPlayingFile=lambda: actual['file'],
                                      seekTime=lambda value: seeks.append(value))
        return env['_resume_watchlist'], state, current, seeks

    def test_actual_start_seek_rechecks_nonce_exact_item_and_uses_current_progress(self):
        row = self.progress(321)
        actual = self.actual()
        method, state, current, seeks = self.resume_method(actual, row)
        method(state, 1, actual, actual['infinity_watchlist_origin'])
        self.assertEqual(seeks, [321])
        current[0]['infinity_watchlist_origin']['token'] = 'c' * 32
        method(state, 1, actual, actual['infinity_watchlist_origin'])
        self.assertEqual(seeks, [321])

    def test_changed_item_invalid_clock_seek_failure_and_zero_replay_are_safe(self):
        row = self.progress(321)
        actual = self.actual()
        method, state, current, seeks = self.resume_method(actual, row)
        current[0]['file'] = 'https://stream/other'
        method(state, 1, actual, actual['infinity_watchlist_origin'])
        self.assertEqual(seeks, [])
        current[0] = copy.deepcopy(actual)
        state.getTotalTime = lambda: 0
        method(state, 1, actual, actual['infinity_watchlist_origin'])
        self.assertEqual(seeks, [])
        state.getTotalTime = lambda: 1200
        state.seekTime = lambda value: (_ for _ in ()).throw(RuntimeError('Not seekable'))
        method(state, 1, actual, actual['infinity_watchlist_origin'])
        self.data['items'] = {}
        state.seekTime = lambda value: seeks.append(value)
        method(state, 1, actual, actual['infinity_watchlist_origin'])
        self.assertEqual(seeks, [0])

    def test_exact_runtime_emitter_pins_and_cached_stamp_detect_tampering(self):
        roots = {'plugin.video.umbrella': Path('/workspace/scratch/umbrella6800-publisher/plugin.video.umbrella'),
                 'plugin.video.pov': Path('/workspace/scratch/fold-source-audit/installed/plugin.video.pov')}
        self.helper.verified_producer = self.verify_source
        for provider, source in roots.items():
            contract = self.helper.PRODUCERS[provider]
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                for name in contract['files']:
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source / name, target)
                sys.modules['xbmcaddon'].Addon = lambda aid: types.SimpleNamespace(getAddonInfo=lambda field: {
                    'path': str(root), 'id': provider, 'version': contract['version']}[field])
                self.assertTrue(self.verify_source(provider))
                self.assertTrue(self.verify_source(provider))
                changed = root / next(name for name in contract['files'] if name != 'addon.xml')
                changed.write_bytes(changed.read_bytes() + b'\n# altered emitter\n')
                self.assertFalse(self.verify_source(provider))

    def test_changed_emitter_or_typed_coordinate_withholds_receipt_enrichment(self):
        actual = self.actual()
        entry = dict(self.saved)
        self.helper.verified_producer = lambda provider: False
        self.assertIs(self.helper.admit(Path('/unused'), actual, entry), entry)
        self.helper.verified_producer = lambda provider: True
        entry['identity'] = self.hub.media_identity('tv', {'tmdb': '603'}, 1, 1)
        entry.update(media='tv', season=1, episode=1)
        self.assertIs(self.helper.admit(Path('/unused'), actual, entry), entry)

    def test_actual_av_arm_existing_writer_series_resume_completion_and_replay(self):
        identity = self.hub.show_identity('tvshow', {'tmdb': '100'})
        anchor = dict(self.saved, key=self.hub.identity_key(identity), identity=identity, media='tv',
                      season=-1, episode=-1, source='plugin://plugin.video.umbrella/?action=seasons&tmdb=100',
                      stable_source='')
        self.data['watchlist'] = {anchor['key']: anchor}
        route = 'plugin://plugin.video.umbrella/?action=play_Item&tmdb=100&season=1&episode=2'
        actual = dict(type='episode', title='Episode', showtitle='Same title', uniqueid={'tmdb': '100'},
                      season=1, episode=2, file='https://stream/episode',
                      infinity_watchlist_origin=self.origin(anchor, route))
        sys.modules['title_metadata'].from_player_item = lambda item: {}
        sys.modules['xbmc'].getInfoLabel = lambda label: ''
        wanted = ('_continue_identity',)
        tree = ast.parse((OVERLAY / 'service.py').read_text())
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
        nodes += [node for cls in tree.body if isinstance(cls, ast.ClassDef) and cls.name == 'InfinityPlayer'
                  for node in cls.body if isinstance(node, ast.FunctionDef) and
                  node.name in ('_arm_continue', '_resume_watchlist', 'persist_continue')]
        writes, seeks = [], []
        env = {'hub': self.hub, 'xbmc': sys.modules['xbmc'], '_serialized_progress': lambda fn: fn,
               'setting_bool': lambda *args: True, '_active_video_player_id': lambda: 1,
               '_continue_player_item': lambda player_id: copy.deepcopy(actual),
               '_continue_show_identity': lambda *args: {}, 'source_identity': lambda *args: None,
               '_prop': lambda *args: '', 'log': lambda *args: None,
               '_load_continue': lambda profile: self.data,
               '_save_continue': lambda profile, data: writes.append(copy.deepcopy(data)),
               'time': types.SimpleNamespace(monotonic=lambda: 100, time=lambda: 1000)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'actual-av-to-writer', 'exec'), env)
        state = types.SimpleNamespace(profile=Path('/unused'), cw_occurrence='1' * 32, cw_item=None,
                                      cw_key=None, cw_pending=True, cw_last_save=0, experience=None,
                                      getTotalTime=lambda: 1200, getTime=lambda: 120,
                                      getPlayingFile=lambda: actual['file'], isPlayingVideo=lambda: True,
                                      seekTime=lambda offset: seeks.append(offset))
        state._resume_watchlist = types.MethodType(env['_resume_watchlist'], state)
        env['_arm_continue'](state)
        self.assertEqual(writes, [])  # Arming/identity admission never writes history.
        self.assertNotIn('_watchlist_origin', state.cw_item)
        self.assertTrue(state.cw_item['show_ids_verified'])
        self.assertEqual(state.cw_item['identity']['scope'], 'episode')
        env['persist_continue'](state, immediate=True)
        self.assertEqual(len(writes), 1)
        self.assertEqual(self.hub.progress_shows(self.data)[0]['episode'], 2)
        self.assertEqual(self.hub.next_episodes(self.data)[0]['episode'], 2)
        self.assertEqual(self.hub.watchlist_progress(self.data, state.cw_item)['position'], 120)
        env['persist_continue'](state, completed=True, force=True)
        self.assertEqual(self.hub.next_episodes(self.data), [])  # No guessed E+1.
        self.assertEqual(len(self.hub.progress_shows(self.data)), 1)
        watched = next(iter(self.data['watched'].values()))
        self.assertEqual(watched['play_count'], 1)
        env['persist_continue'](state, completed=True, force=True)
        self.assertEqual(next(iter(self.data['watched'].values()))['play_count'], 1)
        state.cw_occurrence = '2' * 32
        actual['infinity_watchlist_origin']['token'] = 'c' * 32
        env['_arm_continue'](state)
        self.assertEqual(seeks[-1], 0)
        env['persist_continue'](state, immediate=True)
        self.assertEqual(self.hub.next_episodes(self.data)[0]['episode'], 2)


if __name__ == '__main__': unittest.main(verbosity=2)
