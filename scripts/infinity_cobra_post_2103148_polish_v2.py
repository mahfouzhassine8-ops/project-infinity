#!/usr/bin/env python3
"""Structural matcher shim for the post-2103148 Cobra polish transform.

Normalizes presentation-only preimages that can vary after Runtime-v3,
player-repair and appearance transforms. The locked native engine is untouched.
"""
from __future__ import annotations

import infinity_cobra_post_2103148_polish as base

_original_patch = base.patch


def patch(java: str) -> str:
    # Appearance mode wraps the player-settings title color in cobraThemeColor(),
    # whose nested comma makes the base transform's intentionally narrow regex
    # ambiguous. Normalize only that title expression before applying the polish.
    java = java.replace(
        'TextView title = text("PLAYER SETTINGS", cobraThemeColor("text", mTheme.text), 18,',
        'TextView title = text("PLAYER SETTINGS", mTheme.text, 18,',
        1,
    )

    # Do not guess which background setter an earlier player revision used.
    # Instead, structurally locate openPlayerOverlay and inject the exact dark
    # player-chrome preimage immediately before the info row. That position is
    # after the chrome is constructed/styled, so this becomes the final player
    # chrome background setter while remaining presentation-only. The base pass
    # can then safely move the LIVE/status TextView into the transient chrome,
    # which also keeps it out of PiP when player chrome is hidden.
    a, b = base.span(java, "  private void openPlayerOverlay(Channel channel) {")
    overlay = java[a:b]
    strict = '    mPlayerChrome.setBackgroundColor(Color.argb(215, 4, 6, 10));\n'
    if strict not in overlay:
        if '    mPlayerChrome = new LinearLayout(this);\n' not in overlay:
            raise RuntimeError("player chrome construction missing")
        info_anchor = '    TextView info = text('
        idx = overlay.find(info_anchor)
        if idx < 0:
            raise RuntimeError("player info-row anchor missing")
        overlay = overlay[:idx] + strict + overlay[idx:]
        java = java[:a] + overlay + java[b:]

    return _original_patch(java)


base.patch = patch

if __name__ == "__main__":
    base.main()
