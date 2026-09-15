#!/usr/bin/env bash
# Legitimate one-app Infinity/Cobra validation from the branch head.
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
  scripts/cobra_provider_contract.py \
  scripts/infinity_1_0_9_live_release.py \
  scripts/infinity_1_0_9_live_app_shell.py \
  scripts/infinity_1_0_9_single_app.py \
  scripts/infinity_1_0_9_cobra_legit.py \
  scripts/infinity_touch_startup_guard.py \
  scripts/infinity_upper_layer_repack.py \
  scripts/infinity_player_rotation.py \
  scripts/infinity_1_0_8_deep_rebrand.py \
  scripts/infinity_1_0_8_deep_audio_rebrand.py \
  scripts/infinity_1_0_8_deep_rebrand_preimage.py \
  scripts/infinity_audio_policy_source.py

# Cheap provider/UI/playback contract checks must pass before the long native build.
python3 -m unittest discover -s tests/cobra_live -v
python3 scripts/verify_infinity_live.py
python3 -m unittest discover -s tests/infinity_live -v
if git ls-files 'addons/**' | grep -E '(__pycache__/|\.pyc$)' -q; then
  echo 'Tracked Python cache files are forbidden in Infinity addons' >&2
  exit 1
fi

git clone --depth 1 --branch 21.3-Omega https://github.com/xbmc/xbmc.git kodi
test "$(git -C kodi rev-parse HEAD)" = a3a448d26b8d560a65655dab2cd122994dc4e146

# Recreate the exact accepted Infinity source lineage.
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

# Preserve the proven startup crash guard.
python3 scripts/infinity_touch_startup_guard.py apply --source kodi \
  --receipt engine/touch-startup-guard-source.json
python3 scripts/infinity_touch_startup_guard.py verify --source kodi
python3 tests/infinity_rotation/test_lifecycle.py --source kodi --out preflight/rotation-lifecycle
python3 tests/infinity_rotation/test_history.py
python3 scripts/validate-infinity71-java.py --source kodi \
  --android-jar "$ANDROID_HOME/platforms/android-35/android.jar" --out engine/rotation-java

# Build the one-launcher foundation, then replace its prototype Live shell with
# the legitimate Cobra provider + Media3 runtime.
python3 scripts/infinity_1_0_9_cobra_legit.py source --source kodi \
  --receipt engine/live-app-shell-source.json
python3 scripts/infinity_1_0_9_cobra_legit.py verify-source --source kodi

grep -q 'versionCode 2103133' kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q 'versionName "1.0.9-Cobra-Legitimate-Live-Candidate-1"' kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q "androidx.media3:media3-exoplayer:1.7.1" kodi/tools/android/packaging/xbmc/build.gradle.in
grep -q 'set(TARGET_SDK 35)' kodi/cmake/platform/android/android.cmake
grep -q 'android:name=".InfinityLiveActivity"' kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in
! grep -q 'android:name=".InfinityLiveLauncher"' kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in
grep -q 'android:usesCleartextTraffic="true"' kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in
grep -q 'Choose Your Experience' kodi/tools/android/packaging/xbmc/src/Splash.java.in
grep -q 'class InfinityLiveActivity' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'player_api.php?username=' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'get_live_streams' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'get_live_categories' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'parseM3u' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'new ExoPlayer.Builder' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'setEnableDecoderFallback(true)' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'openMultiView' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'COBRA • LIVE TV' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'Stream could not play' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -q 'ProgramPair pair = guide.get(channel);' kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in
grep -Fq 'CGUIComponent* gui = CServiceBroker::GetGUI();' kodi/xbmc/input/touch/generic/GenericTouchActionHandler.cpp
grep -Fq 'if (gui == nullptr)' kodi/xbmc/input/touch/generic/GenericTouchActionHandler.cpp
! grep -R -E 'com\.cobratv|CobraTV_|libmpv|android\.media\.MediaPlayer' \
  kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in

test -f addons/script.infinity.cobra.theme/addon.xml
test -f addons/script.infinity.cobra.theme/resources/cobra-theme.json
python3 - <<'PY'
from pathlib import Path
manifest = Path('kodi/tools/android/packaging/xbmc/AndroidManifest.xml.in').read_text()
launcher = '<category android:name="android.intent.category.LAUNCHER" />'
assert manifest.count(launcher) == 1, manifest.count(launcher)
assert 'InfinityLiveLauncher' not in manifest
print('PASS: exactly one Android launcher; Cobra remains internal')
PY

echo 'PASS: legitimate Cobra provider, playback, guide, Multi-View and one-app contracts are source-backed'
