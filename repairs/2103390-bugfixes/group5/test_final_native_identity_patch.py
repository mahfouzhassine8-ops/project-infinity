"""Group5 signed-original native crash identity, fail-closed host tests."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import os
import tempfile
import unittest
import final_native_identity_patch as g

APK=Path(os.environ.get("INFINITY_2103390_APK",
      "/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk"))


@unittest.skipUnless(APK.is_file(),"Signed 2103390 required")
class NativeIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pkg=ZipFile(APK)
        cls.engine=cls.pkg.read(g.LIBKODI)
        cls.recorder=cls.pkg.read(g.RECORDER)

    @classmethod
    def tearDownClass(cls):cls.pkg.close()

    def test_01_actual_2103390_signed_hash_and_preimages(self):
        self.assertEqual(g.sha(APK.read_bytes()),g.BASE_APK_SHA)
        self.assertEqual(len(self.pkg.namelist()),7430)
        self.assertEqual(g.sha(self.engine),g.BASE_PACKAGED_ENGINE_SHA)
        self.assertEqual(g.sha(self.recorder),g.BASE_RECORDER_SHA)
        self.assertEqual(self.recorder.count(g.FIELD),1)

    def test_02_stale_2103229_fingerprint_not_loaded_engine(self):
        self.assertNotEqual(g.BASE_PACKAGED_ENGINE_SHA,g.HISTORICAL_ENGINE_SHA)
        self.assertIn(g.HISTORICAL_ENGINE_SHA.encode('ascii'),self.recorder)
        self.assertEqual(g.patch(self.engine,self.recorder).count(g.FIELD),0)

    def test_03_deterministic_patch_full_sha_matches_engine(self):
        patched=g.patch(self.engine,self.recorder)
        self.assertEqual(len(patched),len(self.recorder))
        expected=b"native_engine_sha256="+g.sha(self.engine).encode()+b"\n"
        self.assertIn(expected,patched)
        self.assertEqual(patched.count(expected),1)
        self.assertEqual(patched.replace(expected,g.FIELD),self.recorder)
        self.assertNotIn(g.FIELD,patched)

    def test_04_actual_executable_text_section_identity(self):
        a=g.elf_sections(self.engine)
        off,size=a['.text']
        self.assertGreater(off,0)
        self.assertGreater(size,1000)
        result=g.receipt(self.engine,self.recorder)
        self.assertEqual(result['final_native_engine_sha256'],g.BASE_PACKAGED_ENGINE_SHA)
        self.assertEqual(result['final_native_text_sha256'],hashlib.sha256(self.engine[off:off+size]).hexdigest())
        self.assertFalse(result['crash_root_cause_proven'])
        self.assertTrue(result['crash_symbol_mapping_requires_runtime_maps'])

    def test_05_final_rebuild_fingerprint_is_not_hardcoded_2103390(self):
        changed=bytearray(self.engine)
        # Modify a non-executable padding byte; file remains original ELF shape.
        changed[300]^=1
        native=bytes(changed)
        expected=g.sha(native)
        self.assertNotEqual(expected,g.BASE_PACKAGED_ENGINE_SHA)
        self.assertIn(expected.encode(),g.patch(native,self.recorder))
        self.assertNotIn(g.BASE_PACKAGED_ENGINE_SHA.encode(),g.patch(native,self.recorder))
        # Native symbol mapping does not magically become available from SHA.
        self.assertFalse(g.receipt(native,self.recorder)['root_cause_fix_implemented'])

    def test_06_same_size_rodata_only_no_code_change(self):
        after=g.patch(self.engine,self.recorder)
        start=self.recorder.index(g.FIELD)
        self.assertEqual(self.recorder[:start],after[:start])
        self.assertEqual(self.recorder[start+len(g.FIELD):],after[start+len(g.FIELD):])
        self.assertEqual(len(after),len(self.recorder))
        self.assertEqual(g.elf_sections(after)['.text'],g.elf_sections(self.recorder)['.text'])

    def test_07_wrong_signer_parent_and_unknown_crash_collector_fail(self):
        with tempfile.TemporaryDirectory() as t:
            wrong=Path(t)/'unknown.apk'
            wrong.write_bytes(APK.read_bytes()[:100])
            with self.assertRaises(ValueError):g.staged_inventory(wrong)
        with self.assertRaises(ValueError):g.patch(self.engine,self.recorder+b'a')

    def test_08_do_not_package_protected_cobra_or_shutdown(self):
        receipt=g.staged_inventory(APK)
        self.assertEqual(receipt['changed_apk_members_if_staged'],[g.RECORDER])
        self.assertFalse(receipt['original_native_engine_modified'])
        self.assertFalse(receipt['root_cause_fix_implemented'])
        self.assertFalse(receipt['actual_apk_built'])
        self.assertFalse(receipt['fold_verified'])

    def test_09_native_elf_bad_arch_rejected(self):
        bad=bytearray(self.engine)
        bad[0]=0
        with self.assertRaises(ValueError):g.elf_sections(bytes(bad))
        bad=bytearray(self.engine);bad[0x12]=0
        with self.assertRaises(ValueError):g.elf_sections(bytes(bad))

    def test_10_separate_stage_does_not_modify_original_signed_base(self):
        before=g.sha(APK.read_bytes())
        with tempfile.TemporaryDirectory() as t:
            dest=Path(t)/'stage'
            data=g.stage(APK,dest)
            target=dest/g.RECORDER
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(),g.patch(self.engine,self.recorder))
            self.assertEqual(data['collector_field_after'],g.BASE_PACKAGED_ENGINE_SHA)
            self.assertRaises(ValueError,g.stage,APK,APK.parent)
        self.assertEqual(before,g.sha(APK.read_bytes()))

if __name__=="__main__":unittest.main(verbosity=2)
