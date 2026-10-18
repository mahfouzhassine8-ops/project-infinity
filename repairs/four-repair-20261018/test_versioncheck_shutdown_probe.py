"""Targeted collector must stay PID-bound and cannot grant failed Close acceptance."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import versioncheck_shutdown_probe as target


class TargetedEvidenceTest(unittest.TestCase):
    def test_healthy_corrected_service_needs_actual_runner_and_original_run_message(self):
        observation = {'addon_path': '/addons/service.xbmc.versioncheck',
                       'addon_version': '0.5.28+infinity.1',
                       'settings': {'versioncheck_enable': 'true'}}
        native = 'debug: CPythonInvoker(1, /addons/service.xbmc.versioncheck/resources/lib/runner.py): start processing'
        service = 'debug: Version Check: Version 0.5.28+infinity.1 started'
        self.assertTrue(target.startup_evidence(native + '\n' + service, observation)['ready'])
        for text in (native, service, native.replace('/addons/', '/wrong/'),
                     native + '\n' + service.replace('0.5.28+infinity.1', '0.5.27+matrix.1')):
            self.assertFalse(target.startup_evidence(text, observation)['ready'])
        observation['settings']['versioncheck_enable'] = 'false'
        self.assertTrue(target.startup_evidence(native + '\ndebug: Version Check: Disabled', observation)['ready'])

    def test_original_failed_import_is_observed_without_qualifying_close(self):
        observation = {'addon_path': '/apk/assets/addons/service.xbmc.versioncheck',
                       'addon_version': '0.5.27+matrix.1',
                       'settings': {'versioncheck_enable': 'true'}}
        native = 'debug: CPythonInvoker(1, /apk/assets/addons/service.xbmc.versioncheck/resources/lib/runner.py): failure in script'
        self.assertTrue(target.startup_evidence(native, observation)['ready'])
        self.assertFalse(target.startup_evidence('CAddonMgr::FindAddons: service.xbmc.versioncheck v0.5.27+matrix.1 installed', observation)['ready'])

    def setUp(self):
        self.owner = {'owner': 'old', 'pid': 123}
        self.current = dict(self.owner)
        self.qemu = '1'
        self.live = [{'pid': 123, 'uid': 10167, 'name': 'com.projectinfinity.kodi:kodi'}]
        self.probe = Mock(PRIVATE='/data/user/0/com.projectinfinity.kodi',
                          PROFILE='/profile', PACKAGE='com.projectinfinity.kodi', APP_UID='10167')
        self.probe.read_json.side_effect = lambda *_: self.current
        self.probe.processes.side_effect = lambda: self.live
        self.probe.shell.side_effect = lambda *_a, **_k: self.qemu

    def capture(self):
        report = {'native_owner': self.owner, 'passed': False, 'close_certified': False}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(target, '_command', return_value={'returncode': 0, 'stdout': 'evidence'}) as run:
                target.capture_failure(self.probe, Path(tmp), report)
                evidence = json.loads((Path(tmp) / 'VERSIONCHECK-FAILED-ENGINE.json').read_text())
        self.assertFalse(report['passed'])
        self.assertFalse(report['close_certified'])
        self.probe.rpc.assert_not_called()
        self.probe.adb.assert_not_called()
        return evidence, run.call_args_list

    def test_matching_live_emulator_failure_collects_backtrace_without_retry(self):
        evidence, commands = self.capture()
        self.assertTrue(evidence['captured'])
        self.assertTrue(evidence['same_owner_after'])
        self.assertEqual([('shell', 'debuggerd', '-b', '123')],
                         [call.args for call in commands if 'debuggerd' in call.args])

    def test_no_inspection_of_physical_device_or_replaced_or_wrong_uid_or_dead_engine(self):
        for field in ('physical', 'owner', 'uid', 'dead'):
            with self.subTest(field=field):
                self.setUp()
                if field == 'physical': self.qemu = '0'
                if field == 'owner': self.current['owner'] = 'replacement'
                if field == 'uid': self.live[0]['uid'] = 1000
                if field == 'dead': self.live = []
                evidence, commands = self.capture()
                self.assertFalse(evidence['captured'])
                self.assertEqual([], commands)

    def test_app_helper_collects_metadata_without_subprocess_or_general_environment(self):
        tree = ast.parse(target.DIAGNOSTIC_SOURCE)
        calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        imports = [name.name for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names]
        self.assertNotIn('subprocess', imports)
        for forbidden in ('os.system', 'os.popen', 'os.fork', 'os.execv', 'os.spawnv'):
            self.assertNotIn(forbidden, calls)
        for required in ('os.lstat', 'os.stat', 'os.statvfs', 'os.getpid', 'os.getuid', 'os.readlink'):
            self.assertIn(required, calls)
        env_reads = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and ast.unparse(node.func) == 'os.environ.get']
        self.assertEqual(1, len(env_reads))
        self.assertEqual('PATH', env_reads[0].args[0].value)
        self.assertNotIn('dict(os.environ)', target.DIAGNOSTIC_SOURCE)

    def test_settings_hash_uses_exact_bytes(self):
        payload = b'<settings>\r\n  \xc3\xa9\r\n</settings>\r\n'
        completed = subprocess.CompletedProcess([], 0, payload, b'')
        with patch.object(target.subprocess, 'run', return_value=completed):
            result = target._settings(self.probe)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), result['sha256'])
        self.assertEqual(len(payload), result['bytes'])

    def test_disposable_helper_has_exact_separate_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = target.stage_diagnostic(tmp)
            self.assertEqual(target.DIAGNOSTIC, folder.name)
            self.assertEqual(target.DIAGNOSTIC_SOURCE, (folder / 'default.py').read_text())
            self.assertIn('id="' + target.DIAGNOSTIC + '"', (folder / 'addon.xml').read_text())


if __name__ == '__main__':
    unittest.main()
