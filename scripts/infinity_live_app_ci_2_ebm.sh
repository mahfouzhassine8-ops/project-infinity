#!/usr/bin/env bash
set -euo pipefail

# The base build script owns every renderer/native/compiler contract. Run an
# identity-adjusted copy so Candidate 2 and the Extended Background variant stay
# independently identifiable without editing the protected base script in place.
python3 scripts/infinity_extended_background_mode.py verify --source kodi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
sed \
  -e 's/2103134/2103135/g' \
  -e 's/1\.0\.9-Cobra-Full-Feature-Candidate-2/1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background/g' \
  scripts/infinity_live_app_ci_2.sh > "$tmp"
bash "$tmp"

BASE=engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background-Engine-Base.apk

test -s "$BASE"
test -s engine/extended-background-source.json

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump xmltree "$BASE" AndroidManifest.xml \
  | tee engine/extended-background-manifest.txt
grep -q 'InfinityExtendedBackgroundService' engine/extended-background-manifest.txt
grep -q 'FOREGROUND_SERVICE_SPECIAL_USE' engine/extended-background-manifest.txt
grep -q 'specialUse' engine/extended-background-manifest.txt

python3 - <<'PY'
import hashlib, json, re, zipfile
from pathlib import Path

apk=Path('engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background-Engine-Base.apk')
with zipfile.ZipFile(apk) as z:
    dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex', n))
    for needle in (
        b'InfinityExtendedBackgroundService',
        b'EXTENDED BACKGROUND MODE',
        b'Infinity \xe2\x80\xa2 Extended Background Mode',
        b'FOREGROUND_SERVICE_TYPE_SPECIAL_USE',
    ):
        assert needle in dex, needle

receipt=json.loads(Path('engine/extended-background-source.json').read_text())
assert receipt['extended_background_mode'] is True
assert receipt['default_enabled'] is False
assert receipt['wake_lock'] is False
assert receipt['version_code'] == 2103135
assert receipt['release'] == '1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background'

manifest_path=Path('engine/live-app-shell-engine.json')
manifest=json.loads(manifest_path.read_text())
manifest.update({
    'extended_background_mode': True,
    'extended_background_default_enabled': False,
    'extended_background_foreground_service': True,
    'extended_background_foreground_service_type': 'specialUse',
    'extended_background_visible_notification': True,
    'extended_background_wake_lock': False,
    'extended_background_receipt_sha256': hashlib.sha256(
        Path('engine/extended-background-source.json').read_bytes()).hexdigest(),
})
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
print('PASS: compiled engine contains opt-in Extended Background runtime')
PY
