"""Selected real Python render/membership benchmark; not Android frame acceptance."""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
UNIVERSAL = HERE.parent / 'universal'
sys.path.insert(0, str(UNIVERSAL))
from test_quick_actions import QuickActions, load

CC = HERE / 'overlay/script.infinity.commandcenter'
ORIGINAL = UNIVERSAL / 'overlay/script.infinity.commandcenter'
BASELINES = Path('/workspace/scratch/9491f79db5c3/perf-baselines')


class Harness:
    def __init__(self, source):
        self.fixture = QuickActions(methodName='runTest')
        self.fixture.setUp()
        self.source = source
        self.hub = load('resume_hub', source / 'resume_hub.py')
        self.hub.publish_home = lambda data: None
        self.hub.flush_kodi_sync = lambda *a, **kw: None
        for name in ('title_metadata', 'selection_contract'):
            path = source / (name + '.py')
            load(name, path if path.exists() else ORIGINAL / (name + '.py'))
        with patch.object(sys, 'argv', ['plugin.py', '1', '']):
            self.plugin = load('measured_popup', source / 'plugin.py')
        self.plugin._favourite = lambda *a: (None, None)
        self.plugin.navigation_target = lambda entry, *a, **kw: entry.get('source') or ''
        self.plugin.PARAMS['infinity_trace'] = 'p123'
        self.cards = []
        kodi = sys.modules['xbmcplugin']
        kodi.setPluginCategory = lambda *a: None
        kodi.setContent = lambda *a: None
        kodi.endOfDirectory = lambda *a, **kw: None
        kodi.addDirectoryItem = lambda handle, route, item, **kw: self.cards.append((route, deepcopy(vars(item)), kw))

    def close(self): self.fixture.doCleanups()

    def movie(self, ident, **kwargs):
        identity = self.hub.media_identity('movie', {'tmdb': str(ident)})
        return dict(key=self.hub.identity_key(identity), identity=identity, media='movie',
                    title='Title ' + str(ident), source='plugin://plugin.video.umbrella/?tmdb=' + str(ident),
                    poster='https://example.invalid/poster.jpg', information={'plot': 'Original full synopsis. Last sentence.', 'duration': 6035}, **kwargs)

    def fixture_data(self, count):
        data = dict(schema=2, revision=7, items={}, watched={}, watchlist={}, collection={}, later={}, lists={}, sources={}, ratings={})
        for n in range(count):
            row = self.movie(n + 1, watched_at=n + 1)
            data['watched'][row['key']] = row
        for n in range(100):
            row = self.movie(n + 1 if n % 2 == 0 else 1000000 + n, added_at=100 - n)
            data['watchlist'][row['key']] = row
        watched = list(data['watched'].items())
        data['lists'] = {'Saved ' + str(n): dict(watched[n::2][:500]) for n in range(2)}
        data['navigation_recovery'] = {'original': {'success_verified': True, 'route': 'remembered'}}
        data['extension'] = {'keep': [1, 2]}
        return data

    def write(self, data):
        self.fixture.path.write_text(json.dumps(data))
        self.hub._view_cache = None

    def listing(self):
        self.cards.clear()
        self.plugin.listing('movie', 'watchlist')
        return self.cards


