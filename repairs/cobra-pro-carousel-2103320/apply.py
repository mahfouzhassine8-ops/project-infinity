#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
root=Path(sys.argv[1]).resolve()
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(Path(__file__).with_name('changes.patch').resolve())],cwd=root,check=True)
print('Applied 2103320 over exact verified 2103319 source.')
