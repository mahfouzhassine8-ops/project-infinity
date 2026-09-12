#!/usr/bin/env python3
"""Fail-closed handoff from verified Responsive Bridge v5 presentation to deep branding.

Responsive v5 deliberately replaces the raw Kodi launch image with the approved
Infinity icon. The deep-rebrand layer then owns a complete day/night launch
composition. This tiny adapter runs *after* responsive-v5.py has already
verified its contract and converts only that known v5 splash presentation into
the preimage consumed by the deep branding layer.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

REL = Path("tools/android/packaging/xbmc/res/layout/activity_splash.xml")


def normalize(source: Path) -> None:
    path = source.resolve() / REL
    text = path.read_text(encoding="utf-8")

    required = (
        'android:scaleType="fitCenter"',
        'android:padding="48dp"',
        'android:src="@drawable/project_infinity_icon"',
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise RuntimeError(
            "Refusing unknown splash owner/preimage; responsive v5 must be verified first. Missing: "
            + ", ".join(missing)
        )
    if text.count('android:src="@drawable/project_infinity_icon"') != 1:
        raise RuntimeError("Expected exactly one responsive-v5 splash image owner")
    if text.count('android:scaleType="fitCenter"') != 1:
        raise RuntimeError("Expected exactly one responsive-v5 splash scale owner")
    if text.count('android:padding="48dp"') != 1:
        raise RuntimeError("Expected exactly one responsive-v5 splash padding owner")

    text = text.replace('android:src="@drawable/project_infinity_icon"',
                        'android:src="@drawable/applaunch_screen"', 1)
    # The deep branding layer converts this exact raw-layout scale token back to
    # fitCenter after installing the full Infinity composition.
    text = text.replace('android:scaleType="fitCenter"',
                        'android:scaleType="centerCrop"', 1)
    # Full-screen branded artwork owns its own safe area; do not double-inset it.
    text = text.replace('        android:padding="48dp"\n', '', 1)

    ET.fromstring(text)
    path.write_text(text, encoding="utf-8")
    print("PASS: verified Responsive v5 splash handed off to deep branding owner")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    args = p.parse_args()
    normalize(args.source)


if __name__ == "__main__":
    main()
