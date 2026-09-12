#!/usr/bin/env python3
# Cumulative native responsive reflow layer applied after Infinity Responsive Bridge v5.
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "patches/infinity-native-responsive-reflow/contract.json"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected 1 match, got {count}")
    return text.replace(old, new, 1)


def transform_gradle(text: str) -> str:
    text = replace_once(text, "versionCode 2103109", "versionCode 2103122", "version code")
    return replace_once(
        text,
        'versionName "1.0.8-Responsive-Bridge-v5"',
        'versionName "1.0.9-Native-Responsive-Reflow"',
        "version name",
    )


def transform_window(text: str) -> str:
    text = replace_once(
        text,
        '#include "application/Application.h"\n',
        '#include "addons/Skin.h"\n#include "application/Application.h"\n#include "messaging/ApplicationMessenger.h"\n',
        "native reflow includes",
    )
    text = replace_once(
        text,
        '#include <float.h>\n#include <memory>\n',
        '#include <float.h>\n#include <chrono>\n#include <memory>\n#include <string>\n',
        "native reflow standard includes",
    )

    anchor = '''using namespace KODI;\nusing namespace std::chrono_literals;\n\n'''
    coordinator = r'''using namespace KODI;
using namespace std::chrono_literals;

namespace
{
constexpr auto INFINITY_REFLOW_SETTLE = 220ms;
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
    }

    Publish();
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
      // Startup establishes the already-loaded profile. It is not a transition.
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

    // Reset the settle window on every committed geometry event. Android fold/rotate
    // animations can report several valid intermediate sizes; geometry follows them
    // immediately for touch alignment, while XML profile replacement waits for the
    // final stable profile.
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

    // Use Kodi's own asynchronous built-in path. ReloadSkin runs on Kodi's
    // application thread, preserves active window/focus where supported and restores
    // active video state. Never invoke it from Android's UI/configuration callback.
    CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
                                               "ReloadSkin");
    CLog::Log(LOGINFO,
              "Infinity native responsive reflow: {} -> {} sequence={} settle={}ms",
              m_loadedMode, m_pendingMode, m_pendingSequence,
              std::chrono::duration_cast<std::chrono::milliseconds>(INFINITY_REFLOW_SETTLE).count());
    m_loadedMode = m_pendingMode;
    m_pendingMode.clear();
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
    text = replace_once(text, anchor, coordinator, "native reflow coordinator")

    old_pump = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    new_pump = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  InfinitySkinReflow().Observe();\n  ApplyInfinityGeometry();\n  const auto snapshot = CXBMCApp::Get().InfinityState().Snapshot();\n  InfinitySkinReflow().Pump((snapshot[14] & 1) != 0);\n  return handled;\n}\n'''
    text = replace_once(text, old_pump, new_pump, "message-pump reflow wiring")

    old_commit = '''    CLog::Log(LOGINFO, "Infinity geometry committed: {}x{} generation={} sequence={} (bridge v4)",\n              width, height, request.generation, request.sequence);\n'''
    # Responsive v5 intentionally leaves this log text in the cumulative source.
    new_commit = '''    const auto snapshot = state.Snapshot();\n    InfinitySkinReflow().GeometryCommitted(request.sequence, (snapshot[14] & 1) != 0);\n    CLog::Log(LOGINFO, "Infinity geometry committed: {}x{} generation={} sequence={} (bridge v5)",\n              width, height, request.generation, request.sequence);\n'''
    text = replace_once(text, old_commit, new_commit, "geometry-commit reflow scheduling")
    return text


TRANSFORMS = {
    "tools/android/packaging/xbmc/build.gradle.in": transform_gradle,
    "xbmc/windowing/android/WinSystemAndroid.cpp": transform_window,
}


def apply(source: Path) -> None:
    for rel, transform in TRANSFORMS.items():
        path = source / rel
        if not path.is_file():
            raise ValueError(f"missing source file: {rel}")
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")


def verify(source: Path) -> None:
    gradle = (source / "tools/android/packaging/xbmc/build.gradle.in").read_text(encoding="utf-8")
    window = (source / "xbmc/windowing/android/WinSystemAndroid.cpp").read_text(encoding="utf-8")
    bridge = (source / "tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in").read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    checks = {
        "version_code": "versionCode 2103122" in gradle,
        "version_name": 'versionName "1.0.9-Native-Responsive-Reflow"' in gradle,
        "v5_native_facts_preserved": "Infinity.NativeDisplayRevision" in window and "Infinity.NativeWidthDp" in window,
        "event_driven_java_preserved": "implements View.OnLayoutChangeListener" in bridge and "view.requestLayout()" in bridge,
        "native_owner": 'Infinity.NativeReflowOwner' in window and 'INFINITY_REFLOW_OWNER = "app-v1"' in window,
        "render_thread_owner": "InfinitySkinReflow().GeometryCommitted" in window,
        "async_kodi_reload": 'PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,' in window and '"ReloadSkin"' in window,
        "profile_change_gate": "desired == m_loadedMode" in window and "CurrentSkinMode()" in window,
        "settle_debounce": "INFINITY_REFLOW_SETTLE = 220ms" in window,
        "pip_gate": "pictureInPicture" in window and "pip-bypass" in window,
        "infinity_skin_gate": 'INFINITY_SKIN_ID = "skin.infinity.diggz"' in window,
        "no_java_reload": "ReloadSkin" not in bridge,
        "single_native_reload_site": window.count('"ReloadSkin"') == 1,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError("native reflow verification failed: " + ", ".join(failed))

    if contract["base_bridge_version"] != 5 or contract["version_code"] != 2103122:
        raise ValueError("contract version mismatch")
    print("PASS: native responsive reflow", json.dumps(checks, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "verify"))
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    if args.mode == "source":
        apply(source)
        verify(source)
    else:
        verify(source)


if __name__ == "__main__":
    main()
