#!/usr/bin/env python3
import argparse,subprocess,sys,shutil
from pathlib import Path
here=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
subprocess.run([sys.executable,str(here.parent/'stale-main-task-2103300/prepare_diagnostics.py'),'--root',str(a.root),'--build',str(a.build),'--evidence',str(a.evidence)],check=True)
shutil.copy2(here/'ChooserWeatherSnapshotTest.java',a.build/'xbmc/src/test/java/com/projectinfinity/kodi/ChooserWeatherSnapshotTest.java')
