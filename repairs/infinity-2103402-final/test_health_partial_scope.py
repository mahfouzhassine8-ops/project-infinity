"""Execute the exact signed Python exporter, with controlled failed collectors."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import health_partial_scope as scope


def baseline():
    with ZipFile(os.environ['INFINITY_BASELINE_APK']) as archive:
        return archive.read('assets/addons/' + scope.PATH)


def module(source):
    obj = types.ModuleType('health_partial_test')
    exec(compile(source, scope.PATH, 'exec'), obj.__dict__)
    return obj


def failure(*args, **kwargs):
    raise PermissionError('private-token=SHOULD_NOT_ESCAPE')


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = baseline()
        cls.after = scope.transform(cls.original)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / 'kodi.log'
        self.log.write_text('useful existing diagnostic line\npassword=must_be_redacted\n')
        self.log_hash = hashlib.sha256(self.log.read_bytes()).hexdigest()
        self.env = {'captured_utc': '2026-10-24T19:22:30Z'}
        self.identity = types.SimpleNamespace(collect=lambda: {'runtime_resolved': True})
        self.causal = types.SimpleNamespace(collect=lambda *a: {'read_only': True})
        self.native = types.SimpleNamespace(correlate=lambda *a: {
            'temporal_scope': 'unverified', 'attributable_to_selected_session': False,
            'session_exit': {'status': 'UNVERIFIED', 'summary': 'Unverified session exit'}})
        self.patcher = patch.dict(sys.modules, {'infinity_runtime_identity': self.identity,
            'khc_causal': self.causal, 'khc_native': self.native})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def run_export(self, source=None, **kwargs):
        obj = module(self.after if source is None else source)
        target = self.root / ('export-' + str(len(list(self.root.glob('*.zip')))) + '.zip')
        receipt = obj.build_report(target, None, self.env, self.log,
                                   self.root / 'missing-old.log', **kwargs)
        with ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            contents = {name: archive.read(name) for name in archive.namelist()}
        self.assertFalse(target.with_suffix('.zip.partial').exists())
        self.assertEqual(self.log_hash, hashlib.sha256(self.log.read_bytes()).hexdigest())
        self.assertNotIn(b'must_be_redacted', b''.join(contents.values()))
        self.assertNotIn(b'SHOULD_NOT_ESCAPE', b''.join(contents.values()))
        self.assertFalse(receipt['crash_cause_confirmed'])
        return receipt, contents

    def test_original_loses_report_candidate_keeps_partial_evidence(self):
        for collector, member in [(self.identity, 'runtime-component-identity.json'),
                                  (self.causal, 'causal-tree.json')]:
            with self.subTest(member=member):
                saved = collector.collect
                collector.collect = failure
                with self.assertRaises(PermissionError):
                    self.run_export(self.original)
                self.assertFalse(list(self.root.glob('*.partial')))
                receipt, data = self.run_export()
                status = json.loads(data[member])
                self.assertEqual(status['status'], 'unavailable')
                self.assertFalse(status['available'])
                self.assertIn('export-time/kodi.current.tail.log', data)
                self.assertEqual(json.loads(data['incident.json'])['status'], 'manual_snapshot')
                collector.collect = saved

    def test_failed_correlation_does_not_claim_clean_or_crashed(self):
        self.native.correlate = failure
        with self.assertRaises(PermissionError):
            self.run_export(self.original)
        _, data = self.run_export()
        self.assertEqual(json.loads(data['SESSION-EXIT-STATUS.json'])['status'], 'UNVERIFIED')
        result = json.loads(data['native-incident-correlation.json'])
        self.assertFalse(result['available'])
        self.assertFalse(result['attributable_to_selected_session'])
        self.assertIn(b'no crash or clean-exit conclusion', data['SESSION-EXIT-STATUS.txt'])

    def test_empty_missing_and_denied_native_records_are_explicit(self):
        native = self.root / 'native'; native.mkdir()
        empty = native / 'native-crash-last.txt'; empty.touch()
        receipt, data = self.run_export(native_dirs=[('engine', native)])
        self.assertNotIn('android-optional/engine/native-crash-last.txt', data)
        self.assertIn({'file': 'android-optional/engine/native-crash-last.txt',
                       'reason': 'empty_source', 'available': False}, receipt['omitted'])
        original_iterdir = Path.iterdir
        def denied(path):
            if path == native: raise PermissionError('private path')
            return original_iterdir(path)
        with patch.object(Path, 'iterdir', denied):
            receipt, data = self.run_export(native_dirs=[('engine', native)])
        self.assertTrue(any(r['reason'] == 'directory_unavailable' for r in receipt['omitted']))
        self.assertIn('export-time/kodi.current.tail.log', data)
        self.assertEqual(empty.stat().st_size, 0)

    def test_archive_failure_is_not_swallowed(self):
        original_write = ZipFile.writestr
        def broken(archive, name, *args, **kwargs):
            if name == 'runtime-component-identity.json':
                raise OSError('destination is full')
            return original_write(archive, name, *args, **kwargs)
        with patch.object(ZipFile, 'writestr', broken), self.assertRaises(OSError):
            self.run_export()
        self.assertFalse(list(self.root.glob('*.zip')))
        self.assertFalse(list(self.root.glob('*.partial')))
        self.assertEqual(self.log_hash, hashlib.sha256(self.log.read_bytes()).hexdigest())

    def test_scope_and_success_path_preserve_original_behaviour(self):
        restored = self.after
        for before, after in reversed(scope.CHANGES):
            restored = restored.replace(after.encode(), before.encode(), 1)
        self.assertEqual(restored, self.original)
        with self.assertRaises(ValueError): scope.transform(self.original + b'\n')
        original_receipt, original_data = self.run_export(self.original)
        receipt, data = self.run_export()
        self.assertEqual(set(data), set(original_data))
        for name in data.keys() - {'manifest.json'}:
            self.assertEqual(data[name], original_data[name], name)
        for field in ('files', 'omitted', 'limits', 'metadata'):
            self.assertEqual(receipt[field], original_receipt[field], field)


if __name__ == '__main__':
    unittest.main(verbosity=2)
