#!/usr/bin/env python3
"""Infinity 1.0.9 native surface/rotation handoff.

This patch intentionally sits *after* the accepted Cobra Live source stack.
It fixes the transition ownership bug revealed by on-device rotation testing:
Android's SurfaceHolder already supplies the new renderer size, but the previous
Infinity callback discarded it and re-read the Java View snapshot, which can still
contain the outgoing orientation for one or more frames.

Ownership after this patch:
- SurfaceHolder.surfaceChanged -> immediate renderer target geometry.
- InfinityCoreBridge.onLayoutChange -> settled Java layout / responsive facts.
- CXBMCApp::onResizeWindow -> notification only; it never republishes stale View size.
- CWinSystemAndroid -> sole geometry commit + native skin-profile reflow owner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PACKAGE_RELEASE = "1.0.9-Cobra-Legitimate-Live-Candidate-1"
PACKAGE_VERSION_CODE = 2103133
PATCH_RELEASE = "surface-rotation-handoff-v1"
STABLE_PASSES = 2


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def ensure_before(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    return once(text, anchor, addition + anchor, label)


COORDINATOR = r'''namespace
{
constexpr const char* INFINITY_SKIN_ID = "skin.infinity.diggz";
constexpr const char* INFINITY_REFLOW_OWNER = "app-v2";
constexpr int INFINITY_REFLOW_STABLE_PASSES = 2;

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
      // Startup adopts the profile Kodi already selected; startup is not a reflow.
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

    // A new committed geometry supersedes every older transition. Require only
    // two consecutive render-loop observations of the same target profile.
    // This removes the old 550-1000ms Python debounce without reloading on a
    // one-frame intermediate fold/rotation size.
    m_pendingMode = desired;
    m_pendingSequence = sequence;
    m_stablePasses = 0;
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
      m_stablePasses = 0;
      m_state = "settling";
      Publish();
      return;
    }

    ++m_stablePasses;
    if (m_stablePasses < INFINITY_REFLOW_STABLE_PASSES)
    {
      Publish();
      return;
    }

    CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
                                               "ReloadSkin");
    CLog::Log(LOGINFO,
              "Infinity surface handoff reflow: {} -> {} sequence={} stablePasses={}",
              m_loadedMode, m_pendingMode, m_pendingSequence, m_stablePasses);
    m_loadedMode = m_pendingMode;
    m_pendingMode.clear();
    m_pendingSequence = 0;
    m_stablePasses = 0;
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
    m_stablePasses = 0;
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
    home->SetProperty("Infinity.NativeReflowStablePasses", static_cast<int64_t>(m_stablePasses));
    home->SetProperty("Infinity.NativeReflowRequiredPasses",
                      static_cast<int64_t>(INFINITY_REFLOW_STABLE_PASSES));
  }

  void Reset()
  {
    m_skinId.clear();
    m_loadedMode.clear();
    m_pendingMode.clear();
    m_pendingSequence = 0;
    m_stablePasses = 0;
    m_state = "inactive";
  }

  std::string m_skinId;
  std::string m_loadedMode;
  std::string m_pendingMode;
  uint64_t m_pendingSequence{0};
  int m_stablePasses{0};
  std::string m_state{"inactive"};
};

CInfinitySkinReflowCoordinator& InfinitySkinReflow()
{
  static CInfinitySkinReflowCoordinator coordinator;
  return coordinator;
}
} // namespace

'''


def patch_app(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  // A resize does not destroy the surface. Keep its reference until surfaceDestroyed.\n  InfinitySyncDisplayState();\n}\n'''
    new_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  // Do not republish Java View geometry here. During rotation this callback can\n  // arrive while the View still reports the outgoing orientation. The SurfaceHolder\n  // callback owns the immediate renderer size; OnLayoutChange later confirms it.\n  m_inputHandler.setDPI(GetDPI());\n}\n'''
    text = once(text, old_resize, new_resize, "resize ownership")

    old_surface = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: %dx%d", __PRETTY_FUNCTION__, width, height);\n  // Surface dimensions can be buffer dimensions. The laid-out view is authoritative.\n  InfinitySyncDisplayState();\n}\n'''
    new_surface = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: %dx%d", __PRETTY_FUNCTION__, width, height);\n  // SurfaceHolder is the renderer's earliest authoritative pixel geometry. Queue it\n  // immediately instead of re-reading the Java View, which can still contain the\n  // outgoing orientation at this point. The later OnLayoutChange publication is\n  // still authoritative for responsive/device facts and safely deduplicates or\n  // corrects this request if Android reports another settled size.\n  m_infinity.QueueGeometry(width, height);\n  m_inputHandler.setDPI(GetDPI());\n}\n'''
    text = once(text, old_surface, new_surface, "surfaceChanged early geometry")
    path.write_text(text, encoding="utf-8")


def patch_window(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if 'INFINITY_REFLOW_OWNER = "app-v2"' in text:
        return
    if "CInfinitySkinReflowCoordinator" in text:
        raise RuntimeError("unexpected older native reflow coordinator already present")

    if '#include "addons/Skin.h"' not in text:
        text = ensure_before(text, '#include "application/Application.h"\n',
                             '#include "addons/Skin.h"\n', "skin include")
    if '#include "messaging/ApplicationMessenger.h"' not in text:
        text = ensure_before(text, '#include "application/Application.h"\n',
                             '#include "messaging/ApplicationMessenger.h"\n', "messenger include")
    if '#include <string>' not in text:
        text = ensure_before(text, '#include <memory>\n', '#include <string>\n', "string include")

    ctor = "CWinSystemAndroid::CWinSystemAndroid()"
    text = once(text, ctor, COORDINATOR + ctor, "native coordinator")

    old_pump = '''  const bool handled = m_winEvents->MessagePump();\n  ApplyInfinityGeometry();\n  return handled;\n'''
    new_pump = '''  const bool handled = m_winEvents->MessagePump();\n  InfinitySkinReflow().Observe();\n  ApplyInfinityGeometry();\n  const auto infinityReflowSnapshot = CXBMCApp::Get().InfinityState().Snapshot();\n  InfinitySkinReflow().Pump((infinityReflowSnapshot[14] & 1) != 0);\n  return handled;\n'''
    text = once(text, old_pump, new_pump, "render-loop reflow pump")

    old_equal = '''  if (m_nativeWindow->GetWidth() == width && m_nativeWindow->GetHeight() == height &&\n      m_nWidth == width && m_nHeight == height &&\n      CDisplaySettings::GetInstance().GetResolutionInfo(active).iWidth == width &&\n      CDisplaySettings::GetInstance().GetResolutionInfo(active).iHeight == height)\n  {\n    state.CommitGeometry(request);\n    return;\n  }\n'''
    new_equal = '''  if (m_nativeWindow->GetWidth() == width && m_nativeWindow->GetHeight() == height &&\n      m_nWidth == width && m_nHeight == height &&\n      CDisplaySettings::GetInstance().GetResolutionInfo(active).iWidth == width &&\n      CDisplaySettings::GetInstance().GetResolutionInfo(active).iHeight == height)\n  {\n    if (state.CommitGeometry(request))\n    {\n      const auto infinityReflowSnapshot = state.Snapshot();\n      InfinitySkinReflow().GeometryCommitted(request.sequence,\n                                             (infinityReflowSnapshot[14] & 1) != 0);\n    }\n    return;\n  }\n'''
    text = once(text, old_equal, new_equal, "already-sized geometry commit")

    old_final = '''  if (state.CommitGeometry(request))\n  {\n    if (auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME))\n'''
    new_final = '''  if (state.CommitGeometry(request))\n  {\n    const auto infinityReflowSnapshot = state.Snapshot();\n    InfinitySkinReflow().GeometryCommitted(request.sequence,\n                                           (infinityReflowSnapshot[14] & 1) != 0);\n    if (auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME))\n'''
    text = once(text, old_final, new_final, "resized geometry commit")
    path.write_text(text, encoding="utf-8")


def verify(source: Path) -> dict:
    gradle = source / "tools/android/packaging/xbmc/build.gradle.in"
    app = source / "xbmc/platform/android/activity/XBMCApp.cpp"
    window = source / "xbmc/windowing/android/WinSystemAndroid.cpp"
    bridge = source / "tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in"
    live = source / "tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in"

    gradle_text = gradle.read_text(encoding="utf-8")
    app_text = app.read_text(encoding="utf-8")
    window_text = window.read_text(encoding="utf-8")
    bridge_text = bridge.read_text(encoding="utf-8")
    live_text = live.read_text(encoding="utf-8")

    if f"versionCode {PACKAGE_VERSION_CODE}" not in gradle_text or f'versionName "{PACKAGE_RELEASE}"' not in gradle_text:
        raise RuntimeError("rotation-handoff patch refuses package identity drift from the accepted Cobra base")

    surface_start = app_text.index("void CXBMCApp::surfaceChanged")
    surface_end = app_text.index("void CXBMCApp::surfaceCreated", surface_start)
    surface_body = app_text[surface_start:surface_end]
    resize_start = app_text.index("void CXBMCApp::onResizeWindow")
    resize_end = app_text.index("void CXBMCApp::onDestroyWindow", resize_start)
    resize_body = app_text[resize_start:resize_end]

    checks = {
        "surface_queues_callback_geometry": "m_infinity.QueueGeometry(width, height);" in surface_body,
        "surface_does_not_reread_stale_view": "InfinitySyncDisplayState();" not in surface_body,
        "resize_does_not_reread_stale_view": "InfinitySyncDisplayState();" not in resize_body,
        "java_layout_confirmation_preserved": "onLayoutChange" in bridge_text and "_infinitySyncDisplayState" in bridge_text,
        "native_reflow_owner": 'INFINITY_REFLOW_OWNER = "app-v2"' in window_text,
        "two_pass_settle": "INFINITY_REFLOW_STABLE_PASSES = 2" in window_text,
        "old_timer_removed": "milliseconds{220}" not in window_text,
        "single_reload_site": window_text.count('"ReloadSkin"') == 1,
        "render_thread_geometry_preserved": "SetBuffersGeometry(width, height, 0)" in window_text and "ResizeWindow(width, height" in window_text,
        "pip_bypass": "pip-bypass" in window_text,
        "cobra_runtime_preserved": "class InfinityLiveActivity" in live_text and "new ExoPlayer.Builder" in live_text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("surface rotation handoff verification failed: " + ", ".join(failed))

    return {
        "schema": 1,
        "patch_release": PATCH_RELEASE,
        "package_release": PACKAGE_RELEASE,
        "package_version_code": PACKAGE_VERSION_CODE,
        "native_reflow_owner": "app-v2",
        "surface_geometry_owner": "SurfaceHolder.surfaceChanged",
        "settled_layout_owner": "InfinityCoreBridge.onLayoutChange",
        "stable_render_passes_before_reload": STABLE_PASSES,
        "python_reflow_fallback_expected_disabled": True,
        "skin_mask_required": False,
        "checks": checks,
        "files": {
            str(path.relative_to(source)): sha(path)
            for path in (gradle, app, window, bridge, live)
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("apply", "verify"))
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    if args.mode == "apply":
        patch_app(source / "xbmc/platform/android/activity/XBMCApp.cpp")
        patch_window(source / "xbmc/windowing/android/WinSystemAndroid.cpp")
    data = verify(source)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity native surface rotation handoff", json.dumps(data["checks"], sort_keys=True))


if __name__ == "__main__":
    main()
