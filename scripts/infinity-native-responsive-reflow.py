#!/usr/bin/env python3
"""Install the native responsive-reflow owner on the accepted 2103123 cumulative stack.

This layer is deliberately last. It accepts only the deep-rebrand/audio cumulative
version identity, changes only build.gradle.in + WinSystemAndroid.cpp, and verifies
that Responsive Bridge v5, native media, refresh, diagnostics and Audio Policy API 1
markers survive unchanged around the reflow addition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "patches/infinity-native-responsive-reflow/contract.json"

BASE_CODE = 2103123
NEW_CODE = 2103124
BASE_NAME = "1.0.8-Deep-Rebrand-Audio-1"
NEW_NAME = "1.0.9-Native-Responsive-Reflow-Cumulative"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected 1 match, got {count}")
    return text.replace(old, new, 1)


def ensure_before(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if text.count(anchor) != 1:
        raise ValueError(f"{label}: anchor count {text.count(anchor)}")
    return text.replace(anchor, addition + anchor, 1)


def transform_gradle(text: str) -> str:
    text = replace_once(text, f"versionCode {BASE_CODE}", f"versionCode {NEW_CODE}", "version code")
    return replace_once(text, f'versionName "{BASE_NAME}"', f'versionName "{NEW_NAME}"', "version name")


COORDINATOR = r'''namespace
{
constexpr auto INFINITY_REFLOW_SETTLE = std::chrono::milliseconds{220};
constexpr const char* INFINITY_SKIN_ID = "skin.infinity.diggz";
constexpr const char* INFINITY_REFLOW_OWNER = "app-v1";

class CInfinitySkinReflowCoordinator final
{
public:
  void Observe()
  {
    if (!g_SkinInfo || g_SkinInfo->ID() != INFINITY_SKIN_ID)
    {
      Reset();
      return;
    }

    const std::string skinId = g_SkinInfo->ID();
    if (m_skinId != skinId)
    {
      Reset();
      m_skinId = skinId;
      m_loadedMode = CurrentSkinMode();
      m_state = "ready";
      Publish();
    }
  }

  void GeometryCommitted(uint64_t sequence, bool pictureInPicture)
  {
    Observe();
    if (m_skinId.empty())
      return;

    if (pictureInPicture)
    {
      CancelPending("pip-bypass");
      return;
    }

    const std::string desired = CurrentSkinMode();
    if (desired.empty())
      return;

    if (m_loadedMode.empty())
    {
      // Startup establishes the already-loaded profile; startup is not a transition.
      m_loadedMode = desired;
      m_state = "ready";
      Publish();
      return;
    }

    if (desired == m_loadedMode)
    {
      CancelPending("ready");
      return;
    }

    // Geometry itself commits immediately for correct touch/render alignment. The
    // XML profile reload waits until fold/rotation intermediate sizes have settled.
    m_pendingMode = desired;
    m_pendingSequence = sequence;
    m_pendingSince = std::chrono::steady_clock::now();
    m_state = "settling";
    Publish();
  }

  void Pump(bool pictureInPicture)
  {
    Observe();
    if (m_skinId.empty() || m_pendingMode.empty())
      return;

    if (pictureInPicture)
    {
      CancelPending("pip-bypass");
      return;
    }

    const std::string desired = CurrentSkinMode();
    if (desired.empty() || desired == m_loadedMode)
    {
      CancelPending("ready");
      return;
    }

    if (desired != m_pendingMode)
    {
      m_pendingMode = desired;
      m_pendingSince = std::chrono::steady_clock::now();
      m_state = "settling";
      Publish();
      return;
    }

    if (std::chrono::steady_clock::now() - m_pendingSince < INFINITY_REFLOW_SETTLE)
      return;

    CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
                                               "ReloadSkin");
    CLog::Log(LOGINFO,
              "Infinity native responsive reflow: {} -> {} sequence={} settle={}ms",
              m_loadedMode, m_pendingMode, m_pendingSequence,
              std::chrono::duration_cast<std::chrono::milliseconds>(INFINITY_REFLOW_SETTLE).count());
    m_loadedMode = m_pendingMode;
    m_pendingMode.clear();
    m_pendingSequence = 0;
    m_state = "reloading";
    Publish();
  }

private:
  std::string CurrentSkinMode() const
  {
    if (!g_SkinInfo || g_SkinInfo->ID() != INFINITY_SKIN_ID)
      return {};
    RESOLUTION_INFO res;
    g_SkinInfo->GetSkinPath("Home.xml", &res);
    return res.strMode;
  }

  void CancelPending(const char* state)
  {
    if (m_pendingMode.empty() && m_state == state)
      return;
    m_pendingMode.clear();
    m_pendingSequence = 0;
    m_state = state;
    Publish();
  }

  void Publish() const
  {
    auto* gui = CServiceBroker::GetGUI();
    if (!gui)
      return;
    auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME);
    if (!home)
      return;
    home->SetProperty("Infinity.NativeReflowOwner", INFINITY_REFLOW_OWNER);
    home->SetProperty("Infinity.NativeReflowState", m_state);
    home->SetProperty("Infinity.NativeReflowLoadedProfile", m_loadedMode);
    home->SetProperty("Infinity.NativeReflowPendingProfile", m_pendingMode);
    home->SetProperty("Infinity.NativeReflowSequence", static_cast<int64_t>(m_pendingSequence));
    home->SetProperty("Infinity.NativeReflowSettleMs", static_cast<int64_t>(220));
  }

  void Reset()
  {
    m_skinId.clear();
    m_loadedMode.clear();
    m_pendingMode.clear();
    m_pendingSequence = 0;
    m_pendingSince = {};
    m_state = "inactive";
  }

  std::string m_skinId;
  std::string m_loadedMode;
  std::string m_pendingMode;
  uint64_t m_pendingSequence{0};
  std::chrono::steady_clock::time_point m_pendingSince{};
  std::string m_state{"inactive"};
};

CInfinitySkinReflowCoordinator& InfinitySkinReflow()
{
  static CInfinitySkinReflowCoordinator coordinator;
  return coordinator;
}
} // namespace

'''


def transform_window(text: str) -> str:
    # Cumulative-safe include ownership: add only what is absent.
    if '#include "addons/Skin.h"' not in text:
        text = ensure_before(text, '#include "application/Application.h"\n', '#include "addons/Skin.h"\n', "skin include")
    if '#include "messaging/ApplicationMessenger.h"' not in text:
        text = ensure_before(text, '#include "application/Application.h"\n', '#include "messaging/ApplicationMessenger.h"\n', "messenger include")
    if '#include <chrono>' not in text:
        text = ensure_before(text, '#include <memory>\n', '#include <chrono>\n', "chrono include")
    if '#include <string>' not in text:
        text = ensure_before(text, '#include <memory>\n', '#include <string>\n', "string include")

    if "class CInfinitySkinReflowCoordinator final" not in text:
        ctor = "CWinSystemAndroid::CWinSystemAndroid()"
        if text.count(ctor) != 1:
            raise ValueError(f"native coordinator constructor anchor count {text.count(ctor)}")
        text = text.replace(ctor, COORDINATOR + ctor, 1)

    if "InfinitySkinReflow().Pump" not in text:
        old = "  ApplyInfinityGeometry();\n  return handled;\n"
        new = (
            "  InfinitySkinReflow().Observe();\n"
            "  ApplyInfinityGeometry();\n"
            "  const auto infinityReflowSnapshot = CXBMCApp::Get().InfinityState().Snapshot();\n"
            "  InfinitySkinReflow().Pump((infinityReflowSnapshot[14] & 1) != 0);\n"
            "  return handled;\n"
        )
        if text.count(old) != 1:
            raise ValueError(f"MessagePump anchor count {text.count(old)}")
        text = text.replace(old, new, 1)

    if "InfinitySkinReflow().GeometryCommitted" not in text:
        old = "  if (state.CommitGeometry(request))\n  {\n"
        new = (
            "  if (state.CommitGeometry(request))\n"
            "  {\n"
            "    const auto infinityReflowSnapshot = state.Snapshot();\n"
            "    InfinitySkinReflow().GeometryCommitted(request.sequence, (infinityReflowSnapshot[14] & 1) != 0);\n"
        )
        if text.count(old) != 1:
            raise ValueError(f"geometry commit anchor count {text.count(old)}")
        text = text.replace(old, new, 1)
    return text


TRANSFORMS = {
    "tools/android/packaging/xbmc/build.gradle.in": transform_gradle,
    "xbmc/windowing/android/WinSystemAndroid.cpp": transform_window,
}


def apply(source: Path) -> None:
    # Refuse the previous mistaken responsive-v5-only lineage.
    gradle = (source / "tools/android/packaging/xbmc/build.gradle.in").read_text(encoding="utf-8")
    if f"versionCode {BASE_CODE}" not in gradle or f'versionName "{BASE_NAME}"' not in gradle:
        raise ValueError("Refusing non-cumulative base: expected accepted 2103123 Deep-Rebrand-Audio-1 source")
    for rel, transform in TRANSFORMS.items():
        path = source / rel
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")


def verify(source: Path) -> None:
    gradle = (source / "tools/android/packaging/xbmc/build.gradle.in").read_text(encoding="utf-8")
    window = (source / "xbmc/windowing/android/WinSystemAndroid.cpp").read_text(encoding="utf-8")
    bridge = (source / "tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in").read_text(encoding="utf-8")
    main = (source / "tools/android/packaging/xbmc/src/Main.java.in").read_text(encoding="utf-8")
    cmake = (source / "xbmc/platform/android/activity/CMakeLists.txt").read_text(encoding="utf-8")
    install = (source / "cmake/scripts/android/Install.cmake").read_text(encoding="utf-8")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    checks = {
        "monotonic_version": f"versionCode {NEW_CODE}" in gradle and f'versionName "{NEW_NAME}"' in gradle,
        "v5_bridge": "static final int VERSION = 5" in bridge and "Published responsive v5" in bridge,
        "v5_native_facts": "Infinity.NativeDisplayRevision" in window and "Infinity.NativeWidthDp" in window,
        "refresh_preserved": "InfinityRefreshController" in main,
        "native_media_preserved": "Infinity.NativeDeviceMode" in window,
        "audio_policy_preserved": "Infinity.AudioPolicyApi" in window and "InfinityAudioPolicy.cpp" in cmake,
        "audio_focus_preserved": "InfinityAudioFocusHook.java" in install,
        "native_owner": 'Infinity.NativeReflowOwner' in window and 'INFINITY_REFLOW_OWNER = "app-v1"' in window,
        "render_thread_schedule": "InfinitySkinReflow().GeometryCommitted" in window,
        "async_reload": "TMSG_EXECUTE_BUILT_IN" in window and '"ReloadSkin"' in window,
        "single_reload_site": window.count('"ReloadSkin"') == 1,
        "profile_gate": 'INFINITY_SKIN_ID = "skin.infinity.diggz"' in window,
        "settle_220": "std::chrono::milliseconds{220}" in window,
        "pip_gate": "pip-bypass" in window,
        "java_callbacks_publish_only": "ReloadSkin" not in bridge,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError("native cumulative reflow verification failed: " + ", ".join(failed))
    if contract["base_source_commit"] != "9833c4751e0e5c6961ca32566bb2625151ebf983":
        raise ValueError("wrong cumulative provenance")
    if contract["base_version_code"] != BASE_CODE or contract["version_code"] != NEW_CODE:
        raise ValueError("contract version lineage mismatch")
    print("PASS: cumulative native responsive reflow", json.dumps(checks, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "verify"))
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    if args.mode == "source":
        apply(source)
    verify(source)


if __name__ == "__main__":
    main()
