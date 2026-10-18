"""Host-only positive/negative contracts for nine-item assembler; no APK signing."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("nine_bundle", ROOT / "package_2103390.py")
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class ExactNineAssemblerTests(unittest.TestCase):
    def test_identity_and_selected_components(self):
        self.assertEqual(bundle.CODE, 2103390)
        self.assertEqual(len(bundle.BASE_NAME), len(bundle.NAME))
        self.assertEqual(set(bundle.DISTRIBUTION), set(bundle.gate.VERSIONS))
        self.assertNotIn("script.infinity.addonrecovery", bundle.DISTRIBUTION)
        self.assertNotIn("service.xbmc.versioncheck", bundle.DISTRIBUTION)
        self.assertEqual(bundle.gate.REPAIR_NUMBERS, (1, 2, 3, 4, 5, 6, 9, 10, 12))

    def test_manifest_uses_exact_existing_dependencies(self):
        original = b'<addons>\n  <addon>service.infinity.compat</addon>\n</addons>\n'
        updated = bundle.revised_manifest(original)
        before = bundle.gate.manifest_members(original)
        after = bundle.gate.manifest_members(updated)
        self.assertEqual(after - before, set(bundle.gate.VERSIONS) |
                         (set(bundle.gate.DEPENDENCIES) - before))
        self.assertNotIn("script.infinity.addonrecovery", after)
        self.assertNotIn("service.xbmc.versioncheck", after)
        self.assertEqual(bundle.revised_manifest(updated), updated)

    def sample(self, root, addon, version, member=None):
        archive = root / (addon + ".zip")
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(addon + "/addon.xml",
                       '<addon id="' + addon + '" version="' + version + '"/>')
            z.writestr(member or addon + "/default.py", "pass")
        return archive

    def test_version_and_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            addon = "script.infinity.rails"
            archive = self.sample(root, addon, "0.2.7")
            data, digest = bundle.unzip_component(archive, addon)
            self.assertEqual(digest, bundle.digest(archive))
            self.assertIn("assets/addons/" + addon + "/default.py", data)
            archive = self.sample(root, addon, "0.2.6")
            with self.assertRaisesRegex(ValueError, "Wrong approved add-on"):
                bundle.unzip_component(archive, addon)
            archive = self.sample(root, addon, "0.2.7", addon + "/../foreign.py")
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP member"):
                bundle.unzip_component(archive, addon)

    def test_uihelper_content_is_original_source_plus_one_approved_xml(self):
        src = bundle.ROOT / "repairs/four-repair-20261018"
        files = {"assets/addons/script.infinity.uirepair/" +
                 p.relative_to(src / "addon").as_posix(): p.read_bytes()
                 for p in (src / "addon").rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts}
        files["assets/addons/script.infinity.uirepair/resources/skins/Default/1080i/InfinityItemOptions.xml"] = (
            src / "InfinityItemOptions.xml").read_bytes()
        self.assertTrue(bundle.helper_source_identity(files))
        altered = dict(files)
        key = "assets/addons/script.infinity.uirepair/runtime.py"
        altered[key] += b"\n# unreviewed source change"
        with self.assertRaisesRegex(ValueError, "archive does not contain"):
            bundle.helper_source_identity(altered)

    def test_original_signed_native_name_remains_pinned_after_safe_staging_alias(self):
        # Work's signed receipt names the original published APK, while this
        # workflow stores the exact same bytes under inputs/native.apk.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            staged = root / "native.apk"
            staged.write_bytes(b"pinned signed native byte fixture")
            approved = {
                "file": "Infinity-2103385-UI-Restoration-TEST1.apk",
                "sha256": bundle.digest(staged),
                "native_restored_2103384": False,
                "changed_unsigned_payload": ["AndroidManifest.xml",
                                             "lib/arm64-v8a/libkodi.so"],
            }
            self.assertEqual(
                bundle.verify_signed_native_artifact({"artifacts": [approved]}, staged),
                approved)
            wrong_file = dict(approved, file="Infinity-2103384-Older-APK.apk")
            with self.assertRaisesRegex(ValueError, "Signed native parent lineage"):
                bundle.verify_signed_native_artifact({"artifacts": [wrong_file]}, staged)
            wrong_digest = dict(approved, sha256="0"*64)
            with self.assertRaisesRegex(ValueError, "Signed native parent lineage"):
                bundle.verify_signed_native_artifact({"artifacts": [wrong_digest]}, staged)
            wrong_delta = dict(approved, changed_unsigned_payload=["AndroidManifest.xml"])
            with self.assertRaisesRegex(ValueError, "Signed native parent lineage"):
                bundle.verify_signed_native_artifact({"artifacts": [wrong_delta]}, staged)
            with self.assertRaisesRegex(ValueError, "Signed native parent lineage"):
                bundle.verify_signed_native_artifact({"artifacts": [approved, approved]}, staged)

    def test_original_compat_service_bytes_always_win_over_staged_source(self):
        # Native parent already bundles compatibility metadata that differs
        # from the first-party staging archive. Preserve its exact bytes.
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "original.apk"
            prefix = "assets/addons/service.infinity.compat/"
            original_manifest = b'<addon id="service.infinity.compat" version="0.8.2"><extension point="xbmc.service"/></addon>'
            with zipfile.ZipFile(path, "w") as z:
                z.writestr(prefix + "addon.xml", original_manifest)
                z.writestr(prefix + "runner.py", b"# original signed byte payload")
            staged = {
                prefix + "addon.xml": b'<addon id="service.infinity.compat" version="0.8.2"/>',
                prefix + "runner.py": b"# external old bytes (NOT approved)",
                prefix + "unlisted.py": b"# must not be added to existing service",
                "assets/addons/script.skinshortcuts/addon.xml":
                    b'<addon id="script.skinshortcuts" version="2.0.3"/>',
            }
            with zipfile.ZipFile(path) as z:
                selected, preserved = bundle.preserve_original_embedded_dependencies(z, staged)
            self.assertNotIn(prefix + "addon.xml", selected)
            self.assertNotIn(prefix + "runner.py", selected)
            self.assertNotIn(prefix + "unlisted.py", selected)
            self.assertIn("service.infinity.compat", preserved)
            self.assertEqual(preserved["service.infinity.compat"]["version"], "0.8.2")
            self.assertEqual(set(selected),
                {"assets/addons/script.skinshortcuts/addon.xml"})
            with zipfile.ZipFile(path) as z:
                self.assertEqual(z.read(prefix + "addon.xml"), original_manifest)
                self.assertEqual(z.read(prefix + "runner.py"),
                                 b"# original signed byte payload")

    def test_bogus_original_compat_service_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad-existing.apk"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("assets/addons/service.infinity.compat/addon.xml",
                           '<addon id="service.infinity.compat" version="0.0.0"/>')
            with zipfile.ZipFile(path) as z:
                with self.assertRaisesRegex(ValueError,
                                             "Existing protected dependency ID/version"):
                    bundle.preserve_original_embedded_dependencies(z, {})

    def test_wrong_locked_parent_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "old.apk").write_bytes(b"not signed")
            (root / "locked.apk").write_bytes(b"wrong")
            (root / "proof.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "Locked user-approved"):
                bundle.verify_native_parent(root / "old.apk", root / "locked.apk",
                                            root / "proof.json", "0"*40)


if __name__ == "__main__":
    unittest.main()
