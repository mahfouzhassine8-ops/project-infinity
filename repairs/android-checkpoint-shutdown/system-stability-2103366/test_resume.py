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
                     show_tmdb='123', show_tvdb='456', show_ids_verified=True,
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

    def test_episode_id_never_becomes_series_id(self):
        service = f['service']
        item = dict(type='episode', id=42, season=1, episode=2, showtitle='Example',
                    title='Old episode', uniqueid={'tmdb': '999'}, file='plugin://provider/episode')
        replies = [dict(result=dict(episodedetails=dict(episodeid=42, season=1, episode=2,
                    showtitle='Example', tvshowid=7))),
                   dict(result=dict(tvshowdetails=dict(tvshowid=7, title='Example', uniqueid={'tmdb':'123', 'tvdb':'456'})))]
        with mock.patch.object(service, 'jsonrpc', side_effect=replies) as rpc, mock.patch.object(service.xbmc,'getCondVisibility',return_value=True):
            entry = service._continue_identity(item)
        self.assertEqual(entry['tmdb'], '999')  # Old episode/key/source remain unchanged.
        self.assertEqual(entry['show_tmdb'], '123')
        self.assertTrue(entry['show_ids_verified'])
        self.assertEqual([c.args[0] for c in rpc.call_args_list],
                         ['VideoLibrary.GetEpisodeDetails', 'VideoLibrary.GetTVShowDetails'])
        data = dict(watched={entry['key']:entry}, items={})
        candidate = hub.next_episodes(data)[0]
        with mock.patch.object(plugin, '_has_addon', return_value=True), mock.patch.object(plugin.xbmc, 'executeJSONRPC', side_effect=AssertionError('RPC during listing')):
            target = plugin._target(candidate)
        self.assertIn('tmdb_id=123&season=1&episode=3', target)
        self.assertNotIn('999', target)
        with mock.patch.object(plugin, '_has_addon', return_value=True):
            resumed = plugin._target(entry, render=dict(source_memory=False,installed={}))
        self.assertIn('tmdb_id=123&season=1&episode=2',resumed)

    def test_ambiguous_legacy_ids_cannot_authorize_synthetic_route(self):
        data = self.completed()
        entry = data['watched'][KEY]
        for field in ('show_tmdb', 'show_tvdb', 'show_ids_verified'):
            entry.pop(field)
        original = copy.deepcopy(data)
        candidate = hub.next_episodes(data)[0]
        with mock.patch.object(plugin, '_has_addon', return_value=True):
            self.assertEqual(plugin._target(candidate), '')
            # A caller carrying an old ID or a forged/mismatched scope fails safely.
            for changes in ({'tmdb':'999'}, {'tmdb':'999', 'show_tmdb':'123', 'show_ids_verified':True},
                            {'tmdb':'123', 'show_tmdb':'123', 'show_ids_verified':1}):
                self.assertEqual(plugin._target(dict(candidate, **changes)), '')
        self.assertEqual(data, original)
        self.assertEqual(entry['stable_source'], original['watched'][KEY]['stable_source'])

    def test_native_library_identity_conflicts_and_errors_stay_unavailable(self):
        service=f['service']
        episode=dict(episodeid=42, season=1, episode=2, showtitle='Example', tvshowid=7)
        show=dict(tvshowid=7, title='Example', uniqueid={'tmdb':'123'})
        for update in ({'episodeid':43}, {'episodeid':True}, {'season':2}, {'episode':3},
                       {'showtitle':'Another show'}, {'tvshowid':0}, {'tvshowid':True}):
            with mock.patch.object(service,'jsonrpc',return_value={'result':{'episodedetails':dict(episode,**update)}}) as rpc, mock.patch.object(service.xbmc,'getCondVisibility',return_value=True):
                self.assertEqual(service._continue_show_identity('episode',42,1,2,'Example'),{})
                self.assertEqual(rpc.call_count,1)
        for update in ({'tvshowid':8}, {'tvshowid':True}, {'title':'Another show'},
                       {'uniqueid':{}}, {'uniqueid':{'tmdb':'0'}}, {'uniqueid':'bad'}):
            replies=[{'result':{'episodedetails':episode}}, {'result':{'tvshowdetails':dict(show,**update)}}]
            with mock.patch.object(service,'jsonrpc',side_effect=replies), mock.patch.object(service.xbmc,'getCondVisibility',return_value=True):
                self.assertEqual(service._continue_show_identity('episode',42,1,2,'Example'),{})
        for response in ({'error':{'message':'read failed'}},{'result':'bad'},None):
            with mock.patch.object(service,'jsonrpc',return_value=response), mock.patch.object(service.xbmc,'getCondVisibility',return_value=True):
                self.assertEqual(service._continue_show_identity('episode',42,1,2,'Example'),{})

    def test_no_new_reads_for_movies_unowned_streams_or_listing(self):
        service=f['service']
        with mock.patch.object(service,'jsonrpc',side_effect=AssertionError('unnecessary RPC')):
            for args in (('movie',42,1,2,'Example'), ('episode',-1,1,2,'Example'),
                         ('episode',True,1,2,'Example'), ('episode',42,1,2,'Example'), ('episode',42,1,2,''), ('episode',42,-1,2,'Example')):
                self.assertEqual(service._continue_show_identity(*args),{})
            self.assertNotIn('show_tmdb',service._continue_identity(dict(type='movie',title='Movie',uniqueid={'tmdb':'12'})))
            self.assertNotIn('show_tmdb',service._continue_identity(dict(type='episode',id=True,showtitle='Example',season=1,episode=2)))
        data=self.completed()
        with mock.patch.object(plugin.xbmc,'executeJSONRPC',side_effect=AssertionError('RPC during list')), mock.patch.object(plugin,'_has_addon',return_value=True):
            candidate=hub.next_episodes(data)[0]
            self.assertIn('episode=3',plugin._target(candidate))

    def test_verified_show_grouping_ignores_different_episode_ids(self):
        data=self.completed()
        old=dict(data['watched'][KEY], tmdb='998', episode=1)
        data['watched'][KEY]['tmdb']='999'
        data['watched']['c'*64]=old
        self.assertEqual(len(hub.next_episodes(data)),1)
        self.assertEqual(len(hub.progress_shows(data)),1)
        current=dict(data['watched'][KEY],tmdb='1000',season=2,episode=1,position=417.125,stable_source='plugin://plugin.video.pov/?season=2&episode=1')
        data['items']['b'*64]=current
        self.assertEqual(hub.next_episodes(data),[dict(current,key='b'*64)])
        different=dict(old,show_tmdb='',show_tvdb='123')
        self.assertNotEqual(hub._show_key(different,'d'*64),hub._show_key(old,KEY))

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
