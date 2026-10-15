#!/usr/bin/env bash
set -euo pipefail
mkdir -p followup-runtime
cleanup(){ adb logcat -d > followup-runtime/logcat.txt || true; adb shell dumpsys meminfo com.projectinfinity.kodi > followup-runtime/memory.txt || true; adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/audit-followup followup-runtime/results || true; }
trap cleanup EXIT
adb root
adb wait-for-device
adb install --no-incremental locked279/Infinity-2103279-End-to-End-Repair-RC1.apk | tee followup-runtime/install.txt
adb install --no-incremental instrumentation/Cobra-audit-followup-tests.apk
adb logcat -c
adb shell am instrument -w -r -e class com.projectinfinity.kodi.CobraRuntimeFollowupTest#additionalRuntimeJourney com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee followup-runtime/journey.txt
adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/audit-followup/runtime-results.json followup-runtime/journey-results.json
adb shell am force-stop com.projectinfinity.kodi
adb shell am instrument -w -r -e class com.projectinfinity.kodi.CobraRuntimeFollowupTest#settingsAfterProcessRestart com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee followup-runtime/restart.txt
python3 - <<'PY'
from pathlib import Path
for f in ['journey.txt','restart.txt']:
 s=Path('followup-runtime',f).read_text()
 assert 'OK (1 test)' in s and 'FAILURES' not in s,(f,s[-6000:])
PY
