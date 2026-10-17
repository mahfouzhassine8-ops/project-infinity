#!/usr/bin/env python3
"""Extract production 16x9 row controls/assets for real Kodi renderer comparison."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from skin_build import WATCHED, PARENT_SHA


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(before, after, output):
    files = {}
    report = dict(schema=1, baseline_zip_sha256=PARENT_SHA, profile="16x9",
                  scope="Extracted production provider-row controls, source palette variables, default fonts and assets in a disposable Kodi test skin; not full-skin or Fold acceptance",
                  native_index_verified_by_this_fixture=False, watched_condition=WATCHED, sources={})
    for version, skin in (("before", before), ("after", after)):
        profile = skin / "16x9"
        definitions = {}
        for path in sorted(profile.glob("*.xml")):
            root = ET.parse(path).getroot()
            if root.tag == "includes":
                for node in root:
                    if node.get("name") and node.tag in ("include", "variable", "expression"):
                        definitions[(node.tag, node.get("name"))] = copy.deepcopy(node)
        selected = {("include", "InfinityPluginDirectoryCompact"), ("include", "InfinityPluginDirectoryRegular"),
                    ("variable", "InfinityLegacyBase")}
        done = set(); result = ET.Element("includes")
        while selected - done:
            key = sorted(selected - done)[0]
            done.add(key)
            node = definitions.get(key)
            if node is None:
                raise ValueError("Missing production fixture dependency: " + repr(key))
            result.append(copy.deepcopy(node))
            raw = ET.tostring(node, encoding="unicode")
            selected.update(("variable", name) for name in re.findall(r"\$VAR\[([^,\]]+)", raw))
            selected.update(("expression", name) for name in re.findall(r"\$EXP\[([^\]]+)\]", raw))
            for inc in node.iter("include"):
                name = inc.get("content") or (inc.text or "").strip()
                if name and ("include", name) in definitions:
                    selected.add(("include", name))
        ET.indent(result, space="  ")
        files[version + "/InfinityFixture.xml"] = ET.tostring(result, encoding="utf-8", xml_declaration=True)
        fonts = ET.Element("fonts")
        used = {node.text for node in result.iter("font") if node.text and not node.text.startswith("$")}
        source_fonts = ET.parse(profile / "Font.xml").getroot().find("fontset")
        for font in source_fonts.findall("font"):
            if font.findtext("name") in used:
                fonts.append(copy.deepcopy(font))
                filename = font.findtext("filename")
                files["fonts/" + filename] = (skin / "fonts" / filename).read_bytes()
        if {node.findtext("name") for node in fonts} != used:
            raise ValueError("Fixture fonts are not the production default fontset")
        files[version + "/Fonts.xml"] = ET.tostring(fonts, encoding="utf-8")
        assets = set()
        for node in result.iter():
            value = (node.text or "").strip()
            if "$" not in value and value.lower().endswith((".png", ".jpg")):
                path = skin / "media" / value
                if path.is_file():
                    assets.add(value)
                    files[version + "/media/" + value] = path.read_bytes()
        report["sources"][version] = {"View_50_List.xml": digest(profile / "View_50_List.xml"),
            "Font.xml": digest(profile / "Font.xml"), "definitions": len(done), "assets": len(assets),
            "fixture_sha256": hashlib.sha256(files[version + "/InfinityFixture.xml"]).hexdigest()}
    files["SOURCE-IDENTITY.json"] = (json.dumps(report, indent=2) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    print(json.dumps(dict(file=str(output), bytes=output.stat().st_size, sha256=digest(output), scope=report["scope"])))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.before, args.after, args.output)
