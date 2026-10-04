#!/usr/bin/env python3
"""Compile edited UI helpers against a real Android API jar, not UI emulation."""
from pathlib import Path
import argparse,subprocess,tempfile
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--android-jar',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--ecj',type=Path);a=p.parse_args()
    java=a.source/'tools/android/packaging/xbmc/src'
    with tempfile.TemporaryDirectory(prefix='infinity-java-') as temp:
        dest=Path(temp);files=[]
        for name,base in [('InfinityAndroidKeyboard',HERE),('InfinityGlassOptions',HERE),('InfinityCosmicArt',java),('CobraEmblem',java)]:
            f=dest/(name+'.java');f.write_text((base/(name+'.java.in')).read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'));files.append(str(f))
        # Only the Activity lifecycle dependency is stubbed. All Android UI APIs
        # and the unchanged brand decoder are compiled from real source/API 35.
        stub=dest/'Main.java';stub.write_text('package com.projectinfinity.kodi; class Main extends android.app.Activity { static Main MainActivity; boolean mInfinityStopped; }')
        files.append(str(stub))
        compiler=['java','-jar',str(a.ecj),'-8','-proc:none','-bootclasspath',str(a.android_jar.parent/'core-for-system-modules.jar')] if a.ecj else ['javac']
        subprocess.run(compiler+['-encoding','UTF-8','-cp',str(a.android_jar),'-d',str(dest/'classes')]+files,check=True)
        print('PASS: edited Java helpers compile against Android API 35 (not a device/runtime test)')
