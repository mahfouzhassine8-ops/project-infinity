#!/usr/bin/env python3
"""Compatibility wrapper for the Cobra player presentation repair."""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_cobra_player_presentation_fix as base

LIVE = base.LIVE


def patch(java: str) -> str:
    original = base.replace_between

    def fixed_replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
        # The base repair deliberately supplies the following method marker as a
        # readability suffix. Keep exactly one copy because original() preserves
        # the end marker from the input source.
        if label == "deterministic Fit/Crop implementation" and replacement.endswith(end):
            replacement = replacement[:-len(end)]
        return original(text, start, end, replacement, label)

    base.replace_between = fixed_replace_between
    try:
        return base.patch(java)
    finally:
        base.replace_between = original


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    base.verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: hardened player drawer dismissal + deterministic Fit/Crop repair applied")


if __name__ == "__main__":
    main()
