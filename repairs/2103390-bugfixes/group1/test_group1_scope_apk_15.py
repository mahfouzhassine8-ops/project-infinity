"""Fail-closed 15-file virtual Group #1 integration, original signed 2103390 APK."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import unittest
from zipfile import ZipFile

from cc_preimage_contract_patch import CONSUMERS, CONTRACT_NAME, updated_contract
from clock_orb_patch import family, modify
from continue_horizontal_touch_patch import patch_bytes as touch_patch, TARGET as TOUCH_TARGET
from movie_identity_patch import patch_bytes as movie_patch
from tv_episode_route_patch import patch_bytes as episode_patch

APK=Path('/mnt/data/integrated-2103390/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk')
CC='assets/addons/script.infinity.commandcenter/'
PREFIX='assets/addons/'

@unittest.skipUnless(APK.is_file(),'Original signed 2103390 APK required')
class OnlyGroupOneScopedChanges(unittest.TestCase):
    def test_only_fifteen_original_members_may_change_and_all_dependencies_pass(self):
        from hashlib import sha256
        parent=APK.read_bytes()
        self.assertEqual(sha256(parent).hexdigest(),
                         '778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb')
        with ZipFile(BytesIO(parent)) as z:
            names=z.namelist()
            self.assertEqual(len(names),7430)
            self.assertEqual(len(set(names)),7430)
            plugin=z.read(CC+'plugin.py');hub=z.read(CC+'resume_hub.py')
            changed={}
            for member in names:
                old=z.read(member)
                if member==CC+'plugin.py':
                    new=episode_patch(old)
                elif member==CC+'resume_hub.py':
                    new=movie_patch(old)
                elif member in (PREFIX+consumer+'/'+CONTRACT_NAME for consumer in CONSUMERS):
                    new=updated_contract(old,plugin,hub)
                elif member.startswith(PREFIX+'skin.infinity.diggz/') and family(member[len(PREFIX):]):
                    new=modify(member[len(PREFIX):],old)
                elif member==TOUCH_TARGET:
                    new=touch_patch(old)
                else:
                    new=old
                if new != old:
                    changed[member]=(sha256(old).hexdigest(),sha256(new).hexdigest())
            self.assertEqual(len(changed),15,sorted(changed))
            self.assertEqual(len(names)-len(changed),7415)
            self.assertEqual(sum(n.endswith('Includes_InfinityHomeUnified.xml') for n in changed),10)
            self.assertEqual(sum(n.endswith('/CONTROLLER-PREIMAGES.json') for n in changed),2)
            self.assertIn(TOUCH_TARGET,changed)
            self.assertEqual({x for x in changed if x.endswith('.py')},
                             {CC+'plugin.py',CC+'resume_hub.py'})
            self.assertFalse(any('cobra' in n.lower() or 'shutdown' in n.lower() or 'versioncheck' in n.lower()
                                 or n.startswith('lib/') or n.endswith('controller_access.py')
                                 or n.endswith('script.infinity.watchedbridge/controller.py') for n in changed))

if __name__=='__main__':unittest.main(verbosity=2)
