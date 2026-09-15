#!/usr/bin/env bash
set -euo pipefail

# Recreate and validate the exact accepted Candidate 2 source stack first.
bash scripts/infinity_live_app_ci_1.sh

# Layer Extended Background Mode only after all protected Candidate 2 contracts pass.
python3 -m py_compile \
  scripts/infinity_extended_background_mode.py \
  scripts/infinity_1_0_9_cobra_full_fixups_ebm.py
python3 scripts/infinity_extended_background_mode.py apply \
  --source kodi --receipt engine/extended-background-source.json
python3 scripts/infinity_extended_background_mode.py verify --source kodi

JAVA=kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
SERVICE=kodi/tools/android/packaging/xbmc/src/InfinityExtendedBackgroundService.java.in
MANIFEST=kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in
INSTALL=kodi/cmake/scripts/android/Install.cmake

grep -Fq 'import androidx.media3.common.AudioAttributes;' "$JAVA"
grep -Fq 'InfinityExtendedBackgroundService.sync(this);' "$JAVA"
grep -Fq 'EXTENDED BACKGROUND MODE • OFF' "$JAVA"
grep -Fq 'getBoolean(KEY_ENABLED, false)' "$SERVICE"
grep -Fq 'START_STICKY' "$SERVICE"
grep -Fq 'FOREGROUND_SERVICE_TYPE_SPECIAL_USE' "$SERVICE"
grep -Fq 'android:name=".InfinityExtendedBackgroundService"' "$MANIFEST"
grep -Fq 'android.permission.FOREGROUND_SERVICE_SPECIAL_USE' "$MANIFEST"
grep -Fq 'android:foregroundServiceType="specialUse"' "$MANIFEST"
grep -Fq 'src/InfinityExtendedBackgroundService.java' "$INSTALL"
grep -q 'versionCode 2103135' kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q 'versionName "1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background"' \
  kodi/tools/android/packaging/xbmc/build.gradle.in

! grep -Eq 'PowerManager\.WakeLock|PARTIAL_WAKE_LOCK|FULL_WAKE_LOCK|ACQUIRE_CAUSES_WAKEUP|android\.permission\.WAKE_LOCK' "$SERVICE"

echo 'PASS: Candidate 2 Extended Background preflight layered over protected Candidate 2 source'
