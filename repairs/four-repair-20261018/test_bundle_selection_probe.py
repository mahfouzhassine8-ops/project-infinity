"""Run the real disposable Kodi add-on source observer without Android mocking of its ID contract."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import bundle_selection_probe as target
from package_2103388_all_in_one import IN_SCOPE


class BundleProbeTests(unittest.TestCase):
    def test_pin_exact_all_in_one_ids_with_no_transported_json_argument(self):
        tree=ast.parse(target.SCRIPT)
        assignments=[n for n in tree.body if isinstance(n,ast.Assign) and
                     any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets)]
        self.assertEqual(1,len(assignments))
        pinned=ast.literal_eval(assignments[0].value)
        self.assertEqual(sorted(IN_SCOPE),pinned)
        self.assertEqual(len(pinned),len(set(pinned)))
        self.assertNotIn('json.loads(sys.argv[2])',target.SCRIPT)
        self.assertNotIn('subprocess',target.SCRIPT)
        self.assertNotIn('shutil',target.SCRIPT)

    def test_real_script_publishes_all_verified_component_manifests(self):
        tree=ast.parse(target.SCRIPT)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            locations={}
            for id,version in IN_SCOPE.items():
                p=root/'apk-assets'/id
                p.mkdir(parents=True)
                payload=('<addon id="'+id+'" version="'+(version or '1.0.0')+'" />').encode()
                (p/'addon.xml').write_bytes(payload)
                locations[id]=(str(p),version or '1.0.0',hashlib.sha256(payload).hexdigest())
            module=types.ModuleType('xbmcaddon')
            class Addon:
                def __init__(self,id): self.id=id
                def getAddonInfo(self,key):
                    return locations[self.id][0] if key=='path' else locations[self.id][1]
            module.Addon=Addon
            vfs=types.ModuleType('xbmcvfs')
            path=root/'infinity-all-in-one-selected.json'
            vfs.translatePath=lambda p: str(path) if p.startswith('special://profile/') else p
            with patch.dict(sys.modules,{'xbmcaddon':module,'xbmcvfs':vfs}),patch.object(sys,'argv',['default.py','proof-owner']):
                exec(compile(target.SCRIPT,'bundled-addon-proof','exec'),{})
            result=json.loads(path.read_text())
            self.assertEqual('proof-owner',result['owner'])
            self.assertEqual(set(IN_SCOPE),set(result['addons']))
            self.assertTrue(all(result['addons'][k].get('addon_xml_exists') for k in IN_SCOPE))
            for k,(_,version,digest) in locations.items():
                self.assertEqual(digest,result['addons'][k]['addon_xml_sha256'])
                self.assertEqual(version,result['addons'][k]['version'])

    def test_missing_owner_fails_before_any_mutation(self):
        with self.assertRaisesRegex(ValueError,'Missing exact Kodi owner'):
            with patch.object(sys,'argv',['default.py']):
                fake=types.ModuleType('xbmcvfs')
                fake.translatePath=lambda x: '/tmp/NOT_REAL'
                with patch.dict(sys.modules,{'xbmcvfs':fake,'xbmcaddon':types.ModuleType('xbmcaddon')}):
                    exec(compile(target.SCRIPT,'bundled-addon-proof','exec'),{})

    def test_staged_helper_is_not_copied_to_distributed_apk(self):
        with tempfile.TemporaryDirectory() as td:
            result=target.stage(td)
            self.assertEqual(target.PROBE_ID,result.name)
            self.assertEqual(target.SCRIPT,(result/'default.py').read_text())
            self.assertIn('Never shipped to users',(result/'addon.xml').read_text())


if __name__=='__main__':
    unittest.main()
