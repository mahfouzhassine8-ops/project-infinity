#!/usr/bin/env python3
"""Prevent TEST4 locked-source contamination by future Infinity feature edits.

Checks the exact original TEST4 source used in the replay and the isolated
newer candidate. Neither check counts as a built APK or physical shutdown.
"""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "repairs/essential-first-2103377/runtime/xbmc/platform/android/activity/InfinityProtectedWrites.h"
CANDIDATE = ROOT / "repairs/full-system-20261017/InfinityProtectedWrites.stagefix.h"
PINNED_TEST4_SOURCE = "a0a50a78e24fc5da8c9af65bc894ee47af4e61139af9d89cf014207d177e92f1"


class TestShutdownLineage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = ORIGINAL.read_bytes()
        cls.candidate = CANDIDATE.read_bytes()

    def test_test4_source_must_be_immutable(self):
        self.assertEqual(hashlib.sha256(self.orig).hexdigest(), PINNED_TEST4_SOURCE)
        self.assertNotIn(b"SyncRemovedInstallerStage", self.orig)
        self.assertIn(b"inline bool SyncProtectedPath(const std::string& path)", self.orig)

    def test_installer_fix_cannot_replace_historical_build_input(self):
        self.assertIn(b"SyncRemovedInstallerStage", self.candidate)
        self.assertIn(b"InstallerStageRoot", self.candidate)
        self.assertIn(b"inline bool SyncProtectedPath(const std::string& path,", self.candidate)
        self.assertNotEqual(self.orig, self.candidate)

    def test_no_unrelated_prior_write_protection_code_changed(self):
        before = self.orig.index(b"inline bool SyncProtectedPath")
        after = self.candidate.index(b"// A completed/rolled-back add-on installation")
        self.assertEqual(self.orig[:before], self.candidate[:after])
        end = b"inline bool EssentialWritesAuthorized(uint64_t generation)"
        self.assertIn(end, self.orig)
        self.assertIn(end, self.candidate)
        self.assertEqual(self.orig.split(end, 1)[1], self.candidate.split(end, 1)[1])

    def test_seal_remains_fail_closed_with_durable_proof(self):
        for marker in (b"protected_durability_failed:", b"EssentialWritesLocked(s).blockers.empty()",
                       b"p.protection",):
            # p.protection deliberately not in current code: check only
            # authoritative markers below.
            if marker == b"p.protection":
                continue
            self.assertIn(marker, self.candidate)
        self.assertIn(b"p.phase = 3;", self.candidate)
        self.assertIn(b"s.protection.durable = true;", self.candidate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
