#!/usr/bin/env python3
"""Fail-closed source and preservation contracts for the independent 2103364 candidate.

These checks are not an Android/Fold integration test. Runtime suites, native
compiler, signed APK preservation and physical acceptance must also pass.
"""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "runtime/native/overlay"
ANDROID = ROOT / "runtime/android/overlay/tools/android/packaging/xbmc/src"
BASELINE_INSTALLER = "29024dba601d0eecc939a44b6f58ce81128635b73ff42dbc38bb6007456846b4"


def sha(data):
    return hashlib.sha256(data).hexdigest()


class SourceContracts(unittest.TestCase):
    def test_native_overlay_verified(self):
        manifest = json.loads((ROOT / "runtime/native/manifest.json").read_text())
        selected = (
            "xbmc/addons/Addon.cpp",
            "xbmc/addons/AddonInstaller.cpp",
            "xbmc/platform/android/activity/InfinityCheckpointFile.h",
            "xbmc/platform/android/activity/InfinityShutdownTrace.h",
        )
        for filename in selected:
            with self.subTest(filename=filename):
                self.assertIn(filename, manifest["changed"])
                self.assertEqual(sha((NATIVE / filename).read_bytes()), manifest["after"][filename])
        self.assertEqual(manifest["before"]["xbmc/addons/AddonInstaller.cpp"], BASELINE_INSTALLER)
        self.assertNotIn("xbmc/addons/AddonInstaller.cpp", manifest["added"])
        self.assertFalse(manifest["deleted"])

    def test_settings_confirmed_only_after_write(self):
        source = (NATIVE / "xbmc/addons/Addon.cpp").read_text()
        success = "if (!ConfirmAddonSave(data.m_addonSettings, data.m_userSettingsPath, doc))"
        self.assertEqual(source.count(success), 1)
        self.assertLess(source.index("if (!doc.SaveFile(data.m_userSettingsPath))"),
                        source.index(success))
        self.assertIn("g_checkpointAddonSaveGenerations[path]", source)
        self.assertIn("entry.loadedBytes = bytes;", source)
        self.assertIn("conflicting_loaded_owners", source)
        self.assertIn("loaded_owner_not_serializable", source)

    def test_optional_acl_is_verified_not_discarded(self):
        source = (NATIVE / "xbmc/platform/android/activity/InfinityCheckpointFile.h").read_text()
        self.assertIn('errno == ENODATA && name == "system.posix_acl_access"', source)
        for guard in (
            "before.st_uid != after.st_uid",
            "before.st_ino != after.st_ino",
            "confirmedNames != names",
            'failMetadata("acl_absence_not_verified", EBUSY, name)',
            "Stage::PreserveMetadata",
            "Stage::VerifyMetadata",
        ):
            self.assertIn(guard, source)

    def test_installer_reject_and_package_database(self):
        source = (NATIVE / "xbmc/addons/AddonInstaller.cpp").read_text()
        start = source.index("unsigned int jobID =")
        reject = source.index("if (jobID == 0)", start)
        publish = source.index("m_downloadJobs.insert", start)
        self.assertLess(start, reject)
        self.assertLess(reject, publish)
        self.assertIn("if (!db.AddPackage(m_addon->ID(), package, hash.value))", source)
        self.assertIn("package database update failed", source)

    def test_android_overlay_and_consumed_completion(self):
        manifest = json.loads((ROOT / "runtime/android/manifest.json").read_text())
        selected = (
            "InfinityCheckpointProtocol.java.in",
            "InfinityCloseGuardService.java.in",
            "InfinityKodiShutdown.java.in",
        )
        for name in selected:
            path = "tools/android/packaging/xbmc/src/" + name
            with self.subTest(filename=name):
                self.assertEqual(sha((ANDROID / name).read_bytes()), manifest["after"][path])
        protocol = (ANDROID / selected[0]).read_text()
        self.assertIn("authorization_consumed", protocol)
        self.assertIn("engine_death_elapsed_ms", protocol)
        self.assertIn("confirmedComplete", protocol)
        for name in selected[1:]:
            self.assertIn("InfinityCheckpointProtocol.confirmedComplete(", (ANDROID / name).read_text())
        self.assertIn('checkpointSaved&&consumed&&!revoked', (ANDROID / selected[1]).read_text())

    def test_inherited_resume_speed_contracts(self):
        from importlib.util import spec_from_file_location, module_from_spec
        package = Path(__file__).resolve().parents[3] / "tools/checkpoint-apk/package.py"
        code = package.read_text()
        self.assertIn("VERSION = 2103364", code)
        self.assertIn("Resume-Lifecycle-RC1", code)
        self.assertIn("verify_checkpoint_manifest", code)
        for name in ("service.py", "resume_hub.py", "plugin.py"):
            path = ROOT / ("runtime/commandcenter/overlay/" + name)
            self.assertTrue(path.is_file(), name)
        # No reduced owner registry or replacement script payloads.
        protocol = (ANDROID / "InfinityCheckpointProtocol.java.in").read_text()
        self.assertIn("REQUIRED_OWNER_NAMES", protocol)
        self.assertIn("peripherals", protocol)
        self.assertIn("pvr", protocol)


if __name__ == "__main__":
    unittest.main(verbosity=2)
