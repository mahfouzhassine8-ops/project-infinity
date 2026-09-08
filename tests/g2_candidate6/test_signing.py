"""Real SDK signing tests with disposable fixtures; no repository secrets are used."""
from pathlib import Path
import base64,itertools,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import g2_candidate6_sign as s
from g2_candidate6 import digest,inventory,spec
class SigningTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
  cls.sdk=Path(os.environ['ANDROID_HOME']);cls.unsigned=Path(os.environ['G2_UNSIGNED_APK'])
  key=cls.root/'test.keystore';cert=cls.root/'test.der'
  subprocess.run(['keytool','-genkeypair','-noprompt','-keystore',str(key),'-storepass','fixture-pass','-keypass','fixture-pass','-alias','fixture','-keyalg','RSA','-keysize','2048','-validity','30','-dname','CN=DISPOSABLE TEST FIXTURE'],check=True,capture_output=True)
  subprocess.run(['keytool','-exportcert','-keystore',str(key),'-storepass','fixture-pass','-alias','fixture','-file',str(cert)],check=True,capture_output=True)
  cls.cert=digest(cert.read_bytes());cls.env={k:v for k,v in os.environ.items() if k not in s.NAMES}
  cls.env.update(dict(zip(s.NAMES,[base64.b64encode(key.read_bytes()).decode(),'fixture-pass','fixture-pass','fixture'])))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.out=Path(self.temp.name)/'signed.apk'
 def tearDown(self):self.temp.cleanup()
 def test_no_credentials_remains_unsigned_without_generating_key(self):
  env={k:v for k,v in self.env.items() if k not in s.NAMES}
  result=s.sign(self.unsigned,self.out,self.sdk,self.cert,env)
  self.assertFalse(result['signed']);self.assertFalse(self.out.exists())
 def test_all_fourteen_partial_configs_are_rejected(self):
  for bits in itertools.product([False,True],repeat=4):
   if all(bits) or not any(bits):continue
   env={k:v for k,v in self.env.items() if k not in s.NAMES}
   env.update({n:self.env[n] for n,b in zip(s.NAMES,bits) if b})
   with self.subTest(bits=bits),self.assertRaises(ValueError):s.sign(self.unsigned,self.out,self.sdk,self.cert,env)
  self.assertFalse(self.out.exists())
 def test_wrong_original_certificate_rejected(self):
  with self.assertRaises(ValueError):s.sign(self.unsigned,self.out,self.sdk,spec()['signer_sha256'],self.env)
  self.assertFalse(self.out.exists())
 def test_invalid_supplied_key_never_falls_back(self):
  env=dict(self.env);env[s.NAMES[0]]='not base64!'
  with self.assertRaises(ValueError):s.sign(self.unsigned,self.out,self.sdk,self.cert,env)
  self.assertFalse(self.out.exists())
 def test_matching_fixture_key_signs_and_protects_all_apk_members(self):
  result=s.sign(self.unsigned,self.out,self.sdk,self.cert,self.env)
  self.assertTrue(result['signed']);self.assertEqual(result['signer_sha256'],self.cert)
  self.assertEqual(inventory(self.unsigned),inventory(self.out))
if __name__=='__main__':unittest.main(verbosity=2)
