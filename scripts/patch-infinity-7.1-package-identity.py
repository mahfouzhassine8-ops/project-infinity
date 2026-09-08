from pathlib import Path
import re

root = Path('kodi')
version = root / 'version.txt'
if not version.exists():
    raise SystemExit('Kodi version.txt missing')

s = version.read_text()
old = 'APP_PACKAGE org.xbmc.kodi'
new = 'APP_PACKAGE com.projectinfinity.kodi'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('Unexpected APP_PACKAGE in Kodi version.txt')
version.write_text(s)

# Kodi derives CCompileInfo::GetClass() from APP_PACKAGE, and JNI registration
# derives Main/XBMCSettingsContentObserver/XBMCInputDeviceListener from GetClass().
# Building after this patch therefore makes the native and Java class roots identical.
compile_info = root / 'xbmc/CompileInfo.cpp.in'
jni_main = root / 'xbmc/platform/android/activity/JNIMainActivity.cpp'
for p in (compile_info, jni_main):
    if not p.exists():
        raise SystemExit(f'missing identity source: {p}')

ci = compile_info.read_text()
if 'return "@APP_PACKAGE@";' not in ci or 'std::replace(s_classname.begin(), s_classname.end(),' not in ci:
    raise SystemExit('CompileInfo package/class derivation changed unexpectedly')

jm = jni_main.read_text()
for token in ('CCompileInfo::GetClass()', 'pkgRoot + "/Main"', 'pkgRoot + "/XBMCSettingsContentObserver"', 'pkgRoot + "/XBMCInputDeviceListener"'):
    if token not in jm:
        raise SystemExit(f'JNI class-root contract changed: missing {token}')

print('Infinity package identity mapped at source: com.projectinfinity.kodi')
print('JNI Main and companion classes will register under the same class root.')
