#!/usr/bin/env bash
set -euo pipefail

mkdir -p candidate
BASE=engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Engine-Base.apk
UNSIGNED=candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-unsigned.apk
FINAL=candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2.apk

python3 scripts/infinity71.py overlay --apk "$BASE" \
  --manifest engine/overlay-inventory.json --output candidate/with-lock-unsigned.apk
python3 scripts/infinity_upper_layer_repack.py \
  candidate/with-lock-unsigned.apk candidate/upper-layer-unsigned.apk

python3 scripts/infinity_1_0_9_cobra_full_fixups.py apk \
  --input candidate/upper-layer-unsigned.apk \
  --output "$UNSIGNED" \
  --receipt candidate/cobra-full-branding-apk.json
python3 scripts/infinity_1_0_9_cobra_full_fixups.py verify-apk --apk "$UNSIGNED"

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
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103134' versionName='1.0.9-Cobra-Full-Feature-Candidate-2'" candidate/badging.txt
grep -q "application-label:'Infinity'" candidate/badging.txt
test "$(grep -c '^launchable-activity:' candidate/badging.txt)" -eq 1

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump xmltree "$FINAL" AndroidManifest.xml \
  | tee candidate/manifest.txt
grep -q 'InfinityLiveActivity' candidate/manifest.txt
grep -q 'InfinityCobraRecordingService' candidate/manifest.txt
grep -q 'InfinityCobraReminderReceiver' candidate/manifest.txt
! grep -q 'InfinityLiveLauncher' candidate/manifest.txt
grep -q 'action.OPEN_LIVE' candidate/manifest.txt
grep -q 'usesCleartextTraffic' candidate/manifest.txt

python3 scripts/infinity_1_0_9_cobra_full_fixups.py verify-apk --apk "$FINAL"
python3 scripts/validate_infinity_skin_contract.py

python3 - <<'PY'
import json,re,zipfile
base='engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Engine-Base.apk'
final='candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2.apk'
with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
    for name in a.namelist():
        if name.startswith('lib/') or re.fullmatch(r'classes\d*\.dex', name):
            assert name in b.namelist(), name
            assert a.read(name)==b.read(name), name
    joined=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n))
    required=(
      b'InfinityLiveActivity', b'InfinityCobraFeatureRuntime', b'InfinityCobraRecordingService',
      b'player_api.php?username=', b'get_vod_streams', b'get_series_info', b'RECORDINGS',
      b'4 screens', b'CONTINUE WATCHING', b'cobra-health.json', b'AUDIO / SUBS',
      b'CUSTOM EPG FOR ACTIVE SOURCE', b'Cobra Guide', b'CAST / ROUTE'
    )
    for needle in required: assert needle in joined, needle
    for forbidden in (b'CobraTV_', b'com/cobratv', b'libmpv', b'android/media/MediaPlayer'):
        assert forbidden not in joined, forbidden
    names=set(b.namelist())
    required_theme={
      'assets/addons/script.infinity.cobra.theme/addon.xml',
      'assets/addons/script.infinity.cobra.theme/resources/cobra-theme.json',
    }
    assert required_theme <= names, required_theme - names
    theme=json.loads(b.read('assets/addons/script.infinity.cobra.theme/resources/cobra-theme.json'))
    assert theme['schema']==2
    assert theme['touch_target']>=48
print('PASS: signed Candidate 2 preserves source-built engine and bundles Cobra Theme 1.1 contract')
PY

cp engine/audio-receipts/cumulative-source.json candidate/cumulative-audio-source.json
cp engine/deep-audio-rebrand-source.json candidate/deep-audio-rebrand-source.json
cp engine/player-rotation-source.json candidate/player-rotation-source.json
cp engine/live-release-source.json candidate/live-release-source.json
cp engine/touch-startup-guard-source.json candidate/touch-startup-guard-source.json
cp engine/cobra-full-source.json candidate/cobra-full-source.json
cp engine/live-app-shell-engine.json candidate/live-app-shell-engine.json
cp addons/script.infinity.cobra.theme/resources/cobra-theme.json candidate/cobra-theme.json
cp docs/cobra-candidate-2-feature-contract.md candidate/FEATURE-CONTRACT.md
cp candidate/Infinity-Cobra-Theme-1.1.0.zip candidate/Infinity-Cobra-Theme-1.1.0-fast-update.zip 2>/dev/null || true
sha256sum "$FINAL" | tee candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2.sha256

cat > candidate/DEVICE-TEST.txt <<'EOF'
INFINITY 1.0.9 — COBRA FULL FEATURE CANDIDATE 2
DEVICE ACCEPTANCE REQUIRED — DO NOT LOCK BEFORE THESE PASS

