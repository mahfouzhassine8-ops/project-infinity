#!/usr/bin/env python3
"""Retain inherited suite; update only the intentionally grouped options contract."""
import argparse
from pathlib import Path
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
