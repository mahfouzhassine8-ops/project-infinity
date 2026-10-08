import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('checkpoint_package',HERE/'package.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
OLD={('Lcom/projectinfinity/kodi/Main;','oldNative','()V')}
NEW=OLD|{
 ('Lcom/projectinfinity/kodi/Main;','infinityRegisterCheckpointOwner','(Ljava/lang/String;ILjava/lang/String;)Z'),
 ('Lcom/projectinfinity/kodi/Main;','infinityRequestPersistenceCheckpoint','(Ljava/lang/String;Ljava/lang/String;I)Z'),
 ('Lcom/projectinfinity/kodi/Main;','infinityPersistenceCheckpointStatus','(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;'),
 ('Lcom/projectinfinity/kodi/Main;','infinityAuthorizeCheckpointTermination','(Ljava/lang/String;Ljava/lang/String;I)Z')}
class PackagingTests(unittest.TestCase):
 def test_reviewed_nested_class_removal_does_not_allow_protected_class_removal(self):
  owner='Lcom/projectinfinity/kodi/InfinityKodiShutdown'
  self.assertEqual(p.verify_class_coverage({owner+';',owner+'$OldWorker;'}, {owner+';'}), [owner+'$OldWorker;'])
  for missing in [owner+';', 'Lcom/projectinfinity/kodi/InfinityCobraRecordingService$Worker;', 'Lother/library/Worker;']:
   with self.assertRaisesRegex(RuntimeError,'Protected DEX classes removed'):
    p.verify_class_coverage({missing}, set())
 def test_merge_preserves_payload_and_rejects_unreviewed_changes(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); base=r/'base.apk'; donor=r/'donor.apk'; native=r/'libkodi.so'; out=r/'out.apk'
   native.write_bytes(b'checked engine')
   a={'AndroidManifest.xml':b'old manifest','classes.dex':b'old dex',p.ENGINE:b'old engine','assets/skin/skin.xml':b'protected skin','resources.arsc':b'protected resources','lib/arm64-v8a/other.so':b'protected other JNI','assets/addons/service.infinity.compat/service.py':b'old service','META-INF/CERT.RSA':b'old signature'}
   b={'AndroidManifest.xml':b'new manifest','classes.dex':b'new dex','assets/addons/service.infinity.compat/service.py':b'new service','assets/infinity/checkpoint-controller.zip':b'controller'}
   for path,data in [(base,a),(donor,b)]:
    with zipfile.ZipFile(path,'w') as z:
     for n,v in data.items():z.writestr(n,v)
   allowed={n:hashlib.sha256(v).hexdigest() for n,v in b.items() if n.startswith('assets/')}
   with patch.object(p,'dex_contract',side_effect=[(OLD,{'Main'}),(NEW,{'Main','New'})]):p.merge(base,donor,native,out,allowed)
   with zipfile.ZipFile(out) as z:
    for n in ['assets/skin/skin.xml','resources.arsc','lib/arm64-v8a/other.so']:self.assertEqual(z.read(n),a[n])
    self.assertEqual(z.read(p.ENGINE),native.read_bytes());self.assertEqual(z.read('classes.dex'),b['classes.dex'])
    self.assertNotIn('META-INF/CERT.RSA',z.namelist())
   with patch.object(p,'dex_contract',side_effect=[(OLD,{'Main'}),(OLD,{'Main'})]):
    with self.assertRaisesRegex(RuntimeError,'JNI declaration'):p.merge(base,donor,native,out,allowed)
   with zipfile.ZipFile(donor,'a') as z:z.writestr('assets/unreviewed',b'bad')
   with self.assertRaisesRegex(RuntimeError,'Unreviewed donor asset'):p.merge(base,donor,native,out,allowed)
 def test_jni_allowlist_matches_native_registration(self):
  source=(p.RUNTIME/'runtime/native/overlay/xbmc/platform/android/activity/JNIMainActivity.cpp').read_text()
  for _,name,descriptor in NEW-OLD:self.assertIn('{"'+name+'", "'+descriptor+'"',source)
if __name__=='__main__':unittest.main()
