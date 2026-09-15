#!/usr/bin/env bash
set -euo pipefail

mkdir -p candidate
BASE=engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Engine-Base.apk
UNSIGNED=candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-unsigned.apk
FINAL=candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2.apk

# Fail immediately and descriptively if build-stage ownership/handoff is incomplete.
# This prevents late packaging/signing failures caused by a missing receipt, inventory,
# or mismatched engine filename.
for required in \
  "$BASE" \
  engine/overlay-inventory.json \
  engine/gui-render-hardening-source.json \
  engine/audio-receipts/cumulative-source.json \
  engine/deep-audio-rebrand-source.json \
  engine/player-rotation-source.json \
  engine/live-release-source.json \
  engine/touch-startup-guard-source.json \
  engine/cobra-full-source.json \
  engine/live-app-shell-engine.json \
  candidate/Infinity-Cobra-Theme-1.1.0.zip; do
  if [[ ! -s "$required" ]]; then
    echo "Missing Candidate 2 build/package handoff: $required" >&2
    exit 1
  fi
done

python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path('engine/live-app-shell-engine.json').read_text())
expected={
  'schema':2,
  'version_code':2103134,
  'version_name':'1.0.9-Cobra-Full-Feature-Candidate-2',
  'package':'com.projectinfinity.kodi',
  'application_label':'Infinity',
  'one_apk_two_environments':True,
  'one_android_launcher':True,
  'cobra_live_only':True,
  'live_only_multiview':True,
  'single_audio_owner':True,
  'dvr':True,
  'guide':True,
  'catchup':True,
  'fold_parity':True,
  'real_picture_in_picture':True,
  'rotation_shared_with_infinity':True,
  'refresh_policy_shared_with_infinity':True,
  'copied_cobratv_code':False,
  'renderer_hardening_schema':3,
  'renderer_changed':True,
  'android_resize_hardened':True,
  'protected_geometry_bridge_owner':'xbmc/platform/android/activity/InfinityBridgeState.h',
  'protected_geometry_bridge_rewritten':False,
}
for key,value in expected.items():
    assert m.get(key)==value, (key,m.get(key),value)
assert m.get('provider_contract')==['xtream','m3u'], m.get('provider_contract')
assert m.get('multiview_outputs')==[2,3,4], m.get('multiview_outputs')
assert m.get('player')=='androidx.media3.exoplayer 1.7.1', m.get('player')
assert m.get('source_commit'), 'missing source_commit'
print('PASS: Candidate 2 engine handoff manifest is complete')
PY

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
grep -q 'supportsPictureInPicture' candidate/manifest.txt
grep -q 'resizeableActivity' candidate/manifest.txt
grep -q 'android.supports_size_changes' candidate/manifest.txt
grep -q 'density' candidate/manifest.txt
grep -q 'uiMode' candidate/manifest.txt

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
      b'InfinityCobraDeviceBridge', b'player_api.php?username=', b'get_vod_streams',
      b'get_series_info', b'RECORDINGS', b'4 screens', b'CONTINUE WATCHING',
      b'cobra-health.json', b'AUDIO / SUBS', b'CUSTOM EPG FOR ACTIVE SOURCE', b'Cobra Guide',
      b'CAST / ROUTE', b'PictureInPictureParams', b'infinity_player_rotation',
      b'.kodi/userdata/addon_data/service.infinity.refresh', b'preferredDisplayModeId',
      b'fold-cover', b'fold-inner', b'multiview-start', b'multiview-stop', b'player-close'
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
print('PASS: signed Candidate 2 preserves engine, Cobra Theme 1.1 and Infinity Fold/PiP/rotation/refresh parity')
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
19. Multi-View controls must appear at the bottom, auto-hide after about 3.2 seconds, and reappear on tap. The old permanent top bar must not return.
20. Watch temperature/decoder stability for 4 feeds; 4-feed acceptance is device-dependent until proven on this device.

DVR
21. Record current Live TV. Verify persistent foreground notification and a playable file in Cobra Recordings.
22. Test both a direct MPEG-TS stream and an HLS stream if the provider permits recording.
23. Record from Guide. Test 30m/1h/2h/4h/manual-stop paths and storage guard.
24. Schedule a future recording; test after leaving Cobra. Reboot/package replacement should re-arm future schedules.
25. While provider connection limits allow: watch one while recording another; record from source A while watching source B; play an existing recording while another records.
26. Recordings screen: play, rename and delete. Long-press a scheduled item to cancel.

