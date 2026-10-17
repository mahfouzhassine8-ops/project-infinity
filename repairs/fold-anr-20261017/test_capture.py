#!/usr/bin/env python3
"""Host checks using the actual unchanged TEST4 C++ recorder implementation.

The host shared library is a test fixture, never a replacement Android library.
Its hash is accepted only through unittest patching, not a production bypass.
"""
from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("fold_capture_under_test", HERE / "helper/script.infinity.foldcapture/capture.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class NativeCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="infinity-real-probe-host-")
        cls.folder = Path(cls.temp.name)
        cls.library_path = cls.folder / "probe-host.so"
        source = cls.folder / "probe-host.cpp"
        source.write_text('''
#include "InfinityStabilityProbe.h"
extern "C" void test_configure(const char* path) { InfinityStabilityProbe::Configure(path); }
extern "C" void test_reset(unsigned budget, bool ready) {
  InfinityStabilityProbe::Arm(0);
  InfinityStabilityProbe::written.store(budget);
  InfinityStabilityProbe::configured.store(ready);
}
extern "C" void test_snapshot() { InfinityStabilityProbe::Snapshot("host_test"); }
extern "C" unsigned test_count() { return InfinityStabilityProbe::samples.load(); }
extern "C" long long test_until() { return InfinityStabilityProbe::until.load(); }
''')
        subprocess.run([shutil.which("g++") or "g++", "-std=c++17", "-O0", "-fPIC", "-shared", "-pthread",
                        "-I" + str(ROOT / "repairs/stability-probe-2103377"), str(source),
                        "-o", str(cls.library_path)], check=True)
        cls.library = ctypes.CDLL(str(cls.library_path))
        cls.library.test_configure.argtypes = [ctypes.c_char_p]
        cls.library.test_reset.argtypes = [ctypes.c_uint, ctypes.c_bool]
        cls.library.test_until.restype = ctypes.c_longlong
        cls.log = cls.folder / "native.jsonl"
        cls.library.test_configure(str(cls.log).encode())
        cls.host_hash = hashlib.sha256(cls.library_path.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.library.test_reset(0, True)
        self.log.unlink(missing_ok=True)

    def test_original_cpp_arm_and_deadline_acknowledgement(self):
        with patch.object(capture, "EXPECTED_NATIVE_SHA256", self.host_hash):
            receipt = capture.arm_exact_library(self.library_path)
        self.assertEqual(receipt["window_seconds"], 7200)
        self.assertEqual(receipt["armed_until_monotonic_ms"], self.library.test_until())
        self.assertEqual(self.library.test_count(), 0)

    def test_wrong_engine_rejected_before_any_native_load(self):
        with patch.object(capture.ctypes, "CDLL") as loader:
            with self.assertRaisesRegex(RuntimeError, "differs from TEST4"):
                capture.arm_exact_library(self.library_path)
            loader.assert_not_called()

    def test_existing_recorder_must_be_ready(self):
        self.library.test_reset(0, False)
        with patch.object(capture, "EXPECTED_NATIVE_SHA256", self.host_hash):
            with self.assertRaisesRegex(RuntimeError, "not ready"):
                capture.arm_exact_library(self.library_path)

    def test_low_existing_budget_is_refused(self):
        self.library.test_reset(400 * 1024, True)
        with patch.object(capture, "EXPECTED_NATIVE_SHA256", self.host_hash):
            with self.assertRaisesRegex(RuntimeError, "space is low"):
                capture.arm_exact_library(self.library_path)

    def test_original_native_eight_snapshot_cap_is_preserved(self):
        with patch.object(capture, "EXPECTED_NATIVE_SHA256", self.host_hash):
            capture.arm_exact_library(self.library_path)
        for _ in range(12):
            self.library.test_snapshot()
        records = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(records), 8)
        self.assertTrue(all(row["kind"] == "stability_probe" for row in records))


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="infinity-capture-export-")
        self.folder = Path(self.temp.name)
        self.output = self.folder / "export/capture.zip"

    def tearDown(self):
        self.temp.cleanup()

    def write_probe(self, name, pid):
        (self.folder / name).write_text(json.dumps({"schema": 1, "kind": "stability_probe", "pid": pid}) + "\n")

    def test_export_current_and_previous_only(self):
        for index, name in enumerate(capture.LOG_NAMES):
            self.write_probe(name, 9000 + index)
        (self.folder / "settings.xml").write_text("private-provider-settings-must-not-be-read")
        result = capture.collect(self.output, self.folder, {"skin.infinity.diggz": "1.0.5.223"})
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(set(archive.namelist()), {"manifest.json", *("native/" + name for name in capture.LOG_NAMES)})
            self.assertIsNone(archive.testzip())
            self.assertNotIn(b"private-provider-settings", b"".join(archive.read(name) for name in archive.namelist()))
        self.assertEqual(result["files"][capture.LOG_NAMES[0]]["producer_pids"], [9000])
        self.assertEqual(result["files"][capture.LOG_NAMES[1]]["producer_pids"], [9001])

    def test_missing_snapshots_are_not_success(self):
        with self.assertRaisesRegex(RuntimeError, "No lock snapshots"):
            capture.collect(self.output, self.folder)
        self.assertFalse(self.output.exists())

    def test_oversize_log_is_reported(self):
        self.write_probe(capture.LOG_NAMES[0], 5)
        (self.folder / capture.LOG_NAMES[1]).write_bytes(b"x" * (capture.MAX_LOG_BYTES + 1))
        result = capture.collect(self.output, self.folder)
        self.assertEqual(result["unavailable"], [{"name": capture.LOG_NAMES[1], "reason": "exceeds recorder cap"}])

    def test_malformed_rows_do_not_hide_valid_records(self):
        self.write_probe(capture.LOG_NAMES[0], 8)
        with (self.folder / capture.LOG_NAMES[0]).open("a") as stream:
            stream.write("{incomplete\n[]\n")
        result = capture.collect(self.output, self.folder)
        self.assertEqual(result["files"][capture.LOG_NAMES[0]]["malformed_rows"], 2)

    def test_map_discovery_is_scoped_and_deduplicated(self):
        name = "/data/app/example/com.projectinfinity.kodi/lib/arm64/libkodi.so"
        maps = "1000-2000 r-xp 0 1:2 7 " + name + "\n2000-3000 r--p 0 1:2 7 " + name
        maps += "\n1000-2000 r-xp 0 1:2 7 /data/app/example/libother.so"
        maps += "\n1000-2000 r-xp 0 1:2 7 " + name + " (deleted)"
        self.assertEqual(capture.mapped_native_paths(maps), [name])


if __name__ == "__main__":
    unittest.main(verbosity=2)