ONE APP / REGRESSION
1. Update-install over permanently signed Candidate 1. Confirm versionCode 2103134 and ONE Infinity launcher.
2. Infinity must still boot and Open Cobra Live from the power/stop menu must still open the internal Cobra Activity.
3. Return to Infinity and retest Movies/Shows player, Cinema, rotation, Fold/cover responsive UI, audio policy, AddonBrowser, FileBrowser and Install from ZIP.

MULTI-PROVIDER
4. Add at least two legal/user-owned providers where available. Enable both. Live channels must appear together without restarting Cobra.
5. Rename provider using existing editor; long-press Sources and verify enable/disable, colour and icon changes.
6. Global Live search, Favorites and Recents must resolve the correct source automatically.
7. Bad provider/auth/network paths must remain specific and actionable; no generic cannot-load dead end.

GUIDE / EPG
8. Provider XMLTV current/next must load for each enabled source. Non-active source guide data must NOT be discarded.
9. Add a custom XMLTV URL for the active source; it must fill missing guide channels without invalidating provider EPG.
10. While Live TV is fullscreen, Guide must open while the current video continues behind it.
11. Long-press a guide entry/channel and test programme detail actions: Play, Remind, Record, and Catch-up only when provider archive capability exists.

PLAYBACK
12. Test HLS and MPEG-TS channels. Confirm video+audio, retry/fallback and 12-second stall recovery.
13. Test Audio/Subtitles selector on a stream that exposes multiple tracks.
14. Test Fit/Crop. Test Cast/Route as a SYSTEM route handoff; it is not claimed as a proprietary CobraTV cast backend.
15. Leave Live TV open long enough to exercise the in-Activity 30-minute provider auto-refresh; it must not interrupt an active player or Multi-View.

MULTI-VIEW
16. Test 2, 3 and 4 feeds. Device/provider connection limits may legitimately reject extra streams, but per-tile errors must not collapse other tiles.
17. Exactly one tile may own audio at a time. Switch audio by focus/tap and AUDIO buttons.
18. Wide/Fold: 2 feeds side-by-side and 3/4 in an adaptive grid. Portrait/cover: vertically stacked feeds.
19. Watch temperature/decoder stability for 4 feeds; 4-feed acceptance is device-dependent until proven on this device.

DVR
20. Record current Live TV. Verify persistent foreground notification and a playable file in Cobra Recordings.
21. Test both a direct MPEG-TS stream and an HLS stream if the provider permits recording.
22. Record from Guide. Test 30m/1h/2h/4h/manual-stop paths and storage guard.
23. Schedule a future recording; test after leaving Cobra. Reboot/package replacement should re-arm future schedules.
24. While provider connection limits allow: watch one while recording another; record from source A while watching source B; play an existing recording while another records.
25. Recordings screen: play, rename and delete. Long-press a scheduled item to cancel.

REMINDERS / CATCH-UP
26. Schedule a reminder and confirm notification opens Cobra for the relevant channel.
27. On a provider/channel marked archive-capable, play a past programme using catch-up. Non-archive channels must not falsely expose catch-up.

MOVIES / SERIES
28. Movies aggregates enabled Xtream providers and labels the provider for every title.
29. Series loads seasons/episodes. Play an episode and allow it to end; next episode should auto-start when another episode exists.
30. Stop a movie/episode after >5 seconds. Continue Watching must show the title and resume it. Near-complete titles should clear resume state.
31. Long-press Movies/Series to add/remove My List. Search must work within loaded provider libraries.
32. Verify decoder fallback and error reporting on a title the provider encodes differently from Live TV.

PROFILES / PARENTAL / LOCAL FILES
33. Create a second profile, optional PIN, and adult-category lock. Favorites/Recents/My List/Continue Watching must remain profile-scoped.
34. Test correct/incorrect PIN behavior. Adult-named categories must be filtered when locked.
35. Discover -> My Files must use Android's document picker and play a user-selected local video/audio file without broad-storage permission.

DISCOVER / UX
36. Open Discover modules and verify navigation remains touch/D-pad safe. Remote public web modules are a legal-content shell, not bundled TV content.
37. Verify larger touch targets, faster rail focus and responsive Fold/phone layouts.
38. Install Infinity-Cobra-Theme-1.1.0 as a small ZIP and use Reload Cobra UI Theme. Visual token changes must not require another native APK build.

HEALTH / PRIVACY
39. Trigger at least one provider error and one player error, then Cobra Settings -> Cobra Health Snapshot. Verify useful state is present.
40. Snapshot must contain NO raw username/password or credential-bearing live/movie/series/timeshift URL.
41. No provider credentials, M3U URLs or EPG credentials may be baked into the APK artifact.
42. No proprietary CobraTV code/assets are bundled. This is an independently authored Infinity implementation using behavior/UX as reference only.
EOF

echo 'PASS: Cobra Full Feature Candidate 2 packaged, permanently signed and statically verified'
