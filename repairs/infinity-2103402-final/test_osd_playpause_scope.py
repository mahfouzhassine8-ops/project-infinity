"""Target-only source guard for the 14 1.0.5.242 VideoOSD variants."""
from __future__ import annotations
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile
from osd_playpause_scope import MEMBERS, OLD, NEW, SKIN_SHA256, digest, patch_one, stage

ZIP = Path(os.getenv('INFINITY_2103401_SKIN_ZIP','/mnt/data/skin.infinity.diggz-1.0.5.242.zip'))
HASHES = Path(__file__).with_name('OSD-PREIMAGES.json')


class TestPlayPauseRestoration(unittest.TestCase):
    def test_pinned_archive_and_14_members(self):
        self.assertEqual(digest(ZIP.read_bytes()), SKIN_SHA256)
        with ZipFile(ZIP) as z:
            self.assertEqual({x for x in z.namelist() if x.endswith('/VideoOSD.xml')},set(MEMBERS))
            pre=json.loads(HASHES.read_text())['members']
            self.assertEqual(set(pre),set(MEMBERS))
            for m in MEMBERS:
                self.assertEqual(digest(z.read(m)),pre[m])

    def test_appearance_only_patch_each_variant(self):
        with ZipFile(ZIP) as z:
            for name in MEMBERS:
                with self.subTest(name=name):
                    original=z.read(name)
                    updated=patch_one(original)
                    self.assertNotEqual(original,updated)
                    self.assertEqual(updated.replace(NEW[0],OLD[0]).replace(NEW[1],OLD[1]),original)
                    self.assertEqual(updated.count(b'PlayerControl(Play)'),original.count(b'PlayerControl(Play)'))
                    self.assertEqual(updated.count(b'<control'),original.count(b'<control'))

    def test_fail_closed_when_target_changed(self):
        with ZipFile(ZIP) as z:
            b=z.read(MEMBERS[0])
        self.assertRaises(ValueError,patch_one,b.replace(OLD[0],b'<texturefocus>changed</texturefocus>',1))
        self.assertRaises(ValueError,patch_one,b.replace(b'id="202"',b'id="999"',1))
        self.assertRaises(ValueError,patch_one,b.replace(b'PlayerControl(Play)',b'PlayerControl(Stop)',1))

    def test_staging_never_patches_original_zip(self):
        original_digest=digest(ZIP.read_bytes())
        original_members=json.loads(HASHES.read_text())['members']
        with TemporaryDirectory() as d:
            target=Path(d)
            receipt=stage(ZIP,target,original_members)
            self.assertEqual(receipt['member_count'],14)
            self.assertFalse(receipt['signed_or_installable'])
            self.assertEqual(len(list(target.rglob('VideoOSD.xml'))),14)
            self.assertEqual(len(list(target.rglob('*.xml'))),14)
        self.assertEqual(digest(ZIP.read_bytes()),original_digest)


if __name__=='__main__':
    unittest.main(verbosity=2)
