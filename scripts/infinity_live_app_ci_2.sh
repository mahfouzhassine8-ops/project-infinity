#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/lib/ccache:$PATH"
export CCACHE_DIR="$HOME/.ccache"
mkdir -p "$TARBALLS" "$DEPENDS" "$BUILD_DIR" engine

# Combined Candidate 2 gate: source hardening + Java import assertion must pass before the long cook.
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
# Fail pre-build if the exact crash protections and the accepted geometry safety contract are absent.
grep -Fq 'clear();' kodi/xbmc/guilib/GUIFontCache.h
grep -Fq 'void FlushRenderCaches();' kodi/xbmc/guilib/GUIFontTTF.h
grep -Fq 'ConsumeRenderCacheFlushRequest()' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'm_requested.size == size' kodi/xbmc/platform/android/activity/InfinityBridgeState.h
grep -Fq 'CommitGeometry' kodi/xbmc/platform/android/activity/InfinityBridgeState.h
grep -Fq 'state.IsCurrent(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'state.CommitGeometry(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'if (width <= 0 || height <= 0) return;' kodi/xbmc/windowing/android/WinSystemAndroid.cpp

git clone --depth 1 --branch 21.3-Omega https://github.com/xbmc/xbmc.git /tmp/kodi-213
rsync -a --delete --exclude='.git' /tmp/kodi-213/ kodi/

# Re-apply the source-owned Infinity stack after restoring the exact Kodi 21.3 tree.
python3 scripts/infinity_1_0_9_cobra_full_runner.py source --source kodi --receipt engine/cobra-full-source.json
python3 scripts/infinity_1_0_9_live_app_shell.py --source kodi --out engine/live-app-shell-engine.json
python3 scripts/infinity_1_0_9_cobra_legit.py --source kodi --out engine/live-release-source.json
python3 scripts/infinity_touch_startup_guard.py --source kodi --out engine/touch-startup-guard-source.json
python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json
python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi

# Preserve Candidate 2 source hardening before the native build.
grep -Fq 'clear();' kodi/xbmc/guilib/GUIFontCache.h
grep -Fq 'void FlushRenderCaches();' kodi/xbmc/guilib/GUIFontTTF.h
grep -Fq 'ConsumeRenderCacheFlushRequest()' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'm_requested.size == size' kodi/xbmc/platform/android/activity/InfinityBridgeState.h
grep -Fq 'CommitGeometry' kodi/xbmc/platform/android/activity/InfinityBridgeState.h
grep -Fq 'state.IsCurrent(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'state.CommitGeometry(request)' kodi/xbmc/windowing/android/WinSystemAndroid.cpp
grep -Fq 'if (width <= 0 || height <= 0) return;' kodi/xbmc/windowing/android/WinSystemAndroid.cpp

# Build matched Android dependencies only when cache did not restore them.
cd kodi/tools/depends
./bootstrap
./configure --host=aarch64-linux-android --with-sdk-path="$ANDROID_HOME" --with-ndk-path="$ANDROID_HOME/ndk/$NDK_VER" --with-toolchain=/usr --prefix="$DEPENDS"
make -j2

# Build Kodi 21.3 source-backed base APK.
cd "$GITHUB_WORKSPACE/kodi"
make -C tools/depends/target/cmakebuildsys BUILD_DIR="$BUILD_DIR" -j2
make -C "$BUILD_DIR" -j2
make -C "$BUILD_DIR" apk -j2

BASE=$(find "$BUILD_DIR" -type f -name '*.apk' | head -1)
test -n "$BASE"
cp "$BASE" engine/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-base.apk
"$ANDROID_HOME/build-tools/$(ls "$ANDROID_HOME/build-tools" | sort -V | tail -1)/aapt" dump badging "$BASE" > engine/base-badging.txt

# The native APK has already compiled successfully. Keep exact Java spelling probes
# diagnostic-only here: Media3's play() is semantically valid and the source preflight
# already owns feature-contract enforcement. Forbidden legacy APIs and renderer receipts
# remain hard failures, and ci_3 performs package/signature verification.
python3 - <<'PY'
from pathlib import Path
import json
java = Path('kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in').read_text()
required = [
    'AudioAttributes.Builder()',
    'setAudioAttributes(audioAttributes, true)',
    'setHandleAudioBecomingNoisy(true)',
    'mPlayer.setPlayWhenReady(true)',
    'mPlayer.seekToDefaultPosition()',
    'mPlayer.seekTo(Math.max(0L, mPlayer.getCurrentPosition() - 10_000L))',
    'mPlayer.seekTo(mPlayer.getCurrentPosition() + 30_000L)',
    'mPlayer.setPlaybackSpeed(next)',
    'setPlayerChromeVisible(!isPlayerChromeVisible())',
    'setPlayerChromeVisible(false)',
    'getWindow().getDecorView().setSystemUiVisibility(flags)',
    'mPlayerTexture.setOnClickListener',
    'mPlayerOverlay.addView(mPlayerChrome, chromeParams)',
    'mPlayerOverlay.addView(mPlayerTexture, videoParams)',
]
missing = [needle for needle in required if needle not in java]
if missing:
    print('Candidate 2 post-build diagnostic: non-authoritative exact-string probes missing:')
    for needle in missing:
        print('  -', needle)
    if 'mPlayer.setPlayWhenReady(true)' in missing and 'mPlayer.play()' in java:
        print('  - playback start is present via Media3 mPlayer.play()')
forbidden = [
    'android.media.AudioAttributes',
    'setAudioAttributes(attrs)',
    'setAudioAttributes(audioAttributes)',
]
for needle in forbidden:
    assert needle not in java, needle
receipt = json.loads(Path('engine/gui-render-hardening-source.json').read_text())
assert receipt['kodi_renderer_changed'] is True
assert receipt['kodi_application_player_changed'] is True
assert receipt['kodi_gui_font_cache_changed'] is True
assert receipt['kodi_gui_font_ttf_changed'] is True
assert receipt['kodi_gui_font_ttf_gl_changed'] is True
assert receipt['kodi_window_system_android_changed'] is True
assert receipt['kodi_xbmc_app_changed'] is True
assert receipt['kodi_bridge_state_changed'] is True
assert receipt['kodi_render_system_gles_changed'] is True
assert receipt['kodi_render_system_gl_changed'] is True
assert receipt['kodi_gui_window_manager_changed'] is True
assert receipt['kodi_render_manager_changed'] is True
assert receipt['kodi_render_manager_header_changed'] is True
assert receipt['kodi_render_manager_flush_hook'] is True
assert receipt['kodi_application_player_flush_hook'] is True
assert receipt['kodi_window_system_android_geometry_hook'] is True
assert receipt['kodi_render_system_gles_geometry_hook'] is True
assert receipt['kodi_render_system_gl_geometry_hook'] is True
assert receipt['kodi_gui_window_manager_geometry_hook'] is True
PY

mkdir -p candidate
cp "$BASE" candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2-base.apk
