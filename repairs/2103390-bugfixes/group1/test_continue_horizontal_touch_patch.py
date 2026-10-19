"""Signed 2103390 host tests; never claim physical Fold gesture proof."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from continue_horizontal_touch_patch import (PREIMAGE_SHA256, TARGET, CONTROL_IDS,
                                               digest, patch_bytes, stage,
                                               ORIGINAL_LAYOUT, FIXED_LAYOUT)

APK = Path('/mnt/data/integrated-2103390/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk')
EXPECTED_PARENT='778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'
PREFIX='assets/addons/skin.infinity.diggz/'

@unittest.skipUnless(APK.is_file(),'Original signed 2103390 APK required')
class DefaultFoldContinueHorizontal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apksrc=APK.read_bytes()
        assert digest(cls.apksrc)==EXPECTED_PARENT, 'signed parent SHA differs'
        with ZipFile(BytesIO(cls.apksrc)) as z:
            cls.names=z.namelist()
            cls.original=z.read(TARGET)
            cls.reference=z.read(PREFIX+'16x9/Home.xml')
            cls.other_homes={n:z.read(n) for n in cls.names if n.startswith(PREFIX) and n.endswith('/Home.xml') and n != TARGET}
            cls.skin_manifest=z.read(PREFIX+'addon.xml')

    def test_actual_default_9_20_folder_is_unified(self):
        self.assertIn(b'<res width="1080" height="2400" aspect="9:20" default="true" folder="unified"', self.skin_manifest)
        self.assertEqual(len(self.other_homes),13)
        self.assertEqual(digest(self.original), PREIMAGE_SHA256)

    def test_both_original_default_hitboxes_are_non_numeric(self):
        r=ET.fromstring(self.original)
        for ident in CONTROL_IDS:
            p=r.find('.//control[@id="'+ident+'"]')
            self.assertEqual(p.findtext('orientation'),'horizontal')
            for kind in ('itemlayout','focusedlayout'):
                self.assertEqual(p.find(kind).get('width'),'auto')
                self.assertRaises(ValueError,float,p.find(kind).get('width'))
                self.assertEqual(p.find(kind).get('height'),'97.619048%')

    def test_fix_uses_exact_pre_existing_other_layout_card_measurements(self):
        reference=ET.fromstring(self.reference)
        after=ET.fromstring(patch_bytes(self.original))
        for ident in CONTROL_IDS:
            r=reference.find('.//control[@id="'+ident+'"]')
            x=after.find('.//control[@id="'+ident+'"]')
            for tag in ('itemlayout','focusedlayout'):
                self.assertEqual(x.find(tag).get('width'),r.find(tag).get('width'))
                self.assertEqual(x.find(tag).get('height'),r.find(tag).get('height'))
                self.assertEqual((float(x.find(tag).get('width')),float(x.find(tag).get('height'))),(230.1,410.0))
            self.assertEqual(x.findtext('content'),ET.fromstring(self.original).find('.//control[@id="'+ident+'"]' ).findtext('content'))
            self.assertEqual(x.findtext('visible'),ET.fromstring(self.original).find('.//control[@id="'+ident+'"]' ).findtext('visible'))

    def test_exact_four_tag_byte_only_delta_no_other_panel_or_asset(self):
        after=patch_bytes(self.original)
        self.assertEqual(after,self.original.replace(ORIGINAL_LAYOUT,FIXED_LAYOUT,4))
        self.assertEqual(self.original.count(ORIGINAL_LAYOUT),4)
        self.assertEqual(after.count(FIXED_LAYOUT),4)
        self.assertEqual(len(self.other_homes),13)
        self.assertEqual(len(self.names),7430)
        # Preserves every other Home control, category route, art or provider
        self.assertEqual(after.replace(FIXED_LAYOUT,ORIGINAL_LAYOUT),self.original)

    def test_refuse_mutated_preimage_and_repeat_patch(self):
        with self.assertRaises(ValueError):patch_bytes(self.original+b' ')
        with self.assertRaises(ValueError):patch_bytes(patch_bytes(self.original))

    def test_original_safe_staging_proof(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'original.xml';dst=Path(td)/'staged.xml';src.write_bytes(self.original)
            with self.assertRaises(ValueError):stage(src,src)
            old,new=stage(src,dst)
            self.assertEqual(old, PREIMAGE_SHA256)
            self.assertEqual(new,digest(dst.read_bytes()))
            self.assertEqual(src.read_bytes(),self.original)
            self.assertNotEqual(src.read_bytes(),dst.read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
