import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('view_probe', HERE / 'view_probe.py')
probe = importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class PrivateBoundedProbe(unittest.TestCase):
    def test_no_private_query_path_or_credentials_in_output(self):
        secret = 'secret-movie-name'
        path = 'plugin://plugin.video.redlight/private/' + secret + '?page=2&token=credential&query=personal-search'
        row = probe.route(path, b'unpublished-key')
        self.assertEqual(row['provider'], 'plugin.video.redlight')
        self.assertEqual(row['page'], 2)
        for value in ('private', secret, 'credential', 'personal-search', 'token=', 'query='):
            self.assertNotIn(value, json.dumps(row))
        other = probe.route(path, b'other-session')
        self.assertNotEqual(row['path_token'], other['path_token'])
        self.assertEqual(row, probe.route(path, b'unpublished-key'))

    def test_non_video_sources_and_invalid_page_values_are_not_exported(self):
        for path in ('content://private.authority/my-movie', 'https://name:password@host/private',
                     'plugin://user:password@plugin.video.test/?page=private-title'):
            row = probe.route(path, b'key')
            self.assertIsNone(row['provider']);self.assertIsNone(row['page'])
        self.assertIsNone(probe.route('plugin://plugin.video.test/?page=1&page=2', b'key')['page'])

    def test_readonly_exact_view_database_lookup_and_hash_preservation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'ViewModes6.db';conn = sqlite3.connect(p)
            conn.execute('CREATE TABLE view (window INTEGER, path TEXT, viewMode INTEGER, skin TEXT)')
            conn.execute('INSERT INTO view VALUES (?,?,?,?)', (10025, 'plugin://plugin.video.qa/?page=2', 65536 + 55, 'skin.infinity.diggz'))
            conn.commit();conn.close()
            before = hashlib.sha256(p.read_bytes()).hexdigest()
            row = probe.saved_view(p, 'plugin://plugin.video.qa/?page=2', 'skin.infinity.diggz')
            self.assertEqual(row, {'status':'read-only-match', 'rows':[{'view_id':55, 'skin_matches':True}]})
            self.assertEqual(before, hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(probe.saved_view(p, 'plugin://different/', 'skin.infinity.diggz')['status'], 'no-exact-match')
            missing = Path(d) / 'must-not-create.db'
            self.assertEqual(probe.saved_view(missing, 'plugin://different/', 'skin.infinity.diggz')['status'], 'unavailable')
            self.assertFalse(missing.exists())

    def test_database_contention_does_not_wait_or_change_data(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'view.db';conn = sqlite3.connect(p)
            conn.execute('CREATE TABLE view (window INTEGER, path TEXT, viewMode INTEGER, skin TEXT)');conn.commit()
            conn.execute('BEGIN EXCLUSIVE')
            try:self.assertEqual(probe.saved_view(p, 'plugin://qa', 'skin.infinity.diggz')['status'], 'unavailable')
            finally:conn.rollback();conn.close()

    def test_probe_is_bounded_and_excluded_from_production_overlay(self):
        source = (HERE / 'view_probe.py').read_text()
        self.assertIn('range(180)', source);self.assertIn('monitor.waitForAbort(1)', source)
        self.assertNotIn('executebuiltin', source);self.assertNotIn('xbmc.Player', source)
        self.assertNotIn('setSetting', source)
        self.assertFalse(list((HERE / 'overlay').rglob('view_probe.py')))


if __name__ == '__main__':unittest.main()
