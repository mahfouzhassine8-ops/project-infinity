#!/usr/bin/env python3
"""Fail-closed handoff from verified Responsive Bridge v5 presentation to deep branding.

Responsive v5 deliberately replaces the raw Kodi launch image with the approved
Infinity icon. Audited v4 also already owns one user-facing startup line. The
deep-rebrand layer then owns the complete day/night launch composition and the
full startup wording set. This adapter runs *after* responsive-v5.py has already
verified its contract and converts only those known Infinity v4/v5 presentation
owners into the exact preimages consumed by the deep branding layer.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

LAYOUT = Path("tools/android/packaging/xbmc/res/layout/activity_splash.xml")
SPLASH_JAVA = Path("tools/android/packaging/xbmc/src/Splash.java.in")


def normalize(source: Path) -> None:
    source = source.resolve()
    path = source / LAYOUT
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

    # Audited v4 already rebrands this one stock startup line. Normalize only
    # that exact verified v4 postimage so the deeper branding pass can own and
    # verify the entire startup wording set consistently. No internal state,
    # class, JNI, package, or engine identifier is touched here.
    java_path = source / SPLASH_JAVA
    java = java_path.read_text(encoding="utf-8")
    v4_line = 'mSplash.mTextView.setText("Starting Infinity...");'
    stock_line = 'mSplash.mTextView.setText("Starting @APP_NAME@...");'
    if java.count(v4_line) != 1 or stock_line in java:
        raise RuntimeError("Unexpected audited-v4 startup wording owner/preimage")
    java = java.replace(v4_line, stock_line, 1)
    java_path.write_text(java, encoding="utf-8")

    print("PASS: verified Responsive v5/v4 presentation handed off to deep branding owner")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    args = p.parse_args()
    normalize(args.source)


if __name__ == "__main__":
    main()
