#!/usr/bin/env python3
"""Method-scoped compatibility shim for the Cobra UI frontend transform.

The frontend contract is unchanged. This only replaces its brittle whole-tail
Settings matcher with a structural match scoped to showSettings().
"""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_cobra_ui_frontend as base

LIVE = base.LIVE


def _scroll_settings(text: str) -> str:
    start_marker = "  private void showSettings() {\n"
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError("Cobra UI frontend Settings method missing")
    end = text.find("\n  private ", start + len(start_marker))
    if end < 0:
        raise RuntimeError("Cobra UI frontend Settings method end missing")

    block = text[start:end]
    old = (
        "    mStage.addView(list, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));\n"
    )
    new = (
        "    ScrollView settingsScroll = new ScrollView(this);\n"
        "    settingsScroll.addView(list);\n"
        "    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));\n"
    )
    count = block.count(old)
    if count != 1:
        raise RuntimeError(
            "Cobra UI frontend scrollable settings: expected exactly one Settings "
            f"stage attachment, found {count}"
        )
    block = block.replace(old, new, 1)
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
    base.verify(java)
    required = (
        "ScrollView settingsScroll = new ScrollView(this)",
        "settingsScroll.addView(list)",
        "mStage.addView(settingsScroll",
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra UI frontend matcher repair missing: " + token)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra UI frontend + method-scoped Settings matcher applied")


if __name__ == "__main__":
    main()
