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
            "assets/addons/service.infinity.compat/addon.xml":
                b'<addon id="service.infinity.compat" version="0.7.2"/>',
            "assets/addons/service.xbmc.versioncheck/runner.py": b"original versioncheck code",
            "assets/addons/script.infinity.addonrecovery/default.py": b"preexisting user-visible code",
            "assets/cobra/preserved.bin": b"Cobra original byte data",
            gate.MANIFEST: b"<addons></addons>\n",
        }
        after = dict(old)
        after["AndroidManifest.xml"] = b"new version metadata only"
        after["lib/arm64-v8a/libkodi.so"] = b"compiled 2103384-derived UI input engine"
        root = ET.fromstring(old[gate.MANIFEST])
        for aid, version in gate.VERSIONS.items():
            ET.SubElement(root, "addon").text = aid
            after["assets/addons/" + aid + "/addon.xml"] = (
                '<addon id="' + aid + '" version="' + version + '"/>').encode()
        for aid, version in gate.DEPENDENCIES.items():
            if (aid not in gate.PRESERVED_REGISTRATION_IDS and
                    aid not in {entry.text for entry in root.findall("addon")}):
                ET.SubElement(root, "addon").text = aid
            # A signed original embedded service is authoritative over the
            # non-authoritative first-party staging copy.
            key = "assets/addons/" + aid + "/addon.xml"
            if key not in after:
                after[key] = (
                    '<addon id="' + aid + '" version="' + (version or '1.0.0') + '"/>').encode()
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
            with zipfile.ZipFile(candidate) as z:
                self.assertNotIn("service.infinity.compat",
                    gate.manifest_members(z.read(gate.MANIFEST)))
            self.assertEqual(result["new_or_updated_addons"], gate.VERSIONS)
            self.assertFalse(result["original_crash_fixed"])
            self.assertEqual(result["removed_files"], [])
        finally:
            context.cleanup()

    def test_rejects_new_registration_of_original_unregistered_compat_service(self):
        context, old, candidate = self.setup_fixture()
        try:
            with zipfile.ZipFile(candidate) as z:
                items = {name:z.read(name) for name in z.namelist()}
            old_manifest = items[gate.MANIFEST]
            self.assertNotIn("service.infinity.compat",
                             gate.manifest_members(old_manifest))
            xml = ET.fromstring(old_manifest)
            ET.SubElement(xml, "addon").text = "service.infinity.compat"
            items[gate.MANIFEST] = ET.tostring(xml)
            with zipfile.ZipFile(candidate,"w") as z:
                for name,body in items.items():
                    z.writestr(name,body)
            with self.assertRaisesRegex(ValueError,
                                         "Original embedded Compatibility registration changed"):
                gate.check_apks(old,candidate)
        finally:
            context.cleanup()

    def test_rejects_deletion_of_existing_compatibility_or_other_member(self):
        self.check_bad(drop="assets/addons/service.infinity.compat/runtime_service.py")
        self.check_bad(drop="assets/cobra/preserved.bin")

    def test_locked_compat_version_and_bytes_are_authoritative(self):
        context, old, candidate = self.setup_fixture()
        try:
            self.assertEqual(gate.check_apks(old, candidate)["unchanged_dependency_identities"]
                             ["service.infinity.compat"], None)
        finally:
            context.cleanup()
        self.check_bad({"assets/addons/service.infinity.compat/addon.xml":
                        b'<addon id="service.infinity.compat" version="0.8.2"/>'})
        self.check_bad(add={"assets/addons/service.infinity.compat/unlisted.py": b"foreign"})
        self.check_bad(drop="assets/addons/service.infinity.compat/addon.xml")

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
