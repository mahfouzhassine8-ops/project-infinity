"""Source and functionality checks: no title-only dedupe or persistence writes."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

from movie_identity_patch import patch_bytes, BEFORE_KEY, AFTER_KEY, BEFORE_ENTRIES, AFTER_ENTRIES

SOURCE = Path(os.environ.get('INFINITY_2103390_HUB_PY', '/mnt/data/infinity_group1_review/base/assets/addons/script.infinity.commandcenter/resume_hub.py'))


def hub_for(source):
    xbmc = types.ModuleType('xbmc')
    xbmc.LOGINFO = 1
    xbmc.log = lambda *args: None
    common = types.ModuleType('common')
    common.atomic_json = lambda *args: (_ for _ in ()).throw(AssertionError('No writes permitted'))
    common.read_json = lambda *args: {}
    common.persistence_scope = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('No write scope'))
    sys.modules['xbmc'] = xbmc
    sys.modules['common'] = common
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'resume_hub.py'
        path.write_bytes(source)
        spec = importlib.util.spec_from_file_location('safe_resume_hub_fixture', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def movie(hub, key, tmdb, imdb='tt0000012', updated=100, label='Identical Poster'):
    ident = hub.media_identity('movie', {'tmdb': tmdb, 'imdb': imdb})
    return {'key': key, 'media': 'movie', 'label': label, 'title': label,
            'identity': ident, 'tmdb': tmdb, 'imdb': imdb, 'updated': updated,
            'position': updated, 'duration': 1200, 'source': 'plugin://plugin.video.fixture/?saved=1'}


class IdentityPatchTests(unittest.TestCase):
    def setUp(self):
        if not SOURCE.exists():
            self.skipTest('exact 2103390 Command Center member unavailable')
        self.original = SOURCE.read_bytes()
        self.patched = patch_bytes(self.original)
        self.hub = hub_for(self.patched)

    def test_exact_source_only_changes_two_approved_functions(self):
        self.assertEqual(self.original.decode().count(BEFORE_KEY), 1)
        self.assertEqual(self.original.decode().count(BEFORE_ENTRIES), 1)
        self.assertEqual(self.patched.decode().count(AFTER_KEY), 1)
        self.assertEqual(self.patched.decode().count(AFTER_ENTRIES), 1)
        self.assertEqual(self.patched, self.original.replace(BEFORE_KEY.encode(), AFTER_KEY.encode(), 1)
                         .replace(BEFORE_ENTRIES.encode(), AFTER_ENTRIES.encode(), 1))
        with self.assertRaises(ValueError):
            patch_bytes(self.patched)

    def test_duplicate_verified_movie_shows_one_card_keeps_saved_records(self):
        hub = self.hub
        first = movie(hub, 'a'*64, '123', updated=200)
        recent = movie(hub, 'b'*64, '123', updated=400)
        data = {'items': {first['key']: first, recent['key']: recent}}
        before = copy.deepcopy(data)
        self.assertEqual([x['key'] for x in hub.entries(data, 'movie', 'items')], [recent['key']])
        self.assertEqual(hub.compatible_key(data, movie(hub, 'c'*64, '123', updated=800)), recent['key'])
        self.assertEqual(data, before, 'Read-only projection MUST preserve both stored records')

    def test_same_title_different_ids_remain_distinct(self):
        hub = self.hub
        first = movie(hub, 'a'*64, '123', updated=400)
        second = movie(hub, 'b'*64, '999', updated=200)
        data = {'items': {first['key']: first, second['key']: second}}
        self.assertEqual(len(hub.entries(data, 'movie', 'items')), 2)
        self.assertEqual(hub.compatible_key(data, movie(hub, 'c'*64, '123')), first['key'])

    def test_conflicting_verified_namespaces_must_not_hide_cards(self):
        hub = self.hub
        first = movie(hub, 'a'*64, '123', imdb='tt0000012', updated=400)
        second = movie(hub, 'b'*64, '123', imdb='tt0000099', updated=200)
        data = {'items': {first['key']: first, second['key']: second}}
        self.assertEqual(len(hub.entries(data, 'movie', 'items')), 2)

    def test_unverified_legacy_rows_and_tv_episodes_unchanged(self):
        hub = self.hub
        old={'media':'movie','title':'Identical Poster','label':'Identical Poster','updated':5,
             'source':'plugin://plugin.video.fixture/?id=1'}
        a = hub.media_identity('tv', {'tmdb':'123'}, 1, 4)
        ep = {'media':'tv','identity':a, 'season':1,'episode':4,'updated':9,'label':'Episode'}
        data={'items': {'c'*64:old, 'd'*64:dict(old), 'e'*64:ep, 'f'*64:dict(ep)}}
        self.assertEqual(len(hub.entries(data, 'all', 'items')), 4)

if __name__ == '__main__':
    unittest.main()
