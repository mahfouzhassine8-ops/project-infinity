"""Actual Search functions with existing synthetic platform boundaries only."""
import ast
import os
from pathlib import Path
import sys
import unittest

AUDIT = Path('/tmp/infinity-search-state/repairs/infinity-search-provider-state-20261104')
sys.path.insert(0, str(AUDIT))
import test_shipped_state as shipped
import test_provider_side_effects as effects

HERE = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get('SEARCH_SOURCE', str(HERE/'overlay/assets/addons/script.infinity.commandcenter/infinity_search.py')))
TREE = ast.parse(SOURCE.read_bytes())
CODE = compile(ast.Module(body=[n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in shipped.SELECT], type_ignores=[]), str(SOURCE), 'exec')


class SearchCorrection(unittest.TestCase):
    def setUp(self):
        self.b = shipped.StateDiagnosis(); self.b.setUp()
        self.addCleanup(self.b.doCleanups)
        exec(CODE, self.b.env)

    def test_fresh_result_survives_each_unrelated_revision(self):
        for name in ('Infinity.ContinueWatchingRevision', 'Infinity.ProviderInventory.Revision',
                     'Infinity.ResumeHub.PresentationSnapshot', 'widgetreload', 'widgetreload2',
                     'widgetreload-movies', 'widgetreload-tvshows'):
            with self.subTest(property=name):
                self.b.props.clear()
                self.b.during = lambda: self.b.props.__setitem__(name, 'fixture-change')
                self.assertEqual(self.b.query()[1], 'completed')
                self.assertFalse(any(k.startswith('Infinity.Search.Cache.') for k in self.b.props))

    def test_progress_update_does_not_reject_owned_result(self):
        self.b.during = lambda: self.b.touch(self.b.progress/'continue-watching.json')
        self.assertEqual(self.b.query()[1], 'completed')

    def test_native_failure_is_not_masked_by_revision(self):
        self.b.answer = {'error': {'message': 'fixture failure'}}
        self.b.during = lambda: self.b.props.__setitem__('widgetreload', 'new')
        for status in ('timeout', 'busy', 'cancelled'):
            self.b.native_status = status
            self.assertEqual(self.b.query()[1:3], (status, self.b.answer))

    def test_meaningful_settings_change_still_rejects(self):
        self.b.during = lambda: self.b.settings.write_text('<settings><setting id="filter">new</setting></settings>')
        self.assertEqual(self.b.query()[1], 'state_changed')

    def test_identical_rewrite_remains_explicit_unresolved_gate(self):
        # Retained, NOT a completed repair: timestamp-only writes are still
        # rejected because the same endpoint bytes can conceal an ABA change.
        self.b.during = lambda: self.b.touch(self.b.settings)
        self.assertEqual(self.b.query()[1], 'state_changed')

    def test_intervening_config_change_back_to_original_remains_rejected(self):
        original = self.b.settings.read_bytes()
        def mutate():
            self.b.settings.write_text('<settings><setting id="filter">temporary</setting></settings>')
            self.b.settings.write_bytes(original); self.b.touch(self.b.settings)
        self.b.during = mutate
        self.assertEqual(self.b.query()[1], 'state_changed')

    def test_source_update_and_disable_preserve_original_refusal(self):
        self.b.during = lambda: (self.b.root/'main.py').write_text('# source changed')
        self.assertEqual(self.b.query()[1], 'unavailable')
        self.b.enabled = False
        self.assertEqual(self.b.query()[1], 'unavailable')

    def test_cancellation_takes_priority(self):
        def cancel(): self.b.canceled = True; self.b.props['widgetreload'] = 'new'
        self.b.during = cancel
        self.assertEqual(self.b.query()[1], 'cancelled')

    def test_profile_switch_still_rejects(self):
        other = self.b.profile/'different'; other.mkdir()
        self.b.during = lambda: setattr(self.b, 'profile', other)
        self.assertEqual(self.b.query()[1], 'state_changed')

    def test_stable_cache_hit_uses_no_second_provider(self):
        self.assertEqual(self.b.query()[1], 'completed')
        self.assertEqual(self.b.query()[1], 'completed')
        self.assertEqual(self.b.calls, 1)

    def test_old_cache_not_accepted_under_new_revision(self):
        self.assertEqual(self.b.query()[1], 'completed')
        self.b.props['widgetreload'] = 'new'
        self.assertEqual(self.b.query()[1], 'completed')
        self.assertEqual(self.b.calls, 2)

    def test_cache_hit_race_rejected_without_reissuing_provider(self):
        self.assertEqual(self.b.query()[1], 'completed')
        original = self.b.home.getProperty
        def read(key):
            if key.startswith('Infinity.Search.Cache.'): self.b.props['widgetreload'] = 'new'
            return original(key)
        self.b.home.getProperty = read
        self.assertEqual(self.b.query()[1], 'state_changed')
        self.assertEqual(self.b.calls, 1)

    def test_completed_empty_is_still_empty(self):
        self.b.answer = {'result': {'files': []}}
        self.b.during = lambda: self.b.props.__setitem__('widgetreload', 'new')
        self.assertEqual(self.b.query()[1:3], ('completed', self.b.answer))

    def test_nixtoons_history_is_still_a_release_blocker(self):
        fixture = effects.SideEffectDiagnosis(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        exec(CODE, fixture.b.env)
        search, calls = fixture.nixtoons()
        fixture.b.during = lambda: search(dict(searchType='series', query='synthetic query', path='/search'))
        self.assertEqual(fixture.b.query()[1], 'state_changed')
        self.assertEqual(fixture.writes, ['searchHistory'])
        self.assertEqual(len(calls), 1)

    def test_only_two_search_functions_changed(self):
        before = {n.name:ast.dump(n) for n in ast.parse(shipped.RAW).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        after = {n.name:ast.dump(n) for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        if SOURCE.name == 'infinity_search.py' and 'overlay' in SOURCE.parts:
            self.assertEqual({n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}, {'_query_signature','_provider_result'})
        else: self.assertEqual(before, after)


if __name__ == '__main__': unittest.main(verbosity=2)
