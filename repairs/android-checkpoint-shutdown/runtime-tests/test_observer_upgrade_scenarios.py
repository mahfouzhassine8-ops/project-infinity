#!/usr/bin/env python3
"""Case-routing controls for independent disposable upgrade acceptance.

OS/save peers below verify orchestration only. Actual receipts, seals, package
UID death and database checks remain in the production Android probe.
"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('upgrade_scenarios', HERE/'observer_upgrade_android_probe.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


class UpgradeScenarioTest(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.report = {}
        self.ready = {identity:{'addon':identity} for identity in upgrade.IDS}
        self.early_ready = {}
        self.fail_early = False
        self.fail_loaded = False
        self.fail_reopen = False
        self.owners = iter(({'owner':'loaded','pid':200}, {'owner':'reopened','pid':300}))
        self.patches = [
            patch.object(upgrade, 'wait_owner', side_effect=lambda previous:self.owner('early', previous)),
            patch.object(upgrade.probe, 'wait_ready', side_effect=self.wait_ready),
            patch.object(upgrade, 'wait_services', side_effect=self.wait_services),
            patch.object(upgrade, 'create_missing_directory', side_effect=self.directory),
            patch.object(upgrade, 'close', side_effect=self.close),
            patch.object(upgrade, 'verify_saved_state', side_effect=self.saved),
            patch.object(upgrade.probe, 'enable_first_party', side_effect=lambda *_:self.events.append(('first_party',))),
            patch.object(upgrade.probe, 'shell', side_effect=self.shell),
            patch.object(upgrade.time, 'monotonic', return_value=100),
        ]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)

    def owner(self, identity, previous):
        self.events.append(('wait_owner', identity, previous))
        return {'owner':identity, 'pid':100}

    def wait_ready(self, previous):
        owner = next(self.owners)
        self.events.append(('wait_ready', owner['owner'], previous))
        return owner

    def wait_services(self, owner):
        self.events.append(('services', owner['owner']))
        if self.fail_reopen and owner['owner'] == 'reopened':
            raise RuntimeError('Reopened observers did not initialize')
        return self.ready

    def directory(self, owner):
        self.events.append(('directory', owner['owner']))
        return dict(mkdirs_succeeded=True, essential_settings_written=True)

    def close(self, owner, output):
        self.events.append(('close', owner['owner']))
        if (self.fail_early and owner['owner'] == 'early') or (self.fail_loaded and owner['owner'] == 'loaded'):
            raise AssertionError('Genuine Close receipt failure')
        return dict(passed=True, requested_monotonic=101, ready_at_close=self.early_ready,
                    both_java_seals_verified=True, whole_package_death_verified=True)

    def saved(self, output, require_directory=False):
        self.events.append(('saved', output.name, require_directory))
        return {'fixture':'exact hash'}

    def shell(self, *args, **kwargs):
        self.events.append(('shell', *args))
        if args[0] == 'cat':
            if args[1].endswith('/'+upgrade.DIRECTORY_FIXTURE+'/settings.xml'):
                return upgrade.DIRECTORY_SETTINGS
            identity = args[1].split('/')[-2]
            return '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n'
        return 'Starting activity'

    def run_case(self, scenario):
        upgrade.run_candidate_scenario(scenario, {'owner':'baseline','pid':50}, Path('/unused-disposable-evidence'),
                                       self.report, lambda:self.events.append(('save_report',)))

    def test_early_starts_from_its_own_baseline_and_reopens_after_verified_death(self):
        self.owners = iter(({'owner':'reopened','pid':300},))
        self.run_case('early')
        self.assertIn(('wait_owner','early','baseline'), self.events)
        self.assertEqual([event for event in self.events if event[0]=='close'], [('close','early')])
        self.assertNotIn('candidate_loaded_close', self.report)
        self.assertFalse(any(event[0]=='directory' for event in self.events))
        self.assertLess(self.events.index(('saved','after-early-close',False)), self.events.index(('wait_ready','reopened','early')))
        self.assertEqual(self.report['early_ready_count'],0)
        self.assertEqual(len(self.report['reopen_ready_services']),37)
        self.assertTrue(self.report['saved_data_reopen_verified'])

    def test_loaded_starts_from_its_own_baseline_without_attempting_early_close(self):
        self.run_case('loaded')
        self.assertIn(('wait_ready','loaded','baseline'), self.events)
        self.assertFalse(any(event[0]=='wait_owner' for event in self.events))
        self.assertEqual([event for event in self.events if event[0]=='close'], [('close','loaded')])
        self.assertNotIn('candidate_early_close', self.report)
        self.assertLess(self.events.index(('services','loaded')),self.events.index(('directory','loaded')))
        self.assertLess(self.events.index(('directory','loaded')),self.events.index(('close','loaded')))
        self.assertIn(('saved','after-loaded-close',True), self.events)
        self.assertEqual(len(self.report['candidate_ready_services']),37)
        self.assertTrue(self.report['saved_data_reopen_verified'])

    def test_failed_early_close_is_retained_as_failure_without_loaded_or_reopen_attempt(self):
        self.fail_early = True
        with self.assertRaisesRegex(AssertionError,'Genuine Close'):
            self.run_case('early')
        self.assertFalse(any(event[0] in ('directory','wait_ready','saved') for event in self.events))
        self.assertFalse(self.report.get('saved_data_reopen_verified',False))

    def test_failed_loaded_close_never_claims_saved_data_reopen(self):
        self.fail_loaded = True
        with self.assertRaisesRegex(AssertionError,'Genuine Close'):
            self.run_case('loaded')
        self.assertNotIn(('wait_ready','reopened','loaded'), self.events)
        self.assertFalse(self.report.get('saved_data_reopen_verified',False))

    def test_loaded_reopen_observer_failure_is_not_accepted(self):
        self.fail_reopen = True
        with self.assertRaisesRegex(RuntimeError,'Reopened observers'):
            self.run_case('loaded')
        self.assertFalse(self.report.get('saved_data_reopen_verified',False))

    def test_fully_loaded_timing_cannot_be_reported_as_early(self):
        self.early_ready = self.ready
        with self.assertRaisesRegex(AssertionError,'Early timing control missed startup'):
            self.run_case('early')
        self.assertFalse(any(event[0]=='saved' for event in self.events))

    def test_combined_legacy_route_keeps_both_original_close_controls(self):
        self.run_case('combined')
        self.assertEqual([event for event in self.events if event[0]=='close'], [('close','early'),('close','loaded')])
        self.assertIn(('wait_ready','loaded','early'), self.events)
        self.assertTrue(self.report['saved_data_reopen_verified'])

    def test_invalid_scenario_refused_before_launch(self):
        with self.assertRaises(AssertionError): self.run_case('unknown')
        self.assertFalse(self.events)


if __name__ == '__main__':
    unittest.main(verbosity=2)
