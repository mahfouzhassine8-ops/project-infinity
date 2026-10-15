"""Exercise the Kodi selected-item ingress against the actual store and writer gate."""
import argparse
import importlib
import json
from pathlib import Path
import runpy
import sys
import unittest
from unittest import mock

p = argparse.ArgumentParser(); p.add_argument('--runtime', required=True)
a = p.parse_args(); sys.argv = [sys.argv[0], '--runtime', a.runtime]
f = runpy.run_path(str(Path(__file__).parents[1] / 'runtime-tests/test_runtime_checkpoint.py'), run_name='fixtures')
hub = f['hub']; context = importlib.import_module('context')


class Selected:
    def __init__(self, kind='movie', ids=None, folder=False, dbid=-1, path='plugin://provider/?id=123'):
        self.kind, self.ids = kind, ({'tmdb': '123'} if ids is None else ids)
        self.folder, self.dbid, self.path = folder, dbid, path
        self.properties = {}
    def isFolder(self): return self.folder
    def getVideoInfoTag(self): return self
    def getMediaType(self): return self.kind
    def getUniqueID(self, key): return self.ids.get(key, '')
    def getSeason(self): return 1
    def getEpisode(self): return 2
    def getTitle(self): return 'Selected title'
    def getTVShowTitle(self): return 'Selected show'
    def getLabel(self): return 'Selected title'
    def getPath(self): return self.path
    def getDbId(self): return self.dbid
    def getArt(self, key): return ''
    def setProperty(self, key, value): self.properties[key] = value


class ContextTests(f['RuntimeTests']):
    def test_unknown_folder_untyped_and_title_only_never_mutate(self):
        for item in (None, Selected(folder=True), Selected(kind='tvshow'), Selected(kind=''), Selected(ids={})):
            self.assertIsNone(context.selected_entry(item))
            with mock.patch.object(sys, 'listitem', item, create=True), mock.patch.object(context.xbmc, 'executebuiltin') as call:
                context.main(); self.assertIn('ActivateWindow', call.call_args[0][0])
        self.assertFalse((self.profile / 'resume-hub.json').exists())

    def test_namespace_and_episode_coordinates_are_preserved(self):
        movie = context.selected_entry(Selected())
        tv = context.selected_entry(Selected(kind='episode'))
        other = context.selected_entry(Selected(ids={'tvdb': '123'}))
        self.assertEqual(len({movie['key'], tv['key'], other['key']}), 3)
        self.assertEqual((tv['season'], tv['episode']), (1, 2))

    def test_stale_native_dbid_is_refused(self):
        row = Selected(dbid=42, path='videodb://movies/titles/42')
        self.assertEqual(context.selected_entry(row)['dbid'], 42)
        with mock.patch.object(context.xbmc, 'executeJSONRPC', return_value=json.dumps({'result': {'moviedetails': {'movieid': 42, 'uniqueid': {'tmdb': '999'}}}})):
            self.assertIsNone(context.selected_entry(row))

    def test_verified_provider_item_joins_existing_my_list(self):
        entry = context.selected_entry(Selected())
        self.assertTrue(context.apply_action(self.profile, entry, 'toggle-watchlist'))
        self.assertIn(entry['key'], hub.load(self.profile)['watchlist'])
        self.assertTrue(context.apply_action(self.profile, entry, 'toggle-watchlist'))
        self.assertNotIn(entry['key'], hub.load(self.profile)['watchlist'])

    def test_watched_repeat_is_idempotent_and_unwatched_is_explicit(self):
        entry = context.selected_entry(Selected(dbid=42))
        self.assertTrue(context.apply_action(self.profile, entry, 'mark-watched'))
        self.assertFalse(context.apply_action(self.profile, entry, 'mark-watched'))
        self.assertEqual(hub.load(self.profile)['watched'][entry['key']]['play_count'], 1)
        self.assertTrue(context.apply_action(self.profile, entry, 'mark-unwatched'))
        self.assertNotIn(entry['key'], hub.load(self.profile)['watched'])

    def test_checkpoint_admission_closure_prevents_context_write(self):
        entry = context.selected_entry(Selected())
        self.prepare()
        with self.assertRaises(f['runtime'].AdmissionClosed):
            context.apply_action(self.profile, entry, 'toggle-watchlist')
        self.assertNotIn(entry['key'], hub.load(self.profile)['watchlist'])

    def test_unknown_action_and_forged_key_do_not_write(self):
        entry = context.selected_entry(Selected())
        self.assertFalse(context.apply_action(self.profile, entry, 'arbitrary'))
        entry['key'] = 'f' * 64
        self.assertFalse(context.apply_action(self.profile, entry, 'mark-watched'))

    def test_selected_copy_decoration_has_only_local_properties(self):
        item = Selected(); entry = context.selected_entry(item)
        context.apply_action(self.profile, entry, 'mark-watched')
        context.publish_selected_state(item, entry, hub.load(self.profile))
        self.assertEqual(item.properties['Infinity.ResumeHub.Watched'], 'true')
        self.assertTrue(all(k.startswith('Infinity.ResumeHub.') for k in item.properties))

    def test_resume_requires_verified_route_or_verified_resolver(self):
        entry = context.selected_entry(Selected())
        with mock.patch.object(context.xbmc, 'getCondVisibility', return_value=False):
            self.assertFalse(context.can_resume(entry, {}))
        with mock.patch.object(context.xbmc, 'getCondVisibility', return_value=True):
            self.assertTrue(context.can_resume(entry, {}))
            tv = context.selected_entry(Selected(kind='episode', path=''))
            self.assertFalse(context.can_resume(tv, {}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
