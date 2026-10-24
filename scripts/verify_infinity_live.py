#!/usr/bin/env python3
import argparse
import ast
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED = [
    "addon.xml",
    "default.py",
    "resources/lib/app.py",
    "resources/lib/catalog.py",
    "resources/lib/guide.py",
    "resources/lib/m3u.py",
    "resources/lib/models.py",
    "resources/lib/network.py",
    "resources/lib/providers.py",
    "resources/lib/sources.py",
    "resources/lib/storage.py",
    "resources/lib/ui.py",
    "resources/lib/xmltv.py",
    "resources/icon.png",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--addon", default="addons/script.infinity.live")
    args = parser.parse_args()
    root = Path(args.addon)
    missing = [rel for rel in REQUIRED if not (root / rel).is_file()]
    if missing:
        raise SystemExit("missing Infinity Live files: " + ", ".join(missing))
    xml = ET.parse(root / "addon.xml").getroot()
    if xml.attrib.get("id") != "script.infinity.live":
        raise SystemExit("wrong addon id")
    for path in root.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*.py"))
    forbidden = ["CobraTV", "cobratv", "hardcoded-password", "hardcoded-username"]
    hits = [token for token in forbidden if token in text]
    if hits:
        raise SystemExit("forbidden copied/reference strings: " + ", ".join(hits))
    print("Infinity Live static verification: PASS")
    print(f"Python files parsed: {len(list(root.rglob('*.py')))}")
    print("No third-party CobraTV code/name references are shipped.")


if __name__ == "__main__":
    main()
