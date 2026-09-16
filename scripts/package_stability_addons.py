#!/usr/bin/env python3
"""Build deterministic installable ZIPs for repo-owned Infinity companion add-ons.

This intentionally excludes external locked artifacts (skin, Command Center, Live,
Health Center) whose exact accepted/candidate ZIP bytes are tracked separately.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "candidate" / "stability-addons"

ADDONS = (
    "service.infinity.compat",
    "script.infinity.support",
    "script.infinity.audiopolicy",
    "service.infinity.refresh",
    "script.infinity.cobra.theme",
)

SKIP_NAMES = {"__pycache__", ".DS_Store"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def addon_meta(src: Path) -> tuple[str, str]:
    addon_xml = src / "addon.xml"
    root = ET.parse(addon_xml).getroot()
    addon_id = root.attrib.get("id", "")
    version = root.attrib.get("version", "")
    if addon_id != src.name:
        raise RuntimeError(f"addon id/path mismatch: {src.name} != {addon_id}")
    if not version:
        raise RuntimeError(f"missing version for {addon_id}")
    return addon_id, version


def members(src: Path):
    for p in sorted(src.rglob("*"), key=lambda x: x.as_posix()):
        rel = p.relative_to(src)
        if any(part in SKIP_NAMES for part in rel.parts):
            continue
        if p.is_file() and p.suffix.lower() not in SKIP_SUFFIXES:
            yield p, rel


def package(addon_name: str) -> dict:
    src = ROOT / "addons" / addon_name
    if not src.is_dir():
        raise RuntimeError(f"missing addon source: {src}")
    addon_id, version = addon_meta(src)
    filename = f"{addon_id}-{version}-Stability-Candidate.zip"
    dest = OUT / filename

    # Fixed timestamps make equivalent source trees produce equivalent ZIP bytes.
    epoch = (2026, 9, 15, 0, 0, 0)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path, rel in members(src):
            arcname = f"{addon_id}/{rel.as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=epoch)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(dest) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"CRC failure in {filename}: {bad}")
        names = zf.namelist()
        required = f"{addon_id}/addon.xml"
        if required not in names:
            raise RuntimeError(f"missing {required} in {filename}")
        if any("__pycache__" in n or n.endswith((".pyc", ".pyo")) for n in names):
            raise RuntimeError(f"cached Python bytecode packaged in {filename}")

    digest = sha256(dest)
    (OUT / f"{filename}.sha256").write_text(f"{digest}  {filename}\n", encoding="utf-8")
    return {
        "addon_id": addon_id,
        "version": version,
        "filename": filename,
        "sha256": digest,
        "files": len(list(members(src))),
        "source": f"addons/{addon_id}",
        "device_accepted": False,
    }


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    manifest = [package(name) for name in ADDONS]
    manifest_path = OUT / "STABILITY-ADDON-ZIPS.json"
    manifest_path.write_text(json.dumps({"schema": 1, "artifacts": manifest}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("PASS: deterministic installable stability addon ZIPs built and CRC-verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
