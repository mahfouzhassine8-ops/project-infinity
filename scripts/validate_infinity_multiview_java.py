#!/usr/bin/env python3
"""Validate the Infinity Live TV Media3 owner contract.

Media3 classes are supplied by the Kodi Gradle module. This preflight gate
keeps the source owner deterministic; CI's Gradle compile performs the actual
Android/Media3 type check.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--android-jar", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    template = args.source / "tools/android/packaging/xbmc/src/InfinityMultiViewController.java.in"
    if not template.is_file():
        raise SystemExit("missing InfinityMultiViewController.java.in")
    if not args.android_jar.is_file():
        raise SystemExit("missing Android API jar")

    text = template.read_text(encoding="utf-8").replace("@APP_PACKAGE@", "com.projectinfinity.kodi")
    if "@APP_" in text:
        raise SystemExit("unresolved Android packaging placeholder in Multi-View controller")

    required = (
        "class InfinityMultiViewController",
        "new ExoPlayer.Builder",
        "DefaultHttpDataSource.Factory",
        "DefaultMediaSourceFactory",
        "setVideoTextureView(texture)",
        "clearVideoTextureView(texture)",
        "setAudioAttributes",
        "setAudible(index == mAudioTile)",
        'TAG_SCHEME = "infinity-multiview"',
    )
    for needle in required:
        if needle not in text:
            raise SystemExit("missing Media3 Live TV contract: " + needle)

    forbidden = ("android.media.MediaPlayer", "new MediaPlayer(", "CobraTV", "cobratv", "libmpv")
    for needle in forbidden:
        if needle in text:
            raise SystemExit("forbidden legacy/reference player marker: " + needle)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "InfinityMultiViewController.java").write_text(text, encoding="utf-8")
    print("PASS: Infinity Live TV Media3 owner contract present; Gradle performs the real Android compile")


if __name__ == "__main__":
    main()
