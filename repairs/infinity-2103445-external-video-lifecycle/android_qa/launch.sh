#!/usr/bin/env bash
# Disposable emulator only. Run as ONE shell process: the emulator runner
# otherwise splits multiline script commands and drops Python CLI arguments.
set +e
BASE="$(find runtime-445 -name 'Infinity-2103445-Combined-Original-Signer.apk' -type f -print -quit)"
if [[ -z "$BASE" ]]; then
  echo "BLOCKED: original signed baseline artifact missing"
  exit 1
fi
python3 repairs/infinity-2103445-external-video-lifecycle/android_qa/live_external_qa.py play \
  --apk "$BASE" --media android-evidence/fixture \
  --phase baseline --out android-evidence/baseline-playback
BASE_RESULT=$?
# Do NOT do this on a user's device: isolated disposable CI emulator only.
adb uninstall com.projectinfinity.kodi > android-evidence/qa-only-reinstall.txt 2>&1
python3 repairs/infinity-2103445-external-video-lifecycle/android_qa/live_external_qa.py play \
  --apk android-evidence/disposable-package/qa-DISCARD-DO-NOT-INSTALL-ON-PHONE.apk \
  --media android-evidence/fixture \
  --phase candidate --out android-evidence/corrected-playback
CANDIDATE_RESULT=$?
printf 'Baseline=%s Candidate=%s\n' "$BASE_RESULT" "$CANDIDATE_RESULT" | tee android-evidence/ADB-RESULTS.txt
# Result files and evidence determine PASS/BLOCKED; runner exits zero so both
# phases can always leave their honest artifacts for later review.
exit 0
