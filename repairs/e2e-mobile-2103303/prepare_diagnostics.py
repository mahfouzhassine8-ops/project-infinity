#!/usr/bin/env python3
"""Retain inherited compile/tests and adapt the visibility mask to removed copy."""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--evidence', type=Path, required=True)
a = p.parse_args()
subprocess.run([sys.executable, str(HERE.parent/'chooser-weather-snapshot-2103302/prepare_diagnostics.py'),
                '--root', str(a.root), '--build', str(a.build), '--evidence', str(a.evidence)], check=True)
tests = a.build/'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copy2(HERE/'MobileRepairTest.java', tests/'MobileRepairTest.java')
p = tests/'MotionFrameTest.java'
text = p.read_text()
old = '        View v=ui.stage.getChildAt(i);Rect r=new Rect();'
assert text.count(old) == 1
text = text.replace(old, '''        View v=ui.stage.getChildAt(i);
        // Removed slogans are GONE, not visible control surfaces. Keep the
        // strict zero-pixel-change assertion for every visible child/card.
        if(v.getVisibility()!=View.VISIBLE)continue;
        Rect r=new Rect();''')
p.write_text(text)
