#!/usr/bin/env python3
import argparse, subprocess, sys, shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(here.parent/'cosmic-motion-lifecycle-2103297/prepare_diagnostics.py'),'--root',str(a.root),'--build',str(a.build),'--evidence',str(a.evidence)],check=True)
source=a.root/'shell-kodi/tools/android/packaging/xbmc/src';dest=a.build/'xbmc/java/com/projectinfinity/kodi'
for name in ('Splash','Main','InfinityStartupPreparation','InfinityStartupTrace'):
    (dest/(name+'.java')).write_text((source/(name+'.java.in')).read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi').replace('@APP_NAME@','Kodi').replace('@APP_NAME_LC@','kodi'))
tests=a.build/'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copy2(here/'StartupReliabilityTest.java',tests/'StartupReliabilityTest.java')
# The inherited direct-handoff unit test bypasses boot by design. Mark preparation
# ready explicitly, while new tests exercise the real asynchronous startup route.
path=tests/'StartupLifecycleTest.java';s=path.read_text()
s=s.replace('    a.startXBMC();a.startXBMC();','    ReflectionHelpers.setField(a,"mInfinityPreparationReady",true);\n    a.startXBMC();a.startXBMC();')
path.write_text(s)
