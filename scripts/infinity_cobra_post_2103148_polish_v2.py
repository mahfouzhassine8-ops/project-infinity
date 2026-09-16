#!/usr/bin/env python3
"""Matcher shim for the post-2103148 Cobra polish transform.

Normalizes presentation-only preimages that can vary after the Runtime-v3,
player-repair and appearance transforms. The locked native engine is untouched.
"""
from __future__ import annotations

import re

import infinity_cobra_post_2103148_polish as base

_original_patch = base.patch


def patch(java: str) -> str:
    # Appearance mode wraps the player-settings title color in cobraThemeColor(),
    # which contains a comma and is intentionally normalized before the strict
    # polish matcher replaces the title with the high-contrast player color.
    java = java.replace(
        'TextView title = text("PLAYER SETTINGS", cobraThemeColor("text", mTheme.text), 18,',
        'TextView title = text("PLAYER SETTINGS", mTheme.text, 18,',
        1,
    )

    # Earlier accepted player transforms have used more than one alpha/value for
    # the same dark player chrome. Normalize that presentation-only line to the
    # strict preimage expected by the polish pass. This is intentionally scoped
    # to mPlayerChrome and does not touch TextureView/player/native behavior.
    java, count = re.subn(
        r'^    mPlayerChrome\.setBackgroundColor\(Color\.argb\([^\n]+\)\);\s*$',
        '    mPlayerChrome.setBackgroundColor(Color.argb(215, 4, 6, 10));',
        java,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        # Some presentation revisions use a drawable surface instead of a raw
        # setBackgroundColor call. Normalize only that one player-chrome line.
        java, count = re.subn(
            r'^    mPlayerChrome\.setBackground\([^\n]+\);\s*$',
            '    mPlayerChrome.setBackgroundColor(Color.argb(215, 4, 6, 10));',
            java,
            count=1,
            flags=re.MULTILINE,
        )
    if count != 1:
        raise RuntimeError("player chrome compatibility preimage missing")

    return _original_patch(java)


base.patch = patch

if __name__ == "__main__":
    base.main()
