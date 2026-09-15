#!/usr/bin/env python3
"""Candidate 2 GUI/render hardening driver for the audited Infinity Android source lineage.

This wraps infinity_gui_render_hardening.py and supplies the Android bridge/window transforms that
match Infinity's already-audited geometry and SetEngineReady(false) contracts. All other hardening
and verification is delegated to the base transform.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

BASE = Path(__file__).with_name("infinity_gui_render_hardening.py")
spec = importlib.util.spec_from_file_location("infinity_gui_render_hardening_base", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def patch_xbmc_app_h(path: Path) -> None:
    """Add committed-size dedupe without assuming the surrounding audited formatting."""
    text = path.read_text(encoding="utf-8")
    if "m_committed.size == size && m_committed.generation == m_generation" in text:
        raise RuntimeError("Infinity committed-size dedupe already present unexpectedly")
    anchor = '''    m_requested = {size, m_generation, ++m_sequence};\n'''
    insert = '''    // Reject duplicate geometry that is already committed for the current surface generation.\n    if (m_committed.size == size && m_committed.generation == m_generation)\n    {\n      m_pending = false;\n      return;\n    }\n'''
    path.write_text(
        base.replace_once(text, anchor, insert + anchor, "Infinity committed-size dedupe anchor"),
        encoding="utf-8",
    )


def patch_win_system(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = base.replace_once(
        text,
        '#include "guilib/DispResource.h"\n',
        '#include "guilib/DispResource.h"\n#include "guilib/GUIFontManager.h"\n',
        "WinSystemAndroid GUIFontManager include",
    )

    old = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    new = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  // Android/NDK callbacks only set an atomic request. Consume it here, on Kodi's render/main loop,\n  // while the current GL context and GUI font objects are owned by this thread.\n  if (g_fontManager.ConsumeRenderCacheFlushRequest())\n  {\n    if (g_application.IsInitialized() && CServiceBroker::GetGUI() &&\n        CServiceBroker::GetRenderSystem())\n      g_fontManager.FlushRenderCaches();\n    else\n      g_fontManager.RequestRenderCacheFlush();\n  }\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    text = base.replace_once(text, old, new, "render-thread cache-flush consumer")

    old = '''  state.SetEngineReady(g_application.IsInitialized() && gui && m_android && m_bWindowCreated && m_nativeWindow);\n'''
    new = '''  state.SetEngineReady(g_application.IsInitialized() && gui &&\n                       CServiceBroker::GetRenderSystem() && m_android && m_bWindowCreated &&\n                       m_nativeWindow);\n'''
    text = base.replace_once(text, old, new, "render readiness gate")

    old = '''  if (!state.IsCurrent(request)) return; // An intervening surface/mode/size event superseded it.\n  // This runs in Kodi's main/render loop, not in Android's UI callbacks.\n  // Preserve EGL/surface ownership and the physical display mode/refresh-rate identity.\n  if (!m_nativeWindow->SetBuffersGeometry(width, height, 0) ||\n      !ResizeWindow(width, height, -1, -1))\n'''
    new = '''  if (width <= 0 || height <= 0) return;\n  if (!state.IsCurrent(request)) return; // An intervening surface/mode/size event superseded it.\n  // This runs in Kodi's main/render loop, not in Android's UI callbacks. Flush text geometry before\n  // changing the native buffer/GUI size so stale VBOs cannot survive into the resized frame.\n  g_fontManager.FlushRenderCaches();\n  // Preserve EGL/surface ownership and the physical display mode/refresh-rate identity.\n  if (!m_nativeWindow->SetBuffersGeometry(width, height, 0) ||\n      !ResizeWindow(width, height, -1, -1))\n'''
    text = base.replace_once(text, old, new, "safe geometry application")

    # The audited Infinity 7.1 source stack already clears engine readiness before releasing the
    # native window. Preserve that contract and add the render-thread font/VBO flush between them.
    old = '''bool CWinSystemAndroid::DestroyWindow()\n{\n  CLog::Log(LOGINFO, "CWinSystemAndroid::{}", __FUNCTION__);\n  CXBMCApp::Get().InfinityState().SetEngineReady(false);\n  m_nativeWindow.reset();\n'''
    new = '''bool CWinSystemAndroid::DestroyWindow()\n{\n  CLog::Log(LOGINFO, "CWinSystemAndroid::{}", __FUNCTION__);\n  CXBMCApp::Get().InfinityState().SetEngineReady(false);\n  // Render-thread/context owner: release cached font VBOs before the native window can disappear.\n  if (CServiceBroker::GetGUI() && CServiceBroker::GetRenderSystem())\n    g_fontManager.FlushRenderCaches();\n  m_nativeWindow.reset();\n'''
    text = base.replace_once(text, old, new, "window-destroy font cache flush")
    path.write_text(text, encoding="utf-8")


# base.apply() resolves transforms through its module globals. Override only the two transforms whose
# surrounding text is intentionally different in Infinity's accepted Android bridge lineage.
base.patch_xbmc_app_h = patch_xbmc_app_h
base.patch_win_system = patch_win_system


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify")
    p.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()

    if args.cmd == "apply":
        base.apply(args.source, args.receipt)
    else:
        import json
        print(json.dumps(base.verify(args.source.resolve()), indent=2, sort_keys=True))
        print("PASS: Infinity Kodi 21.3 GUI/render hardening v2 verified")


if __name__ == "__main__":
    main()
