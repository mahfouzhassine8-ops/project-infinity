"""Host-only controls for the non-invasive Fold crash watch."""
import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import fold_passive_crash_watch as watch


class WatchSafetyTests(unittest.TestCase):
    def test_only_approved_read_commands(self):
        allowed = watch.ALLOWED_READS
        self.assertEqual(len(set(allowed)), len(allowed))
        for command in allowed:
            self.assertNotIn('force-stop', command)
            self.assertNotIn('install', command)
            self.assertNotIn('clear', command)
            self.assertNotIn('rm', command)
            self.assertNotIn('input', command)
            self.assertNotIn('-c', command)
        with self.assertRaises(ValueError):
            watch.command('/adb', 'phone', ('shell','am','force-stop',watch.PACKAGE))

    def test_pid_disappearance_is_not_called_crash_and_disconnect_is_not_exit(self):
        def run(args, **kwargs):
            if 'get-state' in args:
                return subprocess.CompletedProcess(args, 0, b'device\n', b'')
            return subprocess.CompletedProcess(args, 1, b'', b'')
        with patch.object(watch.subprocess, 'run', side_effect=run):
            self.assertEqual(watch.current_pid('adb','phone'), (None,'not_running'))
        def disconnected(args, **kwargs):
            return subprocess.CompletedProcess(args, 1, b'', b'device offline')
        with patch.object(watch.subprocess, 'run', side_effect=disconnected):
            self.assertEqual(watch.current_pid('adb','phone'), (None,'adb_unavailable'))

    def test_fast_pid_replacement_preserves_old_process_for_exit_evidence(self):
        self.assertEqual(watch.observe_transition(123, 0, 456, 'observed'),
                         (456, 0, 'engine_pid_replaced', 123))
        self.assertEqual(watch.observe_transition(123, 0, None, 'not_running'),
                         (123, 1, None, None))
        self.assertEqual(watch.observe_transition(123, 1, None, 'not_running'),
                         (None, 0, 'engine_no_longer_observed', 123))
        self.assertEqual(watch.observe_transition(123, 1, None, 'adb_unavailable'),
                         (123, 0, None, None))

    def test_snapshot_is_nonauthoritative_and_preserves_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(watch, 'command', return_value={'returncode':1,'stdout':'','stderr':'denied'}):
                path=watch.capture_exit('adb','phone',Path(tmp),123,1)
            import json
            result=json.loads((path/'SUMMARY.json').read_text())
            self.assertFalse(result['crash_proven'])
            self.assertEqual('unknown_until_exit_metadata_is_examined',result['classification'])
            self.assertFalse(result['native-dropbox_retrieved'])
            self.assertTrue((path/'logcat-crash.json').exists())

    def test_ring_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            ring=watch.RingLog(tmp,segment_bytes=4,max_files=2)
            ring.write(b'abcdefghiJKLmN')
            ring.close()
            files=sorted(Path(tmp).glob('logcat-*.txt'))
            self.assertEqual(2,len(files))
            self.assertLessEqual(sum(x.stat().st_size for x in files),8)

    def test_logcat_stream_never_clears_logs_or_mutates_app(self):
        tree=ast.parse(Path(watch.__file__).read_text())
        literals=[x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
        self.assertNotIn('logcat -c',literals)
        self.assertNotIn('ClearApplicationUserData',literals)


if __name__=='__main__': unittest.main()