REMINDERS / CATCH-UP
27. Schedule a reminder and confirm notification opens Cobra for the relevant channel.
28. On a provider/channel marked archive-capable, play a past programme using catch-up. Non-archive channels must not falsely expose catch-up.

MOVIES / SERIES
29. Movies aggregates enabled Xtream providers and labels the provider for every title.
30. Series loads seasons/episodes. Play an episode and allow it to end; next episode should auto-start when another episode exists.
31. Stop a movie/episode after >5 seconds. Continue Watching must show the title and resume it. Near-complete titles should clear resume state.
32. Long-press Movies/Series to add/remove My List. Search must work within loaded provider libraries.
33. Verify decoder fallback and error reporting on a title the provider encodes differently from Live TV.

PROFILES / PARENTAL / LOCAL FILES
34. Create a second profile, optional PIN, and adult-category lock. Favorites/Recents/My List/Continue Watching must remain profile-scoped.
35. Test correct/incorrect PIN behavior. Adult-named categories must be filtered when locked.
36. Discover -> My Files must use Android's document picker and play a user-selected local video/audio file without broad-storage permission.

DISCOVER / UX
37. Open Discover modules and verify navigation remains touch/D-pad safe. Remote public web modules are a legal-content shell, not bundled TV content.
38. Verify larger touch targets, faster rail focus and responsive Fold/phone layouts.
39. Install Infinity-Cobra-Theme-1.1.0 as a small ZIP and use Reload Cobra UI Theme. Visual token changes must not require another native APK build.

FOLD / PIP / ROTATION / REFRESH — DEVICE PARITY
40. On the cover display in portrait, Live TV categories AND channel rows must remain visible. The channel pane must not collapse to zero width.
41. Open Cobra on the cover display, unfold to the inner display while browsing, and confirm the shell reflows without a crash, duplicate rail, frozen layout, or forced provider re-login.
42. Fold back to the cover display while browsing. Confirm compact layout returns cleanly and touch/D-pad navigation remains usable.
43. Start one Live channel, then fold/unfold during playback. Video/audio should survive; the player surface and controls should resize instead of tearing down the provider session.
44. Start 2-4 feed Multi-View, choose AUDIO 2/3/4, then fold/unfold. The grid must reflow and the same selected audio owner must remain selected.
45. With a single channel playing, press Home/leave Infinity. Cobra should enter real Android Picture-in-Picture when Android allows it. Player chrome must disappear in PiP.
46. If Android rejects PiP or PiP is unavailable, playback must pause rather than leaving hidden/ghost audio running in the background.
47. Enter PiP from Multi-View. Cobra must collapse Multi-View to the current audio-owner tile before PiP so only one feed continues in the PiP window.
48. Return from PiP to Cobra. Confirm the player is interactive, controls return, and closing playback rebuilds the correct cover/inner shell.
49. Enable Infinity's player rotation UNLOCKED mode, play Cobra video, and rotate the Fold. Cobra should use FULL_SENSOR only during active video; leaving playback/PiP/multi-window must return orientation control to Android.
50. Switch Infinity refresh policy between Auto/High Refresh/Balanced/Battery where available. Cobra must read the same policy, request the matching display mode for UI, yield for match-video playback, and yield in PiP/multi-window.
51. With battery saver enabled, verify Cobra caps the high-refresh request. If the device reports severe thermal status, Cobra must also cap/yield rather than forcing high refresh.
52. Check Cobra Health/device diagnostics after cover/inner/PiP tests: device class should report fold-cover/fold-inner where the hinge feature is exposed and window class should move compact/medium/expanded at the 600/840dp thresholds.

HEALTH / PRIVACY
53. Trigger at least one provider error and one player error, then Cobra Settings -> Cobra Health Snapshot. Verify useful state is present.
54. Snapshot must contain NO raw username/password or credential-bearing live/movie/series/timeshift URL.
55. No provider credentials, M3U URLs or EPG credentials may be baked into the APK artifact.
56. No proprietary CobraTV code/assets are bundled. This is an independently authored Infinity implementation using behavior/UX as reference only.
EOF

echo 'PASS: Cobra Full Feature Candidate 2 packaged, permanently signed and statically verified with Fold/PiP acceptance contract'
