#!/usr/bin/env bash
set -euo pipefail
mkdir -p remaining-runtime
cleanup(){ adb logcat -d > remaining-runtime/logcat.txt || true; adb shell dumpsys meminfo com.projectinfinity.kodi > remaining-runtime/memory.txt || true; adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/remaining-audit remaining-runtime/results || true; }
trap cleanup EXIT
adb root
adb wait-for-device
adb install --no-incremental locked280/Infinity-2103280-Audit-Followup-RC1.apk | tee remaining-runtime/install.txt
adb install --no-incremental -r candidate281/Infinity-2103281-Remaining-Audit-RC1.apk | tee remaining-runtime/update.txt
adb install --no-incremental instrumentation/Cobra-audit-followup-tests.apk
adb logcat -c
for method in additionalRuntimeJourney remainingBoundaries; do
  if [ "$method" = settingsAfterProcessRestart ]; then adb shell am force-stop com.projectinfinity.kodi; fi
  adb shell am instrument -w -r -e class "com.projectinfinity.kodi.CobraRuntimeFollowupTest#$method" com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee "remaining-runtime/$method.txt"
  adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/remaining-audit/runtime-results.json "remaining-runtime/$method.json" || true
done
python3 - <<'CHECK'
from pathlib import Path
for f in ['additionalRuntimeJourney','remainingBoundaries']:
 s=Path('remaining-runtime',f+'.txt').read_text()
 assert 'OK (1 test)' in s and 'FAILURES' not in s,(f,s[-6000:])
CHECK
