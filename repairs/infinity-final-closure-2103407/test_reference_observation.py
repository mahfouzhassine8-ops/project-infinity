"""Additional observability cannot acknowledge a failure or alter a test assertion."""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

import android17_reference_observation as observation


class ReferenceObservationTests(unittest.TestCase):
    def test_exact_fixture_inverse_diff_and_every_original_assertion_are_preserved(self):
        path=observation.OLD/'tracking/final-eight/android_selected.py'
        before=path.read_bytes();after=observation.instrument_fixture(before).decode()
        self.assertEqual(after.replace(observation.AFTER,observation.BEFORE,1),before.decode())
        with self.assertRaises(ValueError):observation.instrument_fixture(before+b'\n')
        self.assertEqual(after.count('ui.require('),before.decode().count('ui.require('))

    def test_failed_assertion_and_failed_original_export_cannot_become_success(self):
        lines=[]
        class Output:
            def write_text(self,text):raise PermissionError('fixture export denied')
        result={'passed':False,'failure':'RuntimeError: original assertion failed','traceback':'original context'}
        scope={'result':result,'xbmc':SimpleNamespace(log=lambda *args:lines.append(args[0]),LOGERROR=4),
               'json':json,'os':os,'mode':'final-search-all-enter','output':Output()}
        # Use the actual parsed finally body, retaining nested try/raise.
        tree=ast.parse('def fixture():\n    try:\n        pass\n'+observation.AFTER+'\n')
        statements=tree.body[0].body[0].finalbody
        executable=ast.fix_missing_locations(ast.Module(body=statements,type_ignores=[]))
        with self.assertRaises(PermissionError):exec(compile(executable,'fixture-finally','exec'),scope)
        self.assertFalse(result['passed'])
        original=observation.failed_observation('\n'.join(lines),os.getpid())
        self.assertEqual(original['failure'],'RuntimeError: original assertion failed')
        self.assertIn('INFINITY_FEATURE_FIXTURE_EXPORT_FAILED PermissionError',lines)

    def test_only_exact_pid_selected_failure_is_reported_never_a_pass(self):
        row={'pid':37,'selected_mode':'final-search-all-enter','passed':False,'failure':'original failure'}
        prefix='2026-10-26 info INFINITY_FEATURE_FIXTURE_FAILURE '
        self.assertEqual(observation.failed_observation(prefix+json.dumps(row),37),row)
        for change in ({'pid':38},{'selected_mode':'final-continue'},{'passed':True}):
            self.assertIsNone(observation.failed_observation(prefix+json.dumps(dict(row,**change)),37))
        self.assertIsNone(observation.failed_observation(prefix+'malformed',37))


if __name__=='__main__':unittest.main(verbosity=2)
