#!/usr/bin/env python3
"""Candidate 2 GUI/render hardening driver for Infinity's audited Kodi 21.3 Android lineage.

The accepted Infinity bridge already owns generation/sequence validation, positive-size packing,
duplicate-request rejection and commit-after-success semantics. This driver preserves that protected
bridge instead of rewriting it, then hardens the actual GUIFontCache/CVertexBuffer lifecycle and
moves all Android-triggered font/VBO invalidation onto Kodi's render/main loop.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).with_name("infinity_gui_render_hardening.py")
spec = importlib.util.spec_from_file_location("infinity_gui_render_hardening_base", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def patch_win_system(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = base.replace_once(
        text,
        '#include "guilib/DispResource.h"\n',
        '#include "guilib/DispResource.h"\n#include "guilib/GUIFontManager.h"\n',
        "WinSystemAndroid GUIFontManager include",
    )

    old = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    new = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  // Android/NDK callbacks only publish an atomic invalidation request. Consume it here on Kodi's\n  // render/main loop, where the current GL context and GUI font objects are owned.\n  if (g_fontManager.ConsumeRenderCacheFlushRequest())\n  {\n    if (g_application.IsInitialized() && CServiceBroker::GetGUI() &&\n        CServiceBroker::GetRenderSystem())\n      g_fontManager.FlushRenderCaches();\n    else\n      g_fontManager.RequestRenderCacheFlush();\n  }\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    text = base.replace_once(text, old, new, "render-thread cache-flush consumer")

    old = '''  state.SetEngineReady(g_application.IsInitialized() && gui && m_android && m_bWindowCreated && m_nativeWindow);\n'''
    new = '''  state.SetEngineReady(g_application.IsInitialized() && gui &&\n                       CServiceBroker::GetRenderSystem() && m_android && m_bWindowCreated &&\n                       m_nativeWindow);\n'''
    text = base.replace_once(text, old, new, "render readiness gate")

    old = '''  if (!state.IsCurrent(request)) return; // An intervening surface/mode/size event superseded it.\n  // This runs in Kodi's main/render loop, not in Android's UI callbacks.\n  // Preserve EGL/surface ownership and the physical display mode/refresh-rate identity.\n  if (!m_nativeWindow->SetBuffersGeometry(width, height, 0) ||\n      !ResizeWindow(width, height, -1, -1))\n'''
    new = '''  if (width <= 0 || height <= 0) return;\n  if (!state.IsCurrent(request)) return; // An intervening surface/mode/size event superseded it.\n  // This runs in Kodi's main/render loop, not in Android's UI callbacks. Flush text geometry before\n  // changing native buffers/GUI dimensions so a stale font VBO cannot cross the resize boundary.\n  g_fontManager.FlushRenderCaches();\n  // Preserve EGL/surface ownership and the physical display mode/refresh-rate identity.\n  if (!m_nativeWindow->SetBuffersGeometry(width, height, 0) ||\n      !ResizeWindow(width, height, -1, -1))\n'''
    text = base.replace_once(text, old, new, "safe geometry application")

    old = '''bool CWinSystemAndroid::DestroyWindow()\n{\n  CLog::Log(LOGINFO, "CWinSystemAndroid::{}", __FUNCTION__);\n  CXBMCApp::Get().InfinityState().SetEngineReady(false);\n  m_nativeWindow.reset();\n'''
    new = '''bool CWinSystemAndroid::DestroyWindow()\n{\n  CLog::Log(LOGINFO, "CWinSystemAndroid::{}", __FUNCTION__);\n  CXBMCApp::Get().InfinityState().SetEngineReady(false);\n  // Render/context owner: dispose cached font VBOs before the native window/context can disappear.\n  if (CServiceBroker::GetGUI() && CServiceBroker::GetRenderSystem())\n    g_fontManager.FlushRenderCaches();\n  m_nativeWindow.reset();\n'''
    text = base.replace_once(text, old, new, "window-destroy font cache flush")
    path.write_text(text, encoding="utf-8")


def verify_v2(source: Path) -> dict:
    source = source.resolve()
    rels = [
        "xbmc/guilib/GUIFontCache.h",
        "xbmc/guilib/GUIFontCache.cpp",
        "xbmc/guilib/GUIFontTTF.h",
        "xbmc/guilib/GUIFontTTF.cpp",
        "xbmc/guilib/GUIFontManager.h",
        "xbmc/guilib/GUIFontManager.cpp",
        "xbmc/platform/android/activity/XBMCApp.h",
        "xbmc/platform/android/activity/XBMCApp.cpp",
        "xbmc/windowing/android/WinSystemAndroid.cpp",
    ]
    files = {rel: source / rel for rel in rels}
    for rel, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(path)

    h = files["xbmc/guilib/GUIFontCache.h"].read_text(encoding="utf-8")
    ttfh = files["xbmc/guilib/GUIFontTTF.h"].read_text(encoding="utf-8")
    mgrh = files["xbmc/guilib/GUIFontManager.h"].read_text(encoding="utf-8")
    mgr = files["xbmc/guilib/GUIFontManager.cpp"].read_text(encoding="utf-8")
    apph = files["xbmc/platform/android/activity/XBMCApp.h"].read_text(encoding="utf-8")
    app = files["xbmc/platform/android/activity/XBMCApp.cpp"].read_text(encoding="utf-8")
    win = files["xbmc/windowing/android/WinSystemAndroid.cpp"].read_text(encoding="utf-8")

    # These bridge checks validate the accepted source contract instead of rewriting protected state.
    bridge_checks = {
        "positive_size_pack_rejects_invalid": "if (!size) return;" in apph,
        "duplicate_requested_size_rejected": "m_requested.size == size" in apph,
        "geometry_requires_engine_surface_pending": all(
            token in apph for token in ("m_engineReady", "m_surfaceReady", "m_pending", "m_requested.size")
        ),
        "generation_current_check_exists": "IsCurrent" in apph,
        "commit_after_accept_api_exists": "CommitGeometry" in apph,
        "retry_api_exists": "RetryGeometry" in apph,
    }
    checks = {
        "vertex_assignment_releases_old_buffer": "clear();\n    bufferHandle = other.bufferHandle;" in h,
        "vertex_assignment_assert_removed": "assert(bufferHandle == 0);" not in h,
        "font_flush_api": "void FlushRenderCaches();" in ttfh,
        "manager_atomic_defer": "std::atomic_bool m_renderCacheFlushPending" in mgrh,
        "manager_render_flush": "font->FlushRenderCaches();" in mgr,
        "android_callbacks_request_only": "g_fontManager.RequestRenderCacheFlush();" in app,
        "no_direct_notify_resize_from_callbacks": "NotifyWindowResize" not in app,
        "render_loop_consumes_invalidation": "ConsumeRenderCacheFlushRequest()" in win,
        "render_system_ready_gate": "CServiceBroker::GetRenderSystem()" in win,
        "positive_geometry_runtime_gate": "if (width <= 0 || height <= 0) return;" in win,
        "stale_request_runtime_gate": "state.IsCurrent(request)" in win,
        "commit_occurs_in_render_path": "state.CommitGeometry(request)" in win,
        "pre_resize_font_flush": "g_fontManager.FlushRenderCaches();" in win,
        **bridge_checks,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("GUI/render hardening verification failed: " + ", ".join(failed))

    return {
        "schema": 2,
        "kodi_version": "21.3-Omega",
        "gui_font_cache_hardened": True,
        "renderer_changed": True,
        "android_resize_hardened": True,
        "render_thread_cache_invalidation": True,
        "post_playback_cache_invalidation": True,
        "protected_geometry_bridge_rewritten": False,
        "direct_android_gui_mutation": False,
        "checks": checks,
        "files": {rel: base.sha(path) for rel, path in files.items()},
    }


def apply_v2(source: Path, receipt: Path) -> None:
    source = source.resolve()
    paths = {
        "font_cache_h": source / "xbmc/guilib/GUIFontCache.h",
        "font_cache_cpp": source / "xbmc/guilib/GUIFontCache.cpp",
        "font_ttf_h": source / "xbmc/guilib/GUIFontTTF.h",
        "font_ttf_cpp": source / "xbmc/guilib/GUIFontTTF.cpp",
        "font_manager_h": source / "xbmc/guilib/GUIFontManager.h",
        "font_manager_cpp": source / "xbmc/guilib/GUIFontManager.cpp",
        "xbmc_app_cpp": source / "xbmc/platform/android/activity/XBMCApp.cpp",
        "win_system": source / "xbmc/windowing/android/WinSystemAndroid.cpp",
    }
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    before = {str(path.relative_to(source)): base.sha(path) for path in paths.values()}

    base.patch_font_cache_h(paths["font_cache_h"])
    base.patch_font_cache_cpp(paths["font_cache_cpp"])
    base.patch_font_ttf_h(paths["font_ttf_h"])
    base.patch_font_ttf_cpp(paths["font_ttf_cpp"])
    base.patch_font_manager_h(paths["font_manager_h"])
    base.patch_font_manager_cpp(paths["font_manager_cpp"])
    # Preserve XBMCApp.h exactly: its accepted bridge already rejects invalid/duplicate/stale work.
    base.patch_xbmc_app_cpp(paths["xbmc_app_cpp"])
    patch_win_system(paths["win_system"])

    result = verify_v2(source)
    result["before"] = before
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity Kodi 21.3 GUI/render hardening v2 installed")


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
        apply_v2(args.source, args.receipt)
    else:
        print(json.dumps(verify_v2(args.source.resolve()), indent=2, sort_keys=True))
        print("PASS: Infinity Kodi 21.3 GUI/render hardening v2 verified")


if __name__ == "__main__":
    main()
