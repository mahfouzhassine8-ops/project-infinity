#!/usr/bin/env python3
"""Compile-check the Infinity Multi-View Android controller against a real Android SDK jar."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
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

    text = template.read_text(encoding="utf-8")
    text = text.replace("@APP_PACKAGE@", "com.projectinfinity.kodi")
    if "@APP_" in text:
        raise SystemExit("unresolved Android packaging placeholder in Multi-View controller")

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "com/projectinfinity/kodi"
        src.mkdir(parents=True)
        java = src / "InfinityMultiViewController.java"
        java.write_text(text, encoding="utf-8")
        subprocess.run([
            "javac", "-source", "8", "-target", "8",
            "-cp", str(args.android_jar),
            "-d", str(args.out),
            str(java),
        ], check=True)

    expected = args.out / "com/projectinfinity/kodi/InfinityMultiViewController.class"
    if not expected.is_file():
        raise SystemExit("Multi-View javac output missing")
    print("PASS: Infinity Multi-View controller compiles against Android API")


if __name__ == "__main__":
    main()
