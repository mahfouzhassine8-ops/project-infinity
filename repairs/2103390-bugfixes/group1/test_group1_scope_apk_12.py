"""Strict full 2103390 signed APK dry-run: three source patches, 12 of 7430 only."""
from io import BytesIO
import os
from pathlib import Path
import unittest
from zipfile import ZipFile
from clock_orb_patch import modify, family
from movie_identity_patch import patch_bytes as movie_patch
from tv_episode_route_patch import patch_bytes as episode_patch

PARENT=Path(os.environ.get('INFINITY_2103390_ARTIFACT_ZIP','/mnt/data/Infinity-2103390-Combined-Build-Artifact.zip'))
HUB='assets/addons/script.infinity.commandcenter/resume_hub.py'
PLUGIN='assets/addons/script.infinity.commandcenter/plugin.py'
SKIN='assets/addons/'

class ExactCombinedGroup1Scope12(unittest.TestCase):
    @unittest.skipUnless(PARENT.is_file(),'exact 2103390 artifact required')
    def test_only_twelve_allowed_original_members_change(self):
        with ZipFile(PARENT) as outer:
            name=next(n for n in outer.namelist() if n.endswith('.apk'))
            with ZipFile(BytesIO(outer.read(name))) as apk:
                names=apk.namelist()
                self.assertEqual(len(names),7430)
                self.assertEqual(len(set(names)),len(names))
                changed=[]
                for member in names:
                    original=apk.read(member)
                    if member==HUB:
                        after=movie_patch(original)
                    elif member==PLUGIN:
                        after=episode_patch(original)
                    elif member.startswith(SKIN) and family(member[len(SKIN):]):
                        after=modify(member[len(SKIN):],original)
                    else:
                        after=original
                    if after!=original: changed.append(member)
                    else: self.assertEqual(after,original,member)
                self.assertEqual(len(changed),12)
                self.assertEqual(set(changed)-{HUB,PLUGIN},
                    {member for member in names if member.startswith(SKIN) and family(member[len(SKIN):])})
                self.assertFalse(any('cobra' in v.lower() or v.startswith('lib/') or 'versioncheck' in v.lower() or 'shutdown' in v.lower() for v in changed))

if __name__=='__main__':unittest.main()
