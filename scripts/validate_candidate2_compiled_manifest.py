#!/usr/bin/env python3
"""Validate compiled Candidate 2 Android configChanges semantics.

`aapt dump xmltree` renders android:configChanges as a numeric bitmask in a
compiled APK, so checking for literal strings such as "density" or "uiMode"
produces a false negative. This gate parses the emitted mask and verifies the
actual Android flag bits on the activities that own Infinity/Cobra resizing.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED_ACTIVITIES = (
    "com.projectinfinity.kodi.Main",
    "com.projectinfinity.kodi.InfinityLiveActivity",
)
REQUIRED_BITS = {
    "uiMode": 0x0200,
    "density": 0x1000,
}


def config_mask(manifest: str, fqcn: str) -> int:
    lines = manifest.splitlines()
    marker = f'="{fqcn}"'
    for index, line in enumerate(lines):
        if "android:name" not in line or marker not in line:
            continue

        name_indent = len(line) - len(line.lstrip())
        element_indent = max(0, name_indent - 2)
        for candidate in lines[index + 1 :]:
            stripped = candidate.lstrip()
            indent = len(candidate) - len(stripped)
            if stripped.startswith("E: ") and indent <= element_indent:
                break
            if "android:configChanges" not in candidate:
                continue

            values = re.findall(r"0x([0-9a-fA-F]+)", candidate)
            if not values:
                raise ValueError(
                    f"unparseable android:configChanges for {fqcn}: {candidate}"
                )
            return int(values[-1], 16)

        raise ValueError(f"android:configChanges missing for {fqcn}")

    raise ValueError(f"activity missing from compiled manifest: {fqcn}")


def verify(path: Path) -> None:
    manifest = path.read_text(encoding="utf-8")
    for activity in REQUIRED_ACTIVITIES:
        mask = config_mask(manifest, activity)
        missing = [
            name for name, bit in REQUIRED_BITS.items() if mask & bit != bit
        ]
        if missing:
            raise ValueError(
                f"{activity} configChanges={hex(mask)} is missing: "
                + ", ".join(missing)
            )
        print(
            f"PASS: {activity} configChanges={hex(mask)} includes "
            + "+".join(REQUIRED_BITS)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        type=Path,
        help="Text output from `aapt dump xmltree <apk> AndroidManifest.xml`",
    )
    args = parser.parse_args()
    verify(args.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
