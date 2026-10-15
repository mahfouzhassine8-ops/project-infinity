import hashlib
import io
import json
import unittest
import zipfile
from unittest import mock
import test_verify_2103362 as f
import verify_2103365 as v

def payload(changed=False, unrelated=False):
    raw=f.payload(changed,unrelated)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files={n:z.read(n) for n in z.namelist()}
    manifest=json.loads(files['manifest.json'])
    for row in manifest['files']:
        row['previous']='3'*64
        if changed: row['baseline']=hashlib.sha256(('green '+row['path']).encode()).hexdigest()
    files['manifest.json']=json.dumps(manifest).encode()
    with f.archive(files) as a:return a.fp.getvalue()

class Tests(unittest.TestCase):
    def fixture(self):
        old={'AndroidManifest.xml':b'old','classes.dex':b'classes','lib/arm64-v8a/libkodi.so':b'old','assets/skin.xml':b'protected'}
        new=dict(old,**{'AndroidManifest.xml':b'new','lib/arm64-v8a/libkodi.so':b'new'})
        for n in v.ASSETS: old[n]=payload();new[n]=payload(True)
        return old,new
    def compare(self,a,b,contracts=None):
        contracts=contracts or [({'jni'},{'old'}),({'jni'},{'old'}|v.ADDED)]
        with f.archive(a) as x,f.archive(b) as y,mock.patch.object(v,'dex_contract',side_effect=contracts):return v.compare(x,y)
    def test_exact_delta(self):
        a,b=self.fixture();self.assertEqual(self.compare(a,b)['protected_entries_byte_identical'],1)
    def test_protected_skin_and_unknown_asset_refused(self):
        for key in ('assets/skin.xml','assets/unknown'):
            a,b=self.fixture();b[key]=b'changed'
            with self.assertRaises(RuntimeError):self.compare(a,b)
    def test_unrelated_code_and_bad_preimage_refused(self):
        a,b=self.fixture();b[next(iter(v.ASSETS))]=payload(True,True)
        with self.assertRaises(RuntimeError):self.compare(a,b)
        a,b=self.fixture();n=next(iter(v.ASSETS))
        with zipfile.ZipFile(io.BytesIO(b[n])) as z:files={p:z.read(p) for p in z.namelist()}
        m=json.loads(files['manifest.json']);m['files'][0]['baseline']='0'*64;files['manifest.json']=json.dumps(m).encode()
        with f.archive(files) as z:b[n]=z.fp.getvalue()
        with self.assertRaises(RuntimeError):self.compare(a,b)
    def test_jni_and_unreviewed_class_changes_refused(self):
        for contracts in ([({'jni'},{'old'}),({'other-jni'},{'old'})],
                          [({'jni'},{'old'}),({'jni'},{'old','Lunexpected/Class;'})],
                          [({'jni'},{'old'}),({'jni'},set())]):
            a,b=self.fixture()
            with self.assertRaises(RuntimeError):self.compare(a,b,contracts)

if __name__=='__main__':unittest.main()
