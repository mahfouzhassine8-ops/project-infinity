#!/usr/bin/env python3
import argparse, subprocess, sys, shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(here.parent/'startup-reliability-2103298/prepare_diagnostics.py'),
                '--root',str(a.root),'--build',str(a.build),'--evidence',str(a.evidence)],check=True)
source=a.root/'shell-kodi/tools/android/packaging/xbmc/src';dest=a.build/'xbmc/java/com/projectinfinity/kodi'
for name in ('Splash','Main','InfinityExitCompletion','InfinityPowerControlActivity','InfinityPowerMenuRoutes','InfinityChooserWeather','InfinityStartupPreparation'):
    (dest/(name+'.java')).write_text((source/(name+'.java.in')).read_text()
        .replace('@APP_PACKAGE@','com.projectinfinity.kodi').replace('@APP_NAME@','Kodi').replace('@APP_NAME_LC@','kodi'))
tests=a.build/'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copy2(here/'GracefulExitHandoffTest.java',tests/'GracefulExitHandoffTest.java')
shutil.copy2(here/'PowerMenuRouteTest.java',tests/'PowerMenuRouteTest.java')
shutil.copy2(here/'ChooserWeatherCaptureTest.java',tests/'ChooserWeatherCaptureTest.java')
shutil.copytree(here/'fixtures',a.build/'xbmc/src/test/resources/power-profiles')
