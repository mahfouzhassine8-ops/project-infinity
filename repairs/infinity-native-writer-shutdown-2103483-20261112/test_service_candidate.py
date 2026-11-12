"""Selected source-bound host cases; no actual native image or Kodi execution."""
import ast
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import prepare_service_candidate as patcher

RAW = Path(os.environ['CORE_SOURCE']).read_bytes()
assert hashlib.sha256(RAW).hexdigest() == patcher.SOURCE_SHA


def module(raw):
    # Target code imports stdlib only here, and its __main__ service is not run.
    obj = types.ModuleType('isolated_core_source_fixture')
    exec(compile(raw, 'verified-service.py', 'exec'), obj.__dict__)
    return obj


class Call:
    def __init__(self, value=1, error=None):
        self.value = value
        self.error = error
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.value


class ServiceCases(unittest.TestCase):
    def setUp(self):
        self.core = module(patcher.candidate(RAW))
        self.logs = []
        self.core._log = lambda message, level=None: self.logs.append(message)
        self.native = types.SimpleNamespace(start_core_service=Call(), stop_core_service=Call())

    def loader(self, core, process, fail=False):
        target = '/data/user/0/com.projectinfinity.kodi/code_cache'
        fallback = '/storage/emulated/0/Android/data/com.projectinfinity.kodi/files/.kodi/temp'
        copies = []
        with mock.patch.object(core, 'resolve_paths', return_value=('/fixture/source.so', None)), \
             mock.patch.object(core.platform, 'system', return_value='Android'), \
             mock.patch.object(core.os.path, 'exists', return_value=True), \
             mock.patch.object(core.os.path, 'isdir', side_effect=lambda p: p in (target, fallback)), \
             mock.patch.object(core, 'xbmcvfs', types.SimpleNamespace(translatePath=lambda _: fallback)), \
             mock.patch('builtins.open', return_value=io.BytesIO(process.encode()+b'\0')), \
             mock.patch.object(core.shutil, 'copy2', side_effect=lambda a, b: copies.append(b)), \
             mock.patch.object(core.os, 'chmod'), \
             mock.patch.object(core.ctypes, 'CDLL', side_effect=OSError('fixture load denial') if fail else None,
                               return_value=self.native) as load, \
             mock.patch.object(core, 'is_healthy', return_value=True):
            result = core.start_engine('/fixture/core')
        return copies, load.call_args.args[0], result

    def shutdown(self, handle):
        self.core.xbmc = types.SimpleNamespace(LOGWARNING=2, LOGINFO=1,
            Monitor=lambda: types.SimpleNamespace(abortRequested=lambda: True))
        self.core.xbmcaddon = types.SimpleNamespace(Addon=lambda: types.SimpleNamespace(getAddonInfo=lambda _: '/fixture/core'))
        self.core.xbmcvfs = types.SimpleNamespace(translatePath=lambda x: x)
        with mock.patch.object(self.core, 'is_healthy', return_value=False), \
             mock.patch.object(self.core, 'is_binary_installed', return_value=True), \
             mock.patch.object(self.core, 'update_outdated_binaries'), \
             mock.patch.object(self.core, 'start_engine', return_value=(handle, None)):
            self.core.run_kodi_service()
        self.assertFalse(any('stopped cleanly' in value.lower() for value in self.logs))
        self.assertTrue(any('completion remains unverified' in value for value in self.logs))

    def test_original_exact_process_reaches_external_fallback(self):
        copies, load, _ = self.loader(module(RAW), 'com.projectinfinity.kodi:kodi')
        self.assertEqual(copies, [load])
        self.assertTrue(load.startswith('/storage/'))

    def test_infinity_suffix_uses_package_private_directory(self):
        copies, load, result = self.loader(self.core, 'com.projectinfinity.kodi:kodi')
        self.assertEqual(copies, [load])
        self.assertEqual(load, '/data/user/0/com.projectinfinity.kodi/code_cache/libadulthideout_core.so')
        self.assertIs(result[0], self.native)
        self.assertEqual(self.native.start_core_service.calls, [(8191,)])

    def test_other_process_identity_is_not_rewritten(self):
        _, load, _ = self.loader(self.core, 'different.package:kodi')
        self.assertTrue(load.startswith('/storage/'))

    def test_load_failure_never_calls_native_start(self):
        _, _, result = self.loader(self.core, 'com.projectinfinity.kodi:kodi', fail=True)
        self.assertEqual(result, (None, None))
        self.assertEqual(self.native.start_core_service.calls, [])

    def test_stop_return_one_is_not_completion(self):
        self.shutdown(self.native)
        self.assertEqual(self.native.stop_core_service.calls, [()])
        self.assertTrue(any('result=1' in value and 'unverified' in value for value in self.logs))

    def test_stop_error_is_reported_without_false_success(self):
        self.native.stop_core_service.error = OSError('private fixture text')
        self.shutdown(self.native)
        self.assertTrue(any('Native stop failed (OSError)' in value for value in self.logs))
        self.assertFalse(any('private fixture text' in value for value in self.logs))

    def test_no_native_handle_does_not_invoke_stop(self):
        self.shutdown(None)
        self.assertEqual(self.native.stop_core_service.calls, [])

    def test_unrelated_service_function_ASTs_unchanged(self):
        before, after = ast.parse(RAW), ast.parse(patcher.candidate(RAW))
        functions = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
        a, b = functions(before), functions(after)
        self.assertEqual(a.keys(), b.keys())
        self.assertEqual({n for n in a if a[n] != b[n]}, {'start_engine', 'run_kodi_service'})

    def test_unrecognized_source_generation_is_refused(self):
        with self.assertRaises(AssertionError):
            patcher.candidate(RAW+b'\n')

    def test_preparation_is_unshipped_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);source = root/'original.py';source.write_bytes(RAW)
            out = root/'candidate-UNSHIPPED';result = patcher.prepare(source, out)
            self.assertFalse(result['activation_allowed'])
            self.assertFalse(result['native_completion_proven'])
            self.assertEqual(source.read_bytes(), RAW)
            with self.assertRaises(FileExistsError):
                patcher.prepare(source, out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
