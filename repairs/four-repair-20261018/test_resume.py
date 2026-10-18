"""Actual unchanged CC writer, restart reload, concurrent update and admission tests."""
import importlib.util
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent / 'android-checkpoint-shutdown/installed/overlay/script.infinity.commandcenter'
# Overlay omits unchanged files. Assemble the same source files as the approved
# installation in a disposable fixture directory, never in a user profile.
import tempfile
import shutil
_runtime = tempfile.TemporaryDirectory()
for directory in (HERE.parent / 'android-checkpoint-shutdown/installed/parent/script.infinity.commandcenter', RUNTIME):
    for p in directory.rglob('*'):
        if p.is_file():
            dest = Path(_runtime.name) / p.relative_to(directory)
            dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, dest)
sys.argv = [sys.argv[0], '--runtime', _runtime.name]
fixtures = runpy.run_path(str(HERE.parent / 'android-checkpoint-shutdown/runtime-tests/test_runtime_checkpoint.py'), run_name='four_fixtures')
spec = importlib.util.spec_from_file_location('ui_controller_access', HERE / 'addon/controller_access.py')
access = importlib.util.module_from_spec(spec); spec.loader.exec_module(access)
hub, common, plugin = fixtures['hub'], fixtures['common'], fixtures['plugin']

class ResumeTests(fixtures['RuntimeTests']):
    # Keep inherited durability tests; add real item mutations to the same gate.
    def entry(self, media='movie'):
        identity = hub.media_identity(media, {'tmdb': '123'}, 1, 2)
        key = hub.identity_key(identity)
        return dict(key=key, identity=identity, media=media, tmdb='123', season=1, episode=2,
                    title='Private fixture', label='Private fixture', position=120, duration=1000,
                    dbid=-1, source='plugin://plugin.video.fixture/?id=123')

    def seed(self, media='movie'):
        entry = self.entry(media)
        common.atomic_json(self.profile / hub.CONTINUE_FILE, dict(schema=2, items={entry['key']: entry}, foreign={'retain': 7}))
        return entry

    def restart_read(self):
        fixtures['runtime']._stores.clear()
        hub._view_cache = None
        return hub.load(self.profile)

    def test_movie_and_episode_all_context_mutations_survive_restart(self):
        for media in ('movie', 'tv'):
            with self.subTest(media=media):
                entry = self.seed(media); key = entry['key']
                saved, rows = access.context_rows(plugin, key)
                self.assertEqual([op for _, op in rows], ['mark-watched','reset-progress','toggle-watchlist','toggle-collection','rate','add-list','remove-resume'])
                for op, bucket in [('toggle-watchlist', 'watchlist'), ('toggle-collection', 'collection')]:
                    self.assertTrue(access.mutate(plugin, key, entry, op))
                    self.assertIn(key, self.restart_read()[bucket])
                    self.assertTrue(access.mutate(plugin, key, entry, op))
                    self.assertNotIn(key, self.restart_read()[bucket])
                self.assertTrue(access.mutate(plugin, key, entry, 'rate', choice=8))
                self.assertEqual(self.restart_read()['ratings'][key]['rating'], 8)
                self.assertTrue(access.mutate(plugin, key, entry, 'add-list', name='Fixture List'))
                self.assertIn(key, self.restart_read()['lists']['Fixture List'])
                self.assertTrue(access.mutate(plugin, key, entry, 'mark-watched'))
                data = self.restart_read(); self.assertIn(key, data['watched']); self.assertNotIn(key, data['items'])
                self.assertTrue(access.mutate(plugin, key, entry, 'mark-unwatched'))
                data = self.restart_read(); self.assertNotIn(key, data['watched'])
                self.assertIs(data['infinity_watched_overrides'][key]['watched'], False)
                self.assertEqual(data['foreign'], {'retain': 7})
                for op in ('reset-progress','remove-resume'):
                    entry = self.seed(media)
                    self.assertTrue(access.mutate(plugin, key, entry, op))
                    self.assertNotIn(key, self.restart_read()['items'])

    def test_menu_selection_does_not_write_and_preserves_newer_progress(self):
        entry = self.seed(); key = entry['key']; path = self.profile / hub.CONTINUE_FILE
        before = path.read_bytes()
        access.context_rows(plugin, key)
        self.assertEqual(path.read_bytes(), before)
        data = hub.load(self.profile); data['items'][key]['position'] = 444
        common.atomic_json(path, data)
        self.assertTrue(access.mutate(plugin, key, entry, 'toggle-watchlist'))
        self.assertEqual(self.restart_read()['items'][key]['position'], 444)

    def test_wrong_identity_and_closed_admission_do_not_write(self):
        entry = self.seed(); key = entry['key']; path = self.profile / hub.CONTINUE_FILE
        before = path.read_bytes()
        wrong = dict(entry, identity=hub.media_identity('movie', {'tmdb':'999'}))
        self.assertFalse(access.mutate(plugin, key, wrong, 'mark-watched'))
        self.assertEqual(path.read_bytes(), before)
        self.request('PREPARE'); self.checkpoint.poll()
        with self.assertRaises(Exception): access.mutate(plugin, key, entry, 'toggle-watchlist')
        self.assertEqual(hub.load(self.profile)['items'][key]['identity'], entry['identity'])

if __name__ == '__main__': unittest.main(verbosity=2)
