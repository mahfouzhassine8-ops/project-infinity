"""Negative controls for non-authoritative Android ARM translation evidence."""
import copy
import unittest
from translated_descriptor_evidence import assess, BLOCKER, GUEST_MAPS


def sample():
    identity = {'dev': 21, 'ino': 24844, 'mode': 33060, 'nlink': 1,
                'regular_file': True, 'readlink': GUEST_MAPS,
                'fdinfo': 'pos:\t8192\nflags:\t02100002\nmnt_id:\t0\nino:\t1290\n'}
    pre = dict(android=True, mode='r', writable=False, read_succeeded=True,
               stream_type={'module': '_io', 'name': 'TextIOWrapper'}, errors=[],
               owner='test', nonce='nonce', pid=123, uid=1000, descriptor=160,
               before=identity)
    post = dict(errors=[], read_flush_close_completed=True, closed=True,
                held=False, release_received=True, identity_stable_while_held=True,
                after_hold=copy.deepcopy(identity),
                **{k: pre[k] for k in ('owner', 'nonce', 'pid', 'uid', 'descriptor')})
    kernel = {'readlink_before': dict(returncode=0, stdout=GUEST_MAPS+'\n'),
              'readlink_after': dict(returncode=0, stdout=GUEST_MAPS+'\n'),
              'stat': dict(returncode=0, stdout='1:1290:81ff:0\n'),
              'fdinfo': dict(returncode=0, stdout='pos:\t8192\nflags:\t02100002\nmnt_id:\t0\nino:\t1290\n')}
    return {'captured': True, 'terminal_confirmed': True,
            'same_live_owner_after': True, 'pre': pre, 'post': post,
            'kernel': kernel}, {'phase': 'CHECKPOINT_FAILED', 'error': BLOCKER}


class EvidenceTests(unittest.TestCase):
    def test_actual_shape_identifies_only_mismatch_never_shutdown_pass(self):
        e, r = sample()
        result = assess(e, r)
        self.assertEqual(result['classification'], 'emulator_translated_descriptor_mismatch_observed')
        self.assertFalse(result['durable_close_verified'])
        self.assertFalse(result['can_override_native_protection'])
        self.assertFalse(result['fold_accepted'])

    def test_protected_write_failure_or_real_write_never_waived(self):
        for path, val in [('receipt', 'COMPLETE'), ('kernel_write', True), ('guest_write', True),
                          ('stream', 'Other'), ('kernel_path', '/data/user/0/important.db'),
                          ('kernel_identity', True), ('kernel_status', 1), ('not_closed', True),
                          ('not_released', True), ('not_alive', True), ('different_pid', 999),
                          ('flush_failed', True), ('flags_ro', True), ('other_failure', True)]:
            with self.subTest(path=path):
                e, r = sample()
                if path == 'receipt': r['phase'] = val
                elif path == 'kernel_write': e['pre']['writable'] = val
                elif path == 'guest_write': e['pre']['mode'] = 'w'
                elif path == 'stream': e['pre']['stream_type']['name'] = val
                elif path == 'kernel_path': e['kernel']['readlink_after']['stdout'] = val
                elif path == 'kernel_identity': e['kernel']['stat']['stdout'] = '21:24844:81ff:1'
                elif path == 'kernel_status': e['kernel']['stat']['returncode'] = val
                elif path == 'not_closed': e['post']['closed'] = False
                elif path == 'not_released': e['post']['release_received'] = False
                elif path == 'not_alive': e['same_live_owner_after'] = False
                elif path == 'different_pid': e['post']['pid'] = val
                elif path == 'flush_failed': e['post']['read_flush_close_completed'] = False
                elif path == 'flags_ro': e['kernel']['fdinfo']['stdout'] = 'flags:\t0100000\n'
                elif path == 'other_failure': r['error'] = 'native_admission: protected_durability_failed:/data/user/0/db'
                result = assess(e, r)
                self.assertEqual(result['classification'], 'insufficient_evidence')
                self.assertFalse(result['durable_close_verified'])

    def test_missing_and_corrupted_records_fail_closed(self):
        for evidence, receipt in [(None, {}), ({}, {}), ({'pre': []}, {'phase': 'CHECKPOINT_FAILED', 'error': BLOCKER})]:
            self.assertEqual(assess(evidence, receipt)['classification'], 'insufficient_evidence')


if __name__ == '__main__': unittest.main()
