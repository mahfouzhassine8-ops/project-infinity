#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$TARBALLS" "$DEPENDS" "$BUILD_DIR" engine
cd "$GITHUB_WORKSPACE"

# The preflight step owns reconstruction of the exact accepted Infinity/Cobra source
# lineage. Build stage 2 must compile that verified tree in place; it must never reset
# kodi/ to stock source or replay the version stack independently.
python3 -m py_compile scripts/infinity_gui_render_hardening.py scripts/infinity_gui_render_hardening_v2.py scripts/infinity_gui_render_hardening_v3.py
JAVA=kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -Fq 'import androidx.media3.common.AudioAttributes;' "$JAVA" || {
  echo 'Candidate 2 generated InfinityLiveActivity.java.in is missing Media3 AudioAttributes import' >&2
  exit 1
}
grep -q 'versionCode 2103134' kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q 'versionName "1.0.9-Cobra-Full-Feature-Candidate-2"' kodi/tools/android/packaging/xbmc/build.gradle.in

# Apply and verify the source-built GUI/render crash hardening over the already
# prepared Candidate 2 tree.
python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi
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

# Preserve source-level ownership/privacy gates immediately before the expensive
# native build so a late transform cannot reintroduce forbidden player/code paths.
! grep -R -E 'com\.cobratv|CobraTV_|libmpv|android\.media\.MediaPlayer' \
  kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in \
  kodi/tools/android/packaging/xbmc/src/InfinityCobra*.java.in

cd kodi/tools/depends
./bootstrap
./configure --with-tarballs="$TARBALLS" --host=aarch64-linux-android \
  --with-sdk-path="$ANDROID_HOME" --with-ndk-path="$ANDROID_HOME/ndk/$NDK_VER" \
  --prefix="$DEPENDS" --enable-debug=yes
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"

cd "$GITHUB_WORKSPACE"
CMAKE_BIN=$(sed -n 's/^CMAKE_COMMAND:INTERNAL=//p' "$BUILD_DIR/CMakeCache.txt")
test -x "$CMAKE_BIN"
"$CMAKE_BIN" -S "$GITHUB_WORKSPACE/kodi" -B "$BUILD_DIR" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
python3 scripts/infinity71.py native-check --build-dir "$BUILD_DIR"
make -C "$BUILD_DIR" -j"$(nproc)"
