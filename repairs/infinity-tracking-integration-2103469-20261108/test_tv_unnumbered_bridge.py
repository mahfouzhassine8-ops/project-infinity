"""Selected host bridge contract; retained AV fields are inputs, not new playback."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest

import test_actual_source_item as retained

HERE = retained.HERE
PRODUCER = Path('/workspace/scratch/tracking-provider-reference/plugin.video.watchnixtoons2')
CAPTURE = HERE / 'evidence/native-av-identity-fail-42567028842/queens-blade-e4-actual-av.json'


class UnnumberedEpisodeBridge(unittest.TestCase):
    result = retained.ActualSourceItem.result

    def setUp(self):
        retained.ActualSourceItem.setUp(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'plugin.video.watchnixtoons2'
        self.root.mkdir()
        for path in PRODUCER.rglob('*'):
            if path.is_file() and (path.suffix == '.py' or path.name == 'addon.xml'):
                target = self.root / path.relative_to(PRODUCER)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        self.info = {'id': 'plugin.video.watchnixtoons2', 'version': '0.14.24', 'path': str(self.root)}
        self.site = '0'
        self.settings_read = []
        def get_setting(name):
            self.settings_read.append(name)
            self.assertEqual(name, 'baseURL', 'No provider account/settings read is authorized')
            return self.site
        addon = types.SimpleNamespace(getAddonInfo=lambda name: self.info[name], getSetting=get_setting)
        self.env.update(Path=Path, xbmcaddon=types.SimpleNamespace(Addon=lambda ident: addon),
                        xbmcvfs=types.SimpleNamespace(translatePath=lambda path: path))
        retained.extract(retained.OVERLAY / 'service.py', ('_watchnixtoons_episode_producer',), self.env)
        capture = json.loads(CAPTURE.read_text())
        item = capture['item']
        self.assertTrue(capture['playing'])
        self.assertIn('AVStarted', [event['event'] for event in capture['events']])
        self.state = dict(file=capture['file'], path=item['path'], original=item['original_listitem_url'],
            parent=item['parent_path'], kind=item['media_type'], season=item['season'], episode=item['episode'],
            ids=item['ids'], show=item['show_title'], title=item['title'], label=item['label'])
        original_get = self.player.getPlayingItem
        def get_item():
            playing = original_get()
            playing.getLabel = lambda: playing.state.get('label', playing.state['title'])
            return playing
        self.player.getPlayingItem = get_item

    def local_row(self, parent=None):
        identity = self.hub.watchnixtoons_source_identity(self.state['path'], 'episode', -1, -1)
        return dict(identity=identity, key=self.hub.identity_key(identity), media='tv',
                    source=self.state['path'], stable_source=self.state['path'],
                    source_parent=parent or self.state['parent'], season=-1, episode=-1)

    def test_exact_complete_producer_passes_readonly(self):
        before = retained.copy.deepcopy(self.info)
        self.assertTrue(self.env['_watchnixtoons_episode_producer']())
        self.assertEqual(self.info, before)
        self.assertEqual(set(self.settings_read), {'baseURL'})

    def test_wrong_version_id_or_site_refuses_actual_bridge(self):
        for key, value in [('version', '0.14.25'), ('id', 'other.addon')]:
            with self.subTest(key=key):
                original = self.info[key]
                self.info[key] = value
                self.assertIsNone(self.result())
                self.info[key] = original
        self.site = '1'
        self.assertIsNone(self.result())

    def test_wrong_hash_extra_or_missing_source_refuses_actual_bridge(self):
        path = self.root / 'lib/plugin.py'
        raw = path.read_bytes()
        path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        self.assertIsNone(self.result())
        path.write_bytes(raw)
        extra = self.root / 'extra.py'
        extra.write_bytes(b'# unreviewed producer source')
        self.assertIsNone(self.result())
        extra.unlink()
        path.unlink()
        self.assertIsNone(self.result())

    def test_captured_av_becomes_only_local_unnumbered_episode(self):
        before = copy.deepcopy(self.state)
        entry = self.result({'type': 'movie', 'season': -1, 'episode': -1})
        self.assertEqual((entry['media'], entry['identity']['kind']), ('tv', 'episode'))
        self.assertEqual((entry['season'], entry['episode']), (-1, -1))
        self.assertEqual(entry['identity']['scope'], 'watchnixtoons_local')
        self.assertEqual(set(entry['identity']['ids']), {'wnt2'})
        self.assertEqual(entry['source'], before['original'])
        self.assertEqual(entry['source_parent'], before['parent'])
        self.assertEqual(entry['label'], before['label'])
        self.assertEqual(entry['dbid'], -1)
        self.assertNotIn('show_ids_verified', entry)
        self.assertEqual(self.state, before, 'Native tag and provider state remain unchanged')
        self.assertEqual(self.snapshots, 2)

    def test_unstable_actual_copy_is_refused(self):
        changes = {'file': 'https://media.invalid/changed', 'parent': retained.PARENT,
                   'path': retained.EPISODE, 'original': retained.EPISODE,
                   'kind': 'episode', 'season': 1, 'episode': 4, 'ids': {'tmdb': '603'}}
        for key, value in changes.items():
            with self.subTest(key=key):
                self.snapshots = 0
                self.after = dict(self.state, **{key: value})
                self.assertIsNone(self.result())

    def test_contradictory_json_coords_kind_or_ids_never_infer_e4(self):
        for item in ({'type': 'episode'}, {'season': 1}, {'episode': 4}, {'uniqueid': {'tmdb': '603'}}):
            with self.subTest(item=item): self.assertIsNone(self.result(item))
        for season, episode in [(1, -1), (-1, 4), (0, 0)]:
            self.state.update(season=season, episode=episode)
            self.assertIsNone(self.result())

    def test_cc_replay_needs_prior_exact_local_unknown_episode_parent(self):
        previous = self.local_row()
        self.state['parent'] = 'plugin://script.infinity.commandcenter/?action=library&bucket=watchlist'
        # Membership alone cannot turn a native movie into an episode.
        self.data['watchlist'][previous['key']] = dict(previous, source_parent='')
        self.assertIsNone(self.result())
        self.data['watchlist'].clear()
        self.data['items'][previous['key']] = previous
        result = self.result()
        self.assertEqual(result['identity'], previous['identity'])
        self.assertEqual(result['source_parent'], previous['source_parent'])
        self.site = '1'
        self.assertIsNone(self.result())

    def test_wrong_movie_canonical_or_coordinate_associations_quarantine(self):
        local = self.local_row()
        identities = [self.hub.watchnixtoons_source_identity(self.state['path'], 'movie'),
                      self.hub.media_identity('tv', {}, 1, 4, {'tmdb': '1'}),
                      self.hub.watchnixtoons_source_identity(self.state['path'], 'episode', -1, 4)]
        for identity in identities:
            with self.subTest(identity=identity):
                row = dict(local, identity=identity, media='movie' if identity['kind'] == 'movie' else 'tv',
                    season=identity.get('season', -1), episode=identity.get('episode', -1))
                self.data['items'] = {'a' * 64: row}
                self.assertIsNone(self.result())

    def test_only_exact_proved_local_or_verified_parent_supplies_display(self):
        parent = self.state['parent']
        identity = self.hub.watchnixtoons_source_identity(parent, 'tvshow')
        row = dict(identity=identity, key=self.hub.identity_key(identity), media='tv',
                   source=parent, stable_source=parent, title='Queen’s Blade')
        self.data['watchlist'][row['key']] = row
        self.assertEqual(self.result()['showtitle'], 'Queen’s Blade')
        self.data['collection']['b' * 64] = dict(row, title='Conflicting name')
        self.assertEqual(self.result()['showtitle'], self.state['show'])
        self.data['watchlist'].clear()
        self.data['collection'].clear()
        identity = self.hub.show_identity('tvshow', {'tmdb': '123'})
        row.update(identity=identity, key=self.hub.identity_key(identity), title='Verified parent display')
        slot = retained.sys.modules['context']._watchnixtoons_identity_slot(parent)
        self.data['nixtoons_verified_links'][slot] = row
        result = self.result()
        self.assertEqual(result['show_tmdb'], '123')
        self.assertTrue(result['show_ids_verified'])
        self.assertEqual(result['identity']['scope'], 'watchnixtoons_local')
        self.assertEqual((result['season'], result['episode']), (-1, -1))
        self.assertEqual(result['showtitle'], 'Verified parent display')

    def test_real_movie_catalogue_and_generic_ids_do_not_use_bridge_gate(self):
        self.info['version'] = 'unsupported'
        movie = json.loads((HERE / 'dependency-evidence/PUBLIC-MOVIE-INPUT.json').read_text())
        self.state.update(path=movie['selected']['expected_provider_route'], original=movie['selected']['expected_provider_route'],
                          parent=movie['source_category']['category_route'], show='', title=movie['selected']['label'])
        result = self.result()
        self.assertEqual((result['media'], result['identity']['kind']), ('movie', 'movie'))
        self.assertEqual(self.settings_read, [])
        self.state['ids'] = {'tmdb': '603'}
        self.assertIsNone(self.result())

    def test_existing_projections_keep_unfinished_unknown_child_and_no_successor(self):
        entry = self.result()
        entry.update(position=120, duration=1424, updated=10, resume_revision=1, playback_occurrence='1' * 32)
        self.data['items'][entry['key']] = entry
        self.assertEqual(len(self.hub.progress_shows(self.data)), 1)
        next_row = self.hub.next_episodes(self.data)[0]
        self.assertEqual(next_row['key'], entry['key'])
        self.assertEqual((next_row['season'], next_row['episode']), (-1, -1))
        self.assertNotIn('synthetic_next', next_row)
        self.data['items'].clear()
        self.data['watched'][entry['key']] = dict(entry, watched_at=20, updated=20, completed_occurrence='1' * 32)
        self.assertEqual(self.hub.next_episodes(self.data), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
