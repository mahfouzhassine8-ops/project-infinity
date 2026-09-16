#!/usr/bin/env python3
"""Package Cobra's ZIP-driven presentation contract as a Kodi-installable ZIP.

The package contains no APK/native code. A compatible Cobra UI runtime reads
both the visual tokens and structural UI definition at runtime. Native-only
contracts (renderer, lifecycle, rotation, background/resume and playback) are
explicitly outside this package.
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
    if data.get("schema") not in (1, 2):
        raise RuntimeError("unsupported Cobra theme schema")
    for key in (
        "background", "rail", "panel", "panel2", "focus", "accent",
        "accent_soft", "text", "muted", "line", "row_height",
        "guide_row_height",
    ):
        if key not in data:
            raise RuntimeError("missing Cobra theme token: " + key)
    if data.get("schema") >= 2:
        for key in ("touch_target", "rail_item_height", "motion_ms"):
            if key not in data:
                raise RuntimeError("missing Cobra responsive token: " + key)

    ui_file = SOURCE / "resources" / "cobra-ui.json"
    ui = json.loads(ui_file.read_text(encoding="utf-8"))
    if ui.get("schema") != 1:
        raise RuntimeError("unsupported Cobra UI schema")
    runtime = ui.get("runtime", {})
    if runtime.get("scope") != "cobra-live-only":
        raise RuntimeError("Cobra UI package must remain Cobra Live-only")
    if int(runtime.get("minimum_runtime", 0)) < 3:
        raise RuntimeError("Cobra UI package requires runtime 3+")
    protected = ui.get("protected_contracts", {})
    for key in (
        "rotation", "fold", "background_resume", "renderer",
        "provider_playback", "infinity_handoff",
    ):
        if protected.get(key) != "native":
            raise RuntimeError("Cobra UI ZIP cannot own native contract: " + key)
    nav = ui.get("navigation", {})
    if nav.get("mode") not in ("drawer", "rail", "compact_rail"):
        raise RuntimeError("invalid Cobra navigation mode")
    touch = ui.get("touch", {})
    if not isinstance(touch.get("single_tap_activate"), bool):
        raise RuntimeError("Cobra touch contract missing single_tap_activate")
    multiview = ui.get("multiview", {})
    if int(multiview.get("minimum_tiles", 0)) < 1:
        raise RuntimeError("Cobra MultiView minimum must be at least one tile")
    if int(multiview.get("maximum_tiles", 0)) > 4:
        raise RuntimeError("Cobra MultiView maximum cannot exceed runtime capacity")
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
            f"{ADDON_ID}/resources/cobra-ui.json",
        ):
            if required not in names:
                raise RuntimeError("missing ZIP member: " + required)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{digest}  {output.name}\n", encoding="utf-8"
    )
    print(f"PASS: Cobra Theme/UI {version} ZIP -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = validate()
    output = args.output or Path("candidate") / f"Infinity-Cobra-Theme-{version}.zip"
    build(output)


if __name__ == "__main__":
    main()
