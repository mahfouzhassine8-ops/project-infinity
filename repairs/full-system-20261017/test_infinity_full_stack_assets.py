#!/usr/bin/env python3
"""Host tests for strict real-package import. No Kodi fixture is a product pass."""
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import infinity_full_stack_assets as stack


def manifest(addon, version, requires=()):
    imports = "".join('<import addon="' + i + '" version="' + v + '"/>' for i, v in requires)
    return ('<addon id="' + addon + '" name="Infinity" version="' + version +
            '" provider-name="CI"><requires>' + imports + '</requires></addon>').encode()


class FullStackSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)

    def create_zip(self, payload=None):
        if payload is None:
            payload = {"skin.infinity.diggz/addon.xml":
                       manifest("skin.infinity.diggz", "1.0.5.225",
                                (("script.infinity.rails", "0.2.5"),))}
        archive = self.home / "skin.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for name, data in payload.items():
                if isinstance(data, zipfile.ZipInfo):
                    z.writestr(data, b"symlink")
                else:
                    z.writestr(name, data)
        return archive

    def fake_spec(self, path, count):
        return ("skin.infinity.diggz", "1.0.5.225", stack.digest(path), count)

    def test_actual_production_hashes_and_entry_counts_pinned(self):
        self.assertEqual(stack.SKIN[2], "8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235")
        self.assertEqual(stack.SKIN[3], 3071)
        self.assertEqual(stack.RAILS[2], "5e4ff64592d6f8660d17db1077ed85a368c02f4eb14442760797b1d133c08179")
        self.assertEqual(stack.RAILS[3], 14)

    def test_full_manifest_is_never_rewritten(self):
        archive = self.create_zip()
        dest = self.home / "stage"
        dest.mkdir()
        receipt = stack.archive_to_stage(archive, self.fake_spec(archive, 1), dest)
        expected = zipfile.ZipFile(archive).read("skin.infinity.diggz/addon.xml")
        installed = (dest / "skin.infinity.diggz/addon.xml").read_bytes()
        self.assertEqual(installed, expected)
        self.assertFalse(receipt["production_manifest_modified"])
        self.assertEqual(receipt["requirements"], [("script.infinity.rails", "0.2.5")])

    def test_stock_skin_substitute_rejected(self):
        archive = self.create_zip({"skin.estuary/addon.xml": manifest("skin.estuary", "1.0")})
        dest = self.home / "stage"
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, "Wrong ZIP root"):
            stack.archive_to_stage(archive, self.fake_spec(archive, 1), dest)

    def test_wrong_version_rejected(self):
        archive = self.create_zip({"skin.infinity.diggz/addon.xml":
                                   manifest("skin.infinity.diggz", "1.0.5.224")})
        dest = self.home / "stage"
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, "Wrong production addon ID/version"):
            stack.archive_to_stage(archive, self.fake_spec(archive, 1), dest)

    def test_full_zip_sha_and_entry_count_fail_closed(self):
        archive = self.create_zip()
        dest = self.home / "stage"
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, "full ZIP hash"):
            stack.archive_to_stage(archive, stack.SKIN, dest)
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            stack.archive_to_stage(archive, self.fake_spec(archive, 2), dest)

    def test_zip_slip_refused(self):
        archive = self.create_zip({"skin.infinity.diggz/../payload.py": b"malicious"})
        dest = self.home / "stage"
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            stack.archive_to_stage(archive, self.fake_spec(archive, 1), dest)
        self.assertFalse((self.home / "payload.py").exists())

    def test_symlink_refused(self):
        link = zipfile.ZipInfo("skin.infinity.diggz/skin.py")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive = self.create_zip({"skin.infinity.diggz/skin.py": link})
        dest = self.home / "stage"
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, "Symlinks forbidden"):
            stack.archive_to_stage(archive, self.fake_spec(archive, 1), dest)

    def test_required_first_party_source_must_match_previous_proof(self):
        home = self.home / "evidence"
        for ident, version in stack.PINNED_FIRST_PARTY.items():
            d = home / ident
            d.mkdir(parents=True)
            (d / "addon.xml").write_bytes(manifest(ident, version))
        with self.assertRaisesRegex(ValueError, "source differs"):
            stack.approve_first_party(home)

    def test_dependency_source_never_overwrites_real_rails(self):
        stage = self.home / "stage"
        stage.mkdir()
        dependency = self.home / "script.infinity.rails"
        dependency.mkdir()
        (dependency / "addon.xml").write_bytes(manifest("script.infinity.rails", "0.2.6"))
        (stage / "script.infinity.rails").mkdir()
        with self.assertRaisesRegex(ValueError, "collision"):
            stack.copy_addon(dependency, stage / "script.infinity.rails",
                             "script.infinity.rails", "0.2.6")

    def test_no_ignored_installer_errors(self):
        with self.assertRaisesRegex(ValueError, "Exact FULL ZIP unavailable"):
            stack.archive_to_stage(self.home / "missing.zip", stack.SKIN, self.home)


if __name__ == "__main__":
    unittest.main(verbosity=2)
