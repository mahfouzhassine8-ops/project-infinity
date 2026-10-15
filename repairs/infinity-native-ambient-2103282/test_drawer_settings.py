"""Structural/UI contract for the direct Ambient Home drawer entry."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from lxml import etree as E


PARENT_SHA = "9c34f0b158fbdcc2aae5b74c29f86d0f1b6e6844e56bd8b7ddd677ef49dc9b72"
PROFILES = ("16x9", "20x9", "6x5", "5x6", "portrait")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    assert hashlib.sha256(args.parent.read_bytes()).hexdigest() == PARENT_SHA
    with zipfile.ZipFile(args.parent) as archive:
        old = {name: archive.read(name) for name in archive.namelist()}
    with zipfile.ZipFile(args.candidate) as archive:
        new = {name: archive.read(name) for name in archive.namelist()}

    allowed = {
        "skin.infinity.diggz/addon.xml",
        "skin.infinity.diggz/infinity-skin.json",
        "skin.infinity.diggz/Infinity-Protected-Manifest.json",
        "skin.infinity.diggz/INFINITY_DRAWER_AMBIENT.txt",
        *(f"skin.infinity.diggz/{p}/Custom_1198_InfinityNav.xml" for p in PROFILES),
    }
    changed = {name for name in old if old[name] != new.get(name)} | set(new) - set(old)
    assert changed == allowed, sorted(changed - allowed)

    for profile in PROFILES:
        path = f"skin.infinity.diggz/{profile}/Custom_1198_InfinityNav.xml"
        root = E.fromstring(new[path])
        settings = root.xpath('.//control[@id="1198303"]')[0]
        ambient = root.xpath('.//control[@id="1198306"]')[0]
        power = root.xpath('.//control[@id="1198304"]')[0]
        assert settings.findtext("label") == "SETTINGS"
        assert ambient.findtext("label") == "AMBIENT HOME"
        assert ambient.findtext("onclick") == "RunScript(script.infinity.commandcenter,ambient-home)"
        assert ambient.findtext("enable") == "System.HasAddon(script.infinity.commandcenter)"
        assert settings.findtext("ondown") == "1198306"
        assert ambient.findtext("onup") == "1198303"
        assert ambient.findtext("ondown") == "1198304"
        assert power.findtext("onup") == "1198306"
        settings_bottom = int(settings.findtext("top")) + int(settings.findtext("height"))
        ambient_top = int(ambient.findtext("top"))
        power_top = int(power.findtext("top"))
        assert ambient_top > settings_bottom
        assert power_top > ambient_top + int(ambient.findtext("height"))
        assert len(root.xpath('.//control[@id="1198306"]')) == 1

    manifest = json.loads(new["skin.infinity.diggz/Infinity-Protected-Manifest.json"])
    for path, digest in manifest["protected_files"].items():
        assert hashlib.sha256(new["skin.infinity.diggz/" + path]).hexdigest() == digest, path
    print("PASS: direct Ambient Home drawer entry in", len(PROFILES), "profiles")


if __name__ == "__main__":
    main()
