"""Group #1 task 04: real 2103390 skin-asset byte-level conservation tests."""
from pathlib import Path
import os
import tempfile
import unittest
import zipfile

from clock_orb_patch import BEFORE, OLD, NEW, family, modify, patch_archive

SOURCE = Path(os.environ.get("INFINITY_2103390_SKIN_ZIP", "/mnt/data/skin.infinity.diggz-1.0.5.228-from-Infinity-2103390.zip"))


class ClockOrbTests(unittest.TestCase):
    @unittest.skipUnless(SOURCE.exists(), "exact 2103390 skin asset required")
    def test_only_orb_anchor_moves_in_all_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate.zip"
            summary = patch_archive(SOURCE, candidate)
            self.assertEqual(len(summary["changed_members"]), 10)
            self.assertEqual(summary["source_members"], summary["unchanged_members"] + 10)
            with zipfile.ZipFile(SOURCE) as before, zipfile.ZipFile(candidate) as after:
                self.assertEqual(before.namelist(), after.namelist())
                for name in before.namelist():
                    old = before.read(name)
                    new = after.read(name)
                    if family(name):
                        self.assertEqual(new, old.replace(OLD, NEW, 1), name)
                        self.assertEqual(new.count(NEW), 1)
                        self.assertEqual(new.count(OLD), 0)
                        self.assertEqual(new.count(BEFORE), 1)
                    else:
                        self.assertEqual(old, new, "Unrelated ZIP member changed: " + name)
            with self.assertRaises(ValueError):
                patch_archive(candidate, Path(tmp) / "second-pass.zip")

    @unittest.skipUnless(SOURCE.exists(), "exact 2103390 skin asset required")
    def test_does_not_modify_original_source_or_add_controls(self):
        with zipfile.ZipFile(SOURCE) as z:
            data = z.read("skin.infinity.diggz/16x9/Includes_InfinityHomeUnified.xml")
            before_controls = data.count(b"<control ")
            changed = modify("skin.infinity.diggz/16x9/Includes_InfinityHomeUnified.xml", data)
            self.assertEqual(changed.count(b"<control "), before_controls)
            self.assertEqual(changed.count(b"<label>"), data.count(b"<label>"))
            self.assertEqual(changed.count(b"<texture"), data.count(b"<texture"))
            self.assertEqual(data.count(b'<left>$PARAM[timeleft]</left>'), 2)
            self.assertEqual(changed.count(b'<left>$PARAM[timeleft]</left>'), 1)
            self.assertEqual(changed.count(b"<left>708</left>"), 1)
            self.assertEqual(data.count(b'<label>$INFO[System.Time]</label>'), changed.count(b'<label>$INFO[System.Time]</label>'))


if __name__ == "__main__":
    unittest.main()
