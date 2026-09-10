from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'addons/script.infinity.support'))
import android_logcat as logcat
import support


class LogcatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.exe = self.root / 'logcat'
        self.exe.write_text('fixture placeholder; never executed')
        self.output = self.root / 'capture'

    def tearDown(self):
        self.tmp.cleanup()

    def runner(self, command, **kwargs):
        self.assertIn('--uid=', command[1])
        self.assertEqual(command[2:], ['-b', 'crash', '-d', '-t', '200', '-v', 'threadtime'])
        self.assertEqual(kwargs['timeout'], 5)
        self.assertNotIn('shell', kwargs)
        kwargs['stdout'].write(b'fixture crash entry\n')
        return SimpleNamespace(returncode=0)

    def test_same_uid_only_and_no_shell(self):
        result = logcat.collect(self.output, executable=str(self.exe), runner=self.runner)
        self.assertEqual(result['status'], 'snapshot_collected_not_diagnosed')
        self.assertFalse(result['usable_trace_confirmed'])

    def test_unsupported_is_explicit(self):
        result = logcat.collect(self.output, executable=str(self.root / 'absent'))
        self.assertFalse(result['attempted'])

    def test_permission_failure_no_broader_retry(self):
        calls = []
        def fail(command, **kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=1)
        result = logcat.collect(self.output, executable=str(self.exe), runner=fail)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['status'], 'permission_or_command_unavailable')
        self.assertFalse((self.output / 'same-uid-crash-logcat.txt').exists())

    def test_timeout_is_recorded(self):
        def fail(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 5)
        result = logcat.collect(self.output, executable=str(self.exe), runner=fail)
        self.assertEqual(result['status'], 'timed_out')

    def test_export_size_is_bounded(self):
        def fill(command, **kwargs):
            kwargs['stdout'].write(b'x' * (logcat.MAX_LOGCAT_BYTES + 10))
            return SimpleNamespace(returncode=0)
        result = logcat.collect(self.output, executable=str(self.exe), runner=fill)
        self.assertTrue(result['truncated'])
        self.assertEqual((self.output / 'same-uid-crash-logcat.txt').stat().st_size, logcat.MAX_LOGCAT_BYTES)

    def test_logcat_is_not_exported_without_consent(self):
        import zipfile
        skin = self.root / 'skin'
        skin.mkdir()
        (skin / 'addon.xml').write_text('<addon/>')
        logcat.collect(self.output, executable=str(self.exe), runner=self.runner)
        for consent in (False, True):
            dest = self.root / (str(consent) + '.zip')
            support.make_report(dest, skin, 'skin.fixture', include_native_traces=consent, logcat_root=self.output)
            with zipfile.ZipFile(dest) as archive:
                self.assertEqual('native/same-uid-crash-logcat.txt' in archive.namelist(), consent)


if __name__ == '__main__':
    unittest.main()
