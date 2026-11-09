"""Focused host safety checks; captured Android fields are inputs, not playback.

Reuse the existing AST-extracted actual-item harness without discovering its
historical suite. Do not infer E4 identity from its label, URL or TV parent.
"""
import ast
import copy
import hashlib
import json
import subprocess
import unittest

import test_actual_source_item as retained

HERE = retained.HERE
CAPTURE = HERE / 'evidence/native-av-identity-fail-42567028842/queens-blade-e4-actual-av.json'
BASELINE = '83d1bc15031390c99cb170f20faa2a9720700133'
PARENT = '/anime/queen-s-blade?season=all&lang=dub'


class TVParentIdentitySafety(unittest.TestCase):
    setUp = retained.ActualSourceItem.setUp
    result = retained.ActualSourceItem.result

    def parent(self, source=PARENT):
        return retained.route('actionEpisodesMenu', source)

    def test_exact_publisher_queries_preserve_raw_hash_and_stay_distinct(self):
        keys = []
        for suffix in ('season=all', 'season=all&lang=dub', 'season=all&lang=sub', 'season=all&lang=cartoon'):
            source = '/anime/queen-s-blade?' + suffix
            identity = self.hub.watchnixtoons_source_identity(self.parent(source), 'tvshow')
            expected = hashlib.sha256(('wnt2-source-v1\0actionEpisodesMenu\0' + source + '\0tvshow\0-1\0-1').encode()).hexdigest()
            self.assertEqual(identity['ids'], {'wnt2': expected})
            self.assertEqual(identity['kind'], 'tvshow')
            self.assertNotIn('season', identity)
            keys.append(self.hub.identity_key(identity))
        self.assertEqual(len(set(keys)), 4)

    def test_malformed_or_expanded_query_grammar_is_withheld(self):
        invalid = [
            '/anime/?season=all', '/anime/../x?season=all', '/anime/a/b?season=all',
            '//example.invalid/anime/x?season=all', '/anime/x?season=',
            '/anime/x?season=1', '/anime/x?season=all&',
            '/anime/x?season=all&season=all', '/anime/x?lang=dub&season=all',
            '/anime/x?season=all&lang=', '/anime/x?season=all&lang=DUB',
            '/anime/x?season=all&lang=dub&lang=sub', '/anime/x?season=all&unknown=x',
            '/anime/x?season=all#fragment', '/anime/%2e%2e?season=all',
            '/anime/x?season=all%26lang%3Ddub', '/anime/x?season=all&lang=%64ub',
            '/anime/x%252fother?season=all', '/anime/x?season=all\x00',
        ]
        for source in invalid:
            with self.subTest(source=source):
                self.assertIsNone(self.hub.watchnixtoons_source_identity(self.parent(source), 'tvshow'))
        for extra in ('&action=actionEpisodesMenu', '&url=%2Fanime%2Fother', '&unknown=x', '&unknown='):
            with self.subTest(extra=extra):
                self.assertIsNone(self.hub.watchnixtoons_source_identity(self.parent() + extra, 'tvshow'))
        self.assertIsNone(self.hub.watchnixtoons_source_identity(self.parent(), 'season', 1))
        for kind in ('movie', 'episode'):
            self.assertIsNone(self.hub.watchnixtoons_source_identity(retained.route('actionResolve', PARENT), kind, -1, 4))

    def test_previously_admitted_queryless_and_absolute_keys_are_unchanged(self):
        path = retained.OVERLAY / 'resume_hub.py'
        relative = path.relative_to(HERE.parents[1]).as_posix()
        raw = subprocess.run(['git', '-C', str(HERE.parents[1]), 'show', BASELINE + ':' + relative],
                             capture_output=True, check=True, timeout=10).stdout
        node = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'watchnixtoons_source_identity')
        env = dict(vars(self.hub))
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'unchanged-prior-source-contract', 'exec'), env)
        samples = [('actionEpisodesMenu', '/anime/queen-s-blade', 'tvshow', -1, -1),
                   ('actionEpisodesMenu', '/anime/queen-s-blade', 'season', 1, -1),
                   ('actionResolve', '/queens-blade-episode-4', 'episode', -1, 4),
                   ('actionResolve', '/fantastic-mr-fox', 'movie', -1, -1),
                   ('actionEpisodesMenu', 'https://www.wcostream.tv/anime/queen-s-blade?season=all&lang=dub', 'tvshow', -1, -1)]
        for action, source, kind, season, episode in samples:
            with self.subTest(source=source):
                route = retained.route(action, source)
                old = env['watchnixtoons_source_identity'](route, kind, season, episode)
                self.assertIsNotNone(old)
                self.assertEqual(self.hub.watchnixtoons_source_identity(route, kind, season, episode), old)
                self.assertEqual(self.hub.identity_key(old), self.hub.identity_key(self.hub.watchnixtoons_source_identity(route, kind, season, episode)))

    def test_captured_real_av_wrong_movie_with_actual_tv_parent_is_refused(self):
        capture = json.loads(CAPTURE.read_text())
        item = capture['item']
        self.assertTrue(capture['playing'])
        self.assertIn('AVStarted', [event['event'] for event in capture['events']])
        self.assertEqual((item['media_type'], item['season'], item['episode']), ('movie', -1, -1))
        self.state = dict(file=capture['file'], path=item['path'], original=item['original_listitem_url'],
                          parent=item['parent_path'], kind=item['media_type'], season=item['season'],
                          episode=item['episode'], ids=item['ids'], show=item['show_title'], title=item['title'])
        self.assertEqual(self.state['path'], self.state['original'])
        self.assertIsNotNone(self.hub.watchnixtoons_source_identity(self.state['parent'], 'tvshow'))
        self.assertIsNone(self.result())
        self.assertEqual(self.snapshots, 1, 'Reject before association lookup and entry creation')

    def test_real_movie_catalogue_cc_and_missing_parents_remain_movie(self):
        movie = json.loads((HERE / 'dependency-evidence/PUBLIC-MOVIE-INPUT.json').read_text())
        self.state.update(path=movie['selected']['expected_provider_route'], original=movie['selected']['expected_provider_route'],
                          kind='movie', season=-1, episode=-1, show='', title=movie['selected']['label'])
        parents = [movie['source_category']['category_route'], '',
                   'plugin://script.infinity.commandcenter/?action=library&bucket=watchlist']
        for parent in parents:
            with self.subTest(parent=parent):
                self.state['parent'] = parent
                result = self.result()
                self.assertEqual((result['media'], result['identity']['kind']), ('movie', 'movie'))
                self.assertNotIn('source_parent', result)
                self.assertEqual(result['dbid'], -1)

    def test_queryless_tv_parent_also_blocks_wrong_movie_without_relabeling(self):
        self.state.update(kind='movie', season=-1, episode=-1)
        before = copy.deepcopy(self.state)
        self.assertIsNone(self.result())
        self.assertEqual(self.state, before)

    def test_actual_typed_episode_can_keep_query_parent_without_season_guess(self):
        self.state['parent'] = self.parent()
        result = self.result()
        self.assertEqual(result['source_parent'], self.parent())
        self.assertEqual((result['media'], result['season'], result['episode']), ('tv', -1, 4))
        self.assertNotIn('show_ids_verified', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
