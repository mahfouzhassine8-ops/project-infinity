#!/usr/bin/env python3
"""Offline tests for the native-run provenance gate, not build validation."""
import copy
import unittest

from wait_native import validate_run

RUN = 37245035885
COMMIT = 'ce69872c27138b712dca9bf231c5c8a225cf1402'
REPO = 'mahfouzhassine8-ops/project-infinity'
VALID = {'id': RUN, 'head_sha': COMMIT, 'head_repository': {'full_name': REPO},
         'path': '.github/workflows/infinity-2103306-provider-native-validation.yml',
         'status': 'completed', 'conclusion': 'success'}


class ProvenanceGate(unittest.TestCase):
    def test_only_exact_success_authorizes_package(self):
        self.assertTrue(validate_run(VALID, RUN, COMMIT, REPO))

    def test_non_success_completion_refuses_package(self):
        for conclusion in ('failure', 'cancelled', 'timed_out', 'skipped', 'neutral', None):
            with self.subTest(conclusion=conclusion):
                changed = {**VALID, 'conclusion': conclusion}
                with self.assertRaisesRegex(ValueError, 'did not succeed'):
                    validate_run(changed, RUN, COMMIT, REPO)

    def test_running_and_queued_runs_do_not_authorize_package(self):
        for status in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
            with self.subTest(status=status):
                self.assertFalse(validate_run({**VALID, 'status': status}, RUN, COMMIT, REPO))

    def test_wrong_run_commit_repository_and_workflow_rejected(self):
        changes = [{'id': RUN + 1}, {'head_sha': '0' * 40},
                   {'head_repository': {'full_name': 'someone/else'}},
                   {'path': '.github/workflows/some-other-build.yml'}]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, 'provenance'):
                    validate_run({**copy.deepcopy(VALID), **change}, RUN, COMMIT, REPO)

    def test_missing_provenance_and_unknown_status_rejected(self):
        for field in ('id', 'head_sha', 'head_repository', 'path'):
            changed = copy.deepcopy(VALID)
            del changed[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'provenance'):
                validate_run(changed, RUN, COMMIT, REPO)
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            validate_run({**VALID, 'status': 'unknown'}, RUN, COMMIT, REPO)


if __name__ == '__main__':
    unittest.main(verbosity=2)
