import copy,hashlib,io,json,unittest,zipfile
from unittest import mock
import verify_2103362 as v

def archive(data):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w') as z:
  for n,b in data.items():z.writestr(n,b)
 return zipfile.ZipFile(io.BytesIO(out.getvalue()))
def payload(next=False,unrelated=False):
 names=['service.py','plugin.py','resume_hub.py','common.py'];rows=[];files={}
 for n in names:
  prior=('green '+n).encode();raw=('changed '+n).encode() if next and (n!='common.py' or unrelated) else prior
  row=dict(path=n,before='1'*64,after=hashlib.sha256(raw).hexdigest())
  if next:row['previous']=hashlib.sha256(prior).hexdigest()
  rows.append(row);files['payload/'+n]=raw
 files['manifest.json']=json.dumps(dict(schema=1,addon_id='script.infinity.commandcenter',addon_version='0.3.5.20',addon_xml_sha256='2'*64,files=rows)).encode()
 with archive(files) as a:return a.fp.getvalue()
class Tests(unittest.TestCase):
 def fixture(self):
  old={'AndroidManifest.xml':b'old','lib/arm64-v8a/libkodi.so':b'old','classes.dex':b'classes','assets/skin.xml':b'skin'}
  for n in v.ASSETS:old[n]=payload()
  new=dict(old,**{'AndroidManifest.xml':b'new','lib/arm64-v8a/libkodi.so':b'new'})
  for n in v.ASSETS:new[n]=payload(True)
  return old,new
 def compare(self,a,b):
  with archive(a) as x,archive(b) as y,mock.patch.object(v,'dex_contract',return_value=({'jni'},{'class'})):return v.compare(x,y)
 def test_accepts_reviewed_scripts(self):
  a,b=self.fixture();self.assertEqual(self.compare(a,b)['protected_entries_unchanged'],1)
 def test_rejects_skin_change(self):
  a,b=self.fixture();b['assets/skin.xml']=b'changed'
  with self.assertRaises(RuntimeError):self.compare(a,b)
 def test_rejects_unrelated_cc_code(self):
  a,b=self.fixture();b[next(iter(v.ASSETS))]=payload(True,True)
  with self.assertRaises(RuntimeError):self.compare(a,b)
 def test_rejects_unreviewed_added_asset(self):
  a,b=self.fixture();b['assets/new']=b'new'
  with self.assertRaises(RuntimeError):self.compare(a,b)
if __name__=='__main__':unittest.main()
