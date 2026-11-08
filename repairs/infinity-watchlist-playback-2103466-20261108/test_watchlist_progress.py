"""Selected Watchlist host cases against actual overlay functions; no Kodi app."""
from __future__ import annotations

import copy
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest
from contextlib import nullcontext
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
BASE = Path('/workspace/scratch/infinity-watchlist-2103466/assets/addons/script.infinity.commandcenter')
OVERLAY = HERE / 'overlay/script.infinity.commandcenter'


def load_hub():
    common = types.ModuleType('common')
    common.persistence_scope = nullcontext
    common.setting_bool = lambda *args: True
    common.read_json = lambda path, default: json.loads(path.read_text()) if path.exists() else default
    common.atomic_json = lambda path, data: path.write_text(json.dumps(data))
    sys.modules['common'] = common
    sys.modules['xbmc'] = types.SimpleNamespace(log=lambda *args: None, getSkinDir=lambda: 'skin.infinity.diggz')
    sys.modules['xbmcaddon'] = types.SimpleNamespace(Addon=lambda provider: (_ for _ in ()).throw(RuntimeError('Not installed')))
    sys.modules['xbmcgui'] = types.SimpleNamespace()
    sys.modules['xbmcvfs'] = types.SimpleNamespace(translatePath=lambda path: '/testprofile' if path == 'special://profile' else path)
    sys.path.insert(0, str(BASE))
    sys.path.insert(0, str(OVERLAY))
    spec = importlib.util.spec_from_file_location('watchlist_test_hub', OVERLAY / 'resume_hub.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules['resume_hub'] = module
    sys.modules.pop('saved_playback', None)
    return module


class WatchlistProgress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = load_hub()

    def setUp(self):
        self.data = {'schema': 2, 'revision': 10, 'items': {}, 'watched': {},
                     'watchlist': {}, 'resume_hidden': {}, 'unknown_extension': {'keep': [1, 2]}}

    def row(self, name, ids, *, media='movie', season=-1, episode=-1,
            scope=None, position=120.0, duration=1200.0, updated=100, revision=11,
            occurrence='1' * 32):
        identity = self.hub.media_identity(media, ids, season, episode,
                                         ids if scope == 'show_episode' else None)
        return {'key': hashlib.sha256(name.encode()).hexdigest(), 'identity': identity,
                'media': media, 'season': season, 'episode': episode,
                'title': 'Same title', 'source': 'plugin://plugin.video.umbrella/?original=' + name,
                'position': position, 'duration': duration, 'percentage': position / duration * 100,
                'updated': updated, 'resume_revision': revision, 'playback_occurrence': occurrence}

    def item(self, row):
        self.data['items'][row['key']] = row
        return row

    def select(self, saved):
        before = copy.deepcopy(self.data)
        result = self.hub.watchlist_progress(self.data, saved)
        self.assertEqual(self.data, before)
        return result

    def test_movie_fresh_position_and_original_saved_snapshot_unchanged(self):
        saved = self.row('saved', {'tmdb': '603'}, position=0)
        self.data['watchlist'][saved['key']] = copy.deepcopy(saved)
        actual = self.item(self.row('actual', {'tmdb': '603', 'imdb': 'tt0133093'}, position=321))
        self.assertEqual(self.select(saved)['position'], 321)
        actual['position'] = 3
        actual['resume_revision'] = 12
        self.assertEqual(self.select(saved)['position'], 3)
        self.assertEqual(self.data['watchlist'][saved['key']], saved)

    def test_exact_episode_never_selects_newer_other_episode_or_season(self):
        saved = self.row('saved', {'tmdb': '100'}, media='tv', season=1, episode=1, scope='show_episode')
        exact = self.item(self.row('exact', {'tmdb': '100'}, media='tv', season=1, episode=1,
                                   scope='show_episode', updated=100))
        self.item(self.row('newer', {'tmdb': '100'}, media='tv', season=1, episode=5,
                           scope='show_episode', updated=300))
        self.item(self.row('season2', {'tmdb': '100'}, media='tv', season=2, episode=1,
                           scope='show_episode', updated=400))
        self.assertEqual(self.select(saved)['key'], exact['key'])

    def test_duplicate_agreeing_ids_choose_newest_persisted_revision(self):
        saved = self.row('saved', {'tmdb': '603'})
        self.item(self.row('older', {'tmdb': '603', 'imdb': 'tt0133093'}, revision=11))
        recent = self.item(self.row('newer', {'imdb': 'tt0133093'}, revision=12, position=222))
        self.assertEqual(self.select(saved)['key'], recent['key'])

    def test_transitive_conflicting_ids_quarantine_entire_component(self):
        saved = self.row('saved', {'tmdb': '603'})
        self.item(self.row('left', {'tmdb': '603', 'imdb': 'tt0133093'}))
        self.item(self.row('right', {'tmdb': '604', 'imdb': 'tt0133093'}))
        self.assertIsNone(self.select(saved))

    def test_similar_titles_and_namespaces_do_not_match(self):
        saved = self.row('saved', {'tmdb': '603'})
        self.item(self.row('other', {'tmdb': '604'}))
        self.item(self.row('namespace', {'tvdb': '603'}))
        self.assertIsNone(self.select(saved))

    def test_newest_hidden_alias_does_not_reveal_old_visible_alias(self):
        saved = self.row('saved', {'tmdb': '603'})
        self.item(self.row('older', {'tmdb': '603'}, updated=100))
        newest = self.item(self.row('newest', {'tmdb': '603'}, updated=200))
        self.data['resume_hidden'][newest['key']] = {'occurrence': newest['playback_occurrence']}
        self.assertIsNone(self.select(saved))

    def test_completed_occurrence_cannot_resume_but_new_replay_can(self):
        saved = self.row('saved', {'tmdb': '603'})
        actual = self.item(self.row('actual', {'tmdb': '603'}, updated=200))
        watched = self.row('watched', {'tmdb': '603'}, updated=200, revision=12)
        watched.update(watched=True, watched_at=200, completed_occurrence=actual['playback_occurrence'])
        self.data['watched'][watched['key']] = watched
        self.assertIsNone(self.select(saved))
        actual.update(updated=201, resume_revision=13, playback_occurrence='2' * 32, position=4)
        self.assertEqual(self.select(saved)['position'], 4)

    def test_manual_watched_hides_older_progress(self):
        saved = self.row('saved', {'tmdb': '603'})
        self.item(self.row('actual', {'tmdb': '603'}, updated=100))
        watched = self.row('manual', {'tmdb': '603'}, updated=101, revision=12)
        watched.update(watched=True, watched_at=101)
        self.data['watched'][watched['key']] = watched
        self.assertIsNone(self.select(saved))

    def test_invalid_nonfinite_and_completed_offsets_are_rejected(self):
        saved = self.row('saved', {'tmdb': '603'})
        for position, duration in [(-1, 1200), (math.inf, 1200), (math.nan, 1200),
                                   (120, math.inf), (120, 0), (1200, 1200), (1190, 1200)]:
            with self.subTest(position=position, duration=duration):
                actual = self.row('actual', {'tmdb': '603'})
                actual.update(position=position, duration=duration)
                self.data['items'] = {actual['key']: actual}
                self.assertIsNone(self.hub.watchlist_progress(self.data, saved))

    def test_reload_retains_exact_position_and_unknown_extension(self):
        saved = self.row('saved', {'tmdb': '603'})
        self.item(self.row('actual', {'tmdb': '603'}, position=345.125))
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder)
            self.hub.save(profile, self.data)
            restored = load_hub().load(profile)
            self.assertEqual(self.hub.watchlist_progress(restored, saved)['position'], 345.125)
            self.assertEqual(restored['unknown_extension'], self.data['unknown_extension'])

    def test_show_and_season_are_never_playable_progress_selectors(self):
        for kind in ('tvshow', 'season'):
            saved = {'key': 'a' * 64, 'media': 'tv', 'season': 1, 'episode': -1,
                     'identity': self.hub.show_identity(kind, {'tmdb': '100'}, 1)}
            self.assertIsNone(self.select(saved))

    def test_folder_popup_rows_remain_exact_baseline_behavior(self):
        modules = []
        for path in (BASE / 'plugin.py', OVERLAY / 'plugin.py'):
            tree = ast.parse(path.read_text())
            method = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and
                          node.name == '_menu_rows')
            env = {'hub': self.hub, 'number': lambda value: float(value or 0),
                   '_menu_resume': lambda *args: {'position': 123}, '_later_keys': lambda *args: []}
            exec(compile(ast.Module(body=[method], type_ignores=[]), 'actual-menu-rows', 'exec'), env)
            modules.append(env)
        for kind in ('tvshow', 'season'):
            saved = {'key': 'a' * 64, 'media': 'tv', 'season': 1, 'episode': -1,
                     'source': 'plugin://plugin.video.umbrella/?original=folder',
                     'identity': self.hub.show_identity(kind, {'tmdb': '100'}, 1)}
            before, after = (env['_menu_rows'](saved, self.data, bucket='watchlist') for env in modules)
            self.assertEqual(after, before)

    def test_existing_exact_provider_proof_can_join_raw_and_show_episode_scopes(self):
        from infinity_modules.watchedbridge import bridge_state, provider_contracts
        saved = self.row('saved', {'tmdb': '100'}, media='tv', season=1, episode=1)
        actual = self.item(self.row('actual', {'tmdb': '100'}, media='tv', season=1, episode=1,
                                   scope='show_episode'))
        proof = {'provider': 'plugin.video.umbrella',
                 'proof': provider_contracts.CATALOG['plugin.video.umbrella']['proof'],
                 'identity': bridge_state.identity(saved)}
        self.data[provider_contracts.PROOFS] = {saved['key']: proof}
        self.assertEqual(self.select(saved)['key'], actual['key'])
        proof['identity'] = dict(proof['identity'], episode=5)
        self.assertIsNone(self.select(saved))

    def test_list_item_watchlist_projection_keeps_original_route_and_key(self):
        class ListItem:
            def __init__(self, **kwargs):
                self.properties = {}
                self.kwargs = kwargs
            def setProperty(self, name, value): self.properties[name] = value
            def setPath(self, value): self.kwargs['path'] = value
            def setInfo(self, *args): pass
            def setUniqueIDs(self, *args): pass
            def setArt(self, *args): pass
            def addContextMenuItems(self, *args): pass
        sys.modules['title_metadata'] = types.SimpleNamespace(from_entry=lambda entry: {})
        sys.modules['selection_contract'] = types.SimpleNamespace(publish=lambda *args: None)
        tree = ast.parse((OVERLAY / 'plugin.py').read_text())
        methods = [node for node in tree.body if isinstance(node, ast.FunctionDef) and
                   node.name in ('_apply_identity', '_list_item', '_watchlist_target')]
        env = {'hub': self.hub, 'number': lambda value: float(value or 0),
               'navigation_target': lambda entry, *args: entry['source'],
               '_url': lambda **kwargs: 'plugin://script.infinity.commandcenter/?' + urlencode(kwargs), '_context': lambda *args: [],
               'artwork': lambda value, *args: value,
               'xbmcgui': types.SimpleNamespace(ListItem=ListItem)}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'actual-watchlist-list-item', 'exec'), env)
        saved = self.row('saved', {'tmdb': '603'}, position=0)
        actual = self.item(self.row('actual', {'tmdb': '603'}, position=456))
        render = {'tier': 'standard', 'watched_data': self.data, 'watched_flags': {saved['key']: False}}
        target, item = env['_list_item'](saved, self.data, 'watchlist', render=render)
        self.assertIn('action=watchlist-play', target)
        self.assertEqual(item.properties['Infinity.Watchlist.Destination'], saved['source'])
        self.assertEqual(item.properties['StartOffset'], '456.0')
        self.assertEqual(item.properties['Infinity.ResumeHub.Key'], saved['key'])
        self.assertEqual(saved['position'], 0)
        actual['position'] = 5
        _, fresh = env['_list_item'](saved, self.data, 'watchlist', render=render)
        self.assertEqual(fresh.properties['StartOffset'], '5.0')
        # An ordinary saved-list bucket retains its original rendering path.
        _, untouched = env['_list_item'](saved, self.data, 'collection', render=render)
        self.assertEqual(untouched.properties['StartOffset'], '0')

    def service_writer(self, entry, position, duration):
        tree = ast.parse((OVERLAY / 'service.py').read_text())
        method = next(node for cls in tree.body if isinstance(cls, ast.ClassDef) and
                      cls.name == 'InfinityPlayer' for node in cls.body if isinstance(node, ast.FunctionDef)
                      and node.name == 'persist_continue')
        saves = []
        env = {'_serialized_progress': lambda fn: fn, 'setting_bool': lambda *args: True,
               '_load_continue': lambda profile: self.data,
               '_save_continue': lambda profile, data: saves.append(copy.deepcopy(data)),
               'hub': self.hub, 'time': types.SimpleNamespace(monotonic=lambda: 100, time=lambda: 200),
               'xbmc': types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz')}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'actual-service-writer', 'exec'), env)
        state = types.SimpleNamespace(profile=Path('/unused'), cw_item=copy.deepcopy(entry), cw_key=entry['key'],
                                      cw_occurrence=entry['playback_occurrence'], cw_pending=False, cw_last_save=0,
                                      getTime=lambda: position, getTotalTime=lambda: duration,
                                      isPlayingVideo=lambda: True)
        return env['persist_continue'], state, saves

    def test_natural_end_completion_retains_short_and_unknown_duration_semantics(self):
        for duration in (0, 10, 119):
            with self.subTest(duration=duration):
                self.data['items'] = {}
                self.data['watched'] = {}
                entry = self.row('short', {'tmdb': '603'})
                entry.update(duration=duration, position=0)
                writer, state, saves = self.service_writer(entry, 0, duration)
                writer(state, completed=True, force=True)
                self.assertEqual(self.data['watched'][entry['key']]['play_count'], 1)
                self.assertEqual(len(saves), 1)
                writer(state, completed=True, force=True)
                self.assertEqual(len(saves), 1)

    def test_95_percent_completion_is_independent_of_partial_duration_gate(self):
        entry = self.row('short', {'tmdb': '603'})
        writer, state, saves = self.service_writer(entry, 9.5, 10)
        writer(state, immediate=True)
        writer(state, immediate=True)
        self.assertEqual(self.data['watched'][entry['key']]['play_count'], 1)
        self.assertEqual(len(saves), 1)

    def test_new_partial_minimum_and_released_clock_do_not_create_false_progress(self):
        entry = self.row('actual', {'tmdb': '603'})
        entry['key'] = self.hub.identity_key(entry['identity'])
        for position, duration in ((29, 1200), (30, 6000), (60, 119)):
            with self.subTest(position=position, duration=duration):
                writer, state, saves = self.service_writer(entry, position, duration)
                writer(state, immediate=True)
                self.assertEqual(saves, [])
        writer, state, saves = self.service_writer(entry, 30, 1200)
        writer(state, immediate=True)
        self.assertEqual(self.data['items'][entry['key']]['position'], 30)
        state.getTotalTime = lambda: 0
        writer(state, force=True)
        self.assertEqual(self.data['items'][entry['key']]['position'], 30)
        self.assertEqual(len(saves), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
