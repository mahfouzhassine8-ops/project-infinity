#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$TARBALLS" "$DEPENDS" "$BUILD_DIR" engine
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
BASE=engine/Infinity-1.0.9-Live-AppShell-Candidate-1-Engine-Base.apk
cp "$APK" "$BASE"

python3 scripts/infinity71.py record-engine \
  --apk "$BASE" --output engine/overlay-inventory.json --source-commit "$GITHUB_SHA"

"$ANDROID_HOME/build-tools/34.0.0/aapt" dump badging "$BASE" | tee engine/base-badging.txt
grep -q "package: name='com.projectinfinity.kodi' versionCode='2103131' versionName='1.0.9-Live-AppShell-Candidate-1'" engine/base-badging.txt
grep -q "application-label:'Infinity'" engine/base-badging.txt

python3 - <<'PY'
import hashlib, json, os, re, zipfile
from pathlib import Path
apk=Path('engine/Infinity-1.0.9-Live-AppShell-Candidate-1-Engine-Base.apk')
with zipfile.ZipFile(apk) as z:
    dex={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
    joined=b''.join(z.read(n) for n in dex)
    native=z.read('lib/arm64-v8a/libkodi.so')
    for needle in (
        b'InfinityLiveActivity',
        b'infinity_experience',
        b'Choose your Infinity experience',
        b'androidx/media3/exoplayer/ExoPlayer',
        b'MULTI-VIEW',
        b'XTREAM',
    ):
        assert needle in joined, needle
    for forbidden in (b'CobraTV', b'cobratv', b'libmpv', b'android/media/MediaPlayer'):
        assert forbidden not in joined, forbidden
    native_sha=hashlib.sha256(native).hexdigest()

Path('engine/live-app-shell-engine.json').write_text(json.dumps({
  'schema':1,
  'bridge_version':5,
  'platform_hook_api':2,
  'audio_policy_api':1,
  'player_rotation_api':1,
  'infinity_live_api':1,
  'live_app_shell_api':1,
  'version_code':2103131,
  'version_name':'1.0.9-Live-AppShell-Candidate-1',
  'one_apk_two_environments':True,
  'host_environment':'Infinity/Kodi',
  'live_environment':'InfinityLiveActivity',
  'live_player':'androidx.media3.exoplayer 1.7.1',
  'direct_live_launcher':True,
  'startup_chooser':True,
  'max_simultaneous_live_feeds':2,
  'simultaneous_audio_owners':1,
  'base_apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
  'libkodi_sha256':native_sha,
  'dex':dex,
  'source_commit':os.environ['GITHUB_SHA'],
  'kodi_application_player_changed':False,
  'kodi_renderer_changed':False,
  'runtime_tested':False,
},indent=2,sort_keys=True)+'\n')
PY

echo 'PASS: source-backed Kodi 21.3 AppShell engine built with dedicated Infinity Live Activity'
