#!/usr/bin/env python3
"""Inventory every locked skin XML and profile without modifying the skin."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def inventory(root):
    manifest = ET.parse(root / "addon.xml").getroot()
    assert manifest.get("id") == "skin.infinity.diggz" and manifest.get("version") == "1.0.5.223"
    files, failures = [], []
    profiles = {}
    profile_dirs = {file.parent for file in root.rglob("AddonBrowser.xml")}
    for file in sorted(root.rglob("*.xml")):
        relative = file.relative_to(root).as_posix()
        raw = file.read_bytes()
        try:
            tree = ET.fromstring(raw)
        except ET.ParseError as error:
            failures.append(dict(file=relative, error=str(error)))
            continue
        controls = tree.findall(".//control")
        row = dict(file=relative, sha256=hashlib.sha256(raw).hexdigest(), root=tree.tag,
                   window_id=tree.get("id"), control_types=dict(Counter(x.get("type", "unknown") for x in controls)),
                   animations=len(tree.findall(".//animation")),
                   layouts=len(tree.findall(".//itemlayout")) + len(tree.findall(".//focusedlayout")))
        files.append(row)
        if file.parent in profile_dirs and tree.tag in ("window", "includes"):
            profile = profiles.setdefault(file.parent.relative_to(root).as_posix(), dict(xml_files=0, windows=[], includes=0,
                                                               controls=0, animations=0, layouts=0))
            profile["xml_files"] += 1
            profile["controls"] += len(controls)
            profile["animations"] += row["animations"]
            profile["layouts"] += row["layouts"]
            if tree.tag == "window":
                profile["windows"].append(file.name)
            else:
                profile["includes"] += 1
            if file.name == "Custom_1193_InfinityBrowse.xml":
                panel = tree.find(".//control[@id='50']")
                assert panel is not None
                profile["custom_addon_grid"] = dict(
                    panel_id=50, bounds={name: panel.findtext(name) for name in ("left", "top", "width", "height", "bottom")},
                    layouts=[dict(tag=node.tag, **node.attrib) for node in panel if node.tag in ("itemlayout", "focusedlayout")])
    declared = [dict(node.attrib) for node in manifest.findall("./extension[@point='xbmc.gui.skin']/res")]
    summary = dict(schema=1, scope="LOCKED_SOURCE_INVENTORY_ONLY; NO RENDER OR TOUCH ACCEPTANCE",
                   skin_version=manifest.get("version"), declared_resolutions=declared,
                   xml_files=len(files), xml_parse_failures=failures,
                   profiles=profiles, skin_modified=False, physical_fold_verified=False)
    return summary, dict(summary=summary, files=files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skin-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--detail", type=Path, required=True)
    args = parser.parse_args()
    summary, detail = inventory(args.skin_root)
    for file, data in ((args.summary, summary), (args.detail, detail)):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(dict(xml_files=summary["xml_files"], failures=len(summary["xml_parse_failures"]),
                         profiles={name: value["xml_files"] for name, value in summary["profiles"].items()})))
