#!/usr/bin/env python3
"""Keep four-case dispatch, strict original probe failures and APK identity intact."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('internal_cases',Path(__file__).with_name('run_internal_observer_stage_case.py'))
CASES=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CASES)


class InternalCaseContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.apk=self.root/'candidate.apk';self.apk.write_bytes(b'fixed candidate')
        self.sha=hashlib.sha256(self.apk.read_bytes()).hexdigest()

    def report(self,case,**updates):
        fresh=case=='fresh'
        value=dict(passed=True,physical_fold_accepted=False)
        value['apk_sha256' if fresh else 'candidate_apk_sha256']=self.sha
        if not fresh:value.update(scenario='loaded' if case=='loaded' else 'early',early_boundary='core-initialized' if case=='core-initialized' else 'owner')
        value.update(updates)
        name='ANDROID-PROCESS-PROBE.json' if fresh else 'OBSERVER-UPGRADE-PROBE.json'
        (self.root/name).write_text(json.dumps(value));return value

    def command(self,case):return CASES.command_for(case,self.apk,Path('baseline.apk'),Path('addons'),self.root)

    def test_fresh_preserves_original_java_save_requirement(self):
        cmd=self.command('fresh');self.assertTrue(cmd[1].endswith('essential_android_probe.py'))
        self.assertIn('--require-java-save-proof',cmd);self.assertEqual(cmd[cmd.index('--apk')+1],str(self.apk))

    def test_cold_keeps_owner_boundary(self):
        cmd=self.command('cold');self.assertEqual(cmd[cmd.index('--scenario')+1],'early');self.assertEqual(cmd[cmd.index('--early-boundary')+1],'owner')

    def test_core_keeps_exact_phase_boundary(self):
        cmd=self.command('core-initialized');self.assertEqual(cmd[cmd.index('--scenario')+1],'early');self.assertEqual(cmd[cmd.index('--early-boundary')+1],'core-initialized')

    def test_loaded_keeps_loaded_probe_and_baseline(self):
        cmd=self.command('loaded');self.assertEqual(cmd[cmd.index('--scenario')+1],'loaded');self.assertEqual(cmd[cmd.index('--baseline-apk')+1],'baseline.apk')

    def test_all_exact_original_success_reports_accepted_only_as_internal(self):
        for case in CASES.CASES:
            with self.subTest(case=case):
                self.report(case);proof=CASES.verify_report(case,self.root,self.sha)
                self.assertTrue(proof['passed']);self.assertFalse(proof['apk_deliverable']);self.assertFalse(proof['final_lock_authorized'])

    def test_each_original_failure_is_rejected(self):
        for case in CASES.CASES:
            with self.subTest(case=case):
                self.report(case,passed=False)
                with self.assertRaisesRegex(RuntimeError,'probe result failed'):CASES.verify_report(case,self.root,self.sha)

    def test_wrong_candidate_is_rejected_for_every_case(self):
        for case in CASES.CASES:
            with self.subTest(case=case):
                self.report(case)
                with self.assertRaisesRegex(RuntimeError,'identity'):CASES.verify_report(case,self.root,'f'*64)

    def test_wrong_phase_cannot_count_as_requested_case(self):
        self.report('core-initialized',early_boundary='owner')
        with self.assertRaisesRegex(RuntimeError,'Wrong internal shutdown phase'):CASES.verify_report('core-initialized',self.root,self.sha)

    def test_apk_change_refuses_to_start_probe(self):
        with patch.object(CASES.subprocess,'run') as runner:
            with self.assertRaisesRegex(RuntimeError,'APK changed'):CASES.run_case('fresh',self.apk,Path('base'),Path('addons'),self.root,'f'*64)
            runner.assert_not_called()

    def test_process_failure_propagates_without_success_receipt(self):
        with patch.object(CASES.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['original-probe'])):
            with self.assertRaises(subprocess.CalledProcessError):CASES.run_case('cold',self.apk,Path('base'),Path('addons'),self.root,self.sha)
        self.assertFalse((self.root/'INTERNAL-CASE-IDENTITY.json').exists())

    def test_physical_claim_is_rejected(self):
        self.report('loaded',physical_fold_accepted=True)
        with self.assertRaisesRegex(RuntimeError,'physical Fold'):CASES.verify_report('loaded',self.root,self.sha)

    def test_unknown_case_cannot_fall_back_to_pass(self):
        with self.assertRaises(ValueError):self.command('unknown')
        with self.assertRaises(ValueError):CASES.verify_report('unknown',self.root,self.sha)


if __name__=='__main__':unittest.main(verbosity=2)
