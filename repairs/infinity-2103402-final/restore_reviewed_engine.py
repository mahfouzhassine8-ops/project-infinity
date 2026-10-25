#!/usr/bin/env python3
"""Reconstruct EXACT native 2103401 source and apply only four reviewed 2103402 changes.

Receipts and symlinks are required. This never pulls another Kodi tree, native
binary, provider, Cobra file or user data. Use only on a clean GitHub runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile

from native_ownership_qa import ENGINE_FILES

LINKS = {
    "system/settings/freebsd.xml": "linux.xml",
    "xbmc/platform/darwin/tvos/Assets.xcassets/LaunchImage.launchimage/applaunch_screen.png":
        "../../../../../../media/applaunch_screen.png",
}
COUNT = 9407


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def restore(source_zip, original_map, receipt, overlay, target, out):
    if target.exists() or out.exists():
        raise ValueError("Refusing stale or preexisting native build target")
    expected = json.loads(original_map.read_text())
    origin = json.loads(receipt.read_text())
    owner = json.loads((overlay / "EXACT-NATIVE-OWNER-REPAIR.json").read_text())
    originals = origin.get("original_links")
    if not isinstance(originals, dict) or {n: v["target"] for n, v in originals.items()} != LINKS:
        raise ValueError("Unverified original symlink targets")
    if len(expected) != COUNT or set(owner["allowed_native_changes"]) != set(ENGINE_FILES):
        raise ValueError("Native source inventory or owner scope changed")
    final = dict(expected)
    for name, metadata in owner["allowed_native_changes"].items():
        if expected[name] != metadata["baseline_sha256"]:
            raise ValueError("Native original file pin drift: " + name)
        changed = overlay / name
        if digest(changed.read_bytes()) != metadata["corrected_sha256"]:
            raise ValueError("Native changed file pin drift: " + name)
        final[name] = metadata["corrected_sha256"]
    with ZipFile(source_zip) as z:
        entries = [i for i in z.infolist() if i.filename.startswith("native/") and not i.is_dir()]
        names = [i.filename.removeprefix("native/") for i in entries]
        if len(entries) != COUNT or len(set(names)) != COUNT or set(names) != set(expected):
            raise ValueError("Native source ZIP inventory incomplete or duplicated")
        for i in entries:
            rel = i.filename.removeprefix("native/")
            path = Path(rel)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Disallowed source path: " + rel)
            data = z.read(i)
            if digest(data) != expected[rel]:
                raise ValueError("Invalid native preimage: " + rel)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            dest.chmod((i.external_attr >> 16) & 0o777)
    for name, link in LINKS.items():
        loc = target / name
        loc.unlink()
        loc.symlink_to(link)
        if not loc.resolve().is_relative_to(target.resolve()) or digest(loc.read_bytes()) != expected[name]:
            raise ValueError("Original build symlink hash mismatch: " + name)
    for name in ENGINE_FILES:
        loc = target / name
        if loc.is_symlink():
            raise ValueError("Patched source unexpectedly symbolic")
        loc.write_bytes((overlay / name).read_bytes())
    # Last complete verification proves that 9,403 other files were unchanged.
    actual = {p.relative_to(target).as_posix(): digest(p.read_bytes())
              for p in target.rglob("*") if p.is_file()}
    if actual != final:
        raise ValueError("Full native source inventory differs from exactly approved 4-member patch")
    out.mkdir(parents=True)
    (out / "NATIVE-SOURCE-MAP.json").write_text(json.dumps(final, sort_keys=True, indent=2) + "\n")
    (out / "NATIVE-OWNER-INTEGRATION.json").write_text(json.dumps({
        "original_source_count": COUNT,
        "modified_native_files": sorted(ENGINE_FILES),
        "untouched_sources_verified": COUNT - len(ENGINE_FILES),
        "original_links_verified": LINKS,
        "Cobra_modified": False,
        "CommandCenter_source_pins_disabled": False,
        "user_database_modified": False,
        "source_sha256": final,
        "physical_fold": "NOT_TESTED",
    }, sort_keys=True, indent=2) + "\n")
    print("Native source restored and verified: 9,403 unchanged, 4 exact owner corrections")
    return final


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--map", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--overlay", required=True, type=Path)
    p.add_argument("--target", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    restore(a.source, a.map, a.receipt, a.overlay, a.target, a.out)
