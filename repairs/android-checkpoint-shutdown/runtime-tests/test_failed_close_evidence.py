#!/usr/bin/env python3
"""Failed-Close evidence never retries or grants acceptance; OS peers are mocked."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('failed_close_probe', HERE/'observer_upgrade_android_probe.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


class FailedCloseEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.owner = dict(pid=123, owner='failed-owner')
        self.current = dict(self.owner)
        self.qemu = '1'
        self.live = [dict(pid=123, uid=10167, name=upgrade.probe.PACKAGE+':kodi')]
        self.patches = [patch.object(upgrade.probe, 'APP_UID', '10167'),
            patch.object(upgrade.probe, 'processes', side_effect=lambda:self.live),
            patch.object(upgrade.probe, 'read_json', side_effect=lambda *_:self.current),
            patch.object(upgrade.probe, 'shell', side_effect=self.shell),
            patch.object(upgrade.probe, 'adb', return_value='thread state'),
            patch.object(upgrade, 'ready_services', return_value={}),
            patch.object(upgrade.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'native stack', ''))]
        self.active = [item.start() for item in self.patches]
        for item in self.patches: self.addCleanup(item.stop)

    def shell(self, *args, **kwargs):
        return self.qemu if args[:2] == ('getprop', 'ro.kernel.qemu') else 'mapped native image'

    def capture(self):
        with tempfile.TemporaryDirectory() as directory:
            result = upgrade.capture_failed_close(self.owner, Path(directory))
            files = {p.name:p.read_text() for p in Path(directory).iterdir()}
        return result, files

    def test_matching_failed_emulator_engine_yields_stack_without_acceptance(self):
        result, files = self.capture()
        self.assertTrue(result['captured'])
        self.assertIn('native stack', files['failed-engine-backtrace.txt'])
        self.assertNotIn('passed', result)
        self.assertNotIn('authorization_consumed', result)
        self.active[-1].assert_called_once_with(['adb', 'shell', 'debuggerd', '-b', '123'],
                                               capture_output=True, text=True, timeout=15)

    def test_physical_device_never_receives_stack_request(self):
        self.qemu = '0'
        result, files = self.capture()
        self.assertFalse(result['captured'])
        self.assertFalse(files)
        self.active[-1].assert_not_called()

    def test_replaced_owner_is_never_inspected_as_failed_engine(self):
        self.current['owner'] = 'different-owner'
        result, files = self.capture()
        self.assertFalse(result['captured'])
        self.assertFalse(files)
        self.active[-1].assert_not_called()

    def test_wrong_uid_never_receives_stack_request(self):
        self.live[0]['uid'] = 1000
        result, files = self.capture()
        self.assertFalse(result['captured'])
        self.assertFalse(files)
        self.active[-1].assert_not_called()

    def test_dead_engine_is_not_restarted_for_evidence(self):
        self.live = []
        result, files = self.capture()
        self.assertFalse(result['captured'])
        self.assertFalse(files)
        self.active[-1].assert_not_called()


if __name__ == '__main__':
    unittest.main()
