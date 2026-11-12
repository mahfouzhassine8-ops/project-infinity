"""Selected host-only observation checks; no real Core image or service runs.

Run with unittest in this directory. Exact Python3.11.7 proof belongs to CI;
other interpreter runs are development results only. Fake pinned trace sources
are explicitly qa_fixture actors and cannot establish Core completion.
"""
import _ctypes
import ctypes
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('coreqa_test_observer', HERE / 'observer.py')
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)

FIXTURE = '''def start_engine(lib):
    res = lib.start_core_service(8191)
    after_start = True
    return res

def assigned_other(lib):
    answer = lib.start_core_service(8191)
    return answer

def unassigned(lib):
    res = 987654
    lib.start_core_service(8191)
    return res

def stop_engine(lib):
    lib.stop_core_service()
    after_stop = True
    return after_stop

def health(lib):
    result = lib.is_core_service_running()
    return result
'''


class ObserverContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'pinned-qa-fixture.py'
        self.source.write_text(FIXTURE)
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.rows = []
        self.states = []
        self.previous_trace = sys.gettrace()
        self.original = {(module, name): getattr(module, name) for module, name in
                         [(os, 'chmod'), (os, 'utime'), (shutil, 'copy2'),
                          (_ctypes, 'dlopen'), (ctypes, '_dlopen')] +
                         ([(os, 'setxattr')] if hasattr(os, 'setxattr') else [])}

    def tearDown(self):
        for state in reversed(self.states):
            state.uninstall()
        sys.settrace(self.previous_trace)
        for (module, name), original in self.original.items():
            setattr(module, name, original)
        self.temp.cleanup()

    def install(self, emit=None, source=None, digest=None, actor='qa_fixture'):
        state = observer.install(self.rows.append if emit is None else emit,
                                 str(source or self.source), digest or self.digest, actor=actor)
        self.states.append(state)
        return state

    @contextmanager
    def observing(self, **kwargs):
        state = self.install(**kwargs)
        try:
            yield state
        finally:
            state.uninstall()

    def fixture_functions(self, raw=FIXTURE):
        namespace = {}
        exec(compile(raw, str(self.source), 'exec', dont_inherit=True), namespace)
        return namespace

    def events(self, event, operation=None):
        return [r for r in self.rows if r['event'] == event and
                (operation is None or r.get('operation') == operation)]

    def assert_diagnostic_only(self):
        self.assertTrue(self.rows)
        for row in self.rows:
            self.assertIs(row['completion_proof'], False)
            self.assertLessEqual(len(row['line']), 3000)
            self.assertNotIn('\n', row['line'])
            self.assertEqual(json.loads(row['line'])['actor'], row['actor'])

    def test_actual_chmod_utime_success_preserve_arguments_and_return(self):
        path = self.root / 'metadata-file'
        path.write_bytes(b'metadata')
        original = os.chmod
        seen = []
        def delegated(*args, **kwargs):
            value = original(*args, **kwargs)
            seen.append((args, kwargs, value))
            return value
        with mock.patch.object(os, 'chmod', delegated):
            with self.observing():
                value = os.chmod(path, 0o640, follow_symlinks=True)
                self.assertIs(value, seen[-1][2])
                self.assertIs(seen[-1][0][0], path)
                self.assertEqual(seen[-1][0][1], 0o640)
                self.assertEqual(seen[-1][1], {'follow_symlinks': True})
                ticks = (1600000000000000000, 1600000000123456789)
                self.assertIsNone(os.utime(os.fspath(path), ns=ticks, follow_symlinks=False))
        self.assertEqual(path.stat().st_mode & 0o777, 0o640)
        self.assertEqual(path.stat().st_mtime_ns, ticks[1])
        self.assertTrue(self.events('operation.return', 'chmod'))
        self.assertTrue(self.events('operation.return', 'utime'))
        self.assert_diagnostic_only()

    def test_actual_metadata_failure_reraises_original_exception_object(self):
        original = os.utime
        seen = []
        def delegated(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except OSError as error:
                seen.append((args, kwargs, error))
                raise
        missing = str(self.root / 'missing-file')
        ticks = (1000000000, 2000000000)
        with mock.patch.object(os, 'utime', delegated):
            with self.observing():
                with self.assertRaises(FileNotFoundError) as caught:
                    os.utime(missing, ns=ticks, follow_symlinks=False)
                self.assertIs(caught.exception, seen[-1][2])
                self.assertEqual(seen[-1][:2], ((missing,), {'ns': ticks, 'follow_symlinks': False}))
        error = self.events('operation.error', 'utime')[-1]
        self.assertEqual(error['errno'], caught.exception.errno)
        self.assertEqual(error['exception'], 'FileNotFoundError')

    def test_actual_copy2_xattr_and_nested_metadata_keep_result_identity(self):
        self.assertTrue(hasattr(os, 'setxattr'), 'Selected Linux host requires real xattr support')
        source, destination = self.root / 'source', self.root / 'destination'
        source.write_bytes(b'actual copy2 payload')
        os.setxattr(source, b'user.coreqa', b'private-xattr-value')
        os.chmod(source, 0o640)
        original = shutil.copy2
        seen = []
        def delegated(*args, **kwargs):
            result = original(*args, **kwargs)
            seen.append((args, kwargs, result))
            return result
        with mock.patch.object(shutil, 'copy2', delegated):
            with self.observing():
                result = shutil.copy2(src=source, dst=destination, follow_symlinks=False)
                self.assertIs(result, destination)
                self.assertIs(result, seen[-1][2])
                self.assertEqual(seen[-1][:2], ((), {'src': source, 'dst': destination, 'follow_symlinks': False}))
        self.assertEqual(destination.read_bytes(), source.read_bytes())
        self.assertEqual(os.getxattr(destination, b'user.coreqa'), b'private-xattr-value')
        self.assertEqual(destination.stat().st_mode & 0o777, 0o640)
        parent = self.events('operation.begin', 'copy2')[0]['ticket']
        children = [r for r in self.events('operation.begin') if r.get('parent') == parent]
        self.assertTrue({'chmod', 'utime', 'setxattr'} <= {r['operation'] for r in children})
        self.assertNotIn('private-xattr-value', json.dumps(self.rows))
        self.assert_diagnostic_only()

    def test_actual_copy2_and_xattr_failures_preserve_errors(self):
        with self.observing():
            with self.assertRaises(FileNotFoundError):
                shutil.copy2(self.root / 'missing', self.root / 'destination')
            with self.assertRaises(FileNotFoundError):
                os.setxattr(str(self.root / 'missing'), b'user.coreqa', b'not-logged')
        self.assertTrue(self.events('operation.error', 'copy2'))
        self.assertTrue(self.events('operation.error', 'setxattr'))
        self.assertNotIn('not-logged', json.dumps(self.rows))

    def test_actual_dlopen_none_and_failure_preserve_delegate_objects_and_args(self):
        original = _ctypes.dlopen
        seen = []
        def delegated(*args, **kwargs):
            try:
                result = original(*args, **kwargs)
            except OSError as error:
                seen.append((args, kwargs, error))
                raise
            seen.append((args, kwargs, result))
            return result
        with mock.patch.object(_ctypes, 'dlopen', delegated), mock.patch.object(ctypes, '_dlopen', delegated):
            with self.observing():
                handle = ctypes._dlopen(None, os.RTLD_NOW)
                try:
                    self.assertIs(handle, seen[-1][2])
                    self.assertEqual(seen[-1][:2], ((None, os.RTLD_NOW), {}))
                    missing = str(self.root / 'does-not-exist.so')
                    with self.assertRaises(OSError) as caught:
                        _ctypes.dlopen(missing, os.RTLD_NOW)
                    self.assertIs(caught.exception, seen[-1][2])
                    self.assertEqual(seen[-1][:2], ((missing, os.RTLD_NOW), {}))
                finally:
                    _ctypes.dlclose(handle)
        self.assertEqual(len(self.events('operation.return', 'dlopen')), 1)
        self.assertEqual(len(self.events('operation.error', 'dlopen')), 1)
        self.assertIsNone(self.events('operation.return', 'dlopen')[0]['result'])

    def test_ctypes_function_pointer_is_unproxied_and_real_getpid_runs(self):
        with self.observing():
            library = ctypes.CDLL(None)
            function = library.getpid
            function.argtypes, function.restype = [], ctypes.c_int
            self.assertIsInstance(function, ctypes._CFuncPtr)
            self.assertIs(library.getpid, function)
            self.assertEqual(function(), os.getpid())
        self.assertTrue(self.events('operation.return', 'dlopen'))

    def test_trace_observes_assigned_start_and_only_stop_progress(self):
        functions = self.fixture_functions()
        native = types.SimpleNamespace(start_core_service=lambda port: -23,
                                       stop_core_service=lambda: 77,
                                       is_core_service_running=lambda: 1)
        with self.observing():
            self.assertEqual(functions['start_engine'](native), -23)
            self.assertEqual(functions['assigned_other'](native), -23)
            self.assertTrue(functions['stop_engine'](native))
            self.assertEqual(functions['health'](native), 1)
        rows = self.events('native_call.progressed')
        starts = [r for r in rows if r['symbol'] == 'start_core_service']
        self.assertEqual([r['result'] for r in starts], [-23, -23])
        self.assertTrue(all(r['numeric_return_observed'] for r in starts))
        for row in rows:
            if row['symbol'] != 'start_core_service':
                self.assertFalse(row['numeric_return_observed'])
                self.assertIsNone(row['result'])
        self.assert_diagnostic_only()

    def test_trace_never_uses_stale_res_or_guesses_after_exception(self):
        functions = self.fixture_functions()
        failure = RuntimeError('selected fixture exception')
        def fail(port): raise failure
        with self.observing():
            self.assertEqual(functions['unassigned'](types.SimpleNamespace(start_core_service=lambda port: 42)), 987654)
            with self.assertRaises(RuntimeError) as caught:
                functions['start_engine'](types.SimpleNamespace(start_core_service=fail))
            self.assertIs(caught.exception, failure)
        progressed = self.events('native_call.progressed')
        self.assertEqual(len(progressed), 1)
        self.assertFalse(progressed[0]['numeric_return_observed'])
        self.assertIsNone(progressed[0]['result'])
        self.assertEqual(self.events('native_call.exception')[0]['exception'], 'RuntimeError')

    def test_unknown_source_or_wrong_hash_declines_all_bindings(self):
        for actor, digest, reason in [('core_service', self.digest, 'unrecognized_source'),
                                      ('qa_fixture', '0' * 64, 'source_hash_mismatch')]:
            with self.subTest(actor=actor):
                before = {(m, n): getattr(m, n) for m, n in self.original}
                with self.observing(actor=actor, digest=digest) as state:
                    self.assertEqual(state.bindings, [])
                    self.assertTrue(any(r.get('reason') == reason for r in self.events('coverage.disabled')))
                    for key, original in before.items(): self.assertIs(getattr(*key), original)

    def test_changed_code_with_pinned_filename_is_not_observed_as_native(self):
        changed = self.fixture_functions(FIXTURE.replace('res = lib.start_core_service(8191)', 'res = lib.start_core_service(8192)'))
        with self.observing():
            self.assertEqual(changed['start_engine'](types.SimpleNamespace(start_core_service=lambda port: port)), 8192)
        self.assertTrue(self.events('coverage.code_mismatch'))
        self.assertEqual(self.events('native_call.progressed'), [])

    def test_existing_trace_is_preserved_and_declared_unavailable(self):
        def existing(frame, event, arg): return existing
        sys.settrace(existing)
        with self.observing() as state:
            self.assertIs(sys.gettrace(), existing)
            self.assertFalse(state.trace_owned)
        self.assertIs(sys.gettrace(), existing)
        self.assertTrue(self.events('coverage.trace_unavailable'))

    def test_bounds_emit_failures_and_owned_only_uninstall(self):
        state = self.install()
        state.record('too-large', payload='x' * 4000)
        self.assertTrue(self.events('coverage.record_too_large'))
        for _ in range(4100): state.record('bounded-fixture')
        count = len(self.rows)
        state.record('still-bounded')
        self.assertEqual(len(self.rows), count)
        self.assertEqual(len(self.events('coverage.limit')), 1)
        self.assertLessEqual(count, 4097)
        replacement = lambda *args, **kwargs: None
        os.utime = replacement
        external_trace = lambda frame, event, arg: None
        sys.settrace(external_trace)
        state.uninstall()
        self.assertIs(os.utime, replacement)
        self.assertIs(sys.gettrace(), external_trace)
        state.uninstall()
        for (module, name), original in self.original.items():
            if (module, name) != (os, 'utime'): self.assertIs(getattr(module, name), original)
        self.assert_diagnostic_only()
        sys.settrace(self.previous_trace)
        os.utime = self.original[(os, 'utime')]
        def broken_emit(row): raise RuntimeError('logging unavailable')
        with self.observing(emit=broken_emit):
            path = self.root / 'real-file'
            path.write_bytes(b'real')
            self.assertIsNone(os.chmod(path, 0o600))
            with self.assertRaises(FileNotFoundError): os.utime(str(self.root / 'missing'))

    def test_symlink_copystat_and_capability_sets_are_preserved(self):
        self.assertIn(os.utime, os.supports_follow_symlinks)
        capabilities = {name: set(getattr(os, name)) for name in
                        ('supports_fd', 'supports_dir_fd', 'supports_follow_symlinks')}
        source, target = self.root/'source', self.root/'target'
        source.write_bytes(b'source'); target.write_bytes(b'target')
        src, dst = self.root/'source-link', self.root/'target-link'
        src.symlink_to(source); dst.symlink_to(target)
        stamp = 1600000000123456789
        os.utime(src, ns=(stamp, stamp), follow_symlinks=False)
        shutil.copystat(src, dst, follow_symlinks=False)
        expected = os.lstat(dst).st_mtime_ns
        os.utime(dst, ns=(1700000000000000000, 1700000000000000000), follow_symlinks=False)
        with self.observing():
            self.assertIn(os.utime, os.supports_follow_symlinks)
            shutil.copystat(src, dst, follow_symlinks=False)
            self.assertEqual(os.lstat(dst).st_mtime_ns, expected)
            self.assertEqual(os.readlink(dst), str(target))
            self.assertEqual(target.read_bytes(), b'target')
        for name, original in capabilities.items():
            self.assertEqual(getattr(os, name), original)

    def test_actual_core_service_source_remains_byte_identical_without_execution(self):
        path = Path(os.environ.get('INFINITY_COREQA_SERVICE_SOURCE', '/tmp/infinity-core-service-reference.py'))
        self.assertTrue(path.is_file(), 'Provide the exact83 Core source via INFINITY_COREQA_SERVICE_SOURCE')
        original = path.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), observer.CORE_SOURCE)
        with self.observing(source=path, digest=observer.CORE_SOURCE, actor='core_service'):
            file = self.root / 'harmless-file'
            file.write_bytes(b'not Core execution')
            os.chmod(file, 0o600)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self.events('native_call.before'), [])
        self.assert_diagnostic_only()


if __name__ == '__main__':
    unittest.main(verbosity=2)
