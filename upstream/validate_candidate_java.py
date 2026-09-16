#!/usr/bin/env python3
"""Compile the replayed Infinity Android owner set for an INTERNAL Kodi candidate.

This is the candidate-stage extension of the pinned RC3 Java descriptor gate. It
keeps the same mandatory JNI owner contract while also compiling cumulative
Android-only owners that the later background/control layers generate.
"""
from pathlib import Path
import argparse
import json
import re
import subprocess
import zipfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--android-jar', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--contract', type=Path, required=True)
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
    'InfinityMultiViewController',
    'InfinityExtendedBackgroundService',
    'InfinityBackgroundControlActivity',
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
// The real launcher Activity is outside this focused owner set. The background
// service only needs its Class object while compiling the notification fallback.
class Splash extends android.app.Activity {}
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
expected = json.loads(a.contract.read_text())['jni']
if actual != expected:
    raise SystemExit('Compiled Java descriptors differ: ' + repr(actual))

with zipfile.ZipFile(a.out / 'compile-check.jar', 'w') as archive:
    for file in classes.rglob('*.class'):
        archive.write(file, file.relative_to(classes).as_posix())

for owner in names:
    if not (classes / 'com/projectinfinity/kodi' / (owner + '.class')).is_file():
        raise SystemExit('Android owner did not compile: ' + owner)

required_cumulative = {
    'InfinityExtendedBackgroundService',
    'InfinityBackgroundControlActivity',
}
missing = sorted(required_cumulative.difference(names))
if missing:
    raise SystemExit('Replayed RC3 candidate is missing cumulative Android owner(s): ' + ', '.join(missing))

extra = [name for name in names if name not in mandatory]
print(
    'PASS: internal candidate Android API 34 compile; Main JNI descriptors match the pinned RC3 native contract. '
    + 'Cumulative owners compiled: ' + ', '.join(extra)
)
