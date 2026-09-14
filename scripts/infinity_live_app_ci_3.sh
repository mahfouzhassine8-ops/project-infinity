#!/usr/bin/env bash
set -euo pipefail

mkdir -p candidate
BASE=engine/Infinity-1.0.9-Live-AppShell-Candidate-1-Engine-Base.apk
UNSIGNED=candidate/Infinity-1.0.9-Live-AppShell-Candidate-1-unsigned.apk
FINAL=candidate/Infinity-1.0.9-Live-AppShell-Candidate-1.apk

python3 scripts/infinity71.py overlay --apk "$BASE" \
  --manifest engine/overlay-inventory.json --output candidate/with-lock-unsigned.apk
python3 scripts/infinity_upper_layer_repack.py \
  candidate/with-lock-unsigned.apk candidate/upper-layer-unsigned.apk

python3 scripts/infinity_1_0_9_live_app_shell.py apk \
  --input candidate/upper-layer-unsigned.apk \
  --output "$UNSIGNED" \
  --receipt candidate/live-app-shell-branding-apk.json
python3 scripts/infinity_1_0_9_live_app_shell.py verify-apk --apk "$UNSIGNED"

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
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103131' versionName='1.0.9-Live-AppShell-Candidate-1'" candidate/badging.txt
grep -q "application-label:'Infinity'" candidate/badging.txt

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump xmltree "$FINAL" AndroidManifest.xml \
  | tee candidate/manifest.txt
grep -q 'InfinityLiveActivity' candidate/manifest.txt
grep -q 'InfinityLiveLauncher' candidate/manifest.txt
grep -q 'action.OPEN_LIVE' candidate/manifest.txt

python3 scripts/infinity_1_0_9_live_app_shell.py verify-apk --apk "$FINAL"
python3 scripts/validate_infinity_skin_contract.py

python3 - <<'PY'
import re,zipfile
base='engine/Infinity-1.0.9-Live-AppShell-Candidate-1-Engine-Base.apk'
final='candidate/Infinity-1.0.9-Live-AppShell-Candidate-1.apk'
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
print('PASS: signed AppShell APK preserves source-built DEX/native engine byte-for-byte')
PY

cp engine/audio-receipts/cumulative-source.json candidate/cumulative-audio-source.json
cp engine/deep-audio-rebrand-source.json candidate/deep-audio-rebrand-source.json
cp engine/player-rotation-source.json candidate/player-rotation-source.json
cp engine/live-release-source.json candidate/live-release-source.json
cp engine/touch-startup-guard-source.json candidate/touch-startup-guard-source.json
cp engine/live-app-shell-source.json candidate/live-app-shell-source.json
cp engine/live-app-shell-engine.json candidate/live-app-shell-engine.json
sha256sum "$FINAL" | tee candidate/Infinity-1.0.9-Live-AppShell-Candidate-1.sha256

cat > candidate/DEVICE-TEST.txt <<'EOF'
INFINITY LIVE APP-WITHIN-APP CANDIDATE 1 — DEVICE ACCEPTANCE REQUIRED

This is one installed Infinity APK with two Android environments:
- Infinity/Kodi
- Infinity Live (dedicated Activity + Media3/ExoPlayer)

1. Update-install over the current signed Infinity build. Confirm versionCode 2103131.
2. First normal launch: chooser offers Infinity and Infinity Live.
3. Choose Infinity + "Launch & remember"; relaunch and confirm normal Infinity starts.
4. Infinity Live Settings -> set default to Infinity Live; relaunch and confirm Live starts directly.
5. Set "Ask me each launch"; relaunch and confirm chooser returns.
6. Confirm Android launcher also exposes a direct "Infinity Live" entry from the same installed APK.
7. Add an M3U source. Confirm channels load, groups/categories work, Search filters, Favorites and Recents persist.
8. Add an Xtream-compatible source using server/username/password. Confirm playlist and XMLTV URLs resolve without bundling credentials in the APK.
9. Guide: confirm current/next programme data appears when XMLTV is available.
10. Single-stream playback: confirm video+audio, channel switching, Favorite, Guide and PiP (when device supports PiP).
11. Multi-View: select two different channels. Confirm both video tiles move simultaneously.
12. Multi-View audio: tap or D-pad focus either tile and press OK. Confirm exactly one tile is audible.
13. Fold/cover layouts: wide display uses side-by-side Multi-View; portrait/cover stacks feeds vertically.
14. Back from playback -> Live channel browser. Back from Live root -> normal Infinity.
15. Background/home/app switch: all Live decoders release. No hidden IPTV playback.
16. Regression: normal Infinity player, Cinema, responsive Fold/cover UI, audio policy, rotation, AddonBrowser, FileBrowser and Install from ZIP.
17. Crash regression: aggressively tap during cold launch and during transitions. The native touch-startup GUI null guard must remain effective.
18. Privacy: confirm no provider URL, username, password, M3U or EPG data is bundled in the APK artifact.
19. Do not lock this branch until device acceptance passes.
EOF

echo 'PASS: Infinity Live AppShell Candidate 1 packaged, permanently signed and statically verified'
