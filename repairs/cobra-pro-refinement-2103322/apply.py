#!/usr/bin/env python3
"""Apply the reviewed Cobra refinement delta without fuzzy matching."""
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
patch = Path(__file__).with_name('changes.patch').resolve()
subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', '-p1', '--dry-run', '-i', str(patch)], cwd=root, check=True)
subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', '-p1', '-i', str(patch)], cwd=root, check=True)
print('Applied 2103322 over exact verified locked 2103321 source.')
