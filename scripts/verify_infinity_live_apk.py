#!/usr/bin/env python3
"""Static APK integrity gate for the app-bundled Infinity Live module."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ADDON_ID = "script.infinity.live"
ADDON_PREFIX = f"assets/addons/{ADDON_ID}/"
RELEASE = "1.0.9-Live-Candidate-1"
VERSION_CODE = 2103127
REQUIRED = (
    "addon.xml",
    "default.py",
    "resources/icon.png",
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
    "resources/media/background_dark.png",
    "resources/media/background_light.png",
    "resources/media/panel_dark.png",
    "resources/media/panel_light.png",
    "resources/media/focus_dark.png",
    "resources/media/focus_light.png",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_rotation_gate():
    path = ROOT / "scripts/verify_infinity_player_rotation_apk.py"
    spec = importlib.util.spec_from_file_location("rotation_gate_for_live", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def verify(apk: Path, engine: Path, source_receipt: Path) -> dict:
    rotation = load_rotation_gate()
    result = rotation.verify(apk, engine, source_receipt)
    repo_addon = ROOT / "addons" / ADDON_ID

    with zipfile.ZipFile(apk) as final, zipfile.ZipFile(engine) as base:
        names = final.namelist()
        if len(names) != len(set(names)):
            raise AssertionError("final APK contains duplicate members")
        for rel in REQUIRED:
            member = ADDON_PREFIX + rel
            if member not in names:
                raise AssertionError(("missing Infinity Live member", member))
            source = repo_addon / rel
            if source.is_file() and final.read(member) != source.read_bytes():
                raise AssertionError(("APK Live member differs from reviewed source", rel))
        addon_xml = ET.fromstring(final.read(ADDON_PREFIX + "addon.xml"))
        if addon_xml.get("id") != ADDON_ID or addon_xml.get("version") != "0.1.0":
            raise AssertionError("unexpected Infinity Live add-on identity")
        live_members = [n for n in names if n.startswith(ADDON_PREFIX)]
        if any("__pycache__" in n or n.endswith(".pyc") for n in live_members):
            raise AssertionError("compiled Python cache leaked into APK")
        live_text = b"\n".join(final.read(n) for n in live_members if n.endswith((".py", ".xml", ".json", ".txt"))).decode("utf-8", "ignore")
        for forbidden in ("CobraTV", "cobratv", "hardcoded-password", "hardcoded-username"):
            if forbidden in live_text:
                raise AssertionError(("forbidden third-party/credential marker", forbidden))

        # Live is an upper-layer Python module. The compiled engine must be byte
        # identical before/after overlay, branding and signing.
        compared = []
        for name in base.namelist():
            if name.startswith("lib/") or re.fullmatch(r"classes\d*\.dex", name):
                if name not in names or base.read(name) != final.read(name):
                    raise AssertionError(("compiled engine changed during Live packaging", name))
                compared.append(name)

        addon_hashes = {n[len(ADDON_PREFIX):]: sha(final.read(n)) for n in live_members if not n.endswith("/")}

    result.update({
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "infinity_live_api": 1,
        "infinity_live_addon": ADDON_ID,
        "infinity_live_version": "0.1.0",
        "supported_user_sources": ["m3u", "m3u8", "xmltv", "xtream-style"],
        "bundled_provider_credentials": False,
        "compiled_engine_members_preserved": len(compared),
        "addon_hashes": addon_hashes,
        "runtime_tested": False,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.apk, args.engine, args.source_receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity Live module bundled; compiled engine preserved")
    print("Device acceptance is still required for provider loading, preview, guide and fullscreen round-trip.")


if __name__ == "__main__":
    main()
