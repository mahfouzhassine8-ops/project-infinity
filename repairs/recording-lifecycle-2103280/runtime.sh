#!/usr/bin/env bash
set -euo pipefail
mkdir -p runtime280
cleanup(){ adb logcat -d > runtime280/logcat.txt || true; adb pull /sdcard/Android/data/com.projectinfinity.kodi/files/audit-followup runtime280/results || true; }
trap cleanup EXIT
adb root
adb wait-for-device
adb install --no-incremental locked279/Infinity-2103279-End-to-End-Repair-RC1.apk | tee runtime280/install-parent.txt
adb install --no-incremental -r candidate280/Infinity-2103280-Audit-Followup-RC1.apk | tee runtime280/update.txt
adb install --no-incremental instrumentation280/Cobra-2103280-runtime-tests.apk
adb logcat -c
adb shell am instrument -w -r -e class com.projectinfinity.kodi.CobraRuntimeFollowupTest#additionalRuntimeJourney com.projectinfinity.kodi.test/androidx.test.runner.AndroidJUnitRunner | tee runtime280/instrumentation.txt
python3 - <<'PY'
from pathlib import Path
s=Path('runtime280/instrumentation.txt').read_text();assert 'OK (1 test)' in s and 'FAILURES' not in s,s[-6000:]
PY
