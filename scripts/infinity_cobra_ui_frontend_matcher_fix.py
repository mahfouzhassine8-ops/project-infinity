#!/usr/bin/env python3
"""Method-scoped compatibility shim for the Cobra UI frontend transform.

The frontend contract is unchanged. This only replaces its brittle whole-tail
Settings matcher with a structural match scoped to showSettings().
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import infinity_cobra_ui_frontend as base

LIVE = base.LIVE


def _settings_bounds(text: str) -> tuple[int, int]:
    start_marker = "  private void showSettings() {\n"
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError("Cobra UI frontend Settings method missing")
    end = text.find("\n  private ", start + len(start_marker))
    if end < 0:
        raise RuntimeError("Cobra UI frontend Settings method end missing")
    return start, end


def _scroll_settings(text: str) -> str:
    start, end = _settings_bounds(text)
    block = text[start:end]

    # Some final Candidate/RC3 source shapes already wrap Settings in a ScrollView.
    # Preserve that rather than nesting a second scroller.
    if "new ScrollView(this)" in block and re.search(r"\b\w+\.addView\(list\);", block):
        return text

    # Otherwise replace the one direct Settings-list attachment regardless of
    # whitespace or the exact LayoutParams spelling used by the final transform.
    pattern = re.compile(
        r"(?ms)^(?P<indent>[ \t]*)mStage\.addView\(\s*list\s*,\s*"
        r"new LinearLayout\.LayoutParams\((?P<args>.*?)\)\s*\);[ \t]*$"
    )
    matches = list(pattern.finditer(block))
    if len(matches) != 1:
        hints = [line.strip() for line in block.splitlines() if "addView" in line and "list" in line]
        raise RuntimeError(
            "Cobra UI frontend scrollable settings: expected one direct Settings "
            f"list attachment or an existing ScrollView, found {len(matches)}; hints={hints[:6]}"
        )
    match = matches[0]
    indent = match.group("indent")
    replacement = (
        f"{indent}ScrollView settingsScroll = new ScrollView(this);\n"
        f"{indent}settingsScroll.addView(list);\n"
        f"{indent}mStage.addView(settingsScroll, new LinearLayout.LayoutParams(\n"
        f"{indent}    LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));"
    )
    block = block[:match.start()] + replacement + block[match.end():]
    return text[:start] + block + text[end:]


def patch(java: str) -> str:
    original_once = base.once

    def scoped_once(text: str, old: str, new: str, label: str) -> str:
        if label == "scrollable settings":
            return _scroll_settings(text)
        return original_once(text, old, new, label)

    base.once = scoped_once
    try:
        return base.patch(java)
    finally:
        base.once = original_once


def verify(java: str) -> None:
    required = (
        "REQUEST_COBRA_UI_PACKAGE = 4173",
        "INSTALL COBRA UI PACKAGE",
        "activeCobraUiLabel()",
        "showCobraGuideViewPicker(false)",
        "showGuideGrid()",
        "showGuideCompact()",
        "showGuideFocus()",
        '"TV Grid"',
        "CATEGORY  •  ",
        "installCobraUiPackage(data.getData())",
        "submitCobraIo(() ->",
        "publishCobraUi(() ->",
        "script.infinity.cobra.theme/resources/cobra-ui.json",
        "UI package attempted to own protected contract",
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra UI frontend contract missing: " + token)

    start, end = _settings_bounds(java)
    block = java[start:end]
    scrollable = (
        "settingsScroll.addView(list)" in block
        or ("new ScrollView(this)" in block and re.search(r"\b\w+\.addView\(list\);", block))
    )
    if not scrollable:
        raise RuntimeError("Cobra Settings is not scrollable after frontend patch")

    installer_start = java.find("private void installCobraUiPackage")
    installer_end = java.find("private void playChannel", installer_start)
    if installer_start < 0 or installer_end < 0:
        raise RuntimeError("Cobra UI installer bounds missing")
    if "mIo.execute(() ->" in java[installer_start:installer_end]:
        raise RuntimeError("Cobra UI installer bypassed RC3 guarded async executor")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra UI frontend + format-independent Settings matcher applied")


if __name__ == "__main__":
    main()
