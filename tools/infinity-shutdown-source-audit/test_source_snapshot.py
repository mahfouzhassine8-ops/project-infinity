import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).parent / "script.infinity.shutdownaudit/source_snapshot.py"
spec = importlib.util.spec_from_file_location("snapshot", SOURCE)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


class SnapshotTests(unittest.TestCase):
    def test_source_dependencies_and_privacy_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "plugin.test"
            root.mkdir()
            (root / "addon.xml").write_text('<addon id="plugin.test" version="1.2"><requires><import addon="script.module.test" version="2.0" /></requires></addon>')
            (root / "default.py").write_text("print('source')\n")
            (root / "settings.xml").write_text("account setting must stay private")
            (root / "user.db").write_bytes(b"private database")
            for name in ("userdata", "addon_data", "profile", "cache", "logs"):
                (root / name).mkdir()
                (root / name / "secret.py").write_text("private state")
            external = Path(directory) / "account.txt"
            external.write_text("private account")
            (root / "linked.py").symlink_to(external)
            (root / "linked-directory").symlink_to(root / "profile", target_is_directory=True)
            (root / "module.so").write_bytes(b"opaque native code")
            output = Path(directory) / "export.zip"
            report = snapshot.collect([{"id": "plugin.test", "path": str(root)}], output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"addons/plugin.test/addon.xml", "addons/plugin.test/default.py", "SOURCE-MANIFEST.json"})
                self.assertIsNone(archive.testzip())
                saved = json.loads(archive.read("SOURCE-MANIFEST.json"))
                self.assertEqual(saved, report)
                owner = saved["addons"][0]
                self.assertEqual(owner["dependencies"][0]["id"], "script.module.test")
                self.assertEqual(owner["version"], "1.2")
                self.assertEqual(len(owner["opaque_code"]), 1)
                for entry in owner["files"]:
                    self.assertEqual(hashlib.sha256(archive.read("addons/plugin.test/" + entry["file"])).hexdigest(), entry["sha256"])
                self.assertEqual(set(owner["excluded_links"]), {"linked.py", "linked-directory"})

    def test_unknown_identity_is_reported_without_copying_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "addon.xml").write_text('<addon id="different.addon" version="1" />')
            (root / "default.py").write_text("source")
            output = root / "export.zip"
            report = snapshot.collect([{"id": "plugin.test", "path": str(root)}], output)
            self.assertTrue(report["errors"])
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ["SOURCE-MANIFEST.json"])


if __name__ == "__main__":
    unittest.main()
