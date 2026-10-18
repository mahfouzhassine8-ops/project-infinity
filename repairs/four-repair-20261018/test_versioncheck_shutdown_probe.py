"""Targeted collector must stay PID-bound and cannot grant failed Close acceptance."""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import versioncheck_shutdown_probe as target


class TargetedEvidenceTest(unittest.TestCase):
    def test_full_runtime_identity_rejects_disabled_wrong_source_and_cross_owner(self):
        import android_ui
        import versioncheck_android as package
        expected = {'addon': package.ADDON, 'version': package.VERSION,
                    'archive_sha256': package.ARCHIVE_SHA, 'service_sha256': package.CANDIDATE_SERVICE_SHA,
                    'source_apk_sha256': package.APK_SHA}
        for variant in ('valid', 'disabled', 'wrong_version', 'wrong_source', 'wrong_uid', 'wrong_pid', 'wrong_owner',
                        'changed_owner', 'wrong_archive'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmp:
                owner = {'owner': 'session', 'pid': 123}
                selected = {'owner': 'session', 'pid': 123, 'uid': 10167, 'android': True,
                            'addon_version': package.VERSION, 'service_sha256': package.CANDIDATE_SERVICE_SHA,
                            'addon_path': '/actual/kodi/selected/service.xbmc.versioncheck'}
                details = {'enabled': variant != 'disabled',
                           'version': 'wrong' if variant == 'wrong_version' else package.VERSION}
                if variant == 'wrong_source': selected['service_sha256'] = 'wrong'
                if variant == 'wrong_uid': selected['uid'] = 1000
                if variant == 'wrong_pid': selected['pid'] = 999
                if variant == 'wrong_owner': selected['owner'] = 'other'
                proof = dict(expected)
                if variant == 'wrong_archive': proof['archive_sha256'] = 'wrong'
                calls = []
                def rpc(method, params):
                    calls.append((method, params))
                    if method == 'Addons.GetAddonDetails':
                        return {'addon': details if params['addonid'] == package.ADDON else {'enabled': False}}
                    return 'OK'
                runtime = SimpleNamespace(PRIVATE='/private', PROFILE='/profile', APP_UID=10167, rpc=rpc,
                                          read_json=lambda path: owner if '/files/' in path else selected)
                side_effect = [True, False] if variant == 'changed_owner' else lambda *_: True
                with patch.object(target, '_same_live_owner', side_effect=side_effect), \
                     patch.object(android_ui.time, 'monotonic', side_effect=[0, 1, 61]), \
                     patch.object(android_ui.time, 'sleep'):
                    if variant == 'valid':
                        result = android_ui.verify_versioncheck_candidate(runtime, tmp, proof, 'test')
                        self.assertTrue(result['verified'])
                    else:
                        with self.assertRaises(RuntimeError):
                            android_ui.verify_versioncheck_candidate(runtime, tmp, proof, 'test')
                for method, params in calls:
                    if method in ('Addons.SetAddonEnabled', 'Addons.ExecuteAddon'):
                        self.assertEqual(target.DIAGNOSTIC, params['addonid'])

    def test_descriptor_helper_observes_divergent_flags_then_releases_flushes_and_closes(self):
        for outcome in ('release', 'timeout', 'flush_error'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as tmp:
                prefix = str(Path(tmp) / target.DESCRIPTOR_PREFIX)
                events = []
                class Maps(io.StringIO):
                    mode = 'r'
                    def fileno(self): return 777
                    def writable(self): return False
                    def flush(self):
                        events.append('flush')
                        if outcome == 'flush_error': raise OSError('retained flush failure')
                    def close(self):
                        events.append('close')
                        io.StringIO.close(self)
                maps = Maps('one mapped line\n')
                original_open = open
                def safe_open(path, *args, **kwargs):
                    if path == '/proc/self/maps': return maps
                    if path == '/proc/self/fdinfo/777': return io.StringIO('flags:\t0100002\nino:\t99\n')
                    return original_open(path, *args, **kwargs)
                release = {'owner': 'old', 'nonce': 'wrong' if outcome == 'timeout' else 'request',
                           'pid': os.getpid(), 'descriptor': 777}
                Path(prefix + 'release.json').write_text(json.dumps(release))
                fake_modules = {'xbmc': SimpleNamespace(getCondVisibility=lambda *_: True),
                                'xbmcvfs': SimpleNamespace(translatePath=lambda *_: prefix)}
                identity = SimpleNamespace(st_dev=1, st_ino=42, st_mode=stat.S_IFREG | 0o600, st_nlink=0)
                times = [0, 1, 31] if outcome == 'timeout' else [0, 1]
                with patch.dict(sys.modules, fake_modules), patch('builtins.open', side_effect=safe_open), \
                     patch.object(sys, 'argv', ['helper', 'old', 'request']), \
                     patch('os.fstat', return_value=identity), \
                     patch('os.readlink', return_value='/memfd:[guest /proc/self/maps] (deleted)'), \
                     patch('time.monotonic', side_effect=times), patch('time.sleep'):
                    exec(compile(target.DESCRIPTOR_SOURCE, 'descriptor-helper', 'exec'), {})
                pre = json.loads(Path(prefix + 'pre.json').read_text())
                post = json.loads(Path(prefix + 'post.json').read_text())
                self.assertFalse(pre['writable'])
                self.assertEqual(42, pre['before']['ino'])
                self.assertIn('ino:\t99', pre['before']['fdinfo'])
                self.assertEqual(['flush', 'close'], events)
                self.assertEqual(outcome == 'timeout', post['hold_timed_out'])
                self.assertEqual(outcome != 'flush_error', post['read_flush_close_completed'])
                self.assertTrue(post['closed'])
                self.assertFalse(post['held'])
                if outcome == 'flush_error': self.assertIn('retained flush failure', post['errors'][0]['error'])

    def test_descriptor_metadata_has_no_descriptor_control_or_buffer_unwrap(self):
        tree = ast.parse(target.DESCRIPTOR_SOURCE)
        calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        attributes = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
        for forbidden in ('fcntl', 'ioctl', 'buffer', 'raw', 'dup', 'dup2', 'detach'):
            self.assertNotIn(forbidden, attributes)
        for forbidden in ('os.system', 'os.popen', 'os.fork', 'os.execv', 'os.spawnv'):
            self.assertNotIn(forbidden, calls)
        for required in ('os.fstat', 'os.readlink', 'maps.readline', 'maps.flush', 'maps.close'):
            self.assertIn(required, calls)

    def test_descriptor_host_correlates_and_releases_without_controlling_descriptor(self):
        self.probe.rpc.side_effect = lambda method, params: {'addon': {'enabled': True}} if method == 'Addons.GetAddonDetails' else 'OK'
        pre = {'owner': 'old', 'pid': 123, 'uid': 10167, 'android': True, 'nonce': 'request', 'descriptor': 7}
        post = {**pre, 'release_received': True, 'read_flush_close_completed': False, 'closed': True, 'held': False,
                'errors': [{'stage': 'flush', 'error': 'preserve diagnostic failure'}]}
        commands = []
        def command(*args, **kwargs):
            commands.append(args)
            if args[:2] == ('exec-out', 'cat'):
                payload = pre if args[2].endswith('pre.json') else post
                return {'returncode': 0, 'stdout': json.dumps(payload), 'stderr': ''}
            return {'returncode': 0, 'stdout': 'kernel metadata', 'stderr': ''}
        report = {'native_owner': self.owner, 'android_platform': {'sdk': '37'},
                  'passed': False, 'close_certified': False}
        with tempfile.TemporaryDirectory() as tmp, patch.object(target, '_command', side_effect=command), \
             patch.object(target.uuid, 'uuid4', return_value=SimpleNamespace(hex='request')):
            result = target.capture_readonly_descriptor(self.probe, Path(tmp), report)
            self.assertTrue(result['captured'])
            self.assertTrue(result['terminal_confirmed'])
            self.assertEqual(post['errors'], result['post']['errors'])
            release = json.loads((Path(tmp) / 'readonly-descriptor-release.json').read_text())
            self.assertEqual({'owner': 'old', 'pid': 123, 'nonce': 'request', 'descriptor': 7}, release)
        self.assertFalse(report['passed'])
        self.assertFalse(report['close_certified'])
        observed = [args for args in commands if args[0] == 'shell']
        self.assertEqual([('shell', 'readlink', '/proc/123/fd/7'),
                          ('shell', 'stat', '-L', '-c', '%d:%i:%f:%h', '/proc/123/fd/7'),
                          ('shell', 'cat', '/proc/123/fdinfo/7'),
                          ('shell', 'readlink', '/proc/123/fd/7')], observed)

    def test_descriptor_host_rejects_foreign_and_stale_ready_without_acknowledging(self):
        for field, wrong in (('owner', 'replaced'), ('pid', 999), ('uid', 1000),
                             ('nonce', 'stale'), ('descriptor', -1), ('descriptor', True)):
            with self.subTest(field=field, wrong=wrong), tempfile.TemporaryDirectory() as tmp:
                self.setUp()
                self.probe.rpc.side_effect = lambda method, params: {'addon': {'enabled': True}} if method == 'Addons.GetAddonDetails' else 'OK'
                pre = {'owner': 'old', 'pid': 123, 'uid': 10167, 'android': True,
                       'nonce': 'request', 'descriptor': 7, field: wrong}
                commands = []
                def command(*args, **kwargs):
                    commands.append(args)
                    return {'returncode': 0, 'stdout': json.dumps(pre if args[-1].endswith('pre.json') else {}), 'stderr': ''}
                report = {'native_owner': self.owner, 'android_platform': {'sdk': '37'}}
                clock = iter(range(0, 10000, 40))
                with patch.object(target, '_command', side_effect=command), \
                     patch.object(target.uuid, 'uuid4', return_value=SimpleNamespace(hex='request')), \
                     patch.object(target.time, 'monotonic', side_effect=lambda: next(clock)), patch.object(target.time, 'sleep'):
                    result = target.capture_readonly_descriptor(self.probe, Path(tmp), report)
                self.assertFalse(result['captured'])
                self.assertFalse(result['terminal_confirmed'])
                self.assertIn('identity unavailable or mismatched', result['error'])
                self.assertTrue(all(args[:2] == ('exec-out', 'cat') for args in commands))
                self.assertFalse((Path(tmp) / 'readonly-descriptor-release.json').exists())

    def test_descriptor_metadata_failure_requires_late_closed_terminal_before_close_can_run(self):
        for closed in (True, False):
            with self.subTest(closed=closed), tempfile.TemporaryDirectory() as tmp:
                self.setUp()
                self.probe.rpc.side_effect = lambda method, params: {'addon': {'enabled': True}} if method == 'Addons.GetAddonDetails' else 'OK'
                post = {'owner': 'old', 'pid': 123, 'uid': 10167, 'android': True, 'nonce': 'request',
                        'descriptor': 7, 'closed': closed, 'held': not closed, 'hold_timed_out': True}
                post_reads = []
                commands = []
                def command(*args, **kwargs):
                    commands.append(args)
                    payload = {}
                    if args[-1].endswith('post.json'):
                        post_reads.append(args)
                        if len(post_reads) > 1: payload = post
                    return {'returncode': 0, 'stdout': json.dumps(payload), 'stderr': ''}
                report = {'native_owner': self.owner, 'android_platform': {'sdk': '37'}}
                with patch.object(target, '_command', side_effect=command), \
                     patch.object(target.uuid, 'uuid4', return_value=SimpleNamespace(hex='request')), \
                     patch.object(target.time, 'monotonic', side_effect=[0, 1, 61, 62, 63, 103]), \
                     patch.object(target.time, 'sleep'):
                    result = target.capture_readonly_descriptor(self.probe, Path(tmp), report)
                self.assertFalse(result['captured'])
                self.assertEqual(closed, result['terminal_confirmed'])
                self.assertIn('identity unavailable or mismatched', result['error'])
                self.assertEqual(post, result['post'])
                self.assertTrue(all(args[:2] == ('exec-out', 'cat') for args in commands))
                self.assertFalse((Path(tmp) / 'readonly-descriptor-release.json').exists())

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
