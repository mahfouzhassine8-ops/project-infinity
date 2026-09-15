#!/usr/bin/env python3
"""Source-level hardening for Kodi 21.3 Android GUI font/VBO refresh and resize paths.

This transform is deliberately narrow:
- fixes CVertexBuffer pseudo-move assignment so an already-owned VBO is released on the render thread
  before replacement instead of asserting/crashing;
- adds an explicit GUI font render-cache flush that is only consumed from Kodi's render/main loop;
- Android/NDK resize, surface and playback-stop callbacks only request invalidation and queue immutable
  geometry; they never delete/recreate GL objects directly;
- strengthens Infinity geometry commit gating so invalid/duplicate/already-committed sizes are ignored and
  geometry is only applied when application, GUI, render system, Android window system and native surface
  are ready.

The transform runs after the audited Infinity 7.1 source stack is recreated and does not mutate any
locked baseline artifact in place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = 1


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}")
    return text.replace(old, new, 1)


def patch_font_cache_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = '''  CVertexBuffer& operator=(CVertexBuffer& other)\n  {\n    /* This is used with move-assignment semantics for initialising the object in the font cache */\n    assert(bufferHandle == 0);\n    bufferHandle = other.bufferHandle;\n    other.bufferHandle = 0;\n    size = other.size;\n    m_font = other.m_font;\n    return *this;\n  }\n'''
    new = '''  CVertexBuffer& operator=(CVertexBuffer& other)\n  {\n    /* This is used with move-assignment semantics for initialising the object in the font cache.\n     * A refresh/reload can legitimately hand us a cache slot that still owns a VBO. Releasing the\n     * old buffer here is safe because cache replacement is performed by the Kodi render thread. */\n    if (this == &other)\n      return *this;\n    clear();\n    bufferHandle = other.bufferHandle;\n    other.bufferHandle = 0;\n    size = other.size;\n    other.size = 0;\n    m_font = other.m_font;\n    return *this;\n  }\n'''
    path.write_text(replace_once(text, old, new, "CVertexBuffer replacement hardening"), encoding="utf-8")


def patch_font_cache_cpp(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = '''void CVertexBuffer::clear()\n{\n  if (m_font)\n    m_font->DestroyVertexBuffer(*this);\n}\n'''
    new = '''void CVertexBuffer::clear()\n{\n  if (m_font && bufferHandle != 0)\n    m_font->DestroyVertexBuffer(*this);\n  size = 0;\n}\n'''
    path.write_text(replace_once(text, old, new, "CVertexBuffer clear hardening"), encoding="utf-8")


def patch_font_ttf_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = '''  void Clear();\n\n  bool Load(const std::string& strFilename,\n'''
    new = '''  void Clear();\n  // Render-thread-only: discard cached CPU/GPU text geometry before a window/context transition.\n  void FlushRenderCaches();\n\n  bool Load(const std::string& strFilename,\n'''
    path.write_text(replace_once(text, old, new, "CGUIFontTTF flush declaration"), encoding="utf-8")


def patch_font_ttf_cpp(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    anchor = '''void CGUIFontTTF::Begin()\n{\n'''
    method = '''void CGUIFontTTF::FlushRenderCaches()\n{\n  // Must be called from Kodi's render/main loop while the GL context is current.\n  m_vertexTrans.clear();\n  m_vertex.clear();\n  m_staticCache.Flush();\n  m_dynamicCache.Flush();\n}\n\n'''
    if method in text:
        raise RuntimeError("CGUIFontTTF flush method already present unexpectedly")
    path.write_text(replace_once(text, anchor, method + anchor, "CGUIFontTTF flush implementation"), encoding="utf-8")


def patch_font_manager_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '#include <set>\n',
        '#include <atomic>\n#include <set>\n',
        "GUIFontManager atomic include",
    )
    old = '''  void Clear();\n  void FreeFontFile(CGUIFontTTF* pFont);\n'''
    new = '''  void Clear();\n  // Request can come from Android/NDK callbacks; consume/flush is render-thread-only.\n  void RequestRenderCacheFlush();\n  bool ConsumeRenderCacheFlushRequest();\n  void FlushRenderCaches();\n  void FreeFontFile(CGUIFontTTF* pFont);\n'''
    text = replace_once(text, old, new, "GUIFontManager flush declarations")
    old_private = '''  mutable CCriticalSection m_critSection;\n  std::vector<FontMetadata> m_userFontsCache;\n'''
    new_private = '''  mutable CCriticalSection m_critSection;\n  std::atomic_bool m_renderCacheFlushPending{false};\n  std::vector<FontMetadata> m_userFontsCache;\n'''
    text = replace_once(text, old_private, new_private, "GUIFontManager pending flag")
    path.write_text(text, encoding="utf-8")


def patch_font_manager_cpp(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    anchor = '''void GUIFontManager::Clear()\n{\n'''
    methods = '''void GUIFontManager::RequestRenderCacheFlush()\n{\n  m_renderCacheFlushPending.store(true, std::memory_order_release);\n}\n\nbool GUIFontManager::ConsumeRenderCacheFlushRequest()\n{\n  return m_renderCacheFlushPending.exchange(false, std::memory_order_acq_rel);\n}\n\nvoid GUIFontManager::FlushRenderCaches()\n{\n  for (const auto& font : m_vecFontFiles)\n  {\n    if (font)\n      font->FlushRenderCaches();\n  }\n}\n\n'''
    if methods in text:
        raise RuntimeError("GUIFontManager flush methods already present unexpectedly")
    path.write_text(replace_once(text, anchor, methods + anchor, "GUIFontManager flush implementation"), encoding="utf-8")


def patch_xbmc_app_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = '''    if (!m_active || !m_managed) return;\n    if (m_requested.size == size && m_requested.generation == m_generation) return;\n    m_requested = {size, m_generation, ++m_sequence};\n'''
    new = '''    if (!m_active || !m_managed) return;\n    // Reject duplicate geometry that is already committed for the current surface generation.\n    if (m_committed.size == size && m_committed.generation == m_generation)\n    {\n      m_pending = false;\n      return;\n    }\n    if (m_requested.size == size && m_requested.generation == m_generation) return;\n    m_requested = {size, m_generation, ++m_sequence};\n'''
    path.write_text(replace_once(text, old, new, "Infinity committed-size dedupe"), encoding="utf-8")


def patch_xbmc_app_cpp(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '#include "guilib/GUIComponent.h"\n',
        '#include "guilib/GUIComponent.h"\n#include "guilib/GUIFontManager.h"\n',
        "XBMCApp GUIFontManager include",
    )
    old = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  // A resize does not destroy the surface. Keep its reference until surfaceDestroyed.\n  InfinitySyncDisplayState();\n}\n'''
    new = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  // Android callback thread: request render-cache invalidation only. GL/cache mutation is consumed\n  // later by CWinSystemAndroid::MessagePump on Kodi's render/main loop.\n  g_fontManager.RequestRenderCacheFlush();\n  // A resize does not destroy the surface. Keep its reference until surfaceDestroyed. Geometry is\n  // immutable/queued here; CInfinityBridgeState gates it until the engine/surface are ready.\n  InfinitySyncDisplayState();\n}\n'''
    text = replace_once(text, old, new, "Android resize callback deferral")

    old = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: %dx%d", __PRETTY_FUNCTION__, width, height);\n  // Surface dimensions can be buffer dimensions. The laid-out view is authoritative.\n  InfinitySyncDisplayState();\n}\n'''
    new = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: %dx%d", __PRETTY_FUNCTION__, width, height);\n  // Never touch GL/font resources from the Surface callback. The render loop owns invalidation.\n  if (width > 0 && height > 0)\n    g_fontManager.RequestRenderCacheFlush();\n  // Surface dimensions can be buffer dimensions. The laid-out view is authoritative.\n  InfinitySyncDisplayState();\n}\n'''
    text = replace_once(text, old, new, "surfaceChanged render deferral")

    old = '''void CXBMCApp::OnPlayBackStopped()\n{\n  CLog::Log(LOGDEBUG, "CXBMCApp::{}", __FUNCTION__);\n'''
    new = '''void CXBMCApp::OnPlayBackStopped()\n{\n  CLog::Log(LOGDEBUG, "CXBMCApp::{}", __FUNCTION__);\n  // Post-playback widgets/media windows can refresh immediately. Defer font/VBO invalidation to\n  // Kodi's render loop so stale cached GPU geometry is never replaced from this callback thread.\n  g_fontManager.RequestRenderCacheFlush();\n'''
    text = replace_once(text, old, new, "post-playback render-cache request")

    old = '''void CXBMCApp::surfaceDestroyed(CJNISurfaceHolder holder)\n{\n'''
    new = '''void CXBMCApp::surfaceDestroyed(CJNISurfaceHolder holder)\n{\n  // Mark cached text geometry for render-thread disposal before any later surface/context reuse.\n  g_fontManager.RequestRenderCacheFlush();\n'''
    text = replace_once(text, old, new, "surfaceDestroyed render-cache request")
    path.write_text(text, encoding="utf-8")


def patch_win_system(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '#include "guilib/DispResource.h"\n',
        '#include "guilib/DispResource.h"\n#include "guilib/GUIFontManager.h"\n',
        "WinSystemAndroid GUIFontManager include",
    )
    old = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    new = '''bool CWinSystemAndroid::MessagePump()\n{\n  const bool handled = m_winEvents->MessagePump();\n  // Android/NDK callbacks only set an atomic request. Consume it here, on Kodi's render/main loop,\n  // while the current GL context and GUI font objects are owned by this thread.\n  if (g_fontManager.ConsumeRenderCacheFlushRequest())\n  {\n    if (g_application.IsInitialized() && CServiceBroker::GetGUI() &&\n        CServiceBroker::GetRenderSystem())\n      g_fontManager.FlushRenderCaches();\n    else\n      g_fontManager.RequestRenderCacheFlush();\n  }\n  ApplyInfinityGeometry();\n  return handled;\n}\n'''
    text = replace_once(text, old, new, "render-thread cache-flush consumer")

    old = '''  state.SetEngineReady(g_application.IsInitialized() && gui && m_android && m_bWindowCreated && m_nativeWindow);\n'''
    new = '''  state.SetEngineReady(g_application.IsInitialized() && gui &&\n                       CServiceBroker::GetRenderSystem() && m_android && m_bWindowCreated &&\n                       m_nativeWindow);\n'''
    text = replace_once(text, old, new, "render readiness gate")

    old = '''  if (!state.IsCurrent(request)) return; // An intervening surface/mode/size event superseded it.\n  // This runs in Kodi's main/render loop, not in Android's UI callbacks.\n  // Preserve EGL/surface ownership and the physical display mode/refresh-rate identity.\n  if (!m_nativeWindow->SetBuffersGeometry(width, height, 0) ||\n      !ResizeWindow(width, height, -1, -1))\n'''
    new = '''  if (width <= 0 || height <= 0) return;\n  if (!state.IsCurrent(request)) return; // An intervening surface/mode/size event superseded it.\n  // This runs in Kodi's main/render loop, not in Android's UI callbacks. Flush text geometry before\n  // changing the native buffer/GUI size so stale VBOs cannot survive into the resized frame.\n  g_fontManager.FlushRenderCaches();\n  // Preserve EGL/surface ownership and the physical display mode/refresh-rate identity.\n  if (!m_nativeWindow->SetBuffersGeometry(width, height, 0) ||\n      !ResizeWindow(width, height, -1, -1))\n'''
    text = replace_once(text, old, new, "safe geometry application")

    old = '''bool CWinSystemAndroid::DestroyWindow()\n{\n  CLog::Log(LOGINFO, "CWinSystemAndroid::{}", __FUNCTION__);\n  m_nativeWindow.reset();\n'''
    new = '''bool CWinSystemAndroid::DestroyWindow()\n{\n  CLog::Log(LOGINFO, "CWinSystemAndroid::{}", __FUNCTION__);\n  // Render-thread/context owner: release cached font VBOs before the native window can disappear.\n  if (CServiceBroker::GetGUI() && CServiceBroker::GetRenderSystem())\n    g_fontManager.FlushRenderCaches();\n  m_nativeWindow.reset();\n'''
    text = replace_once(text, old, new, "window-destroy font cache flush")
    path.write_text(text, encoding="utf-8")


def verify(source: Path) -> dict:
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

    checks = {
        "vertex_assignment_releases_old_buffer": "clear();\n    bufferHandle = other.bufferHandle;" in h,
        "vertex_assignment_assert_removed": "assert(bufferHandle == 0);" not in h,
        "font_flush_api": "void FlushRenderCaches();" in ttfh,
        "manager_atomic_defer": "std::atomic_bool m_renderCacheFlushPending" in mgrh,
        "manager_render_flush": "font->FlushRenderCaches();" in mgr,
        "committed_size_dedupe": "m_committed.size == size" in apph,
        "resize_callback_deferred": "g_fontManager.RequestRenderCacheFlush();" in app,
        "render_loop_consumes": "ConsumeRenderCacheFlushRequest()" in win,
        "render_system_ready_gate": "CServiceBroker::GetRenderSystem()" in win,
        "positive_geometry_gate": "if (width <= 0 || height <= 0) return;" in win,
        "pre_resize_font_flush": "g_fontManager.FlushRenderCaches();" in win,
        "no_direct_resize_notify_in_android_callback": "NotifyWindowResize" not in app,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("GUI/render hardening verification failed: " + ", ".join(failed))

    return {
        "schema": SCHEMA,
        "kodi_version": "21.3-Omega",
        "gui_font_cache_hardened": True,
        "renderer_changed": True,
        "android_resize_hardened": True,
        "render_thread_cache_invalidation": True,
        "post_playback_cache_invalidation": True,
        "direct_android_gui_mutation": False,
        "checks": checks,
        "files": {rel: sha(path) for rel, path in files.items()},
    }


def apply(source: Path, receipt: Path) -> None:
    source = source.resolve()
    paths = {
        "font_cache_h": source / "xbmc/guilib/GUIFontCache.h",
        "font_cache_cpp": source / "xbmc/guilib/GUIFontCache.cpp",
        "font_ttf_h": source / "xbmc/guilib/GUIFontTTF.h",
        "font_ttf_cpp": source / "xbmc/guilib/GUIFontTTF.cpp",
        "font_manager_h": source / "xbmc/guilib/GUIFontManager.h",
        "font_manager_cpp": source / "xbmc/guilib/GUIFontManager.cpp",
        "xbmc_app_h": source / "xbmc/platform/android/activity/XBMCApp.h",
        "xbmc_app_cpp": source / "xbmc/platform/android/activity/XBMCApp.cpp",
        "win_system": source / "xbmc/windowing/android/WinSystemAndroid.cpp",
    }
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    before = {str(path.relative_to(source)): sha(path) for path in paths.values()}

    patch_font_cache_h(paths["font_cache_h"])
    patch_font_cache_cpp(paths["font_cache_cpp"])
    patch_font_ttf_h(paths["font_ttf_h"])
    patch_font_ttf_cpp(paths["font_ttf_cpp"])
    patch_font_manager_h(paths["font_manager_h"])
    patch_font_manager_cpp(paths["font_manager_cpp"])
    patch_xbmc_app_h(paths["xbmc_app_h"])
    patch_xbmc_app_cpp(paths["xbmc_app_cpp"])
    patch_win_system(paths["win_system"])

    result = verify(source)
    result["before"] = before
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity Kodi 21.3 GUI/render hardening installed")


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
        apply(args.source, args.receipt)
    else:
        print(json.dumps(verify(args.source.resolve()), indent=2, sort_keys=True))
        print("PASS: Infinity Kodi 21.3 GUI/render hardening verified")


if __name__ == "__main__":
    main()
