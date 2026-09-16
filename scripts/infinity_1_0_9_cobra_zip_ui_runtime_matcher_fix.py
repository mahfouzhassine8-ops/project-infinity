#!/usr/bin/env python3
'''Compatibility repair for the Cobra ZIP-driven UI runtime v3 source transform.

The Runtime v3 contract itself remains version 3. This module only repairs the
build-time matcher used after Candidate 2 device-parity has rewritten Cobra's
responsive rail width. It also keeps the runtime's no-package fallback aligned
with the already-approved Cobra player layout.
'''
from __future__ import annotations

import infinity_1_0_9_cobra_zip_ui_runtime as base


RUNTIME = base.RUNTIME
UI_PATH = base.UI_PATH

_POST_PARITY_RAIL_WIDTH = (
    "    int railWidth = isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156);\n"
)


def _replace_navigation_width(text: str, replacement: str) -> str:
    count = text.count(_POST_PARITY_RAIL_WIDTH)
    if count != 1:
        raise RuntimeError(
            "Cobra ZIP UI runtime navigation width: expected exactly one post-parity "
            f"match, found {count}"
        )
    return text.replace(_POST_PARITY_RAIL_WIDTH, replacement + "\n", 1)


def patch(java: str) -> str:
    original_regex_once = base.regex_once

    def matcher(text: str, pattern: str, replacement: str, label: str) -> str:
        if label == "navigation width":
            return _replace_navigation_width(text, replacement)
        return original_regex_once(text, pattern, replacement, label)

    base.regex_once = matcher
    try:
        java = base.patch(java)
    finally:
        base.regex_once = original_regex_once

    # If cobra-ui.json is absent, malformed, or rejected, Runtime v3 must fall
    # back to the approved Candidate 2 presentation rather than re-introducing
    # Guide into the compact primary player row or hiding Guide/Multi-View from
    # the settings drawer.
    old_primary = '''      Collections.addAll(playerPrimaryActions,
          "previous", "favorite", "guide", "record", "multiview", "next");'''
    new_primary = '''      Collections.addAll(playerPrimaryActions,
          "previous", "favorite", "record", "multiview", "next");'''
    if java.count(old_primary) != 1:
        raise RuntimeError("Cobra ZIP UI runtime fallback primary-action contract drift")
    java = java.replace(old_primary, new_primary, 1)

    old_settings = '''      Collections.addAll(playerSettingsActions,
          "tracks", "subtitles", "aspect", "cast", "source", "close");'''
    new_settings = '''      Collections.addAll(playerSettingsActions,
          "tracks", "subtitles", "aspect", "cast", "source", "guide", "multiview", "close");'''
    if java.count(old_settings) != 1:
        raise RuntimeError("Cobra ZIP UI runtime fallback settings-action contract drift")
    java = java.replace(old_settings, new_settings, 1)
    return java


def verify(java: str) -> None:
    base.verify(java)
    required = (
        "mUi.drawerPortraitWidthDp",
        "mUi.drawerLandscapeWidthDp",
        '"previous", "favorite", "record", "multiview", "next"',
        '"source", "guide", "multiview", "close"',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra ZIP UI matcher repair missing: " + token)
