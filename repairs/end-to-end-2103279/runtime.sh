#!/usr/bin/env bash
set -euo pipefail
mkdir -p runtime279
cleanup(){ adb logcat -d > runtime279/logcat.txt || true; adb shell dumpsys meminfo com.projectinfinity.kodi > runtime279/memory.txt || true; adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/audit279 runtime279/results || true; }
trap cleanup EXIT
adb root
adb wait-for-device
adb shell getprop ro.product.cpu.abilist > runtime279/abis.txt
adb install --no-incremental parent278/Infinity-2103278-Watch-Ambient-RC1.apk | tee runtime279/install-baseline.txt
adb install --no-incremental -r candidate279/Infinity-2103279-End-to-End-Repair-RC1.apk | tee runtime279/update.txt
adb shell dumpsys package com.projectinfinity.kodi > runtime279/package.txt
adb install --no-incremental -r instrumentation279/Cobra-2103279-runtime-tests.apk
adb shell am force-stop com.projectinfinity.kodi
adb logcat -c
adb shell am instrument -w -r -e class com.projectinfinity.kodi.CobraRuntime279Test com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee runtime279/instrumentation.txt
python3 - <<'PY'
from pathlib import Path
s=Path('runtime279/instrumentation.txt').read_text();assert 'OK (1 test)' in s and 'FAILURES' not in s,s[-6000:]
PY
