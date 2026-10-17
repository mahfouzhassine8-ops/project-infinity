#!/usr/bin/env python3
"""Forward .223 skin: typed blue badges, theme-safe titles and visible recovery."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw

PARENT_SHA = "557003afc83a2661fec6ccef921979e264ff28e93595fb633340c618ab69bd56"
WATCHED = "[String.IsEqual(ListItem.DBTYPE,movie) | String.IsEqual(ListItem.DBTYPE,episode)] + [String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),true) | [!String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),false) + [Integer.IsGreater(ListItem.PlayCount,0) | String.IsEqual(ListItem.Overlay,OverlayWatched.png)]]]"
FALSE = "[String.IsEqual(ListItem.DBTYPE,movie) | String.IsEqual(ListItem.DBTYPE,episode)] + String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),false)"
OVERLAYS = ("$VAR[OverlayVar]", "$VAR[ListItemOverlay]")
GEOMETRY = ("left", "right", "top", "bottom", "centerleft", "centerright", "centertop", "centerbottom", "width", "height")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(parent, name, value, **attrs):
    element = ET.SubElement(parent, name, attrs)
    element.text = value
    return element


def write(path, root):
    ET.indent(root, space="  ")
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def tint_name(value):
    return "InfinityWatched224Tint" + digest(value.encode())[:12]


def new_include(tints):
    root = ET.Element("includes")
    for name, normal, softened in (
        ("InfinityWatched224Title", "$VAR[InfinityDiggzPrimaryText]", "$VAR[InfinityDiggzSecondaryText]"),
        ("InfinityWatched224LegacyTitle", "$VAR[InfinityLegacyText]", "$VAR[InfinityLegacySecondary]")):
        variable = ET.SubElement(root, "variable", name=name)
        put(variable, "value", softened, condition=WATCHED)
        put(variable, "value", normal)
    for value in sorted(tints):
        variable = ET.SubElement(root, "variable", name=tint_name(value))
        put(variable, "value", "FFFFFFFF", condition=WATCHED)
        put(variable, "value", value)
    include = ET.SubElement(root, "include", name="InfinityWatched224Badge")
    for name, value in (("size", "24"), ("right", "-12"), ("top", "-8")):
        ET.SubElement(include, "param", name=name, default=value)
    image = ET.SubElement(ET.SubElement(include, "definition"), "control", type="image")
    for name, value in (("right", "$PARAM[right]"), ("top", "$PARAM[top]"), ("width", "$PARAM[size]"),
                        ("height", "$PARAM[size]"), ("aspectratio", "keep"), ("texture", "infinity_watched/badge.png"), ("visible", WATCHED)):
        put(image, name, value)
    return root


def wrap_art(parent, image, size):
    group = ET.Element("control", type="group")
    for child in list(image):
        if child.tag in GEOMETRY:
            image.remove(child)
            group.append(child)
    # Inherit the exact art visibility, including mutually-exclusive missing-art
    # fallbacks; a hidden reflection or fallback must not leave an orphan badge.
    if image.find("visible") is not None:
        group.append(copy.deepcopy(image.find("visible")))
    for name, value in (("left", "0"), ("top", "0"), ("width", "100%"), ("height", "100%")):
        put(image, name, value)
    group.append(image)
    badge = ET.SubElement(group, "include", content="InfinityWatched224Badge")
    ET.SubElement(badge, "param", name="size", value=str(size))
    index = list(parent).index(image)
    parent.remove(image)
    parent.insert(index, group)


def add_badges(scope, size, textures):
    count = 0
    for parent in list(scope.iter()):
        for child in list(parent):
            if child.tag == "control" and child.get("type") == "image" and child.findtext("texture") in textures:
                wrap_art(parent, child, size)
                count += 1
    for control in scope.findall(".//control[@type='label']"):
        if control.findtext("label") == "$INFO[ListItem.Label]":
            color = control.find("textcolor")
            if color is not None and color.text == "$VAR[InfinityDiggzPrimaryText]":
                color.text = "$VAR[InfinityWatched224Title]"
            elif color is not None and color.text == "$VAR[InfinityLegacyText]":
                color.text = "$VAR[InfinityWatched224LegacyTitle]"
    return count


def protect_behavior(before, after, name):
    # Existing actions, IDs, timing and motion are not silently replaced by an
    # image/style pass. The new recovery actions are the sole navigation addition.
    tags = ("onclick", "onload", "onunload", "onfocus", "onup", "onleft", "onright", "ondown", "animation", "scrolltime", "defaultcontrol", "pagecontrol", "views")
    for tag in tags:
        old = Counter((element.text or "", tuple(sorted(element.attrib.items()))) for element in before.iter(tag))
        new = Counter((element.text or "", tuple(sorted(element.attrib.items()))) for element in after.iter(tag))
        if old - new:
            raise ValueError("Existing behavior changed: " + name + " " + tag)
    old = Counter(e.get("id") for e in before.iter("control") if e.get("id"))
    new = Counter(e.get("id") for e in after.iter("control") if e.get("id"))
    if old - new:
        raise ValueError("Native control IDs removed: " + name)


def build(parent_zip, work, output):
    assert digest(parent_zip.read_bytes()) == PARENT_SHA
    work.mkdir(parents=True, exist_ok=True)
    root = work / "skin.infinity.diggz"
    if root.exists():
        raise ValueError("Use a new isolated build directory")
    with zipfile.ZipFile(parent_zip) as archive:
        assert archive.testzip() is None
        archive.extractall(work)
    manifest = ET.parse(root / "addon.xml").getroot()
    assert manifest.get("version") == "1.0.5.223"
    original = {str(p.relative_to(root)): digest(p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    tints = set()
    sources = []
    for path in root.rglob("*.xml"):
        if path.name.startswith("View_") or path.name == "Includes_CinemaBrowse.xml":
            tree = ET.parse(path).getroot()
            for image in tree.findall(".//control[@type='image']"):
                texture = image.find("texture")
                if texture is not None and texture.text in OVERLAYS:
                    for value in (texture.get("colordiffuse"), image.findtext("colordiffuse")):
                        if value:
                            tints.add(value)
    changed_xml, badges, recovery = [], 0, []
    for path in sorted(root.rglob("*.xml")):
        before = ET.parse(path).getroot()
        after = copy.deepcopy(before)
        modified = False
        if path.name == "Includes.xml":
            after.insert(0, ET.Element("include", file="Includes_InfinityWatched224.xml"))
            write(path.parent / "Includes_InfinityWatched224.xml", new_include(tints))
            modified = True
        elif path.name == "Variables.xml":
            for name in ("OverlayVar", "ListItemOverlay"):
                variable = after.find("variable[@name='" + name + "']")
                if variable is not None:
                    condition = WATCHED + (" + !Skin.HasSetting(Disable.OverlayWatched)" if name == "OverlayVar" else "")
                    blue = ET.Element("value", condition=condition)
                    blue.text = "infinity_watched/" + ("poster_badge.png" if name == "OverlayVar" else "badge.png")
                    variable.insert(0, blue)
                    # Keep genuine resumable-state indicators ahead of an
                    # explicit Unwatched suppression of stale provider checks.
                    index = 2 if len(variable) > 1 and "IsResumable" in variable[1].get("condition", "") else 1
                    variable.insert(index, ET.Element("value", condition=FALSE))
                    modified = True
        elif path.name == "Custom_1193_InfinityBrowse.xml":
            controls = after.find("controls")
            counter = next(e for e in controls if e.get("type") == "label" and "Container(50).NumItems" in e.findtext("label", ""))
            counter.set("type", "button"); counter.set("id", "12")
            counter.find("label").text = "Manage add-ons · $INFO[Container(50).NumItems]"
            counter.find("height").text = controls.find("control[@id='10']/height").text
            put(counter, "texturefocus", "infinity_glass/focus.png", border="16", colordiffuse="$VAR[InfinityLegacyAccent]")
            put(counter, "texturenofocus", "infinity_glass/field.png", border="12", colordiffuse="$VAR[InfinityLegacyField]")
            put(counter, "focusedcolor", "$VAR[InfinityLegacyText]")
            counter.find("align").text = "center"
            put(counter, "onclick", "RunScript(script.infinity.addonrecovery)", condition="System.AddonIsEnabled(script.infinity.addonrecovery)")
            put(counter, "onclick", "ActivateWindow(AddonBrowser,addons://user/,return)", condition="!System.AddonIsEnabled(script.infinity.addonrecovery)")
            for name, value in (("onleft", "10"), ("onright", "50"), ("onup", "10"), ("ondown", "50")):
                put(counter, name, value)
            put(controls.find("control[@id='10']"), "ondown", "12")
            badges += add_badges(after.find(".//control[@id='50']"), 28, {"$VAR[PosterThumbVar]"})
            recovery.append(str(path.relative_to(root)))
            modified = True
        elif path.name == "View_50_List.xml":
            for name in ("InfinityPluginDirectoryCompact", "InfinityPluginDirectoryRegular"):
                scope = after.find("include[@name='" + name + "']")
                if scope is not None:
                    badges += add_badges(scope, 24, {"$VAR[InfinityPolishIcon0]", "infinity_ui/icons/addons.png"})
                    modified = True
        elif path.name == "Includes_InfinityHomeUnified.xml":
            for include in after.findall("include"):
                if "ContinueCard" in include.get("name", ""):
                    badges += add_badges(include, 28, {"$VAR[PosterThumbVar]", "$INFO[ListItem.Thumb]"})
                    modified = True
            variable = after.find("variable[@name='InfinityResumeHubWatchedState']")
            if variable is not None:
                negative = ET.Element("value", condition=FALSE); negative.text = "false"
                variable.insert(0, negative); modified = True
        if path.name.startswith("View_") or path.name == "Includes_CinemaBrowse.xml":
            for image in after.findall(".//control[@type='image']"):
                texture = image.find("texture")
                if texture is not None and texture.text in OVERLAYS:
                    if texture.get("colordiffuse"):
                        texture.set("colordiffuse", "$VAR[" + tint_name(texture.get("colordiffuse")) + "]")
                        modified = True
                    color = image.find("colordiffuse")
                    if color is not None and color.text:
                        color.text = "$VAR[" + tint_name(color.text) + "]"; modified = True
                    if path.name == "Includes_CinemaBrowse.xml" and image.findtext("visible") == "!ListItem.IsFolder":
                        image.find("visible").text = "!ListItem.IsFolder | [" + WATCHED + "]"
                        modified = True
            if path.name == "Includes_CinemaBrowse.xml":
                for label in after.findall(".//control[@type='label']"):
                    if label.findtext("label") == "›" and label.findtext("visible") == "ListItem.IsFolder":
                        label.find("visible").text = "ListItem.IsFolder + ![" + WATCHED + "]"; modified = True
        if modified:
            protect_behavior(before, after, str(path.relative_to(root)))
            write(path, after)
            changed_xml.append(str(path.relative_to(root)))
    assert len(recovery) == 13
    # Exact small badge, authored as geometry rather than modifying the approved
    # screenshot. Supersampling keeps the white check crisp at small UI sizes.
    media = root / "media/infinity_watched"; media.mkdir(parents=True)
    image = Image.new("RGBA", (512, 512)); draw = ImageDraw.Draw(image)
    draw.ellipse((12, 12, 500, 500), fill=(16, 141, 229, 255), outline=(255, 255, 255, 245), width=18)
    draw.line([(137, 260), (222, 339), (378, 173)], fill="white", width=40, joint="curve")
    image.resize((128, 128), Image.Resampling.LANCZOS).save(media / "badge.png")
    padded = Image.new("RGBA", (128, 128))
    padded.alpha_composite(image.resize((64, 64), Image.Resampling.LANCZOS), (64, 0))
    padded.save(media / "poster_badge.png")
    manifest.set("version", "1.0.5.224")
    manifest.find("./extension[@point='xbmc.addon.metadata']/description").text = "Infinity .224 experimental: forward from exact locked .223. Typed Infinity-blue watched badges and existing Watchlist/Collection integration, visible non-destructive add-on recovery route, original design/navigation and motion retained. Companion helper/native bridge supplies local cross-provider state when reliable metadata exists. Physical Fold acceptance pending."
    write(root / "addon.xml", manifest)
    protected_path = root / "Infinity-Protected-Manifest.json"
    protected = json.loads(protected_path.read_text())
    for name in list(protected.get("protected_files", {})):
        if name != protected_path.name and (root / name).is_file():
            protected["protected_files"][name] = digest((root / name).read_bytes())
    protected.update(candidate=224, candidate_version="1.0.5.224", skin_version="1.0.5.224", candidate_locked=False,
                     watched_recovery_224=dict(parent_sha256=PARENT_SHA, broad_animations_changed=False,
                                              source_profiles=14, recovery_windows=13, physical_fold_verified=False))
    protected_path.write_text(json.dumps(protected, indent=2, sort_keys=True) + "\n")
    current = {str(p.relative_to(root)): digest(p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    removed = sorted(set(original) - set(current)); assert not removed
    changed = sorted(name for name in original if original[name] != current[name])
    for name in changed:
        assert name in changed_xml or name in ("addon.xml", protected_path.name), name
    for name in original:
        if Path(name).name in ("Home.xml", "AddonBrowser.xml", "FileBrowser.xml", "InfinityFilePreview.xml", "InfinityRailsOptions.xml", "DialogContextMenu.xml", "DialogAddonInfo.xml", "DialogAddonSettings.xml", "VideoOSD.xml", "MusicOSD.xml", "DialogButtonMenu.xml"):
            assert current[name] == original[name], name
    parsed = sum(1 for path in root.rglob("*.xml") if ET.parse(path) is not None)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(current):
            info = zipfile.ZipInfo("skin.infinity.diggz/" + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, (root / name).read_bytes())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    report = dict(schema=1, parent_version="1.0.5.223", version="1.0.5.224", parent_sha256=PARENT_SHA,
                  file=output.name, bytes=output.stat().st_size, sha256=digest(output.read_bytes()),
                  original_files=len(original), unchanged_original_files=len(original)-len(changed),
                  changed=changed, added=sorted(set(current)-set(original)), removed=removed,
                  xml_parsed=parsed, direct_badge_instances=badges, recovery_windows=recovery,
                  existing_native_control_ids_and_actions_retained=True, broad_animations_changed=False,
                  apk_rails_command_center_or_userdata_modified=False, physical_fold_verified=False)
    (output.parent / "SKIN224-PRESERVATION.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("parent-zip", "work", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = build(args.parent_zip, args.work, args.output)
    print(json.dumps({key: value for key, value in result.items() if key not in ("changed", "added", "recovery_windows")}, indent=2))
