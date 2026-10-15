#!/usr/bin/env python3
"""Retain inherited suite; update only the intentionally grouped options contract."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--evidence', type=Path, required=True)
a = p.parse_args()
subprocess.run([sys.executable, str(HERE.parent/'e2e-mobile-2103303/prepare_diagnostics.py'),
                '--root', str(a.root), '--build', str(a.build),
                '--evidence', str(a.evidence)], check=True)
tests = a.build/'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copy2(HERE/'GlassOptionsTest.java', tests/'GlassOptionsTest.java')
# Exercise the real, unchanged Splash callback. The 303 diagnostics tree no
# longer carries the older options harness, so explicitly generate it here.
source = (a.root/'shell-kodi/tools/android/packaging/xbmc/src/Splash.java.in').read_text()
anchor = 'final android.content.DialogInterface.OnClickListener existingAction = '
assert source.count(anchor) == 1
callback = source.split(anchor, 1)[1].split('\n    if (!isAndroidTV()', 1)[0].strip()
assert callback.startswith('(dialogInterface, which) -> {') and callback.endswith('};')
constants = []
for name in ['INFINITY_EXPERIENCE_PREFS', 'INFINITY_EXPERIENCE_DEFAULT']:
    matches = re.findall(r'private static final String '+name+r'\s*=\s*([^;]+);', source)
    assert len(matches) == 1, name
    constants.append('  static final String '+name+' = '+matches[0]+';')
harness = ('package com.projectinfinity.kodi;\n'
           'public class OptionsActionHarness extends android.app.Activity {\n'
           + '\n'.join(constants) + '''
  String launched; int health, recovery;
  private void launchInfinityExperience(String experience) { launched=experience; }
  private void showInfinityHealthCenter() { health++; }
  private void showCobraRecovery() { recovery++; }
  android.content.DialogInterface.OnClickListener listener(String experience) {
    final boolean cobra="live".equals(experience);
    return ''' + callback + '\n  }\n}\n')
(tests/'OptionsActionHarness.java').write_text(harness)
