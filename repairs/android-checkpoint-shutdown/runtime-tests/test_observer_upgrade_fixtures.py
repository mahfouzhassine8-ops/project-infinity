#!/usr/bin/env python3
"""Run actual retained-state/write fixtures with Python optimization 0 and 1.

Kodi APIs are explicit peers; mkdirs and settings files use the real temporary
filesystem. These are fixture controls, not native durability or Fold proof.
"""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('upgrade_fixture_controls', HERE/'observer_upgrade_android_probe.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)

# Exact operation ordering from the failed fixture: the required mkdirs call
# was embedded in assert and disappeared before open(state, 'w') under -O.
FAILED_DIRECTORY_SEQUENCE = """import os, xbmcvfs
assert not os.path.exists(root), 'Directory creation control must start missing'
assert xbmcvfs.mkdirs(root) is True
assert os.path.isdir(root)
state = os.path.join(root, 'settings.xml')
with open(state, 'w') as saved: saved.write('essential')
"""


class OptimizedFixtureTest(unittest.TestCase):
    def fixture(self, folder, *, mkdirs_result=True, create_directory=True, fail_write=False):
        root = Path(folder)/'missing-profile'
        identity = 'service.observerprobe.writer01'
        calls, logs = [], []
        def mkdirs(path):
            calls.append(path)
            if create_directory:
                Path(path).mkdir(parents=True)
                if fail_write: os.symlink('/dev/full', Path(path)/'settings.xml')
            return mkdirs_result
        addon = types.ModuleType('xbmcaddon')
        addon.Addon = lambda:types.SimpleNamespace(getAddonInfo=lambda key:identity if key=='id' else str(root))
        vfs = types.ModuleType('xbmcvfs'); vfs.translatePath = lambda path:path; vfs.mkdirs = mkdirs
        xbmc = types.ModuleType('xbmc'); xbmc.LOGERROR = 4; xbmc.log = lambda *args:logs.append(args)
        xbmc.Monitor = lambda:types.SimpleNamespace(abortRequested=lambda:True)
        return root, identity, calls, logs, {'xbmcaddon':addon, 'xbmcvfs':vfs, 'xbmc':xbmc}

    def execute(self, source, optimization, modules, **variables):
        with patch.dict('sys.modules', modules):
            exec(compile(source, 'actual-upgrade-fixture.py', 'exec', optimize=optimization), variables)

    def test_original_assert_side_effect_reproduces_missing_parent_under_optimization(self):
        with tempfile.TemporaryDirectory() as folder:
            root, _, calls, _, modules = self.fixture(folder)
            with self.assertRaises(FileNotFoundError):
                self.execute(FAILED_DIRECTORY_SEQUENCE, 1, modules, root=str(root))
            self.assertEqual(calls, [])
            self.assertFalse(root.exists())

    def test_original_unoptimized_control_executes_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root, _, calls, _, modules = self.fixture(folder)
            self.execute(FAILED_DIRECTORY_SEQUENCE, 0, modules, root=str(root))
            self.assertEqual(calls, [str(root)])
            self.assertEqual((root/'settings.xml').read_text(), 'essential')

    def test_corrected_directory_fixture_executes_creation_and_real_write_with_both_optimization_levels(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, _, calls, logs, modules = self.fixture(folder)
                self.execute(upgrade.DIRECTORY_SCRIPT, optimization, modules)
                self.assertEqual(calls, [str(root)])
                self.assertEqual((root/'settings.xml').read_text(), upgrade.DIRECTORY_SETTINGS)
                result = json.loads((root/'observation.json').read_text())
                self.assertTrue(result['mkdirs_succeeded'] and result['essential_settings_written'])
                descriptor = result['settings_descriptor']
                info = (root/'settings.xml').stat()
                self.assertEqual(descriptor['inode'], info.st_ino)
                self.assertEqual(descriptor['device'], info.st_dev)
                self.assertEqual(descriptor['target'], str(root/'settings.xml'))
                self.assertEqual(descriptor['requested_mode'], 'w')
                self.assertEqual(descriptor['access_mode'], os.O_WRONLY)
                self.assertEqual(descriptor['requested_flags'], os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
                self.assertEqual(logs, [])

    def test_directory_creation_refusal_fails_before_settings_or_observation(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, _, _, logs, modules = self.fixture(folder, mkdirs_result=False, create_directory=False)
                with self.assertRaisesRegex(RuntimeError, 'mkdirs did not confirm'):
                    self.execute(upgrade.DIRECTORY_SCRIPT, optimization, modules)
                self.assertFalse(root.exists())
                self.assertIn('stage=directory.mkdirs',logs[0][0])

    def test_directory_false_positive_is_refused_even_with_optimization(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, _, _, _, modules = self.fixture(folder, create_directory=False)
                with self.assertRaisesRegex(RuntimeError, 'not a directory'):
                    self.execute(upgrade.DIRECTORY_SCRIPT, optimization, modules)
                self.assertFalse((root/'observation.json').exists())

    def test_preexisting_directory_cannot_be_misreported_as_new_creation(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, _, calls, _, modules = self.fixture(folder)
                root.mkdir()
                with self.assertRaisesRegex(RuntimeError, 'must start missing'):
                    self.execute(upgrade.DIRECTORY_SCRIPT, optimization, modules)
                self.assertEqual(calls, [])
                self.assertFalse((root/'observation.json').exists())

    def test_actual_os_write_failure_never_reports_success(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, _, _, logs, modules = self.fixture(folder, fail_write=True)
                with self.assertRaises(OSError):
                    self.execute(upgrade.DIRECTORY_SCRIPT, optimization, modules)
                self.assertFalse((root/'observation.json').exists())
                self.assertIn('stage=settings.write',logs[0][0])

    def test_matching_retained_service_settings_are_read_and_verified_before_ready(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, identity, calls, _, modules = self.fixture(folder)
                root.mkdir(); state = '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n'
                (root/'settings.xml').write_text(state)
                self.execute(upgrade.SERVICE, optimization, modules)
                result = json.loads((root/'ready.json').read_text())
                self.assertTrue(result['retained_settings_verified'])
                self.assertEqual((root/'settings.xml').read_text(), state)
                self.assertEqual(calls, [])

    def test_wrong_retained_service_settings_fail_before_ready_without_modification(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, _, calls, _, modules = self.fixture(folder)
                root.mkdir(); (root/'settings.xml').write_text('existing data must survive')
                with self.assertRaisesRegex(RuntimeError, 'Retained service state changed'):
                    self.execute(upgrade.SERVICE, optimization, modules)
                self.assertEqual((root/'settings.xml').read_text(), 'existing data must survive')
                self.assertFalse((root/'ready.json').exists())
                self.assertEqual(calls, [])


    def test_ready_receipt_requires_retained_settings_confirmation(self):
        identity = upgrade.IDS[0]
        stale = dict(addon=identity, pid=81, observer_initialized=True)
        with patch.object(upgrade.probe, 'adb', return_value=json.dumps(stale)):
            self.assertEqual(upgrade.ready_services(81), {})
        verified = dict(stale, retained_settings_verified=True)
        with patch.object(upgrade.probe, 'adb', return_value=json.dumps(verified)):
            self.assertEqual(set(upgrade.ready_services(81)), {identity})

    def test_wrong_process_ready_receipt_cannot_confirm_current_retained_state(self):
        verified = dict(addon=upgrade.IDS[0], pid=81, observer_initialized=True, retained_settings_verified=True)
        with patch.object(upgrade.probe, 'adb', return_value=json.dumps(verified)):
            self.assertEqual(upgrade.ready_services(82), {})

    def test_service_new_profile_writes_expected_settings_with_optimization(self):
        for optimization in (0,1):
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory() as folder:
                root, identity, calls, _, modules = self.fixture(folder)
                self.execute(upgrade.SERVICE, optimization, modules)
                self.assertEqual((root/'settings.xml').read_text(), '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n')
                self.assertEqual(calls, [str(root)])
                self.assertTrue(json.loads((root/'ready.json').read_text())['retained_settings_verified'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
