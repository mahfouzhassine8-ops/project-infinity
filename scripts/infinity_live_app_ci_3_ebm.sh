#!/usr/bin/env bash
set -euo pipefail

python3 scripts/infinity_extended_background_mode.py verify --source kodi
python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path('engine/live-app-shell-engine.json').read_text())
expected={
  'version_code':2103135,
  'version_name':'1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background',
  'extended_background_mode':True,
  'extended_background_default_enabled':False,
  'extended_background_foreground_service':True,
  'extended_background_foreground_service_type':'specialUse',
  'extended_background_visible_notification':True,
  'extended_background_wake_lock':False,
}
for key,value in expected.items():
    assert m.get(key)==value, (key,m.get(key),value)
print('PASS: Extended Background engine handoff identity verified')
PY

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
sed \
  -e 's/2103134/2103135/g' \
  -e 's/1\.0\.9-Cobra-Full-Feature-Candidate-2/1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background/g' \
  -e 's/infinity_1_0_9_cobra_full_fixups\.py/infinity_1_0_9_cobra_full_fixups_ebm.py/g' \
  scripts/infinity_live_app_ci_3.sh > "$tmp"
bash "$tmp"

FINAL=candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background.apk

test -s "$FINAL"
cp engine/extended-background-source.json candidate/extended-background-source.json

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging "$FINAL" \
  | tee candidate/extended-background-badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103135' versionName='1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background'" \
  candidate/extended-background-badging.txt

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump xmltree "$FINAL" AndroidManifest.xml \
  | tee candidate/extended-background-manifest.txt
grep -q 'InfinityExtendedBackgroundService' candidate/extended-background-manifest.txt
grep -q 'FOREGROUND_SERVICE_SPECIAL_USE' candidate/extended-background-manifest.txt
grep -q 'specialUse' candidate/extended-background-manifest.txt

python3 - <<'PY'
import json,re,zipfile
from pathlib import Path
apk=Path('candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background.apk')
with zipfile.ZipFile(apk) as z:
    dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
    for needle in (
      b'InfinityExtendedBackgroundService',
      b'EXTENDED BACKGROUND MODE',
      b'Turn off',
      b'Infinity \xe2\x80\xa2 Extended Background Mode',
    ):
        assert needle in dex, needle
receipt=json.loads(Path('candidate/extended-background-source.json').read_text())
assert receipt['default_enabled'] is False
assert receipt['wake_lock'] is False
print('PASS: signed Extended Background APK contains the opt-in runtime and no wake-lock contract')
PY

cat > candidate/BUILD-VARIANT.txt <<'EOF'
INFINITY / COBRA FULL FEATURE CANDIDATE 2 — EXTENDED BACKGROUND VARIANT
Version code: 2103135
Version name: 1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background

This is NOT the original Candidate 2 build (versionCode 2103134).
Extended Background Mode is OFF by default.
Enable it in Cobra -> Settings -> EXTENDED BACKGROUND MODE.
When enabled, Android shows a persistent low-importance notification with a Turn off action.
No wake lock is used. Android may still reclaim the process under strong resource pressure.
EOF

cat >> candidate/DEVICE-TEST.txt <<'EOF'

EXTENDED BACKGROUND MODE — VARIANT-SPECIFIC ACCEPTANCE
57. Confirm this APK reports versionCode 2103135 and versionName ending in Extended-Background. Do not confuse it with base Candidate 2 versionCode 2103134.
58. Cobra -> Settings must show EXTENDED BACKGROUND MODE • OFF on a fresh/default install state.
59. Enable it. Confirm the setting changes to ON and Android shows the Infinity Extended Background Mode notification.
60. Press Home / switch apps without active playback. Return later and confirm Infinity/Cobra session continuity is improved without a forced UI reset during normal background pressure.
61. Use the notification Turn off action. Reopen Cobra Settings and confirm the mode is OFF and the foreground-service notification is gone.
62. Re-enable, then disable from Cobra Settings. Confirm normal Android background behavior returns immediately.
63. With the feature ON, repeat PiP, Fold, rotation, split-screen and player-close tests. The service must not create ghost audio, resume a stopped player, or override PiP pause/cleanup policy.
64. Confirm there is no unusual screen-on behavior or sustained wake lock. The feature raises process priority only through a user-visible Android foreground service.
EOF

sha256sum "$FINAL" | tee candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background.sha256

echo 'PASS: Extended Background Candidate 2 packaged, signed and independently identifiable'
