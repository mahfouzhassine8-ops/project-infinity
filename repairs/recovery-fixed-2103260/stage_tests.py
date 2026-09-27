#!/usr/bin/env python3
"""Reuse all 20 passed tests; add recovery action/window and real drag regression tests."""
import argparse,shutil
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--build-dir',type=Path,required=True);ap.add_argument('--evidence',type=Path,required=True);a=ap.parse_args()
project=Path.cwd();here=Path(__file__).resolve().parent
# Use the last passed test setup, redirecting its baseline paths only.
script=(project/'source259/repair-source/stage_tests.py').read_text()
script=script.replace("here/'GlassHealthFinishTest.java'","project/'source259/repair-source/GlassHealthFinishTest.java'")
script=script.replace("project/'audit259/Splash-before.java.in'","project/'source259/Splash-before.java.in'")
script=script.replace("project/'audit259/health-rows-and-actions.java.inc'","project/'source259/health-rows-and-actions.java.inc'")
exec(compile(script,'passed-259-stage-tests','exec'),{'__file__':str(here/'stage_tests.py')})
out=a.build_dir.resolve()/'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copy2(here/'RecoveryFixedTest.java',out/'RecoveryFixedTest.java')
method=(project/'audit260/recovery-method.java.inc').read_text()
harness='''package com.projectinfinity.kodi;
public class RecoveryActionHarness extends android.app.Activity {
  boolean light,safe,once;int launches,restored;String launched;
  private void launchInfinityExperience(String name,boolean safe,boolean once){this.launched=name;this.safe=safe;this.once=once;launches++;}
  static final class CobraPresentationSafety {
    static void restoreBuiltIn(RecoveryActionHarness owner,Object unused){owner.restored++;}
  }
  private InfinityGlassRecovery.Builder cobraRecoveryDialog(){return new InfinityGlassRecovery.Builder(this,()->light,null,true);}
  void openRecovery(){showCobraRecovery();}
'''+method+'\n}\n'
(out/'RecoveryActionHarness.java').write_text(harness)
