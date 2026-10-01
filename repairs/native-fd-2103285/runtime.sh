#!/usr/bin/env bash
set -euo pipefail
mkdir -p runtime285
cleanup() {
  adb logcat -d > runtime285/logcat.txt || true
  adb shell dumpsys package com.projectinfinity.kodi > runtime285/package.txt || true
}
trap cleanup EXIT
adb root
adb wait-for-device
adb shell getprop ro.product.cpu.abilist > runtime285/emulator-abis.txt
adb push native-evidence/fd-test-android-x86_64 /data/local/tmp/infinity-fd-test
adb shell chmod 755 /data/local/tmp/infinity-fd-test
adb shell /data/local/tmp/infinity-fd-test 2>&1 | tee runtime285/android-bionic-fd-tests.txt
grep -q 'RESULT groups=12 .* PASS' runtime285/android-bionic-fd-tests.txt
# This is a clean disposable emulator, NOT the user's phone.
adb install --no-incremental parent284/Infinity-2103284-Ambient-Surface-Repair-RC1.apk | tee runtime285/install-parent.txt
grep -q Success runtime285/install-parent.txt
adb shell 'mkdir -p /data/user/0/com.projectinfinity.kodi/files && echo infinity-upgrade-preservation-2103284 > /data/user/0/com.projectinfinity.kodi/files/fd285-update-sentinel'
adb shell dumpsys package com.projectinfinity.kodi > runtime285/parent-package.txt
adb install --no-incremental -r candidate285/Infinity-2103285-Native-FD-Crash-Repair-RC1.apk | tee runtime285/update-over-install.txt
grep -q Success runtime285/update-over-install.txt
adb shell cat /data/user/0/com.projectinfinity.kodi/files/fd285-update-sentinel | tr -d '\r' > runtime285/sentinel-after.txt
grep -qx 'infinity-upgrade-preservation-2103284' runtime285/sentinel-after.txt
adb shell dumpsys package com.projectinfinity.kodi > runtime285/package.txt
grep -q 'versionCode=2103285' runtime285/package.txt
adb shell am start -W -n com.projectinfinity.kodi/.Splash | tee runtime285/chooser-start.txt
grep -q 'Status: ok' runtime285/chooser-start.txt
sleep 3
adb shell pidof com.projectinfinity.kodi > runtime285/chooser-pid.txt
test -s runtime285/chooser-pid.txt
printf '%s\n' 'PASS Android x86_64 bionic FD tests and update-over-install 2103284 -> 2103285; synthetic private-file sentinel preserved; chooser starts.' 'NOT TESTED: physical Galaxy Fold, ARM64 Kodi playback, installed skin layout, native ambient hardware, full-system acceptance.' > runtime285/SUMMARY.txt
