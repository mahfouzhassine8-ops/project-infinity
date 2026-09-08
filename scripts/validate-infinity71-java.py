#!/usr/bin/env python3
"""Compile real patched Main/bridge and four unchanged Kodi Android classes.

Uses the real Android SDK API JAR. TV scheduling, JSON-RPC and generated R symbols
are compile-only stubs; this is an API/descriptor check, not an Android runtime test.
"""
from pathlib import Path
import argparse, json, re, shutil, subprocess, tempfile, zipfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--android-jar',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
src=a.out/'src/com/projectinfinity/kodi';src.mkdir(parents=True,exist_ok=True)
root=a.source/'tools/android/packaging/xbmc/src'
for name in ['Main','InfinityCoreBridge','XBMCMainView','XBMCInputDeviceListener','XBMCSettingsContentObserver']:
    t=(root/(name+'.java.in')).read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi').replace('@APP_NAME_LC@','kodi').replace('@APP_NAME@','Kodi')
    (src/(name+'.java')).write_text(t)
(src/'CompileOnlyStubs.java').write_text('''package com.projectinfinity.kodi;
// These unchanged collaborators are not under test.
class R {
 public static final class layout { public static final int activity_main=1; }
 public static final class id { public static final int VideoLayout=2; }
}
class XBMCJsonRPC { public void updateLeanback(android.content.Context c) {} }
class XBMCProperties { public static int getIntProperty(String n,int d) {return d;} }
class XBMCBroadcastReceiver {}
''')
tv=src/'channels/util';tv.mkdir(parents=True,exist_ok=True)
(tv/'TvUtil.java').write_text('''package com.projectinfinity.kodi.channels.util;
public final class TvUtil {
 public static void scheduleSyncingChannel(android.content.Context c) {}
 public static void cancelAllScheduledJobs(android.content.Context c) {}
}
''')
classes=a.out/'classes';classes.mkdir(exist_ok=True)
subprocess.run(['javac','-source','8','-target','8','-parameters','-Xlint:unchecked','-cp',str(a.android_jar.resolve()),'-d',str(classes)]+[str(f) for f in src.rglob('*.java')],check=True)
result=subprocess.run(['javap','-s','-p','-classpath',str(classes),'com.projectinfinity.kodi.Main'],check=True,capture_output=True,text=True)
(a.out/'Main.javap.txt').write_text(result.stdout)
actual={}
for m in re.finditer(r'\bnative\s+\S+\s+(_infinity\w+)\([^)]*\);\s*descriptor:\s*(\S+)',result.stdout): actual[m[1]]=m[2]
expected=json.loads((Path(__file__).resolve().parents[1]/'patches/infinity-7.1-audited/contract.json').read_text())['jni']
if actual != expected: raise SystemExit('Compiled Java descriptors differ: '+repr(actual))
with zipfile.ZipFile(a.out/'compile-check.jar','w') as z:
 for f in classes.rglob('*.class'):z.write(f,f.relative_to(classes).as_posix())
print('PASS: real Android API 34 compile; all nine compiled Main JNI descriptors match the native contract.')
