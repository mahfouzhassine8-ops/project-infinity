#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$TARBALLS" "$DEPENDS" "$BUILD_DIR" engine

# Combined Candidate 2 gate: source hardening + Java import assertion must pass before the long cook.
cd "$GITHUB_WORKSPACE"
python3 -m py_compile scripts/infinity_gui_render_hardening.py scripts/infinity_gui_render_hardening_v2.py
JAVA=kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -Fq 'import androidx.media3.common.AudioAttributes;' "$JAVA" || {
  echo 'Candidate 2 generated InfinityLiveActivity.java.in is missing Media3 AudioAttributes import' >&2
  exit 1
}
python3 scripts/infinity_gui_render_hardening_v2.py apply --source kodi \
  --receipt engine/gui-render-hardening-source.json
python3 scripts/infinity_gui_render_hardening_v2.py verify --source kodi
# Fail pre-build if the exact crash protections and the accepted geometry safety contract are absent.
grep -Fq 'clear();' kodi/xbmc/guilib/GUIFontCache.h
grep -Fq 'void FlushRenderCaches();' kodi/xbmc/guilib/GUIFontTTF.h
grep -Fq 'ConsumeRenderCacheFlushRequest()' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'm_requested.size == size' kodi/xbmc/platform/android/activity/XBMCApp.h
grep -Fq 'CommitGeometry' kodi/xbmc/platform/android/activity/XBMCApp.h
grep -Fq 'state.IsCurrent(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'state.CommitGeometry(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'if (width <= 0 || height <= 0) return;' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
! grep -Fq 'assert(bufferHandle == 0);' kodi/xbmc/guilib/GUIFontCache.h

cd kodi/tools/depends
./bootstrap
./configure --with-tarballs="$TARBALLS" --host=aarch64-linux-android \
  --with-sdk-path="$ANDROID_HOME" --with-ndk-path="$ANDROID_HOME/ndk/$NDK_VER" \
  --prefix="$DEPENDS" --enable-debug=yes

rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz" "$TARBALLS/fontconfig-2.14.0.tar.xz.sha512"
make -C target/fontconfig FULL_URL=https://gstreamer.freedesktop.org/data/src/mirror/fontconfig-2.14.0.tar.xz download
make -j"$(nproc)"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"

cd "$GITHUB_WORKSPACE"
CMAKE_BIN=$(sed -n 's/^CMAKE_COMMAND:INTERNAL=//p' "$BUILD_DIR/CMakeCache.txt")
test -x "$CMAKE_BIN"
"$CMAKE_BIN" -S "$GITHUB_WORKSPACE/kodi" -B "$BUILD_DIR" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
python3 scripts/infinity71.py native-check --build-dir "$BUILD_DIR"
# Native renderer compile happens as part of the one real Candidate 2 cook; no Java-only build is run.
make -C "$BUILD_DIR" -j"$(nproc)"
make -C "$BUILD_DIR" apk -j"$(nproc)"

APK=$(find kodi "$BUILD_DIR" -type f -name '*.apk' -print -quit)
test -n "$APK"
BASE=engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Engine-Base.apk
cp "$APK" "$BASE"

python3 scripts/infinity71.py record-engine \
  --apk "$BASE" --output engine/overlay-inventory.json --source-commit "$GITHUB_SHA"

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging "$BASE" | tee engine/base-badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103134' versionName='1.0.9-Cobra-Full-Feature-Candidate-2'" engine/base-badging.txt
grep -q "application-label:'Infinity'" engine/base-badging.txt
test "$(grep -c '^launchable-activity:' engine/base-badging.txt)" -eq 1

python3 - <<'PY'
import hashlib, json, os, re, zipfile
from pathlib import Path
apk=Path('engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-Engine-Base.apk')
with zipfile.ZipFile(apk) as z:
    dex={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
    joined=b''.join(z.read(n) for n in dex)
    native=z.read('lib/arm64-v8a/libkodi.so')
    required=(
      b'InfinityLiveActivity', b'InfinityCobraFeatureRuntime', b'InfinityCobraRecordingService',
      b'InfinityCobraReminderReceiver', b'InfinityCobraDeviceBridge',
      b'player_api.php?username=', b'get_live_streams', b'get_vod_streams', b'get_series_info',
      b'androidx/media3/exoplayer/ExoPlayer', b'RECORDINGS', b'MULTI-VIEW', b'CONTINUE WATCHING',
      b'cobra_custom_epg:', b'cobra-health.json', b'AUDIO / SUBS', b'CAST / ROUTE',
      b'PictureInPictureParams', b'infinity_player_rotation',
      b'.kodi/userdata/addon_data/service.infinity.refresh', b'preferredDisplayModeId',
      b'fold-cover', b'fold-inner', b'multiview-start', b'multiview-stop', b'player-close'
    )
    for needle in required: assert needle in joined, needle
    for forbidden in (b'CobraTV_', b'com/cobratv', b'libmpv', b'android/media/MediaPlayer'):
        assert forbidden not in joined, forbidden
    native_sha=hashlib.sha256(native).hexdigest()
receipt=json.loads(Path('engine/gui-render-hardening-source.json').read_text())
assert receipt['gui_font_cache_hardened'] is True
assert receipt['renderer_changed'] is True
assert receipt['android_resize_hardened'] is True
assert receipt['protected_geometry_bridge_rewritten'] is False
Path('engine/live-app-shell-engine.json').write_text(json.dumps({
  'schema':2,
  'bridge_version':5,
  'platform_hook_api':2,
  'audio_policy_api':1,
  'player_rotation_api':1,
  'infinity_live_api':3,
  'cobra_runtime_api':2,
  'cobra_device_parity_api':1,
  'version_code':2103134,
  'version_name':'1.0.9-Cobra-Full-Feature-Candidate-2',
  'one_apk_two_environments':True,
  'one_android_launcher':True,
  'host_environment':'Infinity/Kodi',
  'cobra_environment':'InfinityLiveActivity',
  'cobra_player':'androidx.media3.exoplayer 1.7.1',
  'xtream_provider_flow':True,
  'm3u_provider_flow':True,
  'multi_provider':True,
  'xmltv_epg':True,
  'custom_epg_gap_fill':True,
  'guide_playback_behind_overlay':True,
  'vod_movies':True,
  'vod_series':True,
  'series_auto_next':True,
  'continue_watching':True,
  'catchup_archive':True,
  'dvr_foreground_service':True,
  'record_from_guide':True,
  'programme_reminders':True,
  'profiles_parental':True,
  'max_simultaneous_live_feeds':4,
  'simultaneous_audio_owners':1,
  'cobra_fold_window_classes_dp':[600,840],
  'cobra_fold_hinge_awareness':True,
  'cobra_fold_multiview_reflow':True,
  'cobra_fold_multiview_preserves_audio_owner':True,
  'cobra_picture_in_picture':True,
  'cobra_pip_multiview_collapses_to_audio_owner':True,
  'cobra_background_ghost_audio_guard':True,
  'cobra_player_rotation_shared_policy':True,
  'cobra_adaptive_refresh_shared_policy':True,
  'cobra_refresh_battery_saver_guard':True,
  'cobra_refresh_thermal_guard':True,
  'cobra_multiwindow_policy_yield':True,
  'cobra_multiview_transient_chrome':True,
  'health_center_redacted_bridge':True,
  'external_theme_addon':'script.infinity.cobra.theme 1.1.0',
  'base_apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
  'libkodi_sha256':native_sha,
  'dex':dex,
  'source_commit':os.environ['GITHUB_SHA'],
  'kodi_application_player_changed':False,
  'kodi_renderer_changed':True,
  'kodi_gui_font_cache_hardened':True,
  'kodi_android_resize_hardened':True,
  'runtime_tested':False,
},indent=2,sort_keys=True)+'\n')
PY

echo 'PASS: source-backed Kodi 21.3 engine built with Cobra Full Feature Candidate 2 + GUI/render hardening + Infinity Fold device parity'
