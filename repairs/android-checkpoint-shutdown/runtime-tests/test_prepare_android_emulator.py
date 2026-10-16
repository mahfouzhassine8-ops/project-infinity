#!/usr/bin/env python3
"""Failure controls for the bounded infrastructure-only ZIP retry."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from prepare_android_emulator import BAD_ARCHIVE, prepare


class EmulatorPreparationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sdk = self.root / "sdk"
        emulator = self.sdk / "emulator"
        emulator.mkdir(parents=True)
        (emulator / "source.properties").write_text("Pkg.Revision=36.2.12\n")
        (emulator / "emulator").write_text("test executable")
        (emulator / "emulator").chmod(0o700)
        self.out = self.root / "evidence"
        self.calls, self.waits = [], []

    def run_results(self, results):
        def run(command, log):
            self.calls.append(command)
            code, output = results.pop(0)
            log.write_text(output)
            return code, output
        return prepare(self.sdk, self.out, run=run, pause=self.waits.append)

    def report(self):
        return json.loads((self.out / "EMULATOR-PREPARATION.json").read_text())

    def test_success_requires_actual_version_and_no_retry(self):
        report = self.run_results([(0, "installed"), (0, "Android emulator version 36.2.12 (build_id 123)")])
        self.assertTrue(report["passed"])
        self.assertFalse(report["application_test_retried"])
        self.assertEqual(self.waits, [])
        self.assertEqual(self.calls[0][-3:], ["--install", "emulator", "--channel=0"])

    def test_observed_invalid_zip_retries_then_validates(self):
        report = self.run_results([(1, "Warning: " + BAD_ARCHIVE), (0, "installed"),
                                   (0, "Android emulator version 36.2.12")])
        self.assertTrue(report["passed"])
        self.assertEqual(self.waits, [2])
        self.assertTrue(report["attempts"][0]["observed_invalid_emulator_zip"])
        self.assertIn(BAD_ARCHIVE, (self.out / "sdkmanager-attempt-1.log").read_text())

    def test_bad_zip_warning_with_zero_status_is_not_success(self):
        report = self.run_results([(0, BAD_ARCHIVE), (0, "installed"),
                                   (0, "Android emulator version 36.2.12")])
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["attempts"]), 2)

    def test_repeated_bad_zip_fails_after_three_attempts(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(1, BAD_ARCHIVE)] * 3)
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.waits, [2, 4])
        self.assertFalse(self.report()["passed"])

    def test_other_sdk_failure_is_not_retried(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(1, "License not accepted")])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.waits, [])
        self.assertFalse(self.report()["passed"])

    def test_other_package_bad_zip_is_not_retried(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(1, BAD_ARCHIVE.replace("Android Emulator", "Android SDK Platform 30"))])
        self.assertEqual(len(self.calls), 1)

    def test_timeout_is_not_retried_even_with_archive_message(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(124, BAD_ARCHIVE)])
        self.assertEqual(len(self.calls), 1)

    def test_later_non_archive_failure_stops(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(1, BAD_ARCHIVE), (1, "Permission denied")])
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.waits, [2])

    def test_successful_install_without_executable_fails(self):
        (self.sdk / "emulator/emulator").unlink()
        with self.assertRaises(RuntimeError):
            self.run_results([(0, "installed")])
        self.assertFalse(self.report()["passed"])

    def test_non_executable_emulator_fails(self):
        (self.sdk / "emulator/emulator").chmod(0o600)
        with self.assertRaises(RuntimeError):
            self.run_results([(0, "installed")])

    def test_failed_version_command_fails(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(0, "installed"), (1, "loader error")])
        self.assertFalse(self.report()["passed"])

    def test_mismatched_package_version_fails(self):
        with self.assertRaises(RuntimeError):
            self.run_results([(0, "installed"), (0, "Android emulator version 35.0.0")])
        self.assertFalse(self.report()["passed"])

    def test_equivalent_trailing_zero_version_is_accepted(self):
        report = self.run_results([(0, "installed"), (0, "Android emulator version 36.2.12.0")])
        self.assertTrue(report["passed"])
        self.assertEqual(report["executable_revision"], "36.2.12.0")

    def test_actual_subprocess_retries_and_retains_both_logs(self):
        manager = self.sdk / "cmdline-tools/latest/bin/sdkmanager"
        manager.parent.mkdir(parents=True)
        manager.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\n"
                           "counter=Path(__file__).with_suffix('.attempted')\n"
                           "if not counter.exists():\n"
                           " counter.touch()\n print(" + repr(BAD_ARCHIVE) + ")\n raise SystemExit(1)\n"
                           "print('Installed SDK package emulator')\n")
        manager.chmod(0o700)
        executable = self.sdk / "emulator/emulator"
        executable.write_text("#!/bin/sh\necho 'Android emulator version 36.2.12.0 (build_id 123)'\n")
        executable.chmod(0o700)
        report = prepare(self.sdk, self.out, pause=self.waits.append)
        self.assertTrue(report["passed"])
        self.assertEqual(self.waits, [2])
        self.assertIn(BAD_ARCHIVE, (self.out / "sdkmanager-attempt-1.log").read_text())
        self.assertIn("Installed SDK package", (self.out / "sdkmanager-attempt-2.log").read_text())

    def test_actual_subprocess_failure_is_retained_and_terminal(self):
        manager = self.sdk / "cmdline-tools/latest/bin/sdkmanager"
        manager.parent.mkdir(parents=True)
        manager.write_text("#!/bin/sh\necho 'SDK licenses missing' >&2\nexit 1\n")
        manager.chmod(0o700)
        with self.assertRaises(RuntimeError):
            prepare(self.sdk, self.out, pause=self.waits.append)
        self.assertEqual(self.waits, [])
        self.assertFalse(self.report()["passed"])
        self.assertIn("SDK licenses missing", (self.out / "sdkmanager-attempt-1.log").read_text())

    def test_exact_ci_missing_libpulse_is_identified_and_not_retried(self):
        error = ("/usr/local/lib/android/sdk/emulator/qemu/linux-x86_64/qemu-system-x86_64: "
                 "error while loading shared libraries: libpulse.so.0: cannot open shared object file: "
                 "No such file or directory\n")
        with self.assertRaisesRegex(RuntimeError, r"exit 127.*libpulse\.so\.0"):
            self.run_results([(0, "installed"), (127, error)])
        self.assertEqual(self.waits, [])
        self.assertEqual(len(self.calls), 2)
        report = self.report()
        self.assertFalse(report["passed"])
        self.assertEqual(report["version_command"]["exit_code"], 127)
        self.assertEqual(report["version_command"]["output"], error)

    def test_ci_runtime_dependency_is_installed_before_each_preflight(self):
        workflow = (Path(__file__).resolve().parents[3] / ".github/workflows/"
                    "infinity-essential-first-java-process-verification.yml").read_text()
        for job in ("fresh-production-shutdown", "upgrade-early-shutdown", "upgrade-loaded-shutdown"):
            section = re.split(r"\n  \S", workflow.split("\n  " + job + ":\n", 1)[1], maxsplit=1)[0]
            self.assertLess(section.index("apt-get install -y libpulse0"),
                            section.index("prepare_android_emulator.py --out"))

    def test_loader_dependency_evidence_cannot_replace_actual_version(self):
        qemu = self.sdk / "emulator/qemu/linux-x86_64/qemu-system-x86_64"
        qemu.parent.mkdir(parents=True)
        qemu.write_text("controlled dependency target")
        dependencies = "libpulse.so.0 => not found\nlibother.so.1 => not found\nlibc.so.6 => /lib/libc.so.6 (0x1234)\n"
        with self.assertRaisesRegex(RuntimeError, "exit 127"):
            self.run_results([(0, "installed"), (0, dependencies), (127, "loader failure")])
        report = self.report()
        self.assertEqual(report["loader_dependencies"]["missing"], ["libpulse.so.0", "libother.so.1"])
        self.assertFalse(report["passed"])
        self.assertEqual(self.calls[1], ["ldd", str(qemu)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
