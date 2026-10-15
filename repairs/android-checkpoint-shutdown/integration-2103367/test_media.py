"""Run actual resident service, journal, resolver and library sync boundaries."""
import argparse
import copy
import json
from pathlib import Path
import runpy
import sys
import unittest
from unittest import mock

p = argparse.ArgumentParser(); p.add_argument('--runtime', required=True)
a = p.parse_args(); sys.argv = [sys.argv[0], '--runtime', a.runtime]
f = runpy.run_path(str(Path(__file__).parents[1] / 'runtime-tests/test_runtime_checkpoint.py'), run_name='fixtures')
hub, service, plugin, KEY = (f[name] for name in ('hub', 'service', 'plugin', 'KEY'))


class MediaTests(f['RuntimeTests']):
    def test_actual_poll_threshold_stop_and_finalize_count_once(self):
        self.player.position = 897
        for _ in range(4):
            self.player.cw_last_save = 0
            self.player.persist_continue()
            self.assertEqual(hub.load(self.profile)['watched'][KEY]['play_count'], 1)
        self.prepare(); self.player.onPlayBackEnded()
        self.request('FINALIZE', player_freeze_complete=True); self.marker(); self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PARTICIPANT_COMPLETE')
        self.assertEqual(hub.load(self.profile)['watched'][KEY]['play_count'], 1)
        hub._view_cache = None
        self.assertEqual(hub.load_view(self.profile)['watched'][KEY]['play_count'], 1)

    def test_new_replay_counts_once_and_backward_seek_does_not_restore_continue(self):
        self.player.position = 897; self.player.persist_continue(force=True)
        original = hub.load(self.profile)['watched'][KEY]
        self.player.cw_item = dict(original, playback_occurrence='2' * 32)
        self.player.cw_key = KEY; self.player.cw_occurrence = '2' * 32
        self.player.cw_last_save = 0
        self.player.position = 417; self.player.persist_continue()
        self.assertIn(KEY, hub.load(self.profile)['items'])
        self.player.position = 897; self.player.cw_last_save = 0; self.player.persist_continue()
        self.assertEqual(hub.load(self.profile)['watched'][KEY]['play_count'], 2)
        self.player.position = 417; self.player.cw_last_save = 0; self.player.persist_continue()
        self.assertNotIn(KEY, hub.load(self.profile)['items'])
        self.player.onPlayBackEnded()
        self.assertEqual(hub.load(self.profile)['watched'][KEY]['play_count'], 2)

    def test_manual_mark_is_idempotent_and_unwatched_is_explicit(self):
        entry = dict(self.player.cw_item)
        data = {'items': {KEY: entry}}
        data, _ = hub.mark_watched_data(data, KEY)
        for _ in range(3): data, changed = hub.mark_watched_data(data, KEY); self.assertIsNone(changed)
        self.assertEqual(data['watched'][KEY]['play_count'], 1)
        data, _ = hub.mark_unwatched_data(data, KEY); self.assertNotIn(KEY, data['watched'])

    def test_namespaces_media_types_coordinates_and_titles_do_not_alias(self):
        values = [hub.media_identity('movie', {'tmdb':'123'}), hub.media_identity('movie', {'tvdb':'123'}),
                  hub.media_identity('tv', {'tmdb':'123'}, 1, 1), hub.media_identity('tv', {'tmdb':'123'}, 1, 2),
                  hub.media_identity('tv', {}, 1, 1, {'tmdb':'123'})]
        self.assertEqual(len({hub.identity_key(value) for value in values}), len(values))
        self.assertIsNone(hub.media_identity('movie', {}))
        self.assertIsNone(hub.media_identity('tv', {'tmdb':'123'}, True, 1))
        for item in ({'title':'Same'}, {'type':'movie','title':'Same'},
                     {'type':'tvshow','title':'Same','uniqueid':{'tmdb':'123'}},
                     {'type':'episode','title':'Episode','season':1,'episode':2}):
            self.assertIsNone(service._continue_identity(item))

    def test_legacy_compatibility_is_single_exact_route_not_bulk_title_merge(self):
        entry = dict(self.player.cw_item, source='plugin://plugin.video.pov/?movie=123')
        original = dict(entry); original.pop('identity'); original['key'] = 'b'*64
        data = {'items': {'b'*64: original}}
        before = copy.deepcopy(data)
        self.assertEqual(hub.compatible_key(data, entry), 'b'*64)
        self.assertEqual(data, before)
        other = dict(entry, source='plugin://plugin.video.umbrella/?movie=123')
        self.assertEqual(hub.compatible_key(data, other), hub.identity_key(entry['identity']))
        data['items']['c'*64] = dict(original)
        self.assertEqual(hub.compatible_key(data, entry), hub.identity_key(entry['identity']))

    def test_library_id_reuse_wrong_type_or_identity_never_mutates(self):
        for details in ({'movieid':43,'uniqueid':{'tmdb':'123'},'playcount':0},
                        {'movieid':42,'uniqueid':{'tvdb':'123'},'playcount':0},
                        {'movieid':42,'uniqueid':{'tmdb':'999'},'playcount':0},
                        {'episodeid':42,'uniqueid':{'tmdb':'123'},'playcount':0},
                        {'movieid':True,'uniqueid':{'tmdb':'123'},'playcount':0}):
            calls = []
            def rpc(raw):
                row = json.loads(raw); calls.append(row)
                return json.dumps({'result':{'moviedetails':details}})
            with mock.patch.object(hub.xbmc,'executeJSONRPC', side_effect=rpc):
                self.assertFalse(hub.sync_kodi_playcount(self.player.cw_item, True))
            self.assertFalse(any(row['method'].startswith('VideoLibrary.Set') for row in calls))

    def test_failed_identity_sync_stays_in_required_journal(self):
        entry = dict(self.player.cw_item, identity=hub.media_identity('movie',{'tmdb':'999'}))
        data = hub.load(self.profile); hub.queue_kodi_sync(data, entry, True); hub.save(self.profile, data)
        self.assertFalse(hub.flush_kodi_sync(self.profile))
        self.assertEqual(len(hub.load(self.profile)['pending_kodi_sync']), 1)

    def test_native_higher_playcount_preserved_outside_checkpoint(self):
        calls = []
        def rpc(raw):
            row = json.loads(raw); calls.append(row)
            return json.dumps({'result':{'moviedetails':{'movieid':42,'uniqueid':{'tmdb':'123'},'playcount':7}}})
        with mock.patch.object(hub.xbmc,'executeJSONRPC',side_effect=rpc):
            self.assertTrue(hub.sync_kodi_playcount(self.player.cw_item,True))
        self.assertEqual(len(calls),1)

    def show(self, season, episode, catalogue):
        replies = [dict(result=dict(episodedetails=dict(episodeid=42,season=season,episode=episode,showtitle='Show',tvshowid=7))),
                   dict(result=dict(tvshowdetails=dict(tvshowid=7,title='Show',uniqueid={'tmdb':'123'}))),
                   dict(result=dict(episodes=[dict(season=s,episode=e) for s,e in catalogue],limits={'total':len(catalogue)}))]
        with mock.patch.object(service,'jsonrpc',side_effect=replies), mock.patch.object(service.xbmc,'getCondVisibility',return_value=True):
            return service._continue_identity(dict(type='episode',id=42,season=season,episode=episode,
                showtitle='Show',title='Episode',uniqueid={'tmdb':'999'},file='plugin://plugin.video.pov/?episode=999'))

    def test_catalogue_cross_season_finale_specials_and_missing_next(self):
        for season,episode,catalogue,expected in ((1,12,[(1,12),(2,1)],(2,1)),
            (0,3,[(0,3),(0,8),(1,1)],(0,8)), (2,10,[(1,1),(2,10)],None),
            (0,8,[(0,8),(1,1)],None), (1,2,[(1,1),(1,3)],None)):
            entry = self.show(season,episode,catalogue)
            data = {'watched':{entry['key']:entry}}
            result = hub.next_episodes(data)
            if expected is None: self.assertEqual(result,[]); continue
            self.assertEqual((result[0]['season'],result[0]['episode']),expected)
            with mock.patch.object(plugin,'_has_addon',return_value=True):
                route = plugin._target(dict(result[0], stable_source=entry['source']))
            self.assertIn('tmdb_id=123',route); self.assertNotIn('999',route)
            self.assertNotIn('pov',route)

    def test_regular_episode_fallback_never_uses_episode_id_as_series(self):
        entry = dict(media='tv',season=1,episode=2,tmdb='999',updated=0)
        with mock.patch.object(plugin,'_has_addon',return_value=True):
            self.assertEqual(plugin._target(entry), '')
            original = dict(entry,stable_source='plugin://plugin.video.pov/?episode=999')
            self.assertEqual(plugin._target(original),original['stable_source'])
            verified = dict(entry,show_ids_verified=True,show_tmdb='123')
            self.assertIn('tmdb_id=123&season=1&episode=2',plugin._target(verified))

    def test_unavailable_catalogue_retains_verified_show_without_inventing_next(self):
        replies = [dict(result=dict(episodedetails=dict(episodeid=42,season=1,episode=2,showtitle='Show',tvshowid=7))),
                   dict(result=dict(tvshowdetails=dict(tvshowid=7,title='Show',uniqueid={'tmdb':'123'}))),
                   RuntimeError('local catalogue unavailable')]
        with mock.patch.object(service,'jsonrpc',side_effect=replies), mock.patch.object(service.xbmc,'getCondVisibility',return_value=True):
            entry = service._continue_identity(dict(type='episode',id=42,season=1,episode=2,
                showtitle='Show',title='Episode',uniqueid={'tmdb':'999'},file='plugin://plugin.video.pov/?episode=999'))
        self.assertEqual(entry['show_tmdb'],'123')
        self.assertEqual(entry['identity']['scope'],'show_episode')
        self.assertEqual(hub.next_episodes({'watched':{entry['key']:entry}}),[])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MediaTests))
    sys.exit(0 if result.wasSuccessful() else 1)
