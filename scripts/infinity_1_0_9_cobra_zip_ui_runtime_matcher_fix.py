#!/usr/bin/env python3
'''Compatibility repair for the Cobra ZIP-driven UI runtime v3 source transform.

The Runtime v3 contract itself remains version 3. This module hardens the late
presentation anchors that are intentionally rewritten by Candidate 2's final
UI polish. Matchers target structural declarations/expressions rather than
historical formatting while still requiring an unambiguous single match.
'''
from __future__ import annotations

import re

import infinity_1_0_9_cobra_zip_ui_runtime as base


RUNTIME = base.RUNTIME
UI_PATH = base.UI_PATH

_RAIL_WIDTH_DECL = re.compile(
    r"^[ \t]*int railWidth[ \t]*=[^;]+;[ \t]*$",
    re.MULTILINE,
)

_CHANNEL_ROW_HEIGHT_EXPR = re.compile(
    r"dp\(\s*guideMode\s*\?\s*mTheme\.guideRowHeight\s*:\s*mTheme\.rowHeight\s*\)",
    re.MULTILINE,
)


def _replace_navigation_width(text: str, replacement: str) -> str:
    matches = list(_RAIL_WIDTH_DECL.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            "Cobra ZIP UI runtime navigation width: expected exactly one final "
            f"railWidth declaration, found {len(matches)}"
        )
    match = matches[0]
    return text[:match.start()] + replacement + text[match.end():]


def _replace_channel_row_height(text: str) -> str:
    matches = list(_CHANNEL_ROW_HEIGHT_EXPR.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            "Cobra ZIP UI runtime channel row height: expected exactly one final "
            f"guide/channel row-height expression, found {len(matches)}"
        )
    replacement = (
        "dp(guideMode ? mTheme.guideRowHeight\n"
        "              : mUi.channelRowHeight(isPortrait(), mTheme.rowHeight))"
    )
    match = matches[0]
    return text[:match.start()] + replacement + text[match.end():]


def patch(java: str) -> str:
    original_regex_once = base.regex_once
    original_once = base.once

    def regex_matcher(text: str, pattern: str, replacement: str, label: str) -> str:
        if label == "navigation width":
            return _replace_navigation_width(text, replacement)
        return original_regex_once(text, pattern, replacement, label)

    def exact_matcher(text: str, old: str, new: str, label: str) -> str:
        if label == "channel row height":
            return _replace_channel_row_height(text)
        return original_once(text, old, new, label)

    base.regex_once = regex_matcher
    base.once = exact_matcher
    try:
        java = base.patch(java)
    finally:
        base.regex_once = original_regex_once
        base.once = original_once

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
        "mUi.channelRowHeight(isPortrait(), mTheme.rowHeight)",
        '"previous", "favorite", "record", "multiview", "next"',
        '"source", "guide", "multiview", "close"',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra ZIP UI matcher repair missing: " + token)
