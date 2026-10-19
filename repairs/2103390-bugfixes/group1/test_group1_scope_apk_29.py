"""Exact original signed 2103390 member gate: Group #1 only, 29 of 7,430.

Run alongside the prior 19-, 17-, and dual-controller tests. This is an
IN-MEMORY scope gate, not a signed APK/build test or Fold validation.
"""
from __future__ import annotations
from io import BytesIO
import hashlib
import os
from pathlib import Path
import unittest
from zipfile import ZipFile

from clock_orb_patch import family, modify
from movie_identity_patch import patch_bytes as movie_patch
from tv_episode_route_patch import patch_bytes as tv_patch
from cc_preimage_contract_patch import updated_contract, CONSUMERS, CONTRACT_NAME
from continue_horizontal_touch_patch import (
    TARGET as NUMERIC_HOME, patch_bytes as numeric_home_patch,
    ORIGINAL_LAYOUT, FIXED_LAYOUT)
from continue_choice_patch import (
    RUNTIME, home_type, patch_home, patch_runtime)

PARENT = Path(os.environ.get('INFINITY_2103390_APK',
                            '/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk'))
SHA = '778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'
CC = 'assets/addons/script.infinity.commandcenter/'
AD = 'assets/addons/'

@unittest.skipUnless(PARENT.is_file(), 'Exact signed APK not available: no pass claim allowed')
class GroupOneExact29MemberGate(unittest.TestCase):
    def test_exactly_29_allowed_members_no_unrelated_delta(self):
        parent = PARENT.read_bytes()
        self.assertEqual(hashlib.sha256(parent).hexdigest(), SHA)
        with ZipFile(BytesIO(parent)) as apk:
            names = apk.namelist()
            self.assertEqual(len(names), 7430)
            self.assertEqual(len(set(names)), 7430)
            plugin = apk.read(CC + 'plugin.py')
            hub = apk.read(CC + 'resume_hub.py')
            changed = {}
            for member in names:
                before = apk.read(member)
                after = before
                if home_type(member):
                    after = patch_home(member, before)
                    if member == NUMERIC_HOME:
                        independently_verified = numeric_home_patch(before)
                        self.assertEqual(independently_verified,
                                         before.replace(ORIGINAL_LAYOUT, FIXED_LAYOUT, 4))
                        self.assertEqual(after.count(ORIGINAL_LAYOUT), 4)
                        after = after.replace(ORIGINAL_LAYOUT, FIXED_LAYOUT, 4)
                elif member == RUNTIME:
                    after = patch_runtime(before)
                elif member == CC + 'plugin.py':
                    after = tv_patch(before)
                elif member == CC + 'resume_hub.py':
                    after = movie_patch(before)
                elif member in {AD + c + '/' + CONTRACT_NAME for c in CONSUMERS}:
                    after = updated_contract(before, plugin, hub)
                elif member.startswith(AD) and family(member[len(AD):]):
                    after = modify(member[len(AD):], before)
                if after != before:
                    changed[member] = (hashlib.sha256(before).hexdigest(),
                                       hashlib.sha256(after).hexdigest())
            self.assertEqual(len(changed), 29, sorted(changed))
            self.assertEqual(7430 - len(changed), 7401)
            self.assertEqual(sum(bool(home_type(n)) for n in changed), 14)
            self.assertEqual(sum(n.endswith('Includes_InfinityHomeUnified.xml') for n in changed), 10)
            self.assertEqual(sum(n.endswith('/CONTROLLER-PREIMAGES.json') for n in changed), 2)
            self.assertEqual({n for n in changed if n.endswith('.py')},
                             {CC + 'plugin.py', CC + 'resume_hub.py', RUNTIME})
            self.assertFalse(any('cobra' in n.lower() or 'shutdown' in n.lower()
                    or 'versioncheck' in n.lower() or n.startswith('lib/')
                    or n.startswith('assets/addons/plugin.video.') for n in changed),
                    sorted(changed))

if __name__ == '__main__':
    unittest.main(verbosity=2)
