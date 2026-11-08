"""Selected host contract: actual-item WNT fallback, no app/provider execution.

Execute only this module. Extract the actual service function and baseline's
read-only context lookups by AST; use the actual overlay hub. Selected cases
cover copied-item routes/parent, unknown season, canonical exclusions, snapshot
races, JSON contradictions, saved-association conflicts and malformed routes.
No authenticated bootstrap, persistence mutation, provider call or native test.
"""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from contextlib import nullcontext
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
BASE = HERE / 'reference/script.infinity.commandcenter'
OVERLAY = HERE / 'overlay/script.infinity.commandcenter'


def extract(path, names, env):
    nodes = [node for node in ast.parse(path.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise AssertionError('Actual selected functions missing')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)


def route(action, page):
    return 'plugin://plugin.video.watchnixtoons2/?' + urlencode({'action': action, 'url': page})


EPISODE = route('actionResolve', '/queens-blade-episode-4')
PARENT = route('actionEpisodesMenu', '/anime/queens-blade')


class Tag:
    def __init__(self, state): self.state = state
    def getMediaType(self): return self.state['kind']
    def getSeason(self): return self.state['season']
    def getEpisode(self): return self.state['episode']
    def getUniqueID(self, name): return self.state['ids'].get(name, '')
    def getTVShowTitle(self): return self.state['show']
    def getTitle(self): return self.state['title']
    def getPlayCount(self): return 0


class PlayingItem:
    def __init__(self, state): self.state = state
    def getVideoInfoTag(self): return Tag(self.state)
    def getPath(self): return self.state['path']
    def getProperty(self, name):
        return self.state[{'original_listitem_url': 'original', 'ParentPath': 'parent'}[name]]
    def getLabel(self): return self.state['title']
    def getArt(self, name): return ''


class ActualSourceItem(unittest.TestCase):
    def setUp(self):
        common = types.ModuleType('common')
        common.persistence_scope = nullcontext
        # These functions must not be called by the selected read-only path.
        def forbidden(*args, **kwargs): raise AssertionError('Unexpected persistence/provider operation')
        common.read_json = common.atomic_json = forbidden
        sys.modules['common'] = common
        sys.modules['xbmc'] = types.SimpleNamespace(log=lambda *args: None)
        spec = importlib.util.spec_from_file_location('actual_source_hub', OVERLAY / 'resume_hub.py')
        self.hub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.hub)
        self.data = {'schema': 2, 'items': {}, 'watched': {}, 'watchlist': {},
                     'collection': {}, 'later': {}, 'lists': {}, 'nixtoons_verified_links': {}}
        self.hub.load_view = lambda profile: copy.deepcopy(self.data)
        self.state = dict(file='https://media.invalid/temporary.mp4', path=EPISODE,
                          original=EPISODE, parent=PARENT, kind='episode', season=-1,
                          episode=4, ids={}, show='Queen’s Blade', title='Episode 4')
        self.after = None
        self.snapshots = 0
        self.current = None
        self.playing = [True, True]
        def get_item():
            self.current = copy.deepcopy(self.after if self.snapshots and self.after is not None else self.state)
            self.snapshots += 1
            return PlayingItem(self.current)
        self.player = types.SimpleNamespace(
            isPlayingVideo=lambda: self.playing.pop(0) if len(self.playing) > 1 else self.playing[0],
            getPlayingItem=get_item, getPlayingFile=lambda: self.current['file'])
        self.env = {'hub': self.hub, 'addon_profile': lambda: Path('/unused-profile'),
                    'xbmc': types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz',
                                                 Player=lambda: self.player)}
        context = types.ModuleType('context')
        context.__dict__.update(self.env)
        extract(BASE / 'context.py', ('_watchnixtoons_identity_slot', '_watchnixtoons_verified_link',
                '_watchnixtoons_owned_records', '_watchnixtoons_exact_previous'), context.__dict__)
        sys.modules['context'] = context
        extract(OVERLAY / 'service.py', ('_continue_source_item',), self.env)

    def result(self, item=None):
        before = copy.deepcopy(self.data)
        value = self.env['_continue_source_item']({} if item is None else item)
        self.assertEqual(self.data, before, 'Actual fallback/lookups must be read-only')
        return value

    def canonical(self, *, kind='episode', season=1, episode=4, ids=None, source=EPISODE):
        ids = ids or {'tmdb': '603'}
        identity = (self.hub.media_identity('tv', {}, season, episode, ids) if kind == 'episode'
                    else self.hub.show_identity('tvshow', ids) if kind == 'tvshow'
                    else self.hub.media_identity('movie', ids))
        return dict(identity=identity, key=self.hub.identity_key(identity),
                    media='movie' if kind == 'movie' else 'tv', source=source,
                    stable_source=source, season=season, episode=episode, title='Untrusted old title')

    def test_exact_actual_copy_retains_unknown_season_and_provider_parent(self):
        result = self.result({'type': 'episode', 'season': -1, 'episode': 4, 'file': self.state['file']})
        self.assertEqual(result['identity']['scope'], 'watchnixtoons_local')
        self.assertEqual((result['season'], result['episode']), (-1, 4))
        self.assertEqual((result['source'], result['stable_source'], result['source_parent']),
                         (EPISODE, EPISODE, PARENT))
        self.assertEqual(result['dbid'], -1)
        self.assertNotIn('show_ids_verified', result)
        self.assertEqual(self.snapshots, 2)

    def test_cc_or_missing_parent_never_creates_series_association(self):
        for parent in ('', 'plugin://script.infinity.commandcenter/?action=library&bucket=watchlist'):
            with self.subTest(parent=parent):
                self.state['parent'] = parent
                result = self.result()
                self.assertNotIn('source_parent', result)
                self.assertNotIn('show_ids_verified', result)

    def test_actual_or_json_canonical_ids_leave_generic_recorder_unchanged(self):
        self.state['ids'] = {'tmdb': '603'}
        self.assertIsNone(self.result())
        self.state['ids'] = {}
        self.assertIsNone(self.result({'uniqueid': {'tvdb': '123'}}))

    def test_before_after_snapshot_changes_are_rejected(self):
        mutations = {'file': 'https://media.invalid/next.mp4', 'kind': 'movie',
                     'season': 1, 'episode': 5, 'original': route('actionResolve', '/other'),
                     'path': route('actionResolve', '/other'), 'parent': route('actionEpisodesMenu', '/anime/other'),
                     'ids': {'tmdb': '603'}}
        for field, value in mutations.items():
            with self.subTest(field=field):
                self.snapshots = 0
                self.after = dict(self.state, **{field: value})
                self.assertIsNone(self.result())

    def test_json_kind_file_and_episode_contradictions_are_rejected(self):
        for item in ({'type': 'movie'}, {'file': 'https://media.invalid/other.mp4'},
                     {'season': 1}, {'episode': 5}):
            with self.subTest(item=item): self.assertIsNone(self.result(item))

    def test_exact_preapproved_canonical_row_requires_kind_and_coordinates(self):
        self.state['season'] = 1
        row = self.canonical()
        self.data['watchlist'][row['key']] = row
        self.assertEqual(self.result()['identity'], row['identity'])
        for replacement in (self.canonical(kind='movie'), self.canonical(season=2), self.canonical(episode=5)):
            with self.subTest(row=replacement):
                self.data['watchlist'] = {replacement['key']: replacement}
                self.assertIsNone(self.result())

    def test_unknown_season_cannot_reuse_or_upgrade_canonical_saved_episode(self):
        row = self.canonical(season=1)
        self.data['watchlist'][row['key']] = row
        self.assertIsNone(self.result())

    def test_conflicting_exact_canonical_rows_are_quarantined(self):
        self.state['season'] = 1
        for ids in ({'tmdb': '603'}, {'tmdb': '604'}):
            row = self.canonical(ids=ids)
            self.data['watchlist'][row['key']] = row
        self.assertIsNone(self.result())

    def test_only_exact_verified_parent_link_can_supply_canonical_parent(self):
        row = self.canonical(kind='tvshow', source=PARENT)
        slot = sys.modules['context']._watchnixtoons_identity_slot(PARENT)
        self.data['nixtoons_verified_links'][slot] = row
        result = self.result()
        self.assertTrue(result['show_ids_verified'])
        self.assertEqual(result['show_tmdb'], '603')
        self.assertEqual(result['identity']['scope'], 'watchnixtoons_local')
        self.data['nixtoons_verified_links'][slot]['source'] = route('actionEpisodesMenu', '/anime/other')
        result = self.result()
        self.assertNotIn('show_ids_verified', result)

    def test_conflicting_parent_or_child_parent_proof_is_quarantined(self):
        parent = self.canonical(kind='tvshow', source=PARENT)
        slot = sys.modules['context']._watchnixtoons_identity_slot(PARENT)
        self.data['nixtoons_verified_links'][slot] = parent
        other_parent = self.canonical(kind='tvshow', source=PARENT, ids={'tmdb': '604'})
        self.data['collection'][other_parent['key']] = other_parent
        self.assertIsNone(self.result())
        self.data['collection'].clear()
        self.state['season'] = 1
        child = self.canonical(ids={'tmdb': '604'})
        self.data['watchlist'][child['key']] = child
        self.assertIsNone(self.result())

    def test_exact_previous_episode_retains_parent_for_direct_saved_replay(self):
        self.state['parent'] = 'plugin://script.infinity.commandcenter/?action=library&bucket=watchlist'
        identity = self.hub.watchnixtoons_source_identity(EPISODE, 'episode', -1, 4)
        previous = dict(identity=identity, key=self.hub.identity_key(identity), media='tv',
                        source=EPISODE, stable_source=EPISODE, source_parent=PARENT,
                        season=-1, episode=4, title='Unrelated saved label')
        self.data['items'][previous['key']] = previous
        parent = self.canonical(kind='tvshow', source=PARENT)
        slot = sys.modules['context']._watchnixtoons_identity_slot(PARENT)
        self.data['nixtoons_verified_links'][slot] = parent
        result = self.result()
        self.assertEqual(result['source_parent'], PARENT)
        self.assertEqual(result['identity'], identity)
        self.assertEqual((result['season'], result['episode']), (-1, 4))
        self.assertEqual(result['show_tmdb'], '603')
        self.assertTrue(result['show_ids_verified'])

    def test_wrong_coordinates_or_malformed_previous_parent_are_not_inherited(self):
        self.state['parent'] = ''
        identity = self.hub.watchnixtoons_source_identity(EPISODE, 'episode', -1, 5)
        previous = dict(identity=identity, key=self.hub.identity_key(identity), media='tv',
                        source=EPISODE, stable_source=EPISODE, source_parent=PARENT,
                        season=-1, episode=5)
        self.data['items'][previous['key']] = previous
        self.assertIsNone(self.result())
        identity = self.hub.watchnixtoons_source_identity(EPISODE, 'episode', -1, 4)
        previous.update(identity=identity, key=self.hub.identity_key(identity), episode=4)
        for invalid in ('plugin://other/?action=actionEpisodesMenu&url=/anime/queens-blade',
                        PARENT + '&url=/duplicate', EPISODE):
            with self.subTest(parent=invalid):
                previous['source_parent'] = invalid
                self.data['items'] = {previous['key']: previous}
                result = self.result()
                self.assertIsNotNone(result)
                self.assertNotIn('source_parent', result)
                self.assertNotIn('show_ids_verified', result)

    def test_stopped_non_infinity_and_malformed_routes_are_withheld(self):
        self.playing = [False]
        self.assertIsNone(self.result())
        self.playing = [True, False]
        self.assertIsNone(self.result())
        self.playing = [True]
        self.env['xbmc'].getSkinDir = lambda: 'other.skin'
        self.assertIsNone(self.result())
        self.env['xbmc'].getSkinDir = lambda: 'skin.infinity.diggz'
        for invalid in ('plugin://other/?action=actionResolve&url=/episode',
                        EPISODE + '&url=/duplicate', EPISODE + '#fragment',
                        route('actionResolve', 'https://user:password@example.invalid/episode')):
            with self.subTest(route=invalid):
                self.state.update(path=invalid, original=invalid)
                self.assertIsNone(self.result())


if __name__ == '__main__':
    unittest.main(verbosity=2)
