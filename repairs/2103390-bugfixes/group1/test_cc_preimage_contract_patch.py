"""Host-only full signed 2103390 compatibility audit for Group #1 staged source."""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from cc_preimage_contract_patch import (
    CONTRACT_NAME, CONSUMERS, ORIGINAL, PINNED_NAMES, STAGED,
    digest, patch_both, updated_contract,
)
from clock_orb_patch import family, modify
from movie_identity_patch import patch_bytes as movie_patch
from tv_episode_route_patch import patch_bytes as episode_patch

PARENT = Path(os.environ.get('INFINITY_2103390_ARTIFACT_ZIP',
        '/mnt/data/Infinity-2103390-Combined-Build-Artifact.zip'))
CC = 'assets/addons/script.infinity.commandcenter/'
PIN_PREFIX = 'assets/addons/'
SIGN_BASE_SHA256 = '778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'


@unittest.skipUnless(PARENT.is_file(), 'Full original signed 2103390 artifact required')
class DualPinnedConsumerSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(PARENT) as outer:
            apk_names = [x for x in outer.namelist() if x.endswith('.apk')]
            if len(apk_names) != 1:
                raise AssertionError('Expected one original signed 2103390 APK')
            cls.payload = outer.read(apk_names[0])
        assert digest(cls.payload) == SIGN_BASE_SHA256, 'Refusing a different signed parent'
        cls.apk = ZipFile(BytesIO(cls.payload))
        cls.names = cls.apk.namelist()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'apk'):
            cls.apk.close()

    def original(self, path):
        return self.apk.read(path)

    def data(self):
        plugin = self.original(CC + 'plugin.py')
        hub = self.original(CC + 'resume_hub.py')
        pins = [self.original(f'{PIN_PREFIX}{consumer}/{CONTRACT_NAME}')
                for consumer in CONSUMERS]
        return plugin, hub, pins

    def test_both_consumers_have_same_exact_pins_and_retain_all_thirteen(self):
        plugin, hub, pins = self.data()
        self.assertEqual(len(pins), 2)
        self.assertEqual(pins[0], pins[1])
        self.assertEqual(digest(plugin), ORIGINAL['plugin.py'])
        self.assertEqual(digest(hub), ORIGINAL['resume_hub.py'])
        expected = json.loads(pins[0])
        self.assertEqual(len(expected), 13)
        for key, sha in expected.items():
            self.assertEqual(digest(self.original(CC + key)), sha)
        # Both shipping consumers actually use the map to check every source.
        self.assertIn("CONTROLLER-PREIMAGES.json", self.original(
            'assets/addons/script.infinity.uirepair/controller_access.py').decode())
        self.assertIn('for name, wanted in expected.items():', self.original(
            'assets/addons/script.infinity.watchedbridge/controller.py').decode())

    def test_staged_sources_current_guards_fail_but_both_new_guards_succeed(self):
        plugin, hub, pins = self.data()
        final_plugin, final_hub = episode_patch(plugin), movie_patch(hub)
        self.assertEqual(digest(final_plugin), STAGED['plugin.py'])
        self.assertEqual(digest(final_hub), STAGED['resume_hub.py'])
        self.assertNotEqual(json.loads(pins[0])['plugin.py'], digest(final_plugin))
        self.assertNotEqual(json.loads(pins[0])['resume_hub.py'], digest(final_hub))
        for pinned in pins:
            fixed = updated_contract(pinned, plugin, hub)
            mapping = json.loads(fixed)
            original = json.loads(pinned)
            self.assertEqual(set(mapping), set(original))
            for name in original:
                contents = final_plugin if name == 'plugin.py' else (
                    final_hub if name == 'resume_hub.py' else self.original(CC + name))
                self.assertEqual(mapping[name], digest(contents), name)
            for name in original.keys() - PINNED_NAMES:
                self.assertEqual(original[name], mapping[name])
            self.assertEqual(fixed.count(STAGED['plugin.py'].encode()), 1)
            self.assertEqual(fixed.count(STAGED['resume_hub.py'].encode()), 1)

    def test_hash_guard_fail_closed_for_mutations_to_originals(self):
        plugin, hub, pins = self.data()
        with self.assertRaises(ValueError): updated_contract(pins[0] + b' ', plugin, hub)
        with self.assertRaises(ValueError): updated_contract(pins[0], plugin + b'\n', hub)
        with self.assertRaises(ValueError): updated_contract(pins[0], plugin, hub + b'\n')
        with self.assertRaises(ValueError): updated_contract(
            updated_contract(pins[0], plugin, hub), plugin, hub)

    def test_refuses_original_overwrite_and_stages_matching_json_to_two_consumers(self):
        plugin, hub, pins = self.data()
        with tempfile.TemporaryDirectory(prefix='infinity_group1_contract_') as temp:
            root = Path(temp) / 'original' / 'assets' / 'addons'
            targets = Path(temp) / 'candidate' / 'assets' / 'addons'
            (root / 'script.infinity.commandcenter').mkdir(parents=True)
            (root / 'script.infinity.commandcenter/plugin.py').write_bytes(plugin)
            (root / 'script.infinity.commandcenter/resume_hub.py').write_bytes(hub)
            for aid, value in zip(CONSUMERS, pins):
                (root / aid).mkdir(parents=True)
                (root / aid / CONTRACT_NAME).write_bytes(value)
            with self.assertRaises(ValueError): patch_both(root, root)
            hashes = patch_both(root, targets)
            self.assertEqual(set(hashes), set(CONSUMERS))
            for consumer in CONSUMERS:
                self.assertEqual(digest((targets / consumer / CONTRACT_NAME).read_bytes()), hashes[consumer])
                self.assertEqual((root / consumer / CONTRACT_NAME).read_bytes(), pins[0])

    def test_fourteen_member_virtual_apk_inventory_and_no_other_changes(self):
        plugin, hub, pins = self.data()
        self.assertEqual(len(self.names), 7430)
        self.assertEqual(len(self.names), len(set(self.names)))
        allow = {CC + 'plugin.py', CC + 'resume_hub.py'}
        allow.update(f'{PIN_PREFIX}{consumer}/{CONTRACT_NAME}' for consumer in CONSUMERS)
        changed = []
        for filename in self.names:
            old = self.original(filename)
            if filename == CC + 'plugin.py':
                new = episode_patch(old)
            elif filename == CC + 'resume_hub.py':
                new = movie_patch(old)
            elif filename in allow:
                new = updated_contract(old, plugin, hub)
            elif filename.startswith('assets/addons/skin.infinity.diggz/') and family(filename[len(PIN_PREFIX):]):
                new = modify(filename[len(PIN_PREFIX):], old)
                allow.add(filename)
            else:
                new = old
            if new != old:
                changed.append(filename)
            else:
                self.assertEqual(new, old)
        self.assertEqual(len(changed), 14)
        self.assertEqual(set(changed), allow)
        self.assertEqual(len(self.names) - len(changed), 7416)
        self.assertFalse(any('cobra' in name.lower() or '/shutdown' in name.lower()
                or 'versioncheck' in name.lower() or name.startswith('lib/')
                for name in changed))

if __name__ == '__main__':
    unittest.main(verbosity=2)