class MembershipChecks(unittest.TestCase):
    def setUp(self):
        self.h = Harness(CC)
        self.addCleanup(self.h.close)

    def test_flags_match_original_conflicts_aliases_episode_scope_and_precedence(self):
        h = self.h; data = h.fixture_data(200)
        keys = list(data['watchlist'])[:30]
        # Same TMDB with conflicting IMDb must not match; namespace aliases can.
        conflict = h.movie(5000)
        conflict['identity']['ids']['imdb'] = 'tt12345'
        watched = deepcopy(conflict); watched['identity']['ids']['imdb'] = 'tt54321'
        data['watched']['a' * 64] = watched
        data['watchlist'][conflict['key']] = conflict; keys.append(conflict['key'])
        alias = h.movie(5001); alias['identity']['ids']['imdb'] = 'tt77777'
        other = h.movie(9999); other['identity']['ids'] = {'imdb': 'tt77777'}
        data['watched']['b' * 64] = other
        data['watchlist'][alias['key']] = alias; keys.append(alias['key'])
        for kind, season, episode, scope in [('episode', 1, 1, 'show_episode'), ('episode', 1, 2, 'show_episode'), ('episode', 1, 1, 'episode'), ('season', 1, -1, 'show_season'), ('tvshow', -1, -1, 'show')]:
            identity = dict(schema=1, kind=kind, scope=scope, ids={'tmdb': '9000'})
            if season >= 0: identity['season'] = season
            if episode >= 0: identity['episode'] = episode
            key = hashlib.sha256(repr(identity).encode()).hexdigest()
            row = dict(key=key, media='tv', identity=identity, season=season, episode=episode)
            data['watchlist'][key] = row; keys.append(key)
            if kind == 'episode' and scope == 'show_episode' and episode == 1:
                data['watched']['c' * 64] = deepcopy(row)
        # Preserve exact-key membership and lookup precedence even with old malformed rows.
        direct = h.movie(7000); data['items'][direct['key']] = direct
        data['watched'][direct['key']] = 'legacy'; keys.append(direct['key'])
        custom = h.movie(7001); keys.append(custom['key'])
        data['lists']['Duplicate '] = {custom['key']: custom}
        data['lists'][' Duplicate'] = {custom['key']: dict(custom, identity={})}
        keys += ['0' * 64, 'invalid']
        before = deepcopy(data)
        expected = {key: h.hub.is_watched(data, key) for key in keys if h.hub.KEY_RE.fullmatch(key)}
        self.assertEqual(h.hub.watched_flags(data, keys), expected)
        self.assertEqual(data, before)
        self.assertLessEqual(len(h.hub.watched_flags(data, (f'{n:064x}' for n in range(10000)))), 100)

    def test_all_rendered_fields_exactly_match_current34_and_no_per_card_normalize(self):
        h = self.h; data = h.fixture_data(1000); h.write(data)
        original_normalize = h.hub._normalize
        calls = []
        with patch.object(h.hub, '_normalize', lambda value: (calls.append(1), original_normalize(value))[1]):
            candidate = deepcopy(h.listing())
        self.assertLessEqual(len(calls), 3)
        old = Harness(BASELINES / 'cc34')
        try:
            old.write(data)
            self.assertEqual(old.listing(), candidate)
        finally: old.close()

    def test_new_snapshot_and_atomic_replacement_invalidate_display_flags(self):
        h = self.h; data = h.fixture_data(10); h.write(data)
        first = h.hub.load_view(h.fixture.root)
        row = next(iter(first['watchlist'].values()))
        render = h.plugin.prepare_render(first, [row])
        self.assertTrue(render['watched_flags'][row['key']])
        updated = deepcopy(data)
        removed = updated['watched'].pop(row['key'])
        # Same-size atomic replacement exercises inode invalidation, not just changed length.
        other = h.movie(9); other['key'] = 'a' * 64
        raw = json.dumps(updated)
        old_length = h.fixture.path.stat().st_size
        raw += ' ' * (old_length - len(raw.encode()))
        tmp = h.fixture.path.with_suffix('.replacement'); tmp.write_text(raw); tmp.replace(h.fixture.path)
        self.assertEqual(h.fixture.path.stat().st_size, old_length)
        current = h.hub.load_view(h.fixture.root)
        _, card = h.plugin._list_item(row, current, 'watchlist', render=render)
        self.assertEqual(card.info['playcount'], 0)
        self.assertFalse(h.plugin.prepare_render(current, [row])['watched_flags'][row['key']])
        self.assertTrue(render['watched_flags'][row['key']])

    def test_writer_freshness_selection_and_trackit_functions_unchanged(self):
        selected = {'resume_hub.py': ['load', '_view_signature', '_view_data', 'load_view', 'save', 'find_entry', 'is_watched', 'list_entry_keys', 'record_progress'],
                    'plugin.py': ['_target', 'navigation_target', 'recover_entry', 'play_saved', 'show_item_menu', '_mutate_locked', '_context', '_selected_menu_entry']}
        for file, names in selected.items():
            old = ast.parse((BASELINES / 'cc34' / file).read_text())
            new = ast.parse((CC / file).read_text())
            for name in names:
                old_node = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == name)
                new_node = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == name)
                self.assertEqual(ast.dump(old_node), ast.dump(new_node), name)


