"""Narrow, host-only compatibility tests. No Kodi, device, or native Core execution."""
import ast
import builtins
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

SOURCE = Path(__file__).parent / "service.adulthideout.core" / "service.py"
spec = importlib.util.spec_from_file_location("isolated_adulthideout_core_candidate", SOURCE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class AndroidCoreLoaderGuardTests(unittest.TestCase):
    def setUp(self):
        core._FAILED_NATIVE_LOADS.clear()

    def test_compiles_and_preserves_core_interfaces(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({"start_engine", "run_kodi_service",
                         "download_platform_binaries", "prompt_and_install_core"} <= functions)

    def test_only_private_internal_package_paths_accepted(self):
        pkg = "com.projectinfinity.kodi"
        self.assertTrue(core._private_android_load_dir(
            "/data/user/0/" + pkg + "/code_cache", pkg))
        self.assertFalse(core._private_android_load_dir(
            "/storage/emulated/0/Android/data/" + pkg + "/files/.kodi/temp", pkg))
        self.assertFalse(core._private_android_load_dir("/sdcard/Kodi", pkg))
        self.assertFalse(core._private_android_load_dir(
            "/data/user/0/different.package/code_cache", pkg))
        self.assertFalse(core._private_android_load_dir("/data/user/0/" + pkg, ""))

    def test_external_storage_falls_back_without_copy_or_dlopen_and_caches_failure(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Path(td) / "libadulthideout_core.so"
            lib.write_bytes(b"not-an-executable-for-this-host")
            original_open = builtins.open

            def fake_open(path, *args, **kwargs):
                if os.fspath(path) == "/proc/self/cmdline":
                    return io.BytesIO(b"com.projectinfinity.kodi\x00")
                return original_open(path, *args, **kwargs)

            # On the host, special://temp resolves to a real writable directory,
            # but it is outside Android's *internal* private app directory.
            vfs = types.SimpleNamespace(translatePath=lambda value: td)
            with mock.patch.object(core.platform, "system", return_value="Android"), \
                 mock.patch.object(core, "resolve_paths", return_value=(str(lib), None)), \
                 mock.patch.object(core, "xbmcvfs", vfs), \
                 mock.patch("builtins.open", side_effect=fake_open), \
                 mock.patch.object(core.ctypes, "CDLL", side_effect=AssertionError("unsafe dlopen")), \
                 mock.patch.object(core.shutil, "copy2", side_effect=AssertionError("metadata copied")), \
                 mock.patch.object(core.os, "chmod", side_effect=AssertionError("chmod")):
                self.assertEqual(core.start_engine(td), (None, None))
                self.assertEqual(core.start_engine(td), (None, None))
                self.assertIn(core._native_fingerprint(str(lib)), core._FAILED_NATIVE_LOADS)

    def test_new_binary_identity_is_not_permanently_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Path(td) / "libadulthideout_core.so"
            lib.write_bytes(b"first")
            first = core._native_fingerprint(str(lib))
            core._FAILED_NATIVE_LOADS.add(first)
            lib.write_bytes(b"a new library image")
            self.assertNotEqual(core._native_fingerprint(str(lib)), first)

    def test_no_blanket_python_audit_or_essential_shutdown_exemption(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("sys.addaudithook", source)
        self.assertNotIn("InfinityScriptPersistence", source)
        self.assertIn("if not staged_internal:", source)
        self.assertIn("return None, None", source)
        self.assertIn("os.replace(temp, candidate)", source)
        self.assertNotIn("shutil.copy2(lib_path, candidate)", source)


if __name__ == "__main__":
    unittest.main()
