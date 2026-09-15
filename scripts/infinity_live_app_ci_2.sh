#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$TARBALLS" "$DEPENDS" "$BUILD_DIR" engine

# Candidate 2 preflight already recreated and verified the exact Infinity + Cobra
# source lineage in ./kodi. Keep that tree and add the build-stage renderer v3
# hardening exactly once before the native cook.
cd "$GITHUB_WORKSPACE"
python3 -m py_compile scripts/infinity_gui_render_hardening.py scripts/infinity_gui_render_hardening_v2.py scripts/infinity_gui_render_hardening_v3.py
JAVA=kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -Fq 'import androidx.media3.common.AudioAttributes;' "$JAVA" || {
  echo 'Candidate 2 generated InfinityLiveActivity.java.in is missing Media3 AudioAttributes import' >&2
  exit 1
}
python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi \
  --receipt engine/gui-render-hardening-source.json
python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi

grep -Fq 'clear();' kodi/xbmc/guilib/GUIFontCache.h
grep -Fq 'void FlushRenderCaches();' kodi/xbmc/guilib/GUIFontTTF.h
grep -Fq 'ConsumeRenderCacheFlushRequest()' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'm_requested.size == size' kodi/xbmc/platform/android/activity/InfinityBridgeState.h
grep -Fq 'CommitGeometry' kodi/xbmc/platform/android/activity/InfinityBridgeState.h
grep -Fq 'state.IsCurrent(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'state.CommitGeometry(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'if (width <= 0 || height <= 0) return;' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
! grep -Fq 'assert(bufferHandle == 0);' kodi/xbmc/guilib/GUIFontCache.h

# Build the same preflight-prepared source tree. Resetting ./kodi here destroys
# the ordered version lineage required by AppShell / single-app / Cobra layers.
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

# Native compile/package output is authoritative for generated Java behavior.
# Compiled feature and forbidden-owner checks remain hard gates. Renderer checks
# use the schema v3 receipt actually produced by the hardening owner.
python3 - <<'PY'
import hashlib, json, re, zipfile
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
      b'androidx/media3/exoplayer/ExoPlayer', b'RECORDINGS', b'CONTINUE WATCHING',
      b'cobra_custom_epg:', b'cobra-health.json', b'AUDIO / SUBS', b'CAST / ROUTE',
      b'PictureInPictureParams', b'infinity_player_rotation',
      b'.kodi/userdata/addon_data/service.infinity.refresh', b'preferredDisplayModeId',
      b'fold-cover', b'fold-inner', b'multiview-start', b'multiview-stop', b'player-close'
    )
    for needle in required:
        assert needle in joined, needle
    for forbidden in (b'CobraTV_', b'com/cobratv', b'libmpv', b'android/media/MediaPlayer'):
        assert forbidden not in joined, forbidden
    native_sha=hashlib.sha256(native).hexdigest()

receipt=json.loads(Path('engine/gui-render-hardening-source.json').read_text())
assert receipt['schema'] == 3
assert receipt['gui_font_cache_hardened'] is True
assert receipt['renderer_changed'] is True
assert receipt['android_resize_hardened'] is True
assert receipt['render_thread_cache_invalidation'] is True
assert receipt['post_playback_cache_invalidation'] is True
assert receipt['protected_geometry_bridge_owner'] == 'xbmc/platform/android/activity/InfinityBridgeState.h'
assert receipt['protected_geometry_bridge_rewritten'] is False
checks=receipt['checks']
for key in (
  'vertex_assignment_releases_old_buffer','vertex_assignment_assert_removed','font_flush_api',
  'manager_atomic_defer','manager_render_flush','android_callbacks_request_only',
  'no_direct_notify_resize_from_callbacks','render_loop_consumes_invalidation',
  'render_system_ready_gate','positive_geometry_runtime_gate','stale_request_runtime_gate',
  'commit_occurs_in_render_path','pre_resize_font_flush','positive_size_pack_rejects_invalid',
  'duplicate_requested_size_rejected','geometry_requires_engine_surface_pending',
  'generation_current_check_exists','commit_after_accept_api_exists','retry_api_exists'):
    assert checks[key] is True, key

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
  'engine_apk':str(apk),
  'engine_apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
  'native_lib_sha256':native_sha,
  'dex_sha256':dex,
  'renderer_hardening_schema':receipt['schema'],
  'renderer_changed':receipt['renderer_changed'],
  'android_resize_hardened':receipt['android_resize_hardened'],
  'protected_geometry_bridge_owner':receipt['protected_geometry_bridge_owner'],
  'protected_geometry_bridge_rewritten':receipt['protected_geometry_bridge_rewritten'],
  'post_build_dex_contract':'authoritative'
},indent=2,sort_keys=True)+'\n')
PY

mkdir -p candidate
cp "$BASE" candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-base.apk
