#!/usr/bin/env python3
"""Read-only #8 inspection of the exact protected skin .228 source ZIP.

Never rewrites a ZIP member, changes Kodi/native code, or promotes a release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
import zipfile

EXPECTED_SHA = "39f8f041376748fbe209868a33ef51e1cfd59082ee6ebb8ad095e6f85336bdef"
P = "skin.infinity.diggz/"
SENSITIVE = ("InfinityFilePreview.xml", "Includes_InfinityPreview.xml", "FileBrowser.xml",
             "DialogContextMenu.xml", "SelectDialog.xml", "Custom_1193_InfinityBrowse.xml")
SCREEN_NAMES = ("Home.xml", "SettingsCategory.xml", "Custom_1194_InfinityCommandCenter.xml",
                "Custom_1195_InfinityAudioSubtitles.xml", "Custom_1196_InfinityPlaybackSpeed.xml",
                "Custom_1198_InfinityNav.xml", "DialogContextMenu.xml")


def inspect(source: Path):
    h = hashlib.sha256(source.read_bytes()).hexdigest()
    if h != EXPECTED_SHA:
        raise ValueError("Skin .228 source SHA-256 mismatch; refusal")
    result = dict(parent_sha256=h, version="1.0.5.228", physical_fold_verified=False,
                  native_apk_modified=False, cobra_modified=False, inspected={})
    with zipfile.ZipFile(source) as z:
        names = z.namelist()
        if z.testzip() is not None or len(names) != len(set(names)) or len(names) != 3072:
            raise ValueError("Invalid original 3,072-member skin source")
        xml = sorted(n for n in names if n.endswith(".xml"))
        assert ET.fromstring(z.read(P + "addon.xml")).attrib["version"] == "1.0.5.228"
        for name in xml:
            ET.fromstring(z.read(name))
        result["xml_members_parsed"] = len(xml)
        for screen in (*SENSITIVE, *SCREEN_NAMES):
            matches = [n for n in xml if n.endswith("/" + screen)]
            if not matches:
                result["inspected"][screen] = {"absent": True}
                continue
            contents = {n: z.read(n) for n in matches}
            active = P + "unified/" + screen
            if active not in contents:
                raise ValueError("Skin active XML missing: " + active)
            data = contents[active]
            tree = ET.fromstring(data)
            actions = [e.text for e in tree.iter() if e.tag in
                       ("onclick", "onload", "onunload", "onfocus", "onunfocus", "onback")
                       and e.text and ("Preview" in e.text or "preview" in e.text
                                       or "Zip" in e.text or "zip" in e.text)]
            result["inspected"][screen] = dict(
                copies=len(matches), active_sha256=hashlib.sha256(data).hexdigest(),
                active_size=len(data), root_tag=tree.tag,
                controls=[dict(id=e.get("id"), type=e.get("type"),
                    label=e.findtext("label"), visible=e.findtext("visible"),
                    onclick=[v.text for v in e.findall("onclick")],
                    left=e.findtext("left"), top=e.findtext("top"),
                    width=e.findtext("width"), height=e.findtext("height"))
                    for e in tree.iter("control")][:80],
                preview_actions=actions,
                includes=[e.text for e in tree.iter("include") if e.text][:80],
                vars=sorted(set(re.findall(rb'\$VAR\[([^\]]+)\]',data.decode("utf-8").encode()))).__len__()
            )
        result["preview_scripts"] = [n for n in names if "preview" in n.lower() and
                                      n.startswith(P + "resources/")]
        result["preview_xml_members"] = [n for n in names if n.endswith(tuple(SENSITIVE[:2]))]
        for name in (P+"unified/InfinityFilePreview.xml",
                     P+"unified/Includes_InfinityPreview.xml",
                     P+"unified/FileBrowser.xml"):
            if name in names:
                print("\n----- " + name + " -----\n" + z.read(name).decode("utf-8")[:23000])
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--skin", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = inspect(a.skin)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "inspected"}, indent=2))
    for name,row in result["inspected"].items():
        print(name, "copies", row.get("copies"), "sha", row.get("active_sha256"),
              "preview_actions", row.get("preview_actions"),
              "controls", [(c.get("id"), c.get("type"), c.get("label")) for c in row.get("controls",[])])
