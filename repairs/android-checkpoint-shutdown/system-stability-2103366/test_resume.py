"""Actual shipped Resume scripts: episode routing, state preservation and timing."""
import argparse
import copy
import json
import runpy
import sys
import unittest
from pathlib import Path
from unittest import mock

p = argparse.ArgumentParser()
p.add_argument('--runtime', required=True)
a = p.parse_args()
sys.argv = [sys.argv[0], '--runtime', a.runtime]
f = runpy.run_path(str(Path(__file__).parents[1] / 'runtime-tests/test_runtime_checkpoint.py'), run_name='repair_fixtures')
hub, plugin = f['hub'], f['plugin']
KEY = f['KEY']


class ResumeRepairTests(f['RuntimeTests']):
    def completed(self, season=1, episode=2, provider='umbrella'):
        entry = dict(key=KEY, media='tv', tmdb='123', tvdb='456', imdb='ttEpisode',
                     season=season, episode=episode, showtitle='Example', title='Old episode',
                     dbid=42, stable_source='plugin://plugin.video.' + provider + '/?season=1&episode=2',
                     source='https://private.invalid/expiring', position=897, duration=900,
                     percentage=99, poster='old-episode.jpg', fanart='old-episode-bg.jpg',
                     watched_at=1234, updated=1234)
        return dict(watched={KEY: entry}, items={}, sources={KEY: {'route': entry['stable_source']}})

    def test_next_resolves_new_episode_never_inherits_old_source(self):
        for provider in ('umbrella', 'pov', 'seren'):
            for source_memory in (True, False):
                data = self.completed(provider=provider)
                original = copy.deepcopy(data)
                candidate = hub.next_episodes(data)[0]
                self.assertEqual((candidate['season'], candidate['episode']), (1, 3))
                self.assertNotEqual(candidate['key'], KEY)
                for field in ('dbid', 'stable_source', 'source', 'duration', 'imdb', 'poster', 'fanart'):
                    self.assertNotIn(field, candidate)
                # Defence in depth also covers candidates made by an old caller.
                contaminated = dict(candidate, stable_source=data['watched'][KEY]['stable_source'],
                                    source=data['watched'][KEY]['source'])
                memories = {candidate['key']: {'route': data['watched'][KEY]['stable_source']}}
                render = dict(source_memory=source_memory, installed={}, tier='standard')
                with mock.patch.object(plugin, '_has_addon', return_value=True):
                    target = plugin._target(contaminated, memories, render)
                self.assertIn('tmdb_id=123', target)
                self.assertIn('season=1&episode=3', target)
                self.assertNotIn(provider, target)
                self.assertEqual(plugin._context(candidate, data), [])
                self.assertEqual(data, original)

    def test_old_episode_replay_keeps_own_route(self):
        data = self.completed()
        with mock.patch.object(plugin, '_has_addon', return_value=True):
            self.assertEqual(plugin._target(data['watched'][KEY], data['sources']), data['watched'][KEY]['stable_source'])

    def test_unfinished_later_season_keeps_verified_position_and_provider(self):
        data = self.completed(season=1, episode=12)
        key = 'b' * 64
        current = dict(data['watched'][KEY], key=key, season=2, episode=1, position=417.125,
                       stable_source='plugin://plugin.video.pov/?season=2&episode=1')
        data['items'][key] = current
        values = hub.next_episodes(data)
        self.assertEqual(values, [current])
        with mock.patch.object(plugin, '_has_addon', return_value=True):
            self.assertEqual(plugin._target(values[0], data['sources']), current['stable_source'])

    def test_specials_and_exact_numbers(self):
        for season, episode in ((0, 0), (0, 3), ('0', '3'), (2, 8)):
            value = hub.next_episodes(self.completed(season, episode))[0]
            self.assertEqual((value['season'], value['episode']), (int(season), int(episode) + 1))
        for invalid in (None, '', -1, 'missing', 1.5, True, 'nan', '1.0'):
            self.assertEqual(hub.next_episodes(self.completed(season=invalid)), [])
            self.assertEqual(hub.next_episodes(self.completed(episode=invalid)), [])

    def test_missing_helper_or_metadata_is_unavailable_without_network(self):
        for change in ({'tmdb': ''}, {'tmdb': '', 'tvdb': ''}, {'tmdb': 'invalid'}):
            data = self.completed()
            data['watched'][KEY].update(change)
            for value in hub.next_episodes(data):
                with mock.patch.object(plugin, '_has_addon', return_value=False), mock.patch.object(plugin.xbmc, 'executeJSONRPC', side_effect=AssertionError('network/RPC during list')):
                    self.assertEqual(plugin._target(value, data['sources']), '')
        value = hub.next_episodes(self.completed())[0]
        value['episode'] = None
        with mock.patch.object(plugin, '_has_addon', return_value=True):
            self.assertEqual(plugin._target(value), '')

    def test_offline_restart_retains_authoritative_history_and_toggles(self):
        data = hub.save(self.profile, self.completed())
        saved = (self.profile / hub.CONTINUE_FILE).read_bytes()
        hub._view_cache = None
        restored = hub.load_view(self.profile)
        self.assertEqual(hub.next_episodes(restored)[0]['episode'], 3)
        self.assertEqual((self.profile / hub.CONTINUE_FILE).read_bytes(), saved)
        self.assertEqual(restored['watched'], data['watched'])
        unwatched, _ = hub.mark_unwatched_data(restored, KEY)
        self.assertNotIn(KEY, unwatched['watched'])
        # Removing watched state does not invent a new completion or play count.
        self.assertEqual(hub.next_episodes(unwatched), [])

    def test_timing_is_numeric_bounded_and_cannot_report_credentials(self):
        lines = []
        with mock.patch.object(hub.xbmc, 'log', side_effect=lambda row, level: lines.append(row)):
            hub.trace_timing('snapshot_load', hub.time.monotonic(), request='n123', media='tv', items=2,
                             route='https://secret.invalid/token', owner='credential', title='Private title')
            hub.trace_timing('unsafe\nline', title='private')
        self.assertEqual(len(lines), 1)
        row = json.loads(lines[0].split(' ', 1)[1])
        self.assertEqual(set(row), {'schema', 'stage', 'elapsed_ms', 'monotonic_ms', 'request', 'media', 'items', 'pid'})
        self.assertNotIn('secret', lines[0])
        with mock.patch.object(hub.xbmc, 'log', side_effect=RuntimeError('logging unavailable')):
            hub.trace_timing('plugin_complete', items=1)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResumeRepairTests))
    sys.exit(0 if result.wasSuccessful() else 1)
