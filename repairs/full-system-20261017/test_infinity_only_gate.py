#!/usr/bin/env python3
"""Regression tests: stock Kodi, loose badges, and green host-only results fail closed."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import infinity_only_gate as gate


def elf():
    return b"\x7fELF\x02\x01" + b"\0" * 12 + (183).to_bytes(2, "little") + b"\0" * 96


class InfinityOnlyGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.apk = Path(self.temp.name) / "candidate.apk"
        self.write_apk()
        self.sha = gate.digest_file(self.apk)

    def write_apk(self, include_engine=True):
        with zipfile.ZipFile(self.apk, "w") as z:
            z.writestr("AndroidManifest.xml", b"\x03\x00")
            z.writestr("classes.dex", b"dex\n035\0")
            if include_engine:
                z.writestr(gate.ENGINE, elf())

    def command_output(self, argv, **kwargs):
        if "dump" in argv:
            return ("package: name='com.projectinfinity.kodi' versionCode='2103382' "
                    "versionName='1.0.9-Watched-Touch-Bridge-TEST3'\n"
                    "application-label:'Infinity'\n")
        return ("Verifies\nVerified using v1 scheme (JAR signing): true\n"
                "Verified using v2 scheme (APK Signature Scheme v2): true\n"
                "Verified using v3 scheme (APK Signature Scheme v3): true\n"
                "Signer #1 certificate SHA-256 digest: " + gate.CERTIFICATE + "\n")

    def check(self):
        return gate.check_apk(self.apk, self.sha, 2103382, "aapt", "apksigner")

    @mock.patch.object(gate.subprocess, "check_output")
    def test_real_product_identity_passes_but_is_not_release_lock(self, run):
        run.side_effect = self.command_output
        result = self.check()
        self.assertEqual(result["package"], gate.PACKAGE)
        self.assertTrue(result["signed_infinity_apk_verified"])
        self.assertFalse(result["final_lock_authorized"])
        self.assertFalse(result["physical_fold_accepted"])
        self.assertFalse(result["stock_kodi_eligible"])

    @mock.patch.object(gate.subprocess, "check_output")
    def test_stock_kodi_package_never_counts(self, run):
        run.side_effect = lambda argv, **kw: self.command_output(argv, **kw).replace(
            "com.projectinfinity.kodi", "org.xbmc.kodi")
        with self.assertRaisesRegex(gate.GateFailure, "STOCK KODI"):
            self.check()

    @mock.patch.object(gate.subprocess, "check_output")
    def test_unsigned_or_wrong_certificate_never_counts(self, run):
        run.side_effect = lambda argv, **kw: self.command_output(argv, **kw).replace(
            gate.CERTIFICATE, "0" * 64)
        with self.assertRaisesRegex(gate.GateFailure, "signer"):
            self.check()

    @mock.patch.object(gate.subprocess, "check_output")
    def test_missing_signing_scheme_rejected(self, run):
        run.side_effect = lambda argv, **kw: self.command_output(argv, **kw).replace(
            "Verified using v3 scheme (APK Signature Scheme v3): true", "")
        with self.assertRaisesRegex(gate.GateFailure, "scheme v3"):
            self.check()

    @mock.patch.object(gate.subprocess, "check_output")
    def test_unpinned_apk_rejected_before_badging(self, run):
        with self.assertRaisesRegex(gate.GateFailure, "SHA-256"):
            gate.check_apk(self.apk, "0" * 64, 2103382, "aapt", "apksigner")
        run.assert_not_called()

    @mock.patch.object(gate.subprocess, "check_output")
    def test_wrong_version_rejected(self, run):
        run.side_effect = self.command_output
        with self.assertRaisesRegex(gate.GateFailure, "versionCode"):
            gate.check_apk(self.apk, self.sha, 2103383, "aapt", "apksigner")

    @mock.patch.object(gate.subprocess, "check_output")
    def test_missing_native_engine_rejected(self, run):
        self.write_apk(False)
        with self.assertRaisesRegex(gate.GateFailure, "native engine"):
            gate.check_apk(self.apk, gate.digest_file(self.apk), 2103382, "aapt", "apksigner")

    def write_phase(self, **changes):
        value = {
            "case": "fresh", "original_probe_report": "ANDROID-PROCESS-PROBE.json",
            "apk_sha256": self.sha, "passed": True, "apk_deliverable": False,
            "physical_fold_accepted": False, "final_lock_authorized": False,
        }
        value.update(changes)
        path = Path(self.temp.name) / "report.json"
        path.write_text(json.dumps(value))
        return path

    def test_real_signed_probe_receipt_is_scoped_not_release(self):
        result = gate.check_phase(self.write_phase(), self.sha, "fresh")
        self.assertTrue(result["real_signed_android_probe_passed"])
        self.assertFalse(result["release_ready"])

    def test_stock_or_host_success_receipt_is_not_evidence(self):
        path = self.write_phase(passed=True, original_probe_report="kodi-host-test.json")
        with self.assertRaisesRegex(gate.GateFailure, "probe type"):
            gate.check_phase(path, self.sha, "fresh")

    def test_unrelated_candidate_receipt_rejected(self):
        with self.assertRaisesRegex(gate.GateFailure, "different APK"):
            gate.check_phase(self.write_phase(apk_sha256="0" * 64), self.sha, "fresh")

    def test_skipped_failed_or_incomplete_phase_rejected(self):
        for value in (None, False, "success"):
            with self.subTest(value=value):
                with self.assertRaises(gate.GateFailure):
                    gate.check_phase(self.write_phase(passed=value), self.sha, "fresh")

    def test_false_physical_fold_or_release_claim_rejected(self):
        for field in ("physical_fold_accepted", "apk_deliverable", "final_lock_authorized"):
            with self.subTest(field=field):
                with self.assertRaises(gate.GateFailure):
                    gate.check_phase(self.write_phase(**{field: True}), self.sha, "fresh")

    def test_upgrade_phase_requires_correct_case_and_original_probe(self):
        path = self.write_phase(case="loaded", original_probe_report="OBSERVER-UPGRADE-PROBE.json")
        self.assertEqual(gate.check_phase(path, self.sha, "loaded")["case"], "loaded")
        with self.assertRaises(gate.GateFailure):
            gate.check_phase(path, self.sha, "cold")


if __name__ == "__main__":
    unittest.main(verbosity=2)
