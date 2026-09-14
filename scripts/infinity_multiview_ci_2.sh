#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$TARBALLS" "$DEPENDS" "$BUILD_DIR"
cd kodi/tools/depends
./bootstrap
./configure --with-tarballs="$TARBALLS" --host=aarch64-linux-android \
  --with-sdk-path="$ANDROID_HOME" --with-ndk-path="$ANDROID_HOME/ndk/$NDK_VER" \
  --prefix="$DEPENDS" --enable-debug=yes
# Kodi 21.3 pins fontconfig 2.14.0 by SHA-512. Keep that checksum lock and use
# the known-good Freedesktop/GStreamer mirror rather than the unstable legacy URL.
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
APK=$(find kodi "$BUILD_DIR" -type f -name '*.apk' -print -quit); test -n "$APK"
BASE=engine/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1-Engine-Base.apk
cp "$APK" "$BASE"
python3 scripts/infinity71.py record-engine \
  --apk "$BASE" --output engine/overlay-inventory.json --source-commit "$GITHUB_SHA"
"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging "$BASE" | tee engine/base-badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103130' versionName='1.0.9-Live-ExoPlayer-MultiView-Candidate-1'" engine/base-badging.txt
grep -q "application-label:'Infinity'" engine/base-badging.txt
python3 - <<'PY'
import hashlib,json,re,zipfile,os
from pathlib import Path
apk=Path('engine/Infinity-1.0.9-Live-ExoPlayer-MultiView-Candidate-1-Engine-Base.apk')
with zipfile.ZipFile(apk) as z:
    dex={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
    joined=b''.join(z.read(n) for n in dex)
    native=z.read('lib/arm64-v8a/libkodi.so')
    for needle in (
        b'Published responsive v5', b'InfinityAudioFocusHook',
        b'PLAYER_ROTATION_FOLLOW_DEVICE', b'PLAYER_ROTATION_UNLOCKED',
        b'infinity_player_rotation', b'InfinityRotation',
        b'InfinityMultiViewController', b'infinity-multiview',
        b'androidx/media3', b'ExoPlayer', b'android/view/TextureView',
    ):
        assert needle in joined, needle
    for needle in (b'acquireAudioFocus',b'releaseAudioFocus',b'updateAudioPolicy'):
        assert needle in joined,needle
    for forbidden in (b'android/media/MediaPlayer', b'libmpv', b'CobraTV', b'cobratv'):
        assert forbidden not in joined, forbidden
    for needle in (
        b'Infinity.NativeDeviceMode', b'Infinity.AudioPolicyApi',
        b'Infinity AudioPolicy API 1 AudioTrack:', b'infinity-audio-policy.json',
    ):
        assert needle in native,needle
    native_sha=hashlib.sha256(native).hexdigest()
Path('engine/multiview-engine.json').write_text(json.dumps({
  'schema':1,
  'bridge_version':5,
  'platform_hook_api':2,
  'audio_policy_api':1,
  'player_rotation_api':1,
  'infinity_live_api':1,
  'infinity_multiview_api':1,
  'player_engine':'androidx.media3 ExoPlayer 1.9.2',
  'max_simultaneous_live_feeds':2,
  'simultaneous_audio_owners':1,
  'version_code':2103130,
  'version_name':'1.0.9-Live-ExoPlayer-MultiView-Candidate-1',
  'base_apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
  'libkodi_sha256':native_sha,
  'dex':dex,
  'source_commit':os.environ['GITHUB_SHA'],
  'kodi_application_player_changed':False,
  'kodi_renderer_changed':False,
  'android_multiview_overlay_added':True,
  'runtime_tested':False,
},indent=2,sort_keys=True)+'\n')
PY

echo 'PASS: source-backed Kodi 21.3 ExoPlayer Multi-View engine built with protected native/player owners intact'
