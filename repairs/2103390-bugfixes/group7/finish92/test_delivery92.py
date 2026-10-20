"""Build-adapter guards only. No fake Android, native-build or Fold pass."""
import copy
import importlib.util
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('delivery92_under_test', pathlib.Path(__file__).with_name('delivery92.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

class DeliveryGuards(unittest.TestCase):
    def fixture(self):
        old='1'*64; new='2'*64
        data=b'header'+b'native_engine_sha256='+old.encode()+b'\n'+b'unchanged code'
        return data,old,new,{'.rodata':(6,86)}
    def binding(self):
        pins={'a.cpp':'a'*64,'b.cpp':'b'*64};commit='c'*40
        return dict(source_commit=commit,base_source_commit=d.PRODUCER,original_source_count=9404,
            final_source_count=9404,protected_source_count=9402,all_other_sources_byte_identical=True,
            after=pins,before={'a.cpp':'d'*64,'b.cpp':'e'*64},old_group7_native_paths=list(range(8)),
            physical_fold_verified=False,final_lock=False),pins,commit
    def test_identity_only(self):
        data,a,b,sections=self.fixture();new=d.replace_recorder_field(data,a,b,sections)
        self.assertEqual(new.replace(b.encode(),a.encode(),1),data)
        self.assertEqual(len(new),len(data))
    def test_old_engine_refused(self):
        data,a,b,sections=self.fixture()
        with self.assertRaises(RuntimeError):d.replace_recorder_field(data,a,a,sections)
    def test_unknown_recorder_refused(self):
        data,a,b,sections=self.fixture()
        with self.assertRaises(RuntimeError):d.replace_recorder_field(data,'3'*64,b,sections)
    def test_duplicate_identity_refused(self):
        data,a,b,sections=self.fixture()
        with self.assertRaises(RuntimeError):d.replace_recorder_field(data+data,a,b,sections)
    def test_outside_rodata_refused(self):
        data,a,b,_=self.fixture()
        with self.assertRaises(RuntimeError):d.replace_recorder_field(data,a,b,{'.rodata':(0,3)})
    def test_invalid_hash_refused(self):
        data,a,b,sections=self.fixture()
        with self.assertRaises(RuntimeError):d.replace_recorder_field(data,a,'bad',sections)
    def test_exact_binding(self):
        report,pins,commit=self.binding();d.verify_source_binding(report,pins,commit)
    def test_incomplete_binding_refused(self):
        report,pins,commit=self.binding();report['original_source_count']=4501
        with self.assertRaises(RuntimeError):d.verify_source_binding(report,pins,commit)
    def test_unapproved_native_delta_refused(self):
        report,pins,commit=self.binding();report['after']=dict(pins,extra='x')
        with self.assertRaises(RuntimeError):d.verify_source_binding(report,pins,commit)
    def test_stale_provenance_refused(self):
        report,pins,commit=self.binding();report['source_commit']='f'*40
        with self.assertRaises(RuntimeError):d.verify_source_binding(report,pins,commit)
    def test_fake_fold_lock_refused(self):
        report,pins,commit=self.binding();report['final_lock']=True
        with self.assertRaises(RuntimeError):d.verify_source_binding(report,pins,commit)
    def test_ambiguous_input_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/'x').mkdir();(root/'y').mkdir()
            for sub in ('x','y'):(root/sub/'classes.dex').write_bytes(b'input')
            with self.assertRaises(RuntimeError):d.exact_file(root,'*.dex',d.sha(b'input'))
    def test_parent_name_same_length(self):
        self.assertEqual(len(d.OLD_NAME),len(d.NAME))
        self.assertNotEqual(d.OLD_NAME,d.NAME)

class NativeBuildLinkGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.temp.name)
        self.root = self.base / 'kodi'; self.root.mkdir()
        self.dependencies = self.base / 'verified-dependencies'; self.dependencies.mkdir()
        self.include = self.dependencies / 'include'; self.include.mkdir()
        (self.include / 'flatbuffers.h').write_bytes(b'verified dependency header')
        (self.root / 'source.cpp').write_bytes(b'protected original source')
        d.command(['git', '-C', self.root, 'init', '--quiet'])
        self.expected = {'source.cpp':d.digest(self.root / 'source.cpp')}
        self.bridge = self.root / 'tools/depends/target/flatbuffers/include'
        self.bridge.parent.mkdir(parents=True)
    def tearDown(self):
        self.temp.cleanup()
    def check(self):
        return d.native_build_inventory(self.root, self.expected, self.dependencies)
    def test_regular_sources_exact(self):
        self.assertEqual(self.check(), {})
    def test_generated_dependency_bridge_kept(self):
        self.bridge.symlink_to(self.include)
        before = self.bridge.readlink(); proof = self.check()
        self.assertEqual(self.bridge.readlink(), before)
        self.assertEqual(proof['tools/depends/target/flatbuffers/include']['target'], str(self.include))
        self.assertEqual((self.root / 'source.cpp').read_bytes(), b'protected original source')
    def test_external_bridge_rejected(self):
        outside = self.base / 'unverified'; outside.mkdir(); self.bridge.symlink_to(outside)
        with self.assertRaises(RuntimeError):self.check()
    def test_missing_bridge_target_rejected(self):
        self.bridge.symlink_to(self.dependencies / 'missing')
        with self.assertRaises(RuntimeError):self.check()
    def test_arbitrary_untracked_link_rejected(self):
        (self.root / 'invented.h').symlink_to(self.include / 'flatbuffers.h')
        with self.assertRaises(RuntimeError):self.check()
    def test_modified_source_still_rejected(self):
        self.bridge.symlink_to(self.include)
        (self.root / 'source.cpp').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):self.check()
    def test_added_source_still_rejected(self):
        (self.root / 'unexpected.cpp').write_bytes(b'extra')
        with self.assertRaises(RuntimeError):self.check()
    def test_missing_source_still_rejected(self):
        (self.root / 'source.cpp').unlink()
        with self.assertRaises(RuntimeError):self.check()
    def test_tracked_internal_link_kept(self):
        link = self.root / 'tracked.h'; link.symlink_to('source.cpp')
        d.command(['git', '-C', self.root, 'add', 'tracked.h'])
        self.expected['tracked.h'] = self.expected['source.cpp']
        self.assertEqual(self.check()['tracked.h']['origin'], 'unchanged_upstream_git_link')
    def test_changed_tracked_link_rejected(self):
        link = self.root / 'tracked.h'; link.symlink_to('source.cpp')
        d.command(['git', '-C', self.root, 'add', 'tracked.h'])
        link.unlink(); link.symlink_to(self.include / 'flatbuffers.h')
        with self.assertRaises(RuntimeError):self.check()

class SavedIntegrationInterface(unittest.TestCase):
    def test_checked_in_api_matches_delivery_adapter(self):
        release, integration, signer = d.adapters()
        for name in ('native_plan', 'bind_native', 'prepare', 'verified_stage', 'verify_addon_delta'):
            self.assertTrue(callable(getattr(integration, name)), name)
        self.assertEqual(set(integration.FINAL_NATIVE), {release.CONTRACT_PATH, release.COORDINATOR_PATH})
        self.assertEqual(len(release.CHANGED_ADDON_MEMBERS), 8)
        self.assertEqual(len(release.PACKAGES), 5)
        for name in ('native_export_compatibility', 'load_module'):
            self.assertTrue(callable(getattr(signer, name)), name)
        self.assertTrue(callable(signer.nativeidentity.elf_sections))

if __name__=='__main__':unittest.main()
