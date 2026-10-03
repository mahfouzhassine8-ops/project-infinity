#!/usr/bin/env python3
import argparse, subprocess, sys, shutil, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(here.parent/'cosmic-chooser-2103296/prepare_diagnostics.py'),'--root',str(a.root),'--build',str(a.build),'--evidence',str(a.evidence)],check=True)
# Compile/test the identical repaired sources used for the release donor, including Main/Splash.
source=a.root/'shell-kodi/tools/android/packaging/xbmc/src'
dest=a.build/'xbmc/java/com/projectinfinity/kodi'
for name in ('InfinityGlassChooser','Main','Splash','InfinityStartupHandoff'):
    (dest/(name+'.java')).write_text((source/(name+'.java.in')).read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi').replace('@APP_NAME@','Kodi').replace('@APP_NAME_LC@','kodi'))
tests=a.build/'xbmc/src/test/java/com/projectinfinity/kodi'
for name in ('MotionFrameTest.java','StartupLifecycleTest.java'):
    shutil.copy2(here/name,tests/name)
manifest=a.build/'xbmc/AndroidManifest.xml';s=manifest.read_text().replace('/></manifest>','><activity android:name=".Splash" android:launchMode="singleInstance"/><activity android:name=".Main" android:launchMode="singleInstance"/></application></manifest>')
manifest.write_text(s)
(a.evidence/'DIAGNOSTIC-SCOPE.json').write_text(json.dumps({'full_actual_java_shell_compilation':True,'actual_splash_exercised':True,'native_kodi_execution':False,
    'runtime':'Robolectric API 35 native graphics; Android activity/looper lifecycle simulation','physical_fold_verified':False,'kodi_health':'source preservation supplemental only; device report pending','locked':False},indent=2)+'\n')
