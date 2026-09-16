#!/usr/bin/env bash
set -euo pipefail
mkdir -p candidate
python3 scripts/infinity71.py overlay --apk engine/Infinity-1.0.9-Live-Candidate-1-Engine-Base.apk \
  --manifest engine/overlay-inventory.json --output candidate/with-lock-unsigned.apk
python3 scripts/infinity_upper_layer_repack.py candidate/with-lock-unsigned.apk candidate/upper-layer-unsigned.apk
python3 - <<'PY'
import zipfile
with zipfile.ZipFile('candidate/upper-layer-unsigned.apk') as z:
    required=(
      'assets/addons/service.infinity.compat/service.py','assets/addons/service.infinity.refresh/service.py',
      'assets/addons/script.infinity.audiopolicy/addon.xml','assets/addons/script.infinity.audiopolicy/default.py',
      'assets/addons/script.infinity.audiopolicy/contract.json','assets/addons/script.infinity.live/addon.xml',
      'assets/addons/script.infinity.live/default.py','assets/addons/script.infinity.live/resources/lib/app.py',
      'assets/addons/script.infinity.live/resources/lib/m3u.py','assets/addons/script.infinity.live/resources/lib/xmltv.py',
      'assets/addons/script.infinity.live/resources/lib/ui.py')
    for name in required: assert name in z.namelist(),name
    assert not any('__pycache__' in n or n.endswith('.pyc') for n in z.namelist() if 'script.infinity.live/' in n)
PY
python3 scripts/infinity_1_0_9_live_release.py apk --input candidate/upper-layer-unsigned.apk \
  --output candidate/Infinity-1.0.9-Live-Candidate-1-unsigned.apk --receipt candidate/live-branding-apk.json
python3 scripts/infinity_1_0_9_live_release.py verify-apk --apk candidate/Infinity-1.0.9-Live-Candidate-1-unsigned.apk
for name in INFINITY_KEYSTORE_B64 INFINITY_STORE_PASSWORD INFINITY_KEY_PASSWORD INFINITY_KEY_ALIAS; do
  if [[ -z "${!name:-}" ]]; then echo "Missing permanent signing configuration: $name" >&2; exit 2; fi
done
bash scripts/sign-infinity71.sh candidate/Infinity-1.0.9-Live-Candidate-1-unsigned.apk \
  candidate/Infinity-1.0.9-Live-Candidate-1.apk
"$ANDROID_HOME/build-tools/34.0.0/apksigner" verify --verbose --print-certs \
  candidate/Infinity-1.0.9-Live-Candidate-1.apk | tee candidate/signing-verification.txt
grep -qi 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' candidate/signing-verification.txt
"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging candidate/Infinity-1.0.9-Live-Candidate-1.apk | tee candidate/badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103127' versionName='1.0.9-Live-Candidate-1'" candidate/badging.txt
grep -q "application-label:'Infinity'" candidate/badging.txt
python3 scripts/infinity_1_0_9_live_release.py verify-apk --apk candidate/Infinity-1.0.9-Live-Candidate-1.apk
python3 scripts/verify_infinity_live_apk.py --apk candidate/Infinity-1.0.9-Live-Candidate-1.apk \
  --engine engine/Infinity-1.0.9-Live-Candidate-1-Engine-Base.apk \
  --source-receipt engine/audio-receipts/cumulative-source.json --out candidate/infinity-live-verification.json
python3 scripts/validate_infinity_skin_contract.py
python3 - <<'PY'
import re,zipfile
base='engine/Infinity-1.0.9-Live-Candidate-1-Engine-Base.apk'; final='candidate/Infinity-1.0.9-Live-Candidate-1.apk'
with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
    for name in a.namelist():
        if name.startswith('lib/') or re.fullmatch(r'classes\d*\.dex',name): assert a.read(name)==b.read(name),name
    required=('assets/addons/service.infinity.compat/addon.xml','assets/addons/service.infinity.compat/layout_service.py',
      'assets/addons/service.infinity.compat/theme_contract.py','assets/addons/service.infinity.refresh/service.py',
      'assets/addons/script.infinity.audiopolicy/addon.xml','assets/addons/script.infinity.audiopolicy/default.py',
      'assets/addons/script.infinity.audiopolicy/contract.json','assets/addons/script.infinity.live/addon.xml',
      'assets/addons/script.infinity.live/resources/lib/app.py','assets/addons/script.infinity.live/resources/lib/ui.py',
      'assets/media/splash.jpg','assets/media/vendor_logo.png','assets/media/vendor_icon.png')
    for name in required: assert name in b.namelist(),name
print('PASS: final signed APK preserves cumulative engine and bundles reviewed Infinity Live source')
PY
cp engine/audio-receipts/cumulative-source.json candidate/cumulative-audio-source.json
cp engine/deep-audio-rebrand-source.json candidate/deep-audio-rebrand-source.json
cp engine/player-rotation-source.json candidate/player-rotation-source.json
cp engine/live-release-source.json candidate/live-release-source.json
cp engine/live-engine.json candidate/live-engine.json
sha256sum candidate/Infinity-1.0.9-Live-Candidate-1.apk | tee candidate/Infinity-1.0.9-Live-Candidate-1.sha256
cat > candidate/DEVICE-TEST.txt <<'EOF'
DEVICE TEST REQUIRED — build/static success is not runtime acceptance.
1. Install/update Infinity 1.0.9 Live Candidate 1 (versionCode 2103127), then install skin 1.0.5.98.
2. Home/Cinema drawer/universal-nav Live entries must open Infinity Live; Back returns to Infinity.
3. Test authorized M3U/M3U8 + XMLTV + Xtream-style source: groups, logos, preview, switching, favorites, guide, persistence.
4. Test local M3U/Kodi VFS, fullscreen→Back roundtrip, and exit-owned playback cleanup.
5. Test unfolded/wide, cover/portrait, fold transitions, Light/Dark/OLED, and rotation/player regressions.
6. Confirm AddonBrowser/FileBrowser/Install from ZIP and all pre-existing Infinity owners remain functional.
7. Confirm no provider playlist, EPG URL, username or password is bundled in the APK.
Do not promote APK or skin to a locked baseline until device acceptance passes.
EOF
