#!/usr/bin/env python3
"""Matcher shim for the post-2103148 Cobra polish transform."""
from __future__ import annotations

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
    return _original_patch(java)


base.patch = patch

if __name__ == "__main__":
    base.main()
