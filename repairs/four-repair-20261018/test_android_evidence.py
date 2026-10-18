"""Host checks for diagnostic collection, not Android/Fold qualification."""
import ast
import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

HERE = Path(__file__).resolve().parent


class EvidenceTests(unittest.TestCase):
    def test_private_capture_paths_never_control_the_application(self):
        capture = runpy.run_path(str(HERE / 'capture_stop.py'))
        for scenario in ('A', 'B', 'background', 'screensaver', 'fold'):
            with self.subTest(path=scenario), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'private'
                calls = []
                def adb(command, **kwargs):
                    calls.append(command)
                    stdout = 'versionCode=2103386' if 'package' in command else ''
                    return subprocess.CompletedProcess(command, 0, stdout, '')
                with patch('sys.argv', ['capture_stop.py', '--path', scenario, '--out', str(out)]), \
                     patch('shutil.which', return_value='/adb'), \
                     patch('subprocess.check_output', return_value='List of devices attached\nphone\tdevice\n'), \
                     patch('subprocess.run', side_effect=adb), \
                     patch('subprocess.Popen', return_value=Mock()), \
                     patch('builtins.input', return_value=''), \
                     patch('os.umask'), contextlib.redirect_stdout(io.StringIO()):
                    capture['main']()
                events = json.loads((out / 'timeline.json').read_text())
                self.assertEqual(events[0]['stage'], 'capture-started')
                self.assertEqual(events[-1]['stage'], 'reproduction-ended')
                self.assertTrue((out / 'firmware.json').is_file())
                self.assertTrue((out / 'after-threads.json').is_file())
                for command in calls:
                    operation = command[3:]
                    self.assertTrue(operation[0] in ('shell', 'logcat', 'pull'))
                    if operation[0] == 'shell':
                        self.assertIn(operation[1], ('dumpsys', 'getprop', 'date', 'ps', 'log'))
                    self.assertNotIn('debuggerd', operation)
                    self.assertNotIn('-c', operation)

    def diagnostic(self, directory, *, new_boot=False, new_owner=False):
        tree = ast.parse((HERE / 'android_interactions.py').read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                    and n.name == 'diagnostic_dump')
        module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
        owner = dict(pid=12, owner='original', launch='launch', live=True)
        probe = SimpleNamespace(PRIVATE='/private',
            shell=lambda *args: 'new-boot' if new_boot else 'boot',
            read_json=lambda *args: {**owner, 'owner': 'restarted'} if new_owner else owner,
            processes=lambda: [dict(pid=12)])
        def require(ok, message):
            if not ok: raise RuntimeError(message)
        namespace = dict(subprocess=subprocess, time=time, json=json, out=directory,
                         report={'native_owner': owner}, boot_id='boot', probe=probe,
                         require=require)
        exec(compile(module, str(HERE / 'android_interactions.py'), 'exec'), namespace)
        return namespace['diagnostic_dump']

    def test_transport_recovery_retains_failed_read_and_requires_same_engine(self):
        for reboot, restart in ((False, False), (True, False), (False, True)):
            with self.subTest(reboot=reboot, restart=restart), tempfile.TemporaryDirectory() as tmp:
                fn = self.diagnostic(Path(tmp), new_boot=reboot, new_owner=restart)
                outcomes = [subprocess.CompletedProcess([], 255, 'INPUT MANAGER\n', ''),
                            subprocess.CompletedProcess([], 0, '', ''),
                            subprocess.CompletedProcess([], 0, 'Input Dispatcher State:\ncomplete', '')]
                with patch('subprocess.run', side_effect=outcomes) as calls, \
                     contextlib.redirect_stdout(io.StringIO()):
                    if reboot or restart:
                        with self.assertRaises(RuntimeError): fn('selected', 'input')
                    else:
                        self.assertIn('Input Dispatcher State:', fn('selected', 'input'))
                self.assertEqual(calls.call_args_list[1].args[0], ['adb', 'wait-for-device'])
                self.assertEqual((Path(tmp) / 'selected-input-attempt-1-stdout.txt').read_text(),
                                 'INPUT MANAGER\n')

    def test_two_incomplete_reads_remain_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            fn = self.diagnostic(Path(tmp))
            bad = subprocess.CompletedProcess([], 0, 'INPUT MANAGER\n', '')
            with patch('subprocess.run', return_value=bad), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'unavailable after two'):
                    fn('selected', 'input')


if __name__ == '__main__':
    unittest.main()
