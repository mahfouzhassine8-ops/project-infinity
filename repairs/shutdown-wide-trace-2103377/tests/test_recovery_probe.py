import importlib.util,json,os,sys,tempfile,unittest,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'recovery-probe'
sys.path.insert(0,str(HERE));import collector
class RecoveryProbeTest(unittest.TestCase):
    def test_private_data_removed(self):
        original={'schema':1,'phase':'vfs.shutdown.request','backend_category':'curl','operation_id':42,
          'url':'https://private.example/?password=PRIVATE_SECRET','credentials':'PRIVATE_SECRET',
          'outcome':'PRIVATE_SECRET','owner_kind':'PRIVATE_SECRET','target_thread':'PRIVATE_SECRET',
          'addon_id':'PRIVATE_SECRET'}
        s=json.dumps(collector.filtered_row(original))
        self.assertNotIn('PRIVATE_SECRET',s);self.assertNotIn('private.example',s)
        self.assertIn('vfs.shutdown.request',s);self.assertIn('curl',s)
    def test_full_trace_after_two_megabyte_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/collector.NATIVE_FILES[0]
            row=json.dumps({'schema':1,'phase':'vfs.open.return','operation_id':1})+'\n'
            p.write_text(row*40000+json.dumps({'phase':'python.exit_frame','target_thread':'12:service.py:28:refresh_playlist'})+'\n')
            self.assertGreater(p.stat().st_size,2*1024*1024)
            data,info=collector.read_native(d,p.name)
            self.assertEqual(info['filtered_rows'],40001)
            self.assertIn(b'refresh_playlist',data);self.assertFalse(info['changed_during_read'])
    def test_no_unrelated_or_linked_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'secret').write_text('PRIVATE_SECRET')
            (p/collector.NATIVE_FILES[0]).symlink_to(p/'secret')
            with self.assertRaises(OSError):collector.read_native(d,collector.NATIVE_FILES[0])
            with self.assertRaises(Exception):collector.read_native(d,'secret')
    def test_missing_evidence_stays_unknown_and_originals_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            before=os.listdir(d);path=collector.export(d,{},d)
            with zipfile.ZipFile(path) as z:
                report=json.loads(z.read('recovery.json'))
                self.assertFalse(report['shutdown_repaired'])
                self.assertEqual(len(report['source_identity']),8)
                self.assertTrue(all(x['status']=='allowlisted_trace_unavailable' for x in report['native_files'].values()))
            self.assertEqual(len(os.listdir(d)),len(before)+1)
if __name__=='__main__':unittest.main()
