#!/usr/bin/env python3
"""Compile the real patched Infinity Android owner set against the Android SDK.

The audited v4 contract has a small mandatory Java core. Later cumulative layers
add diagnostics, refresh, native-media and audio-policy owners. Stage those
owners when present so this generic JNI descriptor gate remains backward
compatible with v4 while validating the complete source graph of newer builds.
TV scheduling, JSON-RPC and generated resource integers are compile-only stubs;
this is an API/descriptor check, not an Android runtime test.
"""
from pathlib import Path
import argparse, json, re, subprocess, zipfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--android-jar', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)

src = a.out / 'src/com/projectinfinity/kodi'
src.mkdir(parents=True, exist_ok=True)
root = a.source / 'tools/android/packaging/xbmc/src'

mandatory = [
    'Main', 'InfinityCoreBridge', 'XBMCMainView',
    'XBMCInputDeviceListener', 'XBMCSettingsContentObserver',
]
optional = [
    'InfinityRefreshController',
    'InfinityExitDiagnostics',
    'InfinityDiagnosticFiles',
    'XBMCMediaSession',
    'InfinityPlatformHook',
    'InfinityPlatformHooks',
    'InfinitySystemMediaHook',
    'InfinityAudioFocusHook',
]

names = list(mandatory)
for name in optional:
    if (root / (name + '.java.in')).is_file():
        names.append(name)

for name in mandatory:
    path = root / (name + '.java.in')
    if not path.is_file():
        raise SystemExit('Missing mandatory Infinity Android owner: ' + str(path))

for name in names:
    text = (root / (name + '.java.in')).read_text(encoding='utf-8')
    replacements = {
        '@APP_PACKAGE@': 'com.projectinfinity.kodi',
        '@APP_NAME_LC@': 'kodi',
        '@APP_NAME@': 'Infinity',
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    if '@APP_' in text:
        raise SystemExit('Unresolved Android template token in ' + name)
    (src / (name + '.java')).write_text(text, encoding='utf-8')

(src / 'CompileOnlyStubs.java').write_text('''package com.projectinfinity.kodi;
// Unchanged collaborators outside this source-owner contract.
class R {
 public static final class layout { public static final int activity_main=1; }
 public static final class id { public static final int VideoLayout=2; }
 public static final class drawable { public static final int notif_icon=3; }
}
class XBMCJsonRPC { public void updateLeanback(android.content.Context c) {} }
class XBMCProperties { public static int getIntProperty(String n,int d) {return d;} }
class XBMCBroadcastReceiver extends android.content.BroadcastReceiver {
 public void onReceive(android.content.Context c, android.content.Intent i) {}
}
''', encoding='utf-8')

tv = src / 'channels/util'
tv.mkdir(parents=True, exist_ok=True)
(tv / 'TvUtil.java').write_text('''package com.projectinfinity.kodi.channels.util;
public final class TvUtil {
 public static void scheduleSyncingChannel(android.content.Context c) {}
 public static void cancelAllScheduledJobs(android.content.Context c) {}
}
''', encoding='utf-8')

classes = a.out / 'classes'
classes.mkdir(exist_ok=True)
subprocess.run([
    'javac', '-source', '8', '-target', '8', '-parameters', '-Xlint:unchecked',
    '-cp', str(a.android_jar.resolve()), '-d', str(classes),
    *[str(f) for f in src.rglob('*.java')],
], check=True)

result = subprocess.run([
    'javap', '-s', '-p', '-classpath', str(classes), 'com.projectinfinity.kodi.Main'
], check=True, capture_output=True, text=True)
(a.out / 'Main.javap.txt').write_text(result.stdout, encoding='utf-8')

actual = {}
for match in re.finditer(
    r'\bnative\s+\S+\s+(_infinity\w+)\([^)]*\);\s*descriptor:\s*(\S+)',
    result.stdout,
):
    actual[match[1]] = match[2]
expected = json.loads(
    (Path(__file__).resolve().parents[1] / 'patches/infinity-7.1-audited/contract.json').read_text()
)['jni']
if actual != expected:
    raise SystemExit('Compiled Java descriptors differ: ' + repr(actual))

with zipfile.ZipFile(a.out / 'compile-check.jar', 'w') as archive:
    for file in classes.rglob('*.class'):
        archive.write(file, file.relative_to(classes).as_posix())

for owner in names:
    if not (classes / 'com/projectinfinity/kodi' / (owner + '.class')).is_file():
        raise SystemExit('Android owner did not compile: ' + owner)

extra = [name for name in names if name not in mandatory]
print(
    'PASS: real Android API 34 compile; all compiled Main JNI descriptors match the native contract. '
    + ('Cumulative owners compiled: ' + ', '.join(extra) if extra else 'Audited v4 owner set compiled.')
)
