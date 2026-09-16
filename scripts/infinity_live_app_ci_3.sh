#!/usr/bin/env bash
set -euo pipefail

mkdir -p candidate
BASE=engine/Infinity-1.0.9-2in1-SingleApp-Candidate-2-Engine-Base.apk
UNSIGNED=candidate/Infinity-1.0.9-2in1-SingleApp-Candidate-2-unsigned.apk
FINAL=candidate/Infinity-1.0.9-2in1-SingleApp-Candidate-2.apk

python3 scripts/infinity71.py overlay --apk "$BASE" \
  --manifest engine/overlay-inventory.json --output candidate/with-lock-unsigned.apk
python3 scripts/infinity_upper_layer_repack.py \
  candidate/with-lock-unsigned.apk candidate/upper-layer-unsigned.apk

python3 scripts/infinity_1_0_9_single_app.py apk \
  --input candidate/upper-layer-unsigned.apk \
  --output "$UNSIGNED" \
  --receipt candidate/live-app-shell-branding-apk.json
python3 scripts/infinity_1_0_9_single_app.py verify-apk --apk "$UNSIGNED"

for name in INFINITY_KEYSTORE_B64 INFINITY_STORE_PASSWORD INFINITY_KEY_PASSWORD INFINITY_KEY_ALIAS; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing permanent signing configuration: $name" >&2
    exit 2
  fi
done

bash scripts/sign-infinity71.sh "$UNSIGNED" "$FINAL"
"$ANDROID_HOME/build-tools/34.0.0/apksigner" verify --verbose --print-certs "$FINAL" \
  | tee candidate/signing-verification.txt
grep -qi 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' \
  candidate/signing-verification.txt

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging "$FINAL" | tee candidate/badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103132' versionName='1.0.9-2in1-SingleApp-Candidate-2'" candidate/badging.txt
grep -q "application-label:'Infinity'" candidate/badging.txt
test "$(grep -c '^launchable-activity:' candidate/badging.txt)" -eq 1

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump xmltree "$FINAL" AndroidManifest.xml \
  | tee candidate/manifest.txt
grep -q 'InfinityLiveActivity' candidate/manifest.txt
! grep -q 'InfinityLiveLauncher' candidate/manifest.txt
grep -q 'action.OPEN_LIVE' candidate/manifest.txt

python3 scripts/infinity_1_0_9_single_app.py verify-apk --apk "$FINAL"
python3 scripts/validate_infinity_skin_contract.py

python3 - <<'PY'
import re,zipfile
base='engine/Infinity-1.0.9-2in1-SingleApp-Candidate-2-Engine-Base.apk'
final='candidate/Infinity-1.0.9-2in1-SingleApp-Candidate-2.apk'
with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
    for name in a.namelist():
        if name.startswith('lib/') or re.fullmatch(r'classes\d*\.dex', name):
            assert name in b.namelist(), name
            assert a.read(name)==b.read(name), name
    joined=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n))
    for needle in (
        b'InfinityLiveActivity', b'infinity_experience',
        b'androidx/media3/exoplayer/ExoPlayer', b'MULTI-VIEW', b'XTREAM'
    ):
        assert needle in joined, needle
    for forbidden in (b'CobraTV', b'cobratv', b'libmpv', b'android/media/MediaPlayer'):
        assert forbidden not in joined, forbidden
print('PASS: signed single-app APK preserves source-built DEX/native engine byte-for-byte')
PY

cp engine/audio-receipts/cumulative-source.json candidate/cumulative-audio-source.json
cp engine/deep-audio-rebrand-source.json candidate/deep-audio-rebrand-source.json
cp engine/player-rotation-source.json candidate/player-rotation-source.json
cp engine/live-release-source.json candidate/live-release-source.json
cp engine/touch-startup-guard-source.json candidate/touch-startup-guard-source.json
cp engine/live-app-shell-source.json candidate/live-app-shell-source.json
cp engine/live-app-shell-engine.json candidate/live-app-shell-engine.json
sha256sum "$FINAL" | tee candidate/Infinity-1.0.9-2in1-SingleApp-Candidate-2.sha256

cat > candidate/DEVICE-TEST.txt <<'EOF'
INFINITY 2-IN-1 SINGLE-APP CANDIDATE 2 — DEVICE ACCEPTANCE REQUIRED

This is ONE installed Infinity APK/package with two internal experiences:
- Infinity/Kodi
- Cobra (dedicated Live Activity + Media3/ExoPlayer)

There must be ONE Android launcher icon: Infinity. Cobra is entered inside Infinity.

1. Update-install over the current signed Infinity build. Confirm versionCode 2103132.
2. Android launcher/app list: confirm there is exactly ONE Infinity entry and no separate Infinity Live/Cobra entry.
3. First normal launch: chooser offers Infinity and Cobra inside the same app.
4. Choose Infinity + "Launch & remember"; relaunch and confirm normal Infinity starts.
5. Switch to Cobra from the in-app experience path; confirm Cobra opens without launching a second Android app/package.
6. Cobra Settings -> set default to Cobra; relaunch Infinity and confirm Cobra starts directly inside the same package.
7. Set "Ask me each launch"; relaunch and confirm chooser returns.
8. Add an M3U source. Confirm channels load, groups/categories work, Search filters, Favorites and Recents persist.
9. Add an Xtream-compatible source using server/username/password. Confirm playlist and XMLTV URLs resolve without bundling credentials in the APK.
10. Guide: confirm current/next programme data appears when XMLTV is available.
11. Single-stream playback: confirm video+audio, channel switching, Favorite, Guide and PiP (when device supports PiP).
12. Multi-View: select two different channels. Confirm both video tiles move simultaneously.
13. Multi-View audio: tap or D-pad focus either tile and press OK. Confirm exactly one tile is audible.
14. Fold/cover layouts: wide display uses side-by-side Multi-View; portrait/cover stacks feeds vertically.
15. Back from playback -> Cobra channel browser. Back from Cobra root -> normal Infinity.
16. Background/home/app switch: all Live decoders release. No hidden IPTV playback.
17. Regression: normal Infinity player, Cinema, responsive Fold/cover UI, audio policy, rotation, AddonBrowser, FileBrowser and Install from ZIP.
18. Crash regression: aggressively tap during cold launch and during transitions. The native touch-startup GUI null guard must remain effective.
19. Privacy: confirm no provider URL, username, password, M3U or EPG data is bundled in the APK artifact.
20. Do not lock this branch until device acceptance passes.
EOF

echo 'PASS: Infinity 2-in-1 Single-App Candidate 2 packaged, permanently signed and statically verified'
