#!/usr/bin/env bash
set -euo pipefail
mkdir -p remaining-runtime
cleanup(){ adb logcat -d > remaining-runtime/logcat.txt || true; adb shell dumpsys meminfo com.projectinfinity.kodi > remaining-runtime/memory.txt || true; adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/remaining-audit remaining-runtime/results || true; }
trap cleanup EXIT
adb root
adb wait-for-device
adb install --no-incremental locked280/Infinity-2103280-Audit-Followup-RC1.apk | tee remaining-runtime/install.txt
adb install --no-incremental instrumentation/Cobra-remaining-audit-tests.apk
adb logcat -c
adb shell am instrument -w -r -e class com.projectinfinity.kodi.CobraRuntimeFollowupTest#additionalRuntimeJourney com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee remaining-runtime/journey.txt
adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/remaining-audit/runtime-results.json remaining-runtime/journey-results.json
adb shell am force-stop com.projectinfinity.kodi
adb shell am instrument -w -r -e class com.projectinfinity.kodi.CobraRuntimeFollowupTest#settingsAfterProcessRestart com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee remaining-runtime/restart.txt
python3 - <<'PY'
from pathlib import Path
for f in ['journey.txt','restart.txt']:
 s=Path('remaining-runtime',f).read_text()
 assert 'OK (1 test)' in s and 'FAILURES' not in s,(f,s[-6000:])
PY
