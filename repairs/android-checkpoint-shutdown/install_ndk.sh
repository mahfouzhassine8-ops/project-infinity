#!/usr/bin/env bash
set -euo pipefail

ndk_path="$ANDROID_HOME/ndk/$NDK_VER"
ndk_valid() {
  test -x "$ndk_path/toolchains/llvm/prebuilt/linux-x86_64/bin/clang" &&
    test "$(awk -F= '/^Pkg.Revision[[:space:]]*=/{gsub(/[[:space:]]/,"",$2);print $2}' "$ndk_path/source.properties")" = "$NDK_VER" &&
    "$ndk_path/toolchains/llvm/prebuilt/linux-x86_64/bin/clang" --version >/dev/null
}

for attempt in 1 2 3; do
  if sdkmanager 'platform-tools' 'platforms;android-35' 'build-tools;34.0.0' "ndk;$NDK_VER" && ndk_valid; then
    exit 0
  fi
  echo "Pinned Android toolchain installation failed on attempt $attempt" >&2
  if ! ndk_valid; then
    # Only discard this incomplete pinned package in the ephemeral CI SDK.
    rm -rf -- "$ndk_path"
  fi
done
echo "Pinned Android toolchain could not be installed and verified" >&2
exit 1
