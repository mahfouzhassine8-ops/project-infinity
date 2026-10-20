"""Real signed-APK staging checks and synthetic metadata-policy regression tests.

The 9404-entry metadata fixtures are expressly synthetic: these tests do not
claim a reconstructed full Kodi tree, ARM64 compilation or Android execution.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import integration as i
import release as r

COMMIT='f98cf6b395990e6c16ddfd500b9002081afd3291'

class ActualStaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apk=Path(os.environ['INFINITY_2103391_APK'])
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.destination=cls.root/'integration'
        cls.plan=i.prepare(cls.apk,cls.destination)
        cls.stage=cls.destination/'source'

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_01_actual_signed_apk_stage_contains_all_five_matching_packages(self):
        report,expected=i.verified_stage(self.apk,self.stage)
        self.assertEqual(report['component_versions'],{a:v for a,_,v in r.PACKAGES})
        self.assertEqual(len(self.plan['required_addon_member_changes']),8)
        self.assertEqual(set(self.plan['native_paths']),i.NATIVE_PATHS)
        self.assertEqual(self.plan['java_source'],r.JAVA_PATH)
        self.assertEqual({k:r.sha(v) for k,v in expected.items()},self.plan['source_hashes'])

    def test_02_preparation_does_not_create_an_apk_dex_or_installable_zip(self):
        self.assertEqual(list(self.destination.rglob('*.apk')),[])
        self.assertEqual(list(self.destination.rglob('*.dex')),[])
        self.assertEqual(list(self.destination.rglob('*.zip')),[])
        for name in ('android_native_library_compiled','android_dex_compiled','signed_apk_created',
                     'installable_zip_set_created','physical_fold_verified','final_lock'):
            self.assertIs(self.plan[name],False)

    def test_03_already_staged_directory_is_not_overwritten(self):
        marker=self.destination/'INTEGRATION-INPUTS.json';before=marker.read_bytes()
        with self.assertRaises(i.IntegrationError): i.prepare(self.apk,self.destination)
        self.assertEqual(marker.read_bytes(),before)

    def test_04_reviewed_java_source_cannot_be_missing_or_changed(self):
        target=self.stage/'java'/r.JAVA_PATH;before=target.read_bytes()
        try:
            target.write_bytes(before+b'\n')
            with self.assertRaises(i.IntegrationError):i.verified_stage(self.apk,self.stage)
            target.unlink()
            with self.assertRaises(i.IntegrationError):i.verified_stage(self.apk,self.stage)
        finally:target.write_bytes(before)

    def test_05_post_staging_manifest_retag_is_rejected(self):
        target=self.stage/'addons'/r.CC/'addon.xml';before=target.read_bytes()
        try:
            target.write_bytes(before.replace(b'0.3.5.22',b'0.3.5.23',1))
            with self.assertRaises(i.IntegrationError):i.verified_stage(self.apk,self.stage)
        finally:target.write_bytes(before)

    def test_06_extra_staged_runtime_file_is_rejected(self):
        target=self.stage/'addons'/r.CC/'unexpected.py';target.write_bytes(b'pass\n')
        try:
            with self.assertRaises(i.IntegrationError):i.verified_stage(self.apk,self.stage)
        finally:target.unlink()

    def test_07_original_apk_unchanged_and_no_durability_policy_rewrite(self):
        self.assertEqual(r.sha(self.apk.read_bytes()),r.APK_SHA)
        old=r.original_coordinator();new=(self.stage/'native'/r.COORDINATOR_PATH).read_bytes()
        appended=b' && active["addon_version"].asString() != "0.3.5.22"'
        self.assertEqual(new.count(appended),1)
        self.assertEqual(new.replace(appended,b'',1),old)

class NativeLedgerPolicy(unittest.TestCase):
    """Synthetic metadata ONLY; no claim these fixtures are actual Kodi source."""
    def setUp(self):
        self.original={f'fixture-only/source-{n}.cpp':'1'*64 for n in range(i.EXPECTED_FILES-2)}
        self.original.update({r.CONTRACT_PATH:i.ORIGINAL_CLASSIFIER,r.COORDINATOR_PATH:r.FINAL_COORDINATOR_PREIMAGE})
        self.locked=dict(self.original)
        self.delta={'after':{},'changed':[], 'group7_extra_native_delta':[f'old-reviewed-group7-{n}' for n in range(8)],'source_commit':'7'*40}
        self.maps=[{'after':dict(self.original),'changed':[]} for _ in range(2)]

    def plan(self):return i.native_plan(self.original,self.locked,self.delta,self.maps,COMMIT)

    def test_08_only_two_native_hashes_change_all_original_ledger_objects_untouched(self):
        original=copy.deepcopy((self.original,self.locked,self.delta,self.maps))
        after,delta,maps,report=self.plan()
        self.assertEqual({n for n in after if after[n]!=self.original[n]},i.NATIVE_PATHS)
        self.assertEqual(delta['group7_extra_native_delta'],self.delta['group7_extra_native_delta'])
        self.assertEqual((self.original,self.locked,self.delta,self.maps),original)
        self.assertEqual(report['protected_source_count'],9402)
        self.assertFalse(report['native_compiled'])
        for m in maps:self.assertEqual({n for n in m['after'] if m['after'][n]!=self.original[n]},i.NATIVE_PATHS)

    def test_09_unknown_source_missing_source_and_extra_source_are_rejected(self):
        base=dict(self.original)
        for mode in ('mutated','missing','extra'):
            with self.subTest(mode=mode):
                self.original=dict(base)
                if mode=='mutated':self.original['fixture-only/source-0.cpp']='2'*64
                elif mode=='missing':del self.original['fixture-only/source-0.cpp']
                else:self.original['unapproved/new.cpp']='2'*64
                with self.assertRaises(i.IntegrationError):self.plan()
        self.original=base

    def test_10_obsolete_coordinator_and_already_patched_classifier_are_rejected(self):
        for name,wrong in ((r.COORDINATOR_PATH,'2'*64),(r.CONTRACT_PATH,r.NATIVE_PREIMAGE)):
            with self.subTest(name=name):
                original=self.original[name]
                try:
                    self.original[name]=wrong;self.locked[name]=wrong
                    for m in self.maps:m['after'][name]=wrong
                    with self.assertRaises(i.IntegrationError):self.plan()
                finally:
                    self.original[name]=original;self.locked[name]=original
                    for m in self.maps:m['after'][name]=original

    def test_11_incomplete_or_drifted_compiler_manifests_are_rejected(self):
        originals=copy.deepcopy(self.maps)
        for mode in ('missing-pin','drift','one-map'):
            self.maps=copy.deepcopy(originals)
            if mode=='missing-pin':del self.maps[0]['after'][r.CONTRACT_PATH]
            elif mode=='drift':self.maps[1]['after']['fixture-only/source-0.cpp']='a'*64
            else:self.maps.pop()
            with self.assertRaises(i.IntegrationError):self.plan()

    def test_12_original_group7_and_full_commit_identity_are_required(self):
        self.delta['group7_extra_native_delta']=[]
        with self.assertRaises(i.IntegrationError):self.plan()
        self.delta['group7_extra_native_delta']=['x']*8
        with self.assertRaises(i.IntegrationError):i.native_plan(self.original,self.locked,self.delta,self.maps,'HEAD')

class BytecodeBoundary(unittest.TestCase):
    def test_13_one_startup_class_only(self):
        old={i.TARGET_CLASS:'old','com/projectinfinity/kodi/CobraProUi.smali':'protected'}
        new=dict(old);new[i.TARGET_CLASS]='new'
        report=i.verify_dex_class_maps(old,new)
        self.assertEqual(report['protected_classes'],1)
        self.assertFalse(report['android_process_tested'])

    def test_14_missing_router_change_and_unrelated_class_changes_are_rejected(self):
        old={i.TARGET_CLASS:'old','com/projectinfinity/kodi/CobraProUi.smali':'protected'}
        for new in (dict(old),{**old,i.TARGET_CLASS:'new','com/projectinfinity/kodi/CobraProUi.smali':'changed'},
                    {i.TARGET_CLASS:'new'}, {**old,'extra.smali':'new'}):
            with self.assertRaises(i.IntegrationError):i.verify_dex_class_maps(old,new)

    def test_15_source_path_traversal_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for path in ('../file','/file','bad\\file','a//b','a/./b'):
                with self.assertRaises(i.IntegrationError):i.safe_path(root,path)
            (root/'real').mkdir();(root/'alias').symlink_to(root/'real',target_is_directory=True)
            with self.assertRaises(i.IntegrationError):i.safe_path(root,'alias/file')

if __name__=='__main__':unittest.main(verbosity=2)
