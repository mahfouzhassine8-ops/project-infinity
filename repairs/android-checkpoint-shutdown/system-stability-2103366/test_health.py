"""Conditional Health parser against the actual protected Fold close receipt."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

p = argparse.ArgumentParser()
p.add_argument('--receipt', type=Path, required=True)
a = p.parse_args()
ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('reviewed_health', ROOT / 'health/overlay/khc_lifecycle.py')
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)
RECEIPT = json.loads(a.receipt.read_text())


class HealthTests(unittest.TestCase):
    def mutate_native(self, edit):
        row = copy.deepcopy(RECEIPT)
        native = row['native_receipt']
        edit(native)
        row['native_json'] = json.dumps(native, separators=(',', ':'))
        row['native_proof_sha256'] = hashlib.sha256(row['native_json'].encode()).hexdigest()
        return row

    def test_actual_close_resolves_only_previous_close(self):
        result = health.checkpoint_state(RECEIPT)
        self.assertEqual(result['state'], 'RESOLVED')
        self.assertFalse(result['active'])
        self.assertEqual(result['evidence_scope'], 'previous_close')
        self.assertEqual(result['current_process_health'], 'UNVERIFIED')

    def test_ordered_authorization_and_death_are_required(self):
        for field in ('safe_elapsed_ms', 'terminate_requested_elapsed_ms', 'authorization_consumed_elapsed_ms',
                      'engine_death_elapsed_ms', 'safe_epoch_ms', 'authorization_consumed_epoch_ms', 'engine_death_epoch_ms'):
            for value in (0, -1, True, '123'):
                row = copy.deepcopy(RECEIPT)
                row[field] = value
                self.assertEqual(health.checkpoint_state(row)['state'], 'UNVERIFIED')
        row = copy.deepcopy(RECEIPT)
        row['engine_death_elapsed_ms'] = row['started_elapsed_ms'] - 1
        self.assertEqual(health.checkpoint_state(row)['state'], 'UNVERIFIED')

    def test_unknown_failed_or_incomplete_owner_never_recovers(self):
        changes = (
            lambda n: n['owners'].pop(),
            lambda n: n['owners'].append(copy.deepcopy(n['owners'][0])),
            lambda n: n['owners'][0].update(error='commit failed'),
            lambda n: n['owners'][0].update(dirty=True),
            lambda n: n.update(required_jobs=1),
            lambda n: n.update(errors=1),
            lambda n: n.update(owner='other-owner'),
            lambda n: n.update(generation=n['generation'] + 1),
            lambda n: n.update(pid=n['pid'] + 1),
        )
        for change in changes:
            self.assertEqual(health.checkpoint_state(self.mutate_native(change))['state'], 'UNVERIFIED')
        row = copy.deepcopy(RECEIPT)
        row['native_proof_sha256'] = '0' * 64
        self.assertEqual(health.checkpoint_state(row)['state'], 'UNVERIFIED')
        row['phase'] = 'CHECKPOINT_FAILED'
        self.assertEqual(health.checkpoint_state(row)['state'], 'ACTIVE')

    def test_failure_text_never_counts_as_authorization_success(self):
        failures = ('real-debrid unauthorized', 'bad_token')
        positives = ('real-debrid auth', 'real-debrid successfully authorized', 'real-debrid token refreshed')
        for failed in ('real-debrid auth failed', 'real-debrid authentication error',
                       'real-debrid auth unauthorized', 'real-debrid successfully authorized: failure'):
            result = health.marker_state(['plugin.video.fixture real-debrid unauthorized',
                                         'plugin.video.fixture ' + failed], failures, positives)
            self.assertEqual(result, 'REFRESH / AUTH FAILURE')
        for lines in (
            ['plugin.video.fixture real-debrid unauthorized', 'plugin.video.other real-debrid token refreshed'],
            ['real-debrid unauthorized', 'plugin.video.fixture real-debrid token refreshed'],
            ['plugin.video.fixture real-debrid token refreshed', 'plugin.video.fixture real-debrid unauthorized'],
        ):
            self.assertEqual(health.marker_state(lines, failures, positives), 'REFRESH / AUTH FAILURE')
        self.assertEqual(health.marker_state(['plugin.video.fixture real-debrid unauthorized',
                         'plugin.video.fixture real-debrid token refreshed'], failures, positives), 'RECOVERED / SUCCESS AFTER ERROR')


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HealthTests))
    raise SystemExit(0 if result.wasSuccessful() else 1)
