#!/usr/bin/env python3
"""Package the native Cobra visual contract as a Kodi-installable ZIP.

This intentionally contains no APK/native code. InfinityLiveActivity reads the
installed JSON tokens at runtime, so visual tuning can be tested without a full
Kodi/Android rebuild.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ADDON_ID = "script.infinity.cobra.theme"
SOURCE = ROOT / "addons" / ADDON_ID


def addon_version() -> str:
    root = ET.fromstring((SOURCE / "addon.xml").read_text(encoding="utf-8"))
    if root.attrib.get("id") != ADDON_ID:
        raise RuntimeError("unexpected Cobra theme addon id")
    version = root.attrib.get("version", "").strip()
    if not version:
        raise RuntimeError("Cobra theme version missing")
    return version


def validate() -> str:
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)
    version = addon_version()
    theme = SOURCE / "resources" / "cobra-theme.json"
    data = json.loads(theme.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise RuntimeError("unsupported Cobra theme schema")
    for key in (
        "background", "rail", "panel", "panel2", "focus", "accent",
        "accent_soft", "text", "muted", "line", "row_height",
        "guide_row_height",
    ):
        if key not in data:
            raise RuntimeError("missing Cobra theme token: " + key)
    return version


def build(output: Path) -> None:
    version = validate()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(SOURCE.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            arc = f"{ADDON_ID}/{path.relative_to(SOURCE).as_posix()}"
            z.write(path, arc)
    with zipfile.ZipFile(output) as z:
        names = set(z.namelist())
        for required in (
            f"{ADDON_ID}/addon.xml",
            f"{ADDON_ID}/resources/cobra-theme.json",
        ):
            if required not in names:
                raise RuntimeError("missing ZIP member: " + required)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{digest}  {output.name}\n", encoding="utf-8"
    )
    print(f"PASS: Cobra Theme {version} ZIP -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = validate()
    output = args.output or Path("candidate") / f"Infinity-Cobra-Theme-{version}.zip"
    build(output)


if __name__ == "__main__":
    main()
