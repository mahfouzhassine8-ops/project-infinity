"""Real Android signing tests using deleted, explicitly non-production fixtures."""
import importlib.util,hashlib,os,re,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('fixture_support',ROOT/'tests/infinity71_packaging/test_followup.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
class MobileSigning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        legacy.FollowupTests.setUpClass(); f=legacy.FollowupTests
        cls.root=f.root;cls.unsigned=f.unsigned;cls.inventory=f.inventory
        cls.env={k:v for k,v in f.env.items() if k!='INFINITY_SIGNER_SHA256'}
        cert=cls.root/'public.der'
        r=legacy.run(['keytool','-exportcert','-keystore',f.key,'-storepass',f.password,'-alias','fixture','-file',cert])
        if r.returncode:raise RuntimeError('Fixture certificate export failed')
        cls.expected=hashlib.sha256(cert.read_bytes()).hexdigest()
        cls.good=dict(f.stable_env,INFINITY_SIGNER_SHA256=cls.expected)
    @classmethod
    def tearDownClass(cls):legacy.FollowupTests.tearDownClass()
    def sign(self,name,env):
        out=self.root/(name+'.apk')
        return out,legacy.run(['bash',ROOT/'scripts/sign-infinity-mobile.sh',self.unsigned,out],env)
    def test_missing_key_stops_without_new_identity(self):
        out,r=self.sign('mobile-absent',self.env);self.assertEqual(r.returncode,3);self.assertFalse(out.exists())
    def test_each_missing_field_stops(self):
        fields=(*legacy.SECRET_NAMES,'INFINITY_SIGNER_SHA256')
        for i,name in enumerate(fields):
            env=dict(self.good);env.pop(name)
            out,r=self.sign('mobile-partial-'+str(i),env)
            self.assertEqual(r.returncode,3);self.assertFalse(out.exists())
    def test_wrong_pinned_certificate_stops(self):
        out,r=self.sign('mobile-wrong-cert',dict(self.good,INFINITY_SIGNER_SHA256='0'*64))
        self.assertEqual(r.returncode,3);self.assertFalse(out.exists())
    def test_matching_key_keeps_identity_across_packages(self):
        for name in ('mobile-first','mobile-second'):
            out,r=self.sign(name,self.good);self.assertEqual(r.returncode,0,r.stderr)
            legacy.m.verify_overlay(out,self.inventory)
            report=out.with_suffix('.signing.txt').read_text()
            self.assertIn('certificate SHA-256 digest: '+self.expected,report)
            self.assertIn('Verified using v2 scheme (APK Signature Scheme v2): true',report)
    def test_invalid_key_does_not_create_output(self):
        out,r=self.sign('mobile-invalid',dict(self.good,INFINITY_KEYSTORE_B64='invalid-data'))
        self.assertNotEqual(r.returncode,0);self.assertFalse(out.exists())
if __name__=='__main__':unittest.main(verbosity=2)
