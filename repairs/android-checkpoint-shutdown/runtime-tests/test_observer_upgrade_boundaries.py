#!/usr/bin/env python3
"""Upgrade-only process classification; original Close still requires UID death.

Uses the failed Android run's actual completed baseline Close and receiver
origin. OS process/maps peers below are explicit test inputs, not device proof.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('observer_upgrade_probe', HERE/'observer_upgrade_android_probe.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)
EVIDENCE = json.loads((HERE/'evidence/upgrade-receiver-38887412457.json').read_text())


class UpgradeBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.completed = copy.deepcopy(EVIDENCE['baseline_loaded_close'])
        self.receipt = copy.deepcopy(self.completed['receipt'])
        self.live = [dict(pid=EVIDENCE['receiver_pid'], uid=10167, name=EVIDENCE['receiver_process_name'])]
        self.logs = EVIDENCE['receiver_origin']
        self.maps = '70000000-70001000 r-xp 0 00:00 1 /apex/com.android.art/lib64/libart.so\n'
        self.patches = [patch.object(upgrade.probe, 'processes', side_effect=lambda:self.live),
                        patch.object(upgrade.probe, 'read_json', side_effect=lambda *_:self.receipt),
                        patch.object(upgrade.probe, 'adb', side_effect=lambda *_a, **_k:self.logs),
                        patch.object(upgrade.probe, 'shell', side_effect=lambda *_a, **_k:self.maps)]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)

    def accept(self):
        return upgrade.saved_state_boundary(self.completed)

    def test_actual_update_receiver_origin_is_accepted_only_before_launch(self):
        result = self.accept()
        self.assertTrue(result['passed'])
        self.assertEqual(result['native_maps_absent'], [EVIDENCE['receiver_pid']])
        self.assertIn('not a new shutdown/death proof', result['scope'])

    def test_close_boundary_still_refuses_same_receiver_process(self):
        with self.assertRaisesRegex(AssertionError, 'whole-UID death'):
            upgrade.saved_state_boundary()

    def test_quiet_post_close_and_post_update_both_accepted(self):
        self.live = []
        self.assertTrue(upgrade.saved_state_boundary()['passed'])
        self.assertTrue(self.accept()['passed'])

    def test_native_engine_process_refused_before_launch(self):
        self.live.append(dict(pid=9000, uid=10167, name=upgrade.probe.PACKAGE+':kodi'))
        with self.assertRaisesRegex(AssertionError, 'Unexpected package process'):
            self.accept()

    def test_original_engine_pid_cannot_be_reclassified_as_receiver(self):
        self.live[0]['pid'] = self.receipt['pid']
        with self.assertRaisesRegex(AssertionError, 'Closed engine PID'):
            self.accept()

    def test_other_java_process_origin_refused(self):
        self.logs = self.logs.replace('InfinityCobraBootReceiver', 'UnknownReceiver')
        with self.assertRaisesRegex(AssertionError, 'receiver origin'):
            self.accept()

    def test_unrelated_receiver_pid_refused(self):
        self.live[0]['pid'] += 1
        with self.assertRaisesRegex(AssertionError, 'receiver origin'):
            self.accept()

    def test_native_engine_image_in_main_process_refused(self):
        self.maps += '/data/app/package/lib/arm64/libkodi.so\n'
        with self.assertRaisesRegex(AssertionError, 'Native engine loaded'):
            self.accept()

    def test_python_image_in_main_process_refused(self):
        self.maps += '/data/app/package/lib/arm64/libpython3.11.so\n'
        with self.assertRaisesRegex(AssertionError, 'Native engine loaded'):
            self.accept()

    def test_unreadable_process_maps_fail_closed(self):
        self.maps = ''
        with self.assertRaisesRegex(AssertionError, 'image identity'):
            self.accept()

    def test_receiver_that_naturally_finishes_during_observation_is_not_killed(self):
        self.maps = ''
        with patch.object(upgrade.probe, 'processes', side_effect=[self.live, []]):
            result = self.accept()
        self.assertEqual(result['naturally_finished_receivers'], [EVIDENCE['receiver_pid']])

    def test_missing_original_save_confirmation_refused(self):
        self.receipt['checkpoint_saved'] = False
        with self.assertRaises(AssertionError): self.accept()

    def test_changed_receipt_identity_refused(self):
        self.receipt['owner'] = 'new-owner'
        with self.assertRaises(AssertionError): self.accept()

    def test_missing_original_whole_uid_confirmation_refused(self):
        self.completed['whole_package_death_verified'] = False
        with self.assertRaises(AssertionError): self.accept()


if __name__ == '__main__':
    unittest.main(verbosity=2)
