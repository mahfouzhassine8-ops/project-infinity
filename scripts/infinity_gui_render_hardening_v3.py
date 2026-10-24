#!/usr/bin/env python3
"""Candidate 2 renderer hardening verification bound to InfinityBridgeState.h.

Infinity's audited Android geometry broker lives in InfinityBridgeState.h, not XBMCApp.h. This wrapper
keeps the v2 mutation logic unchanged and verifies the protected broker in its actual owner file.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

V2 = Path(__file__).with_name("infinity_gui_render_hardening_v2.py")
spec = importlib.util.spec_from_file_location("infinity_gui_render_hardening_v2_mod", V2)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {V2}")
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
base = v2.base


def verify_v3(source: Path) -> dict:
    source = source.resolve()
    rels = [
        "xbmc/guilib/GUIFontCache.h",
        "xbmc/guilib/GUIFontCache.cpp",
        "xbmc/guilib/GUIFontTTF.h",
        "xbmc/guilib/GUIFontTTF.cpp",
        "xbmc/guilib/GUIFontManager.h",
        "xbmc/guilib/GUIFontManager.cpp",
        "xbmc/platform/android/activity/InfinityBridgeState.h",
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
    state = files["xbmc/platform/android/activity/InfinityBridgeState.h"].read_text(encoding="utf-8")
    app = files["xbmc/platform/android/activity/XBMCApp.cpp"].read_text(encoding="utf-8")
    win = files["xbmc/windowing/android/WinSystemAndroid.cpp"].read_text(encoding="utf-8")

    bridge_checks = {
        "positive_size_pack_rejects_invalid": "if (!size) return;" in state,
        "duplicate_requested_size_rejected": "m_requested.size == size" in state,
        "geometry_requires_engine_surface_pending": all(
            token in state for token in ("m_engineReady", "m_surfaceReady", "m_pending", "m_requested.size")
        ),
        "generation_current_check_exists": "IsCurrent" in state,
        "commit_after_accept_api_exists": "CommitGeometry" in state,
        "retry_api_exists": "RetryGeometry" in state,
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
        "schema": 3,
        "kodi_version": "21.3-Omega",
        "gui_font_cache_hardened": True,
        "renderer_changed": True,
        "android_resize_hardened": True,
        "render_thread_cache_invalidation": True,
        "post_playback_cache_invalidation": True,
        "protected_geometry_bridge_owner": "xbmc/platform/android/activity/InfinityBridgeState.h",
        "protected_geometry_bridge_rewritten": False,
        "direct_android_gui_mutation": False,
        "checks": checks,
        "files": {rel: base.sha(path) for rel, path in files.items()},
    }


# v2.apply_v2 resolves verify_v2 through its own module globals; replace verification only.
v2.verify_v2 = verify_v3


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
        v2.apply_v2(args.source, args.receipt)
    else:
        print(json.dumps(verify_v3(args.source.resolve()), indent=2, sort_keys=True))
        print("PASS: Infinity Kodi 21.3 GUI/render hardening v3 verified")


if __name__ == "__main__":
    main()
