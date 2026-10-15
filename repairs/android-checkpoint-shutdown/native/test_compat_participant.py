#!/usr/bin/env python3
"""Exercise the actual embedded compat participant and legacy start policy."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument('--source-root', type=Path, required=True,
                    help='runtime-embedded-addons directory')
args, remaining = parser.parse_known_args()
sys.dont_write_bytecode = True
sys.path.insert(0, str(args.source_root / 'service.infinity.compat'))
import checkpoint_runtime as runtime

xbmc = types.ModuleType('xbmc')
xbmc.LOGINFO, xbmc.LOGWARNING, xbmc.LOGERROR = 1, 2, 3
xbmc.log = lambda *args: None
sys.modules['xbmc'] = xbmc
for name in ('xbmcaddon', 'xbmcgui', 'xbmcvfs'):
    sys.modules[name] = types.ModuleType(name)
spec = importlib.util.spec_from_file_location('compat_service_under_test',
    args.source_root / 'service.infinity.compat' / 'service.py')
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class Addon:
    def __init__(self):
        self.settings = {}
    def getSetting(self, key):
        return self.settings.get(key, '')
    def setSetting(self, key, value):
        self.settings[key] = value


class CompatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.profile, self.control = self.root / 'profile', self.root / 'control'
        self.profile.mkdir()
        self.control.mkdir()
        runtime._dirty_files.clear()
        runtime._dirty_directories.clear()
        runtime._write_failures.clear()
        self.identity = dict(schema=1, pid=os.getpid(), owner='engine_owner_123456')
        self.request = dict(self.identity, session='session_1234567890', phase='PREPARE')
        self.write('engine.json', dict(self.identity, native_api=1))
        self.write('request.json', self.request)
        self.addon = Addon()
        service.register_start(self.profile, self.addon)
        self.subject = runtime.CompatCheckpoint(self.profile, self.control)

    def write(self, name, value):
        (self.control / name).write_text(json.dumps(value))

    def response(self):
        return json.loads((self.control / 'compat-response.json').read_text())

    def test_checked_success_is_one_way(self):
        self.assertTrue(self.subject.poll())
        result = self.response()
        self.assertEqual('PARTICIPANT_COMPLETE', result['status'])
        self.assertEqual(self.request['session'], result['session'])
        self.assertFalse(result['global_safe_to_terminate'])
        self.assertTrue(result['guard_frozen'])
        self.assertEqual([{'name': 'critical_files', 'ok': True},
                          {'name': 'clean_marker', 'ok': True}], result['operations'])
        self.assertFalse((self.profile / 'startup-marker.json').exists())
        self.write('request.json', dict(self.request, session='different_session_123'))
        with mock.patch.object(runtime, '_sync', side_effect=AssertionError('replayed')):
            self.assertTrue(self.subject.poll())
        self.assertEqual(result, self.response())

    def test_normal_closes_do_not_trigger_false_safe_mode(self):
        for _ in range(6):
            self.assertTrue(self.subject.poll())
            self.assertEqual('PARTICIPANT_COMPLETE', self.response()['status'])
            auto_safe, count, _ = service.register_start(self.profile, self.addon)
            self.assertFalse(auto_safe)
            self.assertEqual(0, count)
            self.subject = runtime.CompatCheckpoint(self.profile, self.control)
        self.assertNotEqual('safe', self.addon.getSetting('compat_mode'))

    def test_pending_dirty_file_failure_blocks_complete(self):
        missing = self.profile / 'required-backup.xml'
        runtime._dirty_files.add(missing)
        self.assertTrue(self.subject.poll())
        self.assertEqual('CHECKPOINT_FAILED', self.response()['status'])
        self.assertTrue((self.profile / 'startup-marker.json').exists())

    def test_critical_write_failure_is_sticky(self):
        with self.assertRaises(OSError):
            with runtime.critical_write(self.profile / 'required.xml'):
                raise OSError('disk full')
        self.assertTrue(self.subject.poll())
        self.assertEqual('CHECKPOINT_FAILED', self.response()['status'])

    def test_namespace_failure_blocks_complete(self):
        actual = runtime._sync
        calls = []
        def fail_after_unlink(path, directory=False):
            calls.append(str(path))
            if directory and not (self.profile / 'startup-marker.json').exists():
                raise OSError('directory fsync failed')
            return actual(path, directory)
        with mock.patch.object(runtime, '_sync', side_effect=fail_after_unlink):
            self.assertTrue(self.subject.poll())
        self.assertEqual('CHECKPOINT_FAILED', self.response()['status'])
        self.assertTrue(self.subject.parked)

    def test_wrong_identity_never_acknowledged(self):
        self.write('request.json', dict(self.request, owner='wrong_owner_123456'))
        self.assertFalse(self.subject.poll())
        self.assertFalse((self.control / 'compat-response.json').exists())
        self.write('request.json', dict(self.request, schema=True))
        self.assertFalse(self.subject.poll())

    def test_missing_history_fails(self):
        (self.profile / 'startup-history.json').unlink()
        self.assertTrue(self.subject.poll())
        self.assertEqual('CHECKPOINT_FAILED', self.response()['status'])

    def test_critical_write_records_new_parent_namespaces(self):
        path = self.profile / 'new' / 'nested' / 'backup.xml'
        with runtime.critical_write(path):
            path.parent.mkdir(parents=True)
            path.write_bytes(b'<xml/>')
        self.assertIn(path, runtime._dirty_files)
        self.assertTrue({path.parent, path.parent.parent, self.profile}.issubset(
            runtime._dirty_directories))
        self.assertTrue(self.subject.poll())
        self.assertEqual('PARTICIPANT_COMPLETE', self.response()['status'])


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]] + remaining)
