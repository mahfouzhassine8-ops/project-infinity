#!/usr/bin/env python3
"""Validate diagnostic transforms using a copy of the actual locked shell.

A synthetic native digest exercises identity binding ONLY; no APK is built here.
"""
import argparse,json,shutil,tempfile,unittest
from pathlib import Path
import android_apply

class AndroidScope(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='shutdown325-guard-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'shell'
        shutil.copytree(SOURCE,self.root)
    def apply(self):return android_apply.apply(self.root,PROOF,'1'*64)
    def test_exact_four_file_change_and_identity_binding(self):
        before=android_apply.snapshot(self.root);r=self.apply()
        self.assertEqual(r['before'],before);self.assertEqual(r['changed'],android_apply.ALLOWED)
        self.assertEqual(set(r['after']),set(before));self.assertEqual(len(before),254)
        java=self.root/'tools/android/packaging/xbmc/src'
        self.assertIn('1'*64,(java/'InfinityHealthExport.java.in').read_text())
        self.assertIn('1'*64,(java/'InfinityExitDiagnostics.java.in').read_text())
    def test_main_has_only_three_diagnostic_calls(self):
        name='tools/android/packaging/xbmc/src/Main.java.in'
        old=(self.root/name).read_text();self.apply();new=(self.root/name).read_text()
        markers=('exit.androidDestroy.enter','exit.nativeActivityDestroy.enter','exit.nativeActivityDestroy.returned')
        for marker in markers:
            line='    InfinityExitCompletion.trace(this, "'+marker+'");\n'
            # Calls inside the try block have two extra spaces.
            needle=next(s+'\n' for s in new.splitlines() if 'InfinityExitCompletion.trace(this, "'+marker+'")' in s)
            self.assertEqual(new.count(needle),1);new=new.replace(needle,'',1)
        self.assertEqual(new,old)
    def test_all_close_route_bodies_unchanged(self):
        name='tools/android/packaging/xbmc/src/InfinityExitCompletion.java.in'
        old=(self.root/name).read_text();self.apply();new=(self.root/name).read_text()
        old=old[old.index('  static final class Plan {'):old.index('  static void record(Context context, String phase) {')]
        new=new[new.index('  static final class Plan {'):new.index('  // Capture at the producer,')]
        self.assertEqual(old,new)
    def test_rejects_unrelated_source_drift_before_editing(self):
        victim=next(p for p in self.root.rglob('*Cobra*.java.in'))
        victim.write_text(victim.read_text()+'\n// synthetic guard test only\n')
        before=android_apply.snapshot(self.root)
        with self.assertRaisesRegex(ValueError,'Source differs'):self.apply()
        self.assertEqual(before,android_apply.snapshot(self.root))
    def test_rejects_missing_or_invalid_native_identity(self):
        before=android_apply.snapshot(self.root)
        for identity in ('','a'*63,'not-a-native-digest'):
            with self.assertRaises(ValueError):android_apply.apply(self.root,PROOF,identity)
        self.assertEqual(before,android_apply.snapshot(self.root))
    def test_no_input_files_or_raw_provider_data_added_to_exporter(self):
        self.apply();text=(self.root/'tools/android/packaging/xbmc/src/InfinityHealthExport.java.in').read_text()
        section=text[text.index('  private static void attachShutdown'):text.index('  private static void put(')] if '  private static void put(' in text[text.index('  private static void attachShutdown'):] else text[text.index('  private static void attachShutdown'):text.index('  /** Returns true')]
        self.assertNotIn('.delete(',section);self.assertNotIn('listFiles(',section)
        self.assertNotIn('getSharedPreferences(',section)
        self.assertIn('getCanonicalFile()',section)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--proof',type=Path,required=True)
    args,rest=parser.parse_known_args();SOURCE=args.source;PROOF=args.proof
    unittest.main(argv=['test_android.py',*rest],verbosity=2)
