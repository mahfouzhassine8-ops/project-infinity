"""Synthetic APK-delta negative controls; does NOT qualify an Infinity APK."""
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET
import zipfile

import scope_gate as gate


class ContractTests(unittest.TestCase):
    def test_current_approved_sources_and_only_nine_numbers(self):
        report = gate.check_sources()
        self.assertEqual(report["scope"], [1, 2, 3, 4, 5, 6, 9, 10, 12])
        self.assertEqual(report["excluded_new_work"], [7, 8, 11])
        self.assertFalse(report["physical_fold_verified"])

    def setup_fixture(self, candidate_change=None, drop=None, add=None):
        candidate_change = candidate_change or {}
        add = add or {}
        old = {
            "AndroidManifest.xml": b"original manifest",
            "classes.dex": b"original Java/Dex",
            "lib/arm64-v8a/libkodi.so": b"old engine",
            "lib/arm64-v8a/libinfinitycrash.so": b"unchanged original crash recorder",
            "lib/arm64-v8a/libunchanged.so": b"untouched native library",
            "assets/addons/service.infinity.compat/runtime_service.py": b"original compatibility code",
            "assets/addons/service.xbmc.versioncheck/runner.py": b"original versioncheck code",
            "assets/addons/script.infinity.addonrecovery/default.py": b"preexisting user-visible code",
            "assets/cobra/preserved.bin": b"Cobra original byte data",
            gate.MANIFEST: b"<addons><addon>service.infinity.compat</addon></addons>\n",
        }
        after = dict(old)
        after["AndroidManifest.xml"] = b"new version metadata only"
        after["lib/arm64-v8a/libkodi.so"] = b"compiled 2103384-derived UI input engine"
        root = ET.fromstring(old[gate.MANIFEST])
        for aid, version in gate.VERSIONS.items():
            ET.SubElement(root, "addon").text = aid
            after["assets/addons/" + aid + "/addon.xml"] = (
                '<addon id="' + aid + '" version="' + version + '"/>').encode()
        after[gate.MANIFEST] = ET.tostring(root)
        after.update(candidate_change)
        after.update(add)
        if drop:
            del after[drop]
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name)
        for name, rows in (("old.apk", old), ("new.apk", after)):
            with zipfile.ZipFile(path / name, "w") as z:
                for p, body in rows.items():
                    z.writestr(p, body)
        return tmp, path / "old.apk", path / "new.apk"

    def check_bad(self, candidate_change=None, drop=None, add=None):
        context, old, candidate = self.setup_fixture(candidate_change, drop, add)
        try:
            with self.assertRaisesRegex(ValueError, "exact-scope gate failed"):
                gate.check_apks(old, candidate)
        finally:
            context.cleanup()

    def test_exact_allowlist_and_unmodified_native_crash_recorder(self):
        context, old, candidate = self.setup_fixture()
        try:
            result = gate.check_apks(old, candidate)
            self.assertTrue(result["original_native_crash_recorder_preserved"])
            self.assertTrue(result["versioncheck_unchanged"])
            self.assertEqual(result["new_or_updated_addons"], gate.VERSIONS)
            self.assertFalse(result["original_crash_fixed"])
            self.assertEqual(result["removed_files"], [])
        finally:
            context.cleanup()

    def test_rejects_deletion_of_existing_compatibility_or_other_member(self):
        self.check_bad(drop="assets/addons/service.infinity.compat/runtime_service.py")
        self.check_bad(drop="assets/cobra/preserved.bin")

    def test_rejects_mutation_to_cobra_diagnostics_or_native_shutdown_libraries(self):
        self.check_bad({"assets/cobra/preserved.bin": b"modified"})
        self.check_bad({"lib/arm64-v8a/libinfinitycrash.so": b"new unapproved recorder"})
        self.check_bad({"lib/arm64-v8a/libunchanged.so": b"native changed"})

    def test_rejects_changes_to_skipped_7_and_11(self):
        self.check_bad({"assets/addons/script.infinity.addonrecovery/default.py": b"changed"})
        self.check_bad({"assets/addons/service.xbmc.versioncheck/runner.py": b"changed"})
        self.check_bad(add={"assets/addons/script.infinity.addonrecovery/addon.xml": b"<addon/>"})

    def test_rejects_unrelated_extra_service_or_ui(self):
        self.check_bad(add={"assets/addons/service.unexpected/runner.py": b"unexpected"})
        self.check_bad({"classes.dex": b"rewritten classes.dex"})

    def test_rejects_version_downgrade_or_missing_integrated_component(self):
        self.check_bad({"assets/addons/script.infinity.rails/addon.xml":
                         b'<addon id="script.infinity.rails" version="0.2.6"/>'})
        self.check_bad(drop="assets/addons/script.infinity.watchedbridge/addon.xml")


if __name__ == "__main__":
    unittest.main()
