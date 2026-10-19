"""Group7 exact source-only combined delta checks, signed 2103390 parent."""
from pathlib import Path
from zipfile import ZipFile
import json,os,tempfile,unittest
import stage_all_in_one as g

APK=Path(os.environ.get("INFINITY_2103390_APK",
     "/mnt/data/Infinity-2103390-original.apk"))

@unittest.skipUnless(APK.is_file(),"Original 2103390 APK absent: never silently green")
class CombinedScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.updates,cls.additions,cls.ledger=g.staged_sources(APK)

    def test_01_original_signed_2103390_proven(self):
        self.assertEqual(g.sha(APK.read_bytes()),g.PARENT_SHA256)
        self.assertEqual(self.ledger["original_members"],7430)

    def test_02_all_approved_groups_exact_narrow_counts(self):
        self.assertEqual(self.ledger["per_group_original_counts"],
                         {"01":29,"02":42,"04":41,"06":13})
        self.assertEqual(len(self.updates),125)
        self.assertEqual(self.ledger["source_untouched_original_members"],7305)

    def test_03_group3_uses_exact_same_runtime_not_second_competing_file(self):
        runtime=g.choice.RUNTIME
        self.assertEqual(self.updates[runtime][0],"01+03")
        modified=self.updates[runtime][1]
        self.assertEqual(modified.count(b"elif action == 'home-choice':"),1)
        self.assertEqual(modified.count(b"elif action == 'option-b':"),1)
        compile(modified,runtime,"exec")

    def test_04_two_additive_first_party_modal_files_only(self):
        self.assertEqual(set(self.additions),set(g.option_stage.NEW_FILES))
        self.assertEqual(len(self.additions),2)
        self.assertTrue(all(k.startswith("assets/addons/script.infinity.uirepair/") for k in self.additions))

    def test_05_no_skipped_task19_fake_fix_or_unapproved_features(self):
        self.assertEqual(self.ledger["task19_movies_tv_reload"],"DEFERRED_UNFIXED")
        self.assertEqual(self.ledger["group5_sigsegv_139"],"ROOT_CAUSE_UNPROVEN_NOT_FIXED")
        self.assertEqual(self.ledger["new_features_after_this_release"],"FREEZE_BUGFIXES_ONLY")
        self.assertEqual(set(self.updates),{x["path"] for x in self.ledger["changes"]})

    def test_06_original_kodi_native_shutdown_cobra_remain_out_of_skin_allowlist(self):
        names=set(self.updates)|set(self.additions)
        self.assertFalse(any("cobra" in k.lower() for k in names))
        self.assertFalse(any("shutdown" in k.lower() for k in names))
        self.assertFalse(any(k.startswith(("lib/","assets/system/",
                      "assets/addons/plugin.")) for k in names))

    def test_07_serialize_xml_all_staged_only(self):
        import xml.etree.ElementTree as ET
        for k,(_,v) in self.updates.items():
            if k.endswith(".xml"):ET.fromstring(v)
        for k,v in self.additions.items():
            if k.endswith(".xml"):ET.fromstring(v)

    def test_08_refuse_reapplication_to_different_signed_apk(self):
        with tempfile.TemporaryDirectory() as t:
            bad=Path(t)/"untrusted.apk";bad.write_bytes(APK.read_bytes()[:80])
            with self.assertRaises(ValueError):g.staged_sources(bad)

    def test_09_parent_immutable_after_staging(self):
        before=g.sha(APK.read_bytes())
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/"stage"
            receipt=g.export_stage(APK,target)
            self.assertEqual(len(list(target.rglob("*.xml")))>20,True)
            self.assertEqual(receipt["source_modified_original_members"],125)
            self.assertEqual(len(json.loads((target/"GROUP7-SOURCE-SCOPE.json").read_text())["changes"]),125)
        self.assertEqual(before,g.sha(APK.read_bytes()))

    def test_10_no_signing_or_apk_claim_in_source_gate(self):
        self.assertFalse(self.ledger["signed_apk_in_this_step"])
        self.assertFalse(self.ledger["compiled_android_engine_in_this_step"])
        self.assertFalse(self.ledger["physical_fold_verified"])
if __name__=="__main__":unittest.main(verbosity=2)
