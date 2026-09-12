#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get("INFINITY_KODI_SOURCE", ROOT / "kodi"))
CONTRACT = json.loads((ROOT / "patches/infinity-native-responsive-reflow/contract.json").read_text())

window = (SOURCE / "xbmc/windowing/android/WinSystemAndroid.cpp").read_text(encoding="utf-8")
bridge = (SOURCE / "tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in").read_text(encoding="utf-8")
main = (SOURCE / "tools/android/packaging/xbmc/src/Main.java.in").read_text(encoding="utf-8")
gradle = (SOURCE / "tools/android/packaging/xbmc/build.gradle.in").read_text(encoding="utf-8")
manifest = (SOURCE / "tools/android/packaging/xbmc/AndroidManifest.xml.in").read_text(encoding="utf-8")
splash_theme = (SOURCE / "tools/android/packaging/xbmc/res/values-v31/infinity_splash_theme.xml").read_text(encoding="utf-8")
cmake = (SOURCE / "xbmc/platform/android/activity/CMakeLists.txt").read_text(encoding="utf-8")
install = (SOURCE / "cmake/scripts/android/Install.cmake").read_text(encoding="utf-8")
state = (SOURCE / "xbmc/platform/android/activity/InfinityBridgeState.h").read_text(encoding="utf-8")

checks = {
    "strictly_newer_than_accepted_2103123": "versionCode 2103124" in gradle,
    "version_name": 'versionName "1.0.9-Native-Responsive-Reflow-Cumulative"' in gradle,
    # Package identity is asserted from the signed APK with aapt in the package job.
    # At source/preflight level the authoritative contract must remain pinned.
    "package_identity_contract": CONTRACT.get("package_id") == "com.projectinfinity.kodi",
    "v5_bridge_preserved": "static final int VERSION = 5" in bridge,
    "layout_listener_preserved": "implements View.OnLayoutChangeListener" in bridge,
    "java_callbacks_publish_only": "ReloadSkin" not in bridge,
    "generation_contract_preserved": "generation == m_generation" in state and "sequence == m_requested.sequence" in state,
    "native_refresh_preserved": "InfinityRefreshController" in main,
    "native_media_preserved": "Infinity.NativeDeviceMode" in window,
    "audio_policy_preserved": "Infinity.AudioPolicyApi" in window and "InfinityAudioPolicy.cpp" in cmake,
    "audio_focus_preserved": "InfinityAudioFocusHook.java" in install,
    # Deep branding owns launcher icon bindings in the manifest and the Android 12+
    # splash icon in the dedicated values-v31 theme resource, not in the manifest.
    "deep_branding_preserved": (
        'android:icon="@mipmap/ic_launcher"' in manifest
        and 'android:roundIcon="@mipmap/ic_launcher_round"' in manifest
        and "windowSplashScreenAnimatedIcon" in splash_theme
    ),
    "native_owner_marker": "Infinity.NativeReflowOwner" in window,
    "profile_gate": 'INFINITY_SKIN_ID = "skin.infinity.diggz"' in window,
    "profile_selector": 'GetSkinPath("Home.xml", &res)' in window,
    "settled_reflow": "std::chrono::milliseconds{220}" in window,
    "commit_before_schedule": window.find("state.CommitGeometry(request)") < window.find("InfinitySkinReflow().GeometryCommitted"),
    "app_thread_dispatch": "TMSG_EXECUTE_BUILT_IN" in window and '"ReloadSkin"' in window,
    "single_reload_site": window.count('"ReloadSkin"') == 1,
    "pip_bypass": window.count("pip-bypass") >= 2,
    "startup_no_reload_comment": "Startup establishes the already-loaded profile" in window,
}

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("FAIL: " + ", ".join(failed))

assert CONTRACT["kodi_sha"] == "a3a448d26b8d560a65655dab2cd122994dc4e146"
assert CONTRACT["base_source_commit"] == "9833c4751e0e5c6961ca32566bb2625151ebf983"
assert CONTRACT["base_version_code"] == 2103123
assert CONTRACT["version_code"] == 2103124
assert CONTRACT["base_bridge_version"] == 5
assert CONTRACT["owner"] == "native-app"
assert CONTRACT["reflow"]["settle_ms"] == 220

print("PASS: cumulative 2103123 -> 2103124 native responsive reflow contract")
for key in sorted(checks):
    print(f"PASS: {key}")
