#!/usr/bin/env python3
"""Exact parent source drift, no destructive shortcuts, and two-service manifest scope."""
import argparse,copy,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
import apply as repair
spec=importlib.util.spec_from_file_location('package326',Path(__file__).with_name('package.py'))
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)
def method(text,signature):
 a=text.index(signature);b=text.index('\n  }',a)+4;return text[a:b]
class Source(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'source';shutil.copytree(SOURCE,self.root)
 def apply(self):return repair.apply('android',self.root,PROOF,Path(self.tmp.name)/'receipt.json','1'*64)
 def test_full_parent_and_exact_scope(self):
  r=self.apply();self.assertEqual(len(r['changed']),8);self.assertEqual(len(r['before']),254);self.assertEqual(len(r['after']),256)
  repair.verify(self.root,Path(self.tmp.name)/'receipt.json')
 def test_false_parent_rejected_before_write(self):
  p=self.root/repair.SRC/'Main.java.in';p.write_text(p.read_text()+'\n// drift\n');before=repair.snapshot(self.root)
  with self.assertRaises(ValueError):self.apply()
  self.assertEqual(before,repair.snapshot(self.root))
 def test_owner_status_rules_and_native_ui_callbacks_unchanged(self):
  a=(self.root/repair.SRC/'InfinityKodiShutdown.java.in').read_text();main=(self.root/repair.SRC/'Main.java.in').read_bytes();self.apply()
  b=(self.root/repair.SRC/'InfinityKodiShutdown.java.in').read_text();self.assertEqual(b.replace('  static String localOwnerToken(){return processToken;}\n',''),a)
  self.assertEqual(main,(self.root/repair.SRC/'Main.java.in').read_bytes())
 def test_force_and_legacy_dispatch_bodies_unchanged(self):
  a=(self.root/repair.SRC/'InfinityExitCompletion.java.in').read_text();self.apply();b=(self.root/repair.SRC/'InfinityExitCompletion.java.in').read_text()
  for signature in ('  static void afterStop(Main owner)','  static void requestForce(Main owner, Context context)','  static void finishForce(Context app, Runnable terminator)'):
   self.assertEqual(method(a,signature),method(b,signature))
 def test_no_forced_or_early_task_removal_in_normal_dispatch(self):
  self.apply();b=(self.root/repair.SRC/'InfinityExitCompletion.java.in').read_text();normal=b[b.index('  static boolean requestNormal(Main owner)'):b.index('  static void afterStop')]
  for forbidden in ('finishAndRemoveTask(','.finish(', 'killProcess(', 'System.exit(', 'forceStopPackage'):
   self.assertNotIn(forbidden,normal)
  self.assertIn('InfinityCloseNativeLease.acquire(owner)',normal);self.assertIn('claimGuardedDispatch()',normal)
 def test_new_services_never_autocreate_or_stick_or_load_jni(self):
  self.apply()
  for n in ('InfinityCloseGuardService.java.in','InfinityCloseNativeLease.java.in'):
   t=(self.root/repair.SRC/n).read_text()
   self.assertNotIn('System.loadLibrary(',t);self.assertNotIn('return START_STICKY',t);self.assertNotIn('BIND_AUTO_CREATE;',t);self.assertNotIn('killProcess(',t)
  t=(self.root/repair.SRC/'InfinityCloseGuardService.java.in').read_text();self.assertIn('MAX_PROTECTION_MS=150000',t);self.assertIn('onTimeout(int startId)',t)
class Manifest(unittest.TestCase):
 def setUp(self):
  self.old=MANIFEST.read_text()
  self.add='''      E: service (line=204)
        A: android:name(0x01010003)="com.projectinfinity.kodi.InfinityCloseGuardService" (Raw: "com.projectinfinity.kodi.InfinityCloseGuardService")
        A: android:exported(0x01010010)=(type 0x12)0x0
        A: android:stopWithTask(0x0101036a)=(type 0x12)0x0
        A: android:foregroundServiceType(0x01010599)=(type 0x11)0x800
      E: service (line=205)
        A: android:name(0x01010003)="com.projectinfinity.kodi.InfinityCloseNativeLease" (Raw: "com.projectinfinity.kodi.InfinityCloseNativeLease")
        A: android:exported(0x01010010)=(type 0x12)0x0
        A: android:process(0x01010011)=":kodi" (Raw: ":kodi")
        A: android:stopWithTask(0x0101036a)=(type 0x12)0x0
'''
  at=self.old.index('      E: service ');self.new=self.old[:at]+self.add+self.old[at:]
 def test_only_two_services_permitted(self):package.verify_manifest_pair(self.old,self.new)
 def test_exported_guard_rejected(self):
  with self.assertRaises(RuntimeError):package.verify_manifest_pair(self.old,self.new.replace(self.add,self.add.replace('(type 0x12)0x0','(type 0x12)0xffffffff',1)))
 def test_wrong_guard_type_rejected(self):
  with self.assertRaises(RuntimeError):package.verify_manifest_pair(self.old,self.new.replace('(type 0x11)0x800','(type 0x11)0x1'))
 def test_misplaced_lease_rejected(self):
  with self.assertRaises(RuntimeError):package.verify_manifest_pair(self.old,self.new.replace(self.add,self.add.replace('\":kodi\"','\":other\"')))
 def test_extra_manifest_change_rejected(self):
  with self.assertRaises(RuntimeError):package.verify_manifest_pair(self.old,self.new.replace('E: uses-permission ','E: changed-permission ',1))
 def test_missing_service_rejected(self):
  with self.assertRaises(RuntimeError):package.verify_manifest_pair(self.old,self.old)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);a,other=p.parse_known_args();SOURCE=a.source;PROOF=a.proof;MANIFEST=a.manifest
 unittest.main(argv=['test_source.py',*other],verbosity=2)