def timed(call):
    started = time.perf_counter(); call()
    return round((time.perf_counter() - started) * 1000, 3)


def benchmark(source, size):
    h = Harness(source)
    try:
        data = h.fixture_data(size); h.write(data)
        before = h.fixture.path.read_bytes()
        cold_read = timed(lambda: h.hub.load_view(h.fixture.root))
        warm_read = [timed(lambda: h.hub.load_view(h.fixture.root)) for _ in range(3)]
        h.hub._view_cache = None
        cold_listing = timed(h.listing)
        warm_listing = [timed(h.listing) for _ in range(3)]
        key = list(data['watchlist'])[1]
        h.hub._view_cache = None
        cold_popup = timed(lambda: h.plugin.show_item_menu(key, bucket='watchlist'))
        warm_popup = [timed(lambda: h.plugin.show_item_menu(key, bucket='watchlist')) for _ in range(3)]
        assert h.fixture.path.read_bytes() == before
        assert h.fixture.writers == 0
        return dict(watched=size, visible_cards=len(h.cards), custom_list_entries=sum(map(len, data['lists'].values())),
                    fixture_bytes=len(before), cold_snapshot_ms=cold_read, warm_snapshot_ms=warm_read,
                    cold_listing_ms=cold_listing, warm_listing_ms=warm_listing,
                    cold_popup_cancel_ms=cold_popup, warm_popup_cancel_ms=warm_popup,
                    warm_listing_median_ms=statistics.median(warm_listing), warm_popup_median_ms=statistics.median(warm_popup),
                    file_unchanged=True, writer_entries=0)
    finally: h.close()


def main():
    global BASELINES
    parser = argparse.ArgumentParser(); parser.add_argument('--baseline-dir', type=Path, default=BASELINES)
    args = parser.parse_args(); BASELINES = args.baseline_dir
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MembershipChecks))
    if not result.wasSuccessful(): return 1
    sources = {'cc33': BASELINES / 'cc33', 'cc34': BASELINES / 'cc34', 'candidate35': CC}
    rows = {}
    for name, source in sources.items():
        rows[name] = []
        for size in (100, 1000, 4000):
            row = benchmark(source, size); rows[name].append(row)
            print(name, size, json.dumps(row), flush=True)
    hashes = {name: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('*.py')} for name, source in sources.items()}
    evidence = dict(schema=1, result='PASS', tests=result.testsRun,
                    test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), sources=hashes,
                    measurements=rows,
                    limits=['Host CPython timings; mocked Kodi ListItems and modal cancellation.',
                            'Real listing, snapshot, membership, metadata and selection functions; provider navigation validation and favourites RPC stubbed.',
                            'Profile reads use real JSON file IO; native participant digest/admission verification is not measured.',
                            'Warm means existing in-process snapshot; cold means empty snapshot cache, not cold OS caches.',
                            '4000 watched rows are a scalable retained-profile fixture, not claimed device inventory.',
                            'No Android17/Fold execution, frame-pacing, touch latency, memory-pressure or shutdown acceptance.'])
    (HERE / 'POPUP-PERFORMANCE-HOST.json').write_text(json.dumps(evidence, indent=2) + '\n')
    return 0


if __name__ == '__main__': sys.exit(main())
