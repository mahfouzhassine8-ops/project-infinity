#!/usr/bin/env bash
set -euo pipefail

mkdir -p candidate
BASE=engine/Infinity-1.0.9-Cobra-Legitimate-Live-Candidate-1-Engine-Base.apk
UNSIGNED=candidate/Infinity-1.0.9-Cobra-Legitimate-Live-Candidate-1-unsigned.apk
FINAL=candidate/Infinity-1.0.9-Cobra-Legitimate-Live-Candidate-1.apk

python3 scripts/infinity71.py overlay --apk "$BASE" \
  --manifest engine/overlay-inventory.json --output candidate/with-lock-unsigned.apk
python3 scripts/infinity_upper_layer_repack.py \
  candidate/with-lock-unsigned.apk candidate/upper-layer-unsigned.apk

python3 scripts/infinity_1_0_9_cobra_legit.py apk \
  --input candidate/upper-layer-unsigned.apk \
  --output "$UNSIGNED" \
  --receipt candidate/live-app-shell-branding-apk.json
python3 scripts/infinity_1_0_9_cobra_legit.py verify-apk --apk "$UNSIGNED"

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
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103133' versionName='1.0.9-Cobra-Legitimate-Live-Candidate-1'" candidate/badging.txt
grep -q "application-label:'Infinity'" candidate/badging.txt
test "$(grep -c '^launchable-activity:' candidate/badging.txt)" -eq 1

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump xmltree "$FINAL" AndroidManifest.xml \
  | tee candidate/manifest.txt
grep -q 'InfinityLiveActivity' candidate/manifest.txt
! grep -q 'InfinityLiveLauncher' candidate/manifest.txt
grep -q 'action.OPEN_LIVE' candidate/manifest.txt
grep -q 'usesCleartextTraffic' candidate/manifest.txt

python3 scripts/infinity_1_0_9_cobra_legit.py verify-apk --apk "$FINAL"
python3 scripts/validate_infinity_skin_contract.py

python3 - <<'PY'
import re,zipfile
base='engine/Infinity-1.0.9-Cobra-Legitimate-Live-Candidate-1-Engine-Base.apk'
final='candidate/Infinity-1.0.9-Cobra-Legitimate-Live-Candidate-1.apk'
with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
    for name in a.namelist():
        if name.startswith('lib/') or re.fullmatch(r'classes\d*\.dex', name):
            assert name in b.namelist(), name
            assert a.read(name)==b.read(name), name
    joined=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n))
    for needle in (
        b'InfinityLiveActivity', b'infinity_experience',
        b'player_api.php?username=', b'get_live_streams', b'get_live_categories',
        b'androidx/media3/exoplayer/ExoPlayer', b'MULTI-VIEW',
        b'Stream could not play'
    ):
        assert needle in joined, needle
    for forbidden in (b'CobraTV_', b'com/cobratv', b'libmpv', b'android/media/MediaPlayer'):
        assert forbidden not in joined, forbidden
    names=set(b.namelist())
    required_theme={
      'assets/addons/script.infinity.cobra.theme/addon.xml',
      'assets/addons/script.infinity.cobra.theme/resources/cobra-theme.json',
    }
    assert required_theme <= names, required_theme - names
print('PASS: signed APK preserves source-built engine and bundles independent Cobra theme addon')
PY

cp engine/audio-receipts/cumulative-source.json candidate/cumulative-audio-source.json
cp engine/deep-audio-rebrand-source.json candidate/deep-audio-rebrand-source.json
cp engine/player-rotation-source.json candidate/player-rotation-source.json
cp engine/live-release-source.json candidate/live-release-source.json
cp engine/touch-startup-guard-source.json candidate/touch-startup-guard-source.json
cp engine/live-app-shell-source.json candidate/live-app-shell-source.json
cp engine/live-app-shell-engine.json candidate/live-app-shell-engine.json
cp addons/script.infinity.cobra.theme/resources/cobra-theme.json candidate/cobra-theme.json
sha256sum "$FINAL" | tee candidate/Infinity-1.0.9-Cobra-Legitimate-Live-Candidate-1.sha256

cat > candidate/DEVICE-TEST.txt <<'EOF'
INFINITY 1.0.9 — COBRA LEGITIMATE LIVE CANDIDATE 1
DEVICE ACCEPTANCE REQUIRED — DO NOT LOCK BEFORE THESE PASS

ONE APP CONTRACT
1. Update-install over the current permanently signed Infinity build. Confirm versionCode 2103133.
2. Android launcher/app list must show exactly ONE Infinity entry. No separate Cobra or Infinity Live icon.
3. Launch Infinity -> Choose Your Experience -> Infinity or Cobra. Both must stay in the same Android package.
4. Remember Infinity, relaunch; remember Cobra, relaunch; Ask on Next Launch must restore the chooser.

PROVIDER LOGIN — NON-NEGOTIABLE
5. Add the real Xtream-compatible service using server + username + password. TEST & SAVE must authenticate and populate Live channels.
6. If the provider uses plain http://, it must still connect. If available, test an https:// provider too.
7. Wrong password must produce a specific provider/authentication error, not a generic "cannot load" message.
8. Bad hostname must report server/DNS failure; unreachable server must report timeout; HTTP failures must show the HTTP code.
9. Add a real M3U/M3U8 source. Verify channel names, groups, relative stream URLs and provider User-Agent/Referer headers when supplied.

LIVE TV + GUIDE
10. Categories/groups must populate and filter correctly. Search, Favorites and Recents must persist.
11. XMLTV must populate current/next programme text when the provider exposes guide data. EPG failure must not break playable channels.
12. Selecting a channel must create a visible Media3/ExoPlayer surface with VIDEO AND AUDIO.
13. Test both MPEG-TS and HLS channels when available. Xtream TS/HLS fallback must retry once when the provider's preferred container fails.
14. PREV/NEXT, Favorite, Guide, Back and player chrome must work with touch and D-pad/remote navigation.

MULTI-VIEW
15. Choose Multi-View and select a second channel. Both tiles must render moving video simultaneously.
16. Switching focus/tapping AUDIO 1 or AUDIO 2 must leave exactly one audible tile without recreating Infinity.
17. Wide/Fold inner display: feeds side by side. Portrait/cover: feeds stack vertically.

INFINITY REGRESSION
18. Return to Infinity must restore the normal Infinity/Kodi experience and release Cobra players.
19. Confirm normal Infinity Movies/Shows player, Cinema, rotation, responsive Fold/cover UI, audio policy, AddonBrowser, FileBrowser and Install from ZIP remain intact.
20. Aggressively tap during cold launch/transitions; the native touch-startup crash guard must remain effective.

FAST VISUAL UPDATE CONTRACT
21. Cobra Settings -> RELOAD COBRA UI THEME must reread script.infinity.cobra.theme/resources/cobra-theme.json.
22. Future color/spacing/row-height visual tuning ships as a small Cobra Theme ZIP; it must not require another native APK build.

PRIVACY / SOURCE BOUNDARY
23. No provider URL, username, password, M3U or EPG credentials may be baked into the APK artifact.
24. No proprietary CobraTV code/assets are bundled. Cobra is an independently authored Infinity experience.
EOF

echo 'PASS: legitimate Cobra Live candidate packaged, permanently signed and statically verified'
