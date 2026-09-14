#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y autoconf bison build-essential curl flex gawk git gperf \
  lib32stdc++6 lib32z1 lib32z1-dev libcurl4-openssl-dev unzip zip zlib1g-dev \
  ccache python3 nasm yasm imagemagick fonts-dejavu-core rapidjson-dev
sdkmanager 'platform-tools' 'platforms;android-35' 'build-tools;34.0.0' "ndk;$NDK_VER" >/dev/null
mkdir -p "$HOME/.android" preflight engine
if [ ! -f "$HOME/.android/debug.keystore" ]; then
  keytool -genkeypair -noprompt -keystore "$HOME/.android/debug.keystore" \
    -storepass android -keypass android -alias androiddebugkey -keyalg RSA -keysize 2048 \
    -validity 10000 -dname 'CN=Android Debug,O=Android,C=US'
fi

python3 -m py_compile \
  scripts/infinity_1_0_9_live_release.py \
  scripts/infinity_1_0_9_multiview_release.py \
  scripts/verify_infinity_live.py \
  scripts/verify_infinity_multiview.py \
  scripts/verify_infinity_multiview_apk.py \
  scripts/validate_infinity_multiview_java.py \
  scripts/infinity_upper_layer_repack.py \
  scripts/infinity_player_rotation.py \
  scripts/verify_infinity_player_rotation_apk.py \
  scripts/infinity_1_0_8_deep_rebrand.py \
  scripts/infinity_1_0_8_deep_audio_rebrand.py \
  scripts/infinity_1_0_8_deep_rebrand_preimage.py \
  scripts/infinity_audio_policy_source.py
python3 scripts/verify_infinity_live.py
python3 scripts/verify_infinity_multiview.py
python3 -m unittest discover -s tests/infinity_live -v
python3 -m unittest discover -s tests/infinity_multiview -v
if git ls-files 'addons/script.infinity.live/**' | grep -E '(__pycache__/|\.pyc$)' -q; then
  echo 'Tracked Python cache files are forbidden in script.infinity.live' >&2; exit 1
fi

git clone --depth 1 --branch 21.3-Omega https://github.com/xbmc/xbmc.git kodi
test "$(git -C kodi rev-parse HEAD)" = a3a448d26b8d560a65655dab2cd122994dc4e146

# Recreate the exact already-green Infinity source lineage first.
python3 scripts/infinity_audio_policy_source.py kodi --receipts engine/audio-receipts
python3 - <<'PY'
import importlib.util
from pathlib import Path
path=Path('scripts/infinity-responsive-v5.py')
spec=importlib.util.spec_from_file_location('responsive_v5_current', path)
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
source=Path('kodi'); module.install_refresh_controller(source); module.verify_refresh_controller(source)
PY
python3 scripts/validate_infinity_audio_policy.py --source kodi \
  --android-jar "$ANDROID_HOME/platforms/android-35/android.jar" --out preflight/audio-validation
python3 tests/infinity_audio/test_config.py --source kodi --out preflight/audio-config
python3 scripts/validate_infinity_skin_contract.py
python3 scripts/infinity_1_0_8_deep_rebrand_preimage.py --source kodi
python3 scripts/infinity_1_0_8_deep_audio_rebrand.py source --source kodi \
  --receipt engine/deep-audio-rebrand-source.json
python3 scripts/infinity_1_0_8_deep_audio_rebrand.py verify-source --source kodi
python3 scripts/infinity_player_rotation.py apply --source kodi --receipt engine/player-rotation-source.json
python3 scripts/infinity_player_rotation.py verify --source kodi
python3 scripts/infinity_1_0_9_live_release.py source --source kodi --receipt engine/live-release-source.json
python3 scripts/infinity_1_0_9_live_release.py verify-source --source kodi

# Multi-View is the only new source owner after the accepted Live candidate.
python3 scripts/infinity_1_0_9_multiview_release.py source --source kodi \
  --receipt engine/multiview-release-source.json
python3 scripts/infinity_1_0_9_multiview_release.py verify-source --source kodi
python3 scripts/validate_infinity_multiview_java.py --source kodi \
  --android-jar "$ANDROID_HOME/platforms/android-35/android.jar" --out preflight/multiview-java

# Preserve all established player/rotation lifecycle gates, and require the
# cumulative Java validator itself to stage the optional Multi-View owner.
python3 tests/infinity_rotation/test_lifecycle.py --source kodi --out preflight/rotation-lifecycle
python3 tests/infinity_rotation/test_history.py
grep -Fq "'InfinityMultiViewController'" scripts/validate-infinity71-java.py
python3 scripts/validate-infinity71-java.py --source kodi \
  --android-jar "$ANDROID_HOME/platforms/android-35/android.jar" --out engine/rotation-java

grep -q 'versionCode 2103130' kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q 'versionName "1.0.9-Live-ExoPlayer-MultiView-Candidate-1"' kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q "androidx.media3:media3-exoplayer:1.7.1" kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q "set(TARGET_SDK 35)" kodi/cmake/platform/android/android.cmake
grep -q 'PLAYER_ROTATION_FOLLOW_DEVICE' kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in
grep -q 'PLAYER_ROTATION_UNLOCKED' kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in
grep -q 'SCREEN_ORIENTATION_FULL_SENSOR' kodi/tools/android/packaging/xbmc/src/Main.java.in
grep -q '_infinityHasActiveVideo' kodi/tools/android/packaging/xbmc/src/Main.java.in
grep -q 'InfinityMultiViewController mInfinityMultiView' kodi/tools/android/packaging/xbmc/src/Main.java.in
grep -q 'mInfinityMultiView.handleIntent(intent)' kodi/tools/android/packaging/xbmc/src/Main.java.in
grep -q 'new ExoPlayer.Builder' kodi/tools/android/packaging/xbmc/src/InfinityMultiViewController.java.in
grep -q 'new TextureView(mActivity)' kodi/tools/android/packaging/xbmc/src/InfinityMultiViewController.java.in
! grep -q 'ACCELEROMETER_ROTATION' kodi/tools/android/packaging/xbmc/src/Main.java.in
! grep -R -E 'CobraTV|cobratv|libmpv|android.media.MediaPlayer' kodi/tools/android/packaging/xbmc/src/InfinityMultiViewController.java.in

echo 'PASS: ExoPlayer Multi-View preflight recreated accepted Infinity stack and added only the isolated 2-up owner'
