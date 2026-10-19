"""Group #1 signed-base read-only audit: ONLY staged 11 APK members may change."""
from pathlib import Path
from io import BytesIO
import os
import unittest
from zipfile import ZipFile

from clock_orb_patch import modify, family
from movie_identity_patch import patch_bytes

PARENT=Path(os.environ.get('INFINITY_2103390_ARTIFACT_ZIP','/mnt/data/Infinity-2103390-Combined-Build-Artifact.zip'))
HUB='assets/addons/script.infinity.commandcenter/resume_hub.py'
SKIN='assets/addons/'

class ExactCombinedGroup1Scope(unittest.TestCase):
    @unittest.skipUnless(PARENT.is_file(),'real signed 2103390 APK required')
    def test_whole_apk_member_inventory_and_prohibited_files(self):
        with ZipFile(PARENT) as outer:
            apkname=next(n for n in outer.namelist() if n.endswith('.apk'))
            with ZipFile(BytesIO(outer.read(apkname))) as apk:
                names=apk.namelist()
                self.assertEqual(len(names),7430)
                diff=[]
                for name in names:
                    source=apk.read(name)
                    if name==HUB:
                        patched=patch_bytes(source)
                    elif name.startswith(SKIN) and family(name[len(SKIN):]):
                        patched=modify(name[len(SKIN):],source)
                    else:
                        patched=source
                    if patched!=source:
                        diff.append(name)
                    else:
                        self.assertEqual(source,patched)
                self.assertEqual(len(diff),11)
                self.assertIn(HUB,diff)
                self.assertEqual(sum(name.startswith(SKIN+'skin.infinity.diggz/') for name in diff),10)
                self.assertFalse(any('cobra' in name.lower() for name in diff))
                self.assertFalse(any(name.startswith('lib/') or 'native' in name.lower() for name in diff))
                self.assertFalse(any('shutdown' in name.lower() or 'versioncheck' in name.lower() for name in diff))
                self.assertTrue(all(name==HUB or name.endswith('/Includes_InfinityHomeUnified.xml') for name in diff))

if __name__=='__main__':unittest.main()
