#!/usr/bin/env python3
"""Infinity 1.0.5 Candidate 1 - TEST-ONLY Diggz compatibility patcher.

Purpose:
- keep the Diggz skin/build for browsing, menus, widgets and add-ons;
- replace only the playback OSD/seek UI with Infinity's protected versions;
- merge the Infinity theme/color variables needed by those player XMLs;
- fail closed if expected files are missing instead of silently damaging a skin.

Inputs:
  1) audited Infinity APK containing skin.estuary
  2) Diggz skin ZIP (the skin add-on itself, not a whole Kodi backup)
Output:
  patched Diggz skin ZIP for testing.

This does NOT edit the installed profile, switch skins, modify libkodi.so, or touch
Android signing. It is deliberately a compatibility experiment, not a release.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

INF_SKIN = "assets/addons/skin.estuary/"
PROTECTED_PLAYER_XML = ("VideoOSD.xml", "DialogSeekBar.xml")
INF_VARS = INF_SKIN + "xml/Variables.xml"
INF_FONTS = INF_SKIN + "xml/Font.xml"

VAR_RE = re.compile(r"\$VAR\[(InfinityColor_[^\]]+)\]")
FONT_RE = re.compile(r"<font>(Infinity[^<]+)</font>")


def _read_zip(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate ZIP entries in {path}")
        return {n: z.read(n) for n in names if not n.endswith("/")}


def _detect_skin_root(files: dict[str, bytes]) -> str:
    addon_candidates = [n for n in files if n.endswith("addon.xml")]
    for addon in sorted(addon_candidates, key=len):
        root = addon[:-len("addon.xml")]
        if root + "xml/VideoOSD.xml" in files and root + "xml/Variables.xml" in files:
            return root
    raise ValueError("Diggz ZIP does not look like a skin add-on with xml/VideoOSD.xml and xml/Variables.xml")


def _merge_named_variables(source: bytes, target: bytes, wanted: set[str]) -> bytes:
    src = ET.fromstring(source)
    dst = ET.fromstring(target)
    source_vars = {v.get("name"): v for v in src.findall("variable") if v.get("name")}
    missing = sorted(wanted - set(source_vars))
    if missing:
        raise ValueError("Infinity source is missing required variables: " + ", ".join(missing))
    for old in list(dst.findall("variable")):
        if old.get("name") in wanted:
            dst.remove(old)
    for name in sorted(wanted):
        dst.append(copy.deepcopy(source_vars[name]))
    return ET.tostring(dst, encoding="utf-8", xml_declaration=True)


def _merge_named_fonts(source: bytes, target: bytes, wanted: set[str]) -> bytes:
    if not wanted:
        return target
    src = ET.fromstring(source)
    dst = ET.fromstring(target)
    src_sets = src.findall("fontset")
    dst_sets = dst.findall("fontset")
    if not src_sets or not dst_sets:
        raise ValueError("Font.xml has no fontset")
    src_by_name = {}
    for fs in src_sets:
        for font in fs.findall("font"):
            name = font.findtext("name")
            if name in wanted:
                src_by_name[name] = font
    missing = sorted(wanted - set(src_by_name))
    if missing:
        raise ValueError("Infinity source is missing required fonts: " + ", ".join(missing))
    for fs in dst_sets:
        for old in list(fs.findall("font")):
            if old.findtext("name") in wanted:
                fs.remove(old)
        for name in sorted(wanted):
            fs.append(copy.deepcopy(src_by_name[name]))
    return ET.tostring(dst, encoding="utf-8", xml_declaration=True)


def patch(infinity_apk: Path, diggz_zip: Path, out_zip: Path, receipt: Path) -> None:
    inf = _read_zip(infinity_apk)
    diggz = _read_zip(diggz_zip)
    root = _detect_skin_root(diggz)

    player_payload: dict[str, bytes] = {}
    combined_text = ""
    for name in PROTECTED_PLAYER_XML:
        src_name = INF_SKIN + "xml/" + name
        if src_name not in inf:
            raise ValueError("Infinity APK missing " + src_name)
        player_payload[root + "xml/" + name] = inf[src_name]
        combined_text += inf[src_name].decode("utf-8", errors="strict") + "\n"

    wanted_vars = set(VAR_RE.findall(combined_text))
    wanted_fonts = set(FONT_RE.findall(combined_text))
    if not wanted_vars:
        raise ValueError("Protected Infinity player XML contains no InfinityColor variables; source mismatch suspected")

    vars_path = root + "xml/Variables.xml"
    fonts_path = root + "xml/Font.xml"
    if vars_path not in diggz:
        raise ValueError("Diggz skin missing Variables.xml")
    diggz[vars_path] = _merge_named_variables(inf[INF_VARS], diggz[vars_path], wanted_vars)

    if wanted_fonts:
        if fonts_path not in diggz:
            raise ValueError("Diggz skin missing Font.xml required by Infinity player")
        diggz[fonts_path] = _merge_named_fonts(inf[INF_FONTS], diggz[fonts_path], wanted_fonts)

    diggz.update(player_payload)

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(diggz):
            z.writestr(name, diggz[name])

    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        "status": "test-only-candidate-1",
        "candidate": "Infinity 1.0.5 Candidate 1",
        "diggz_skin_root": root,
        "protected_player_files": list(PROTECTED_PLAYER_XML),
        "merged_theme_variables": sorted(wanted_vars),
        "merged_fonts": sorted(wanted_fonts),
        "engine_changed": False,
        "android_signing_changed": False,
        "installed_profile_changed": False,
        "device_tested": False,
        "scope": "Diggz remains owner of browsing UI; Infinity owns playback OSD/seek UI",
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("infinity_apk", type=Path)
    p.add_argument("diggz_skin_zip", type=Path)
    p.add_argument("out_zip", type=Path)
    p.add_argument("receipt", type=Path)
    a = p.parse_args()
    patch(a.infinity_apk, a.diggz_skin_zip, a.out_zip, a.receipt)


if __name__ == "__main__":
    main()
