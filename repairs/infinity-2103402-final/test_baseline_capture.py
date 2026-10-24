"""Host collector safety/failure tests; not Android or device evidence."""
from pathlib import Path
import sys
import tempfile
import unittest

import capture_baseline as collector


class CaptureTests(unittest.TestCase):
    def test_fixed_commands_are_read_only_and_preserve_buffers(self):
        forbidden = {'install', 'uninstall', 'clear', 'force-stop', 'kill', 'killall',
                     'setprop', 'root', 'reboot', 'am', '-c', 'settings'}
        for name, command in collector.commands():
            self.assertFalse(forbidden.intersection(command), name)
            self.assertNotIn('sh', command)
            if command[0] == 'logcat': self.assertIn('-d', command)
        self.assertIn(('exit-info.txt', ['shell', 'dumpsys', 'activity', 'exit-info', collector.PACKAGE]), collector.commands())

    def test_bounded_output_and_partial_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'limited.txt'
            result = collector.capture([sys.executable, '-c', "print('x'*1000000)"], path, limit=1024)
            self.assertEqual(path.stat().st_size, 1024)
            self.assertEqual(result['status'], 'output_limit_or_read_failure')
            path = Path(temp) / 'failed.txt'
            result = collector.capture([sys.executable, '-c', "import sys; print('partial'); sys.exit(7)"], path)
            self.assertEqual(result['status'], 'command_failed')
            self.assertEqual(result['returncode'], 7)
            self.assertEqual(path.read_text(), 'partial\n')

    def test_timeout_and_missing_tool_are_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            result = collector.capture([sys.executable, '-c', 'import time; time.sleep(10)'],
                                       Path(temp) / 'timeout.txt', timeout=.1)
            self.assertEqual(result['status'], 'timeout')
            result = collector.capture([str(Path(temp) / 'missing-adb')], Path(temp) / 'missing.txt')
            self.assertEqual(result['status'], 'unavailable')
            self.assertEqual(result['error_type'], 'FileNotFoundError')


if __name__ == '__main__': unittest.main(verbosity=2)
