#!/usr/bin/env bash
set -euo pipefail
mkdir -p candidate
BASE=engine/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1-Engine-Base.apk
UNSIGNED=candidate/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1-unsigned.apk
FINAL=candidate/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1.apk

python3 scripts/infinity71.py overlay --apk "$BASE" \
  --manifest engine/overlay-inventory.json --output candidate/with-lock-unsigned.apk
python3 scripts/infinity_upper_layer_repack.py candidate/with-lock-unsigned.apk candidate/upper-layer-unsigned.apk
python3 - <<'PY'
import zipfile
with zipfile.ZipFile('candidate/upper-layer-unsigned.apk') as z:
    required=(
      'assets/addons/service.infinity.compat/service.py',
      'assets/addons/service.infinity.refresh/service.py',
      'assets/addons/script.infinity.audiopolicy/addon.xml',
      'assets/addons/script.infinity.audiopolicy/default.py',
      'assets/addons/script.infinity.audiopolicy/contract.json',
      'assets/addons/script.infinity.live/addon.xml',
      'assets/addons/script.infinity.live/default.py',
      'assets/addons/script.infinity.live/resources/lib/app.py',
      'assets/addons/script.infinity.live/resources/lib/ui.py',
      'assets/addons/script.infinity.live/resources/lib/focus.py',
      'assets/addons/script.infinity.live/resources/lib/multiview.py',
      'assets/addons/script.infinity.live/resources/lib/m3u.py',
      'assets/addons/script.infinity.live/resources/lib/xmltv.py',
    )
    for name in required: assert name in z.namelist(),name
    assert not any('__pycache__' in n or n.endswith('.pyc') for n in z.namelist() if 'script.infinity.live/' in n)
PY

python3 scripts/infinity_1_0_9_multiview_release.py apk --input candidate/upper-layer-unsigned.apk \
  --output "$UNSIGNED" --receipt candidate/multiview-branding-apk.json
python3 scripts/infinity_1_0_9_multiview_release.py verify-apk --apk "$UNSIGNED"

for name in INFINITY_KEYSTORE_B64 INFINITY_STORE_PASSWORD INFINITY_KEY_PASSWORD INFINITY_KEY_ALIAS; do
  if [[ -z "${!name:-}" ]]; then echo "Missing permanent signing configuration: $name" >&2; exit 2; fi
done
bash scripts/sign-infinity71.sh "$UNSIGNED" "$FINAL"
"$ANDROID_HOME/build-tools/34.0.0/apksigner" verify --verbose --print-certs "$FINAL" | tee candidate/signing-verification.txt
grep -qi 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' candidate/signing-verification.txt
"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging "$FINAL" | tee candidate/badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103130' versionName='1.0.9-Live-ExoPlayer-MultiView-Candidate-1'" candidate/badging.txt
grep -q "application-label:'Infinity'" candidate/badging.txt
python3 scripts/infinity_1_0_9_multiview_release.py verify-apk --apk "$FINAL"
python3 scripts/verify_infinity_multiview_apk.py --apk "$FINAL" --engine "$BASE" \
  --source-receipt engine/audio-receipts/cumulative-source.json --out candidate/infinity-multiview-verification.json
python3 scripts/validate_infinity_skin_contract.py

python3 - <<'PY'
import re,zipfile
base='engine/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1-Engine-Base.apk'
final='candidate/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1.apk'
with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
    for name in a.namelist():
        if name.startswith('lib/') or re.fullmatch(r'classes\d*\.dex',name):
            assert name in b.namelist(),name
            assert a.read(name)==b.read(name),name
    required=(
      'assets/addons/service.infinity.compat/addon.xml',
      'assets/addons/service.infinity.compat/layout_service.py',
      'assets/addons/service.infinity.compat/theme_contract.py',
      'assets/addons/service.infinity.refresh/service.py',
      'assets/addons/script.infinity.audiopolicy/addon.xml',
      'assets/addons/script.infinity.audiopolicy/default.py',
      'assets/addons/script.infinity.audiopolicy/contract.json',
      'assets/addons/script.infinity.live/addon.xml',
      'assets/addons/script.infinity.live/resources/lib/app.py',
      'assets/addons/script.infinity.live/resources/lib/ui.py',
      'assets/addons/script.infinity.live/resources/lib/focus.py',
      'assets/addons/script.infinity.live/resources/lib/multiview.py',
      'assets/media/splash.jpg','assets/media/vendor_logo.png','assets/media/vendor_icon.png')
    for name in required: assert name in b.namelist(),name
print('PASS: signed Multi-View APK preserves its source-built DEX/native engine byte-for-byte')
PY

cp engine/audio-receipts/cumulative-source.json candidate/cumulative-audio-source.json
cp engine/deep-audio-rebrand-source.json candidate/deep-audio-rebrand-source.json
cp engine/player-rotation-source.json candidate/player-rotation-source.json
cp engine/live-release-source.json candidate/live-release-source.json
cp engine/multiview-release-source.json candidate/multiview-release-source.json
cp engine/multiview-engine.json candidate/multiview-engine.json
sha256sum "$FINAL" | tee candidate/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1.sha256

cat > candidate/DEVICE-TEST.txt <<'EOF'
INFINITY LIVE MULTI-VIEW CANDIDATE 1 — DEVICE ACCEPTANCE REQUIRED
Build/static success is not runtime acceptance. Do not lock this candidate until these pass.

1. Install/update Infinity 1.0.9 Live MultiView Candidate 1 (versionCode 2103130).
2. Keep the existing Infinity Live skin 1.0.5.98. Candidate 1 injects MULTI-VIEW from the bundled Live module; no new skin ZIP is required.
3. Infinity -> Live: select a primary channel, choose MULTI-VIEW, then select a different second channel.
4. Unfolded/wide display: confirm two independently moving live feeds render side-by-side.
5. Cover/portrait display: confirm the two feeds stack vertically and remain usable.
6. D-pad: Left/Up selects feed 1; Right/Down selects feed 2; OK/Enter transfers audio to the focused feed. Confirm exactly one feed is audible.
7. Touch: tap either feed and confirm focus/audio transfers cleanly.
8. Back/Escape: Multi-View closes both Android players and returns directly to the same Infinity Live session.
9. Home/background/app switch: both Multi-View decoders must release immediately; no background IPTV playback.
10. Test at least HLS+HLS and, when your provider supports it, TS+HLS. A device/provider decoder limitation may mark one tile UNAVAILABLE; Infinity must not crash.
11. Test channel URLs that require User-Agent/Referer/Origin headers when legitimately supplied by your provider.
12. Confirm normal single-stream Live preview/fullscreen still works after leaving Multi-View.
13. Regression: player rotation, normal video player, Cinema, responsive Fold/cover layouts, audio policy, AddonBrowser, FileBrowser and Install from ZIP.
14. Confirm no provider playlist, EPG URL, username or password is bundled in the APK. Multi-View request files are one-shot and deleted by the Android controller after reading.
15. Do not promote 4-up yet. First prove stable two-decoder hardware behavior on the target device.
EOF

echo 'PASS: Infinity Live ExoPlayer Multi-View Candidate 1 packaged, permanently signed and statically verified'
