"""Add a direct Ambient Home entry below SETTINGS in the Infinity drawer.

This is a skin-only forward patch built from the locked 1.0.5.175 ambient
candidate.  It reuses the existing Command Center ``ambient-home`` action, so
the drawer does not create another setting or another playback/ambient owner.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import zipfile
from pathlib import Path

from lxml import etree as E


PARENT_SHA = "9c34f0b158fbdcc2aae5b74c29f86d0f1b6e6844e56bd8b7ddd677ef49dc9b72"
PROFILES = ("16x9", "20x9", "6x5", "5x6", "portrait")
EXPECTED_MODIFIED = {
    "skin.infinity.diggz/addon.xml",
    "skin.infinity.diggz/infinity-skin.json",
    "skin.infinity.diggz/Infinity-Protected-Manifest.json",
    "skin.infinity.diggz/INFINITY_DRAWER_AMBIENT.txt",
    *(f"skin.infinity.diggz/{p}/Custom_1198_InfinityNav.xml" for p in PROFILES),
}


def _child(root: E._Element, tag: str, text: str) -> None:
    node = E.SubElement(root, tag)
    node.text = text


def _copy_visual(settings: E._Element, ambient: E._Element) -> None:
    for tag in (
        "font",
        "align",
        "aligny",
        "textoffsetx",
        "textoffsety",
        "texturefocus",
        "texturenofocus",
        "textcolor",
        "focusedcolor",
        "disabledcolor",
    ):
        source = settings.find(tag)
        if source is not None:
            ambient.append(copy.deepcopy(source))


def patch_drawer(data: bytes, profile: str) -> bytes:
    root = E.fromstring(data)
    controls = root.find("controls")
    assert controls is not None, profile
    settings = root.xpath('.//control[@id="1198303"]')
    power = root.xpath('.//control[@id="1198304"]')
    divider = root.xpath('.//control[@id="1198955"]')
    assert len(settings) == len(power) == len(divider) == 1, profile
    assert not root.xpath('.//control[@id="1198306"]'), profile

    settings_node = settings[0]
    power_node = power[0]
    divider_node = divider[0]
    left = settings_node.findtext("left")
    top = int(settings_node.findtext("top"))
    width = settings_node.findtext("width")
    height = int(settings_node.findtext("height"))
    settings_bottom = top + height
    ambient_top = settings_bottom + 8
    power_top = ambient_top + height + 8

    # Make the focus path explicit for remotes and keyboard navigation.
    _child(settings_node, "ondown", "1198306")
    # The existing power row stays the same action; only its position and
    # focus handoff move down to make room for Ambient Home.
    old_power_top = int(power_node.findtext("top"))
    power_node.find("top").text = str(power_top)
    _child(power_node, "onup", "1198306")
    divider_node.find("top").text = str(power_top - 3)

    ambient = E.Element("control", type="button", id="1198306")
    _child(ambient, "left", left)
    _child(ambient, "top", str(ambient_top))
    _child(ambient, "width", width)
    _child(ambient, "height", str(height))
    _child(ambient, "label", "AMBIENT HOME")
    _copy_visual(settings_node, ambient)
    _child(ambient, "enable", "System.HasAddon(script.infinity.commandcenter)")
    _child(ambient, "onclick", "RunScript(script.infinity.commandcenter,ambient-home)")
    _child(ambient, "onup", "1198303")
    _child(ambient, "ondown", "1198304")
    # Insert immediately before POWER so the visual/focus order is
    # SETTINGS -> AMBIENT HOME -> POWER.
    controls.insert(controls.index(power_node), ambient)

    # Keep the power icon aligned with its shifted button.
    shift = power_top - old_power_top
    for image in root.xpath('.//control[@type="image"]'):
        texture = image.findtext("texture") or ""
        if "infinity_ui/icons/power.png" in texture:
            if image.find("top") is not None:
                image.find("top").text = str(int(image.findtext("top")) + shift)

    return E.tostring(root, encoding="UTF-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert hashlib.sha256(args.parent.read_bytes()).hexdigest() == PARENT_SHA

    args.out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.parent) as archive:
        original = {name: archive.read(name) for name in archive.namelist()}
    files = dict(original)

    changed = []
    for profile in PROFILES:
        name = f"skin.infinity.diggz/{profile}/Custom_1198_InfinityNav.xml"
        files[name] = patch_drawer(files[name], profile)
        changed.append(name)

    addon_name = "skin.infinity.diggz/addon.xml"
    addon = files[addon_name].decode()
    assert 'version="1.0.5.175"' in addon
    addon = addon.replace('version="1.0.5.175"', 'version="1.0.5.176"', 1)
    addon = addon.replace(
        "Infinity Native Video Ambient RC1 extends the locked 1.0.5.173 Experience 1–9 skin.",
        "Infinity Native Video Ambient Settings RC1 extends the locked 1.0.5.173 Experience 1–9 skin.",
    )
    files[addon_name] = addon.encode()

    skin_json_name = "skin.infinity.diggz/infinity-skin.json"
    skin_meta = json.loads(files[skin_json_name])
    skin_meta.update(
        candidate=176,
        candidate_name="Infinity Native Video Ambient Settings RC1",
        native_video_ambient_settings_drawer={
            "entry": "AMBIENT HOME",
            "location": "Infinity drawer / SYSTEM / directly below SETTINGS",
            "action": "RunScript(script.infinity.commandcenter,ambient-home)",
            "modes": ["off", "subtle", "immersive"],
            "command_center_unchanged": "0.3.5.17",
        },
    )
    files[skin_json_name] = json.dumps(skin_meta, indent=2, sort_keys=True).encode()

    manifest_name = "skin.infinity.diggz/Infinity-Protected-Manifest.json"
    manifest = json.loads(files[manifest_name])
    manifest["candidate"] = "Infinity Native Video Ambient Settings 1.0.5.176 RC1"
    ambient = dict(manifest.get("native_video_ambient", {}))
    ambient.update(
        drawer_entry="AMBIENT HOME",
        drawer_location="SYSTEM / directly below SETTINGS",
        drawer_action="RunScript(script.infinity.commandcenter,ambient-home)",
        drawer_modes=["off", "subtle", "immersive"],
        device_verified=False,
    )
    manifest["native_video_ambient"] = ambient

    notice_name = "skin.infinity.diggz/INFINITY_DRAWER_AMBIENT.txt"
    files[notice_name] = (
        "Infinity 1.0.5.176 — direct Ambient Home drawer entry\n\n"
        "Location: Infinity drawer > SYSTEM > SETTINGS, immediately below SETTINGS and above POWER.\n"
        "Action: the existing Command Center ambient-home selector.\n"
        "Modes: Off, Subtle, Immersive. One setting; no second ambient owner.\n"
        "Command Center 0.3.5.17 is unchanged.\n"
    ).encode()

    # The manifest remains the source of truth for its protected-file digests.
    for path in list(manifest.get("protected_files", {})):
        full = "skin.infinity.diggz/" + path
        if full in files:
            manifest["protected_files"][path] = hashlib.sha256(files[full]).hexdigest()
    files[manifest_name] = json.dumps(manifest, indent=2, sort_keys=True).encode()

    changed_all = {name for name in original if files[name] != original[name]}
    added = {name for name in files if name not in original}
    assert changed_all | added == EXPECTED_MODIFIED, sorted((changed_all | added) - EXPECTED_MODIFIED)

    for name, data in files.items():
        if name.endswith(".xml"):
            E.fromstring(data)

    destination = args.out / "Infinity-Mobile-1.0.5.176-Native-Video-Ambient-Settings-RC1.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=6)

    report = {
        "parent_sha256": PARENT_SHA,
        "candidate_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "candidate_version": "1.0.5.176",
        "modified_files": sorted(changed_all | added),
        "drawer_entry": "AMBIENT HOME",
        "drawer_location": "SYSTEM / directly below SETTINGS / above POWER",
        "action": "RunScript(script.infinity.commandcenter,ambient-home)",
        "modes": ["off", "subtle", "immersive"],
        "command_center_unchanged": "0.3.5.17",
        "apk_parent": 2103282,
        "physical_device_verified": False,
    }
    (args.out / "drawer-settings-preservation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
