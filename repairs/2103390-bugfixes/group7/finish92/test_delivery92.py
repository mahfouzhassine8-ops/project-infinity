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

if __name__=='__main__':unittest.main()
