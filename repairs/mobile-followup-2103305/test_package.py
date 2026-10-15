#!/usr/bin/env python3
"""Source/preservation contracts for the Java-only candidate packager."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("candidate3305", HERE / "package_candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class SourceContracts(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="infinity3305-package-test-")
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name)
        route = self.source / candidate.TARGET
        route.parent.mkdir(parents=True)
        route.write_bytes((HERE / "InfinityPowerMenuRoutes.java.in").read_bytes())
        for i in range(249):
            (self.source / ("protected-%03d" % i)).write_text("protected\n")
        after = candidate.manifest(self.source)
        before = dict(after)
        before[candidate.TARGET] = "7c162799c8ac0a0c507e70767b475f3fe9dcd7f53533201eb2002213199faf22"
        self.baseline = {"source_commit": candidate.BASE_SOURCE_COMMIT, "files": before}
        self.proof = {"source_commit": "exact-test-commit", "files": after, "weather_isolation_audit_passed": True}
        self.receipt = {"parent_source_commit": candidate.BASE_SOURCE_COMMIT,
                        "before": before, "after": after, "changed": [candidate.TARGET],
                        "native_changed": False, "skin_changed": False,
                        "weather_changed": False, "shutdown_policy_changed": False}

    def verify(self):
        return candidate.verify_source(self.source, self.proof, self.receipt, self.baseline, "exact-test-commit")

    def test_exact_one_helper_passes(self):
        self.assertEqual(250, self.verify())

    def test_changed_protected_file_is_rejected(self):
        (self.source / "protected-007").write_text("unexpected\n")
        with self.assertRaisesRegex(RuntimeError, "manifest differs"):
            self.verify()

    def test_missing_source_is_rejected(self):
        (self.source / "protected-007").unlink()
        with self.assertRaisesRegex(RuntimeError, "source count"):
            self.verify()

    def test_unrelated_commit_is_rejected(self):
        self.proof["source_commit"] = "another-commit"
        with self.assertRaisesRegex(RuntimeError, "build commit"):
            self.verify()

    def test_weather_gate_is_required(self):
        self.proof["weather_isolation_audit_passed"] = False
        with self.assertRaisesRegex(RuntimeError, "weather isolation"):
            self.verify()

    def test_extra_allowlisted_delta_is_rejected(self):
        self.receipt["changed"].append("protected-007")
        with self.assertRaisesRegex(RuntimeError, "one route installer"):
            self.verify()

    def test_wrong_parent_manifest_is_rejected(self):
        self.baseline = copy.deepcopy(self.baseline)
        self.baseline["files"]["protected-007"] = "wrong-parent"
        with self.assertRaisesRegex(RuntimeError, "locked APK"):
            self.verify()

    def test_unintended_policy_changes_are_rejected(self):
        for key in ("native_changed", "skin_changed", "weather_changed", "shutdown_policy_changed"):
            with self.subTest(key=key):
                self.receipt[key] = True
                with self.assertRaisesRegex(RuntimeError, "policy/payload"):
                    self.verify()
                self.receipt[key] = False

    def test_version_and_native_parent_are_pinned(self):
        self.assertEqual(2103305, candidate.VERSION_CODE)
        self.assertEqual("81884f5591d0912b031c6cc8dd6e8c6e198a84ddd95d03a878624fbb1e0425fa", candidate.BASE_APK_SHA)
        self.assertEqual("b6724bc5cff3f3e79c5035f82e77be331535a9e3a7bf33e7650b7ab1e95c0626", candidate.BASE_NATIVE_SHA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
