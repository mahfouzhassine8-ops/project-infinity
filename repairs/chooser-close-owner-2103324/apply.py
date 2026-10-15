#!/usr/bin/env python3
"""Apply only the reviewed shutdown monitor and chooser dispatch correction."""
import subprocess
import sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-i',
                str(Path(__file__).with_name('changes.patch'))],cwd=root,check=True)

