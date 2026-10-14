#!/usr/bin/env python3
"""Skin-only, hash-pinned add-on tile launch fix; original 2103377 RC5 APK untouched.

Kodi dynamic <content> needs target="videos" for folder item activation.
All profiles of custom Browse dialog 1193 are corrected without rerouting
the add-ons or changing tile shape/focus. Exact parent skin is mandatory.
"""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

PARENT_SHA="460762f78ad2a1cb2d54639e973d20a5958de0c22575a0d7f228b7f1cdc73815"
CANDIDATE_SHA="2f251ccca12bb88c439ad94c11d17a2b55c233ecfb4e4cdbe01f8d9ba4cc0880"
ROOT="skin.infinity.diggz/"
PROFILES=("16x9","20x9","5x6","6x5","portrait",
"responsive/base","responsive/landscape","responsive/portrait","responsive/square",
"responsive/tall","responsive/ultrawide","responsive/wide","unified")
PATHS={f"{ROOT}{p}/Custom_1193_InfinityBrowse.xml" for p in PROFILES}
BEFORE='<content>$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>'
AFTER='<content target="videos">$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>'

def digest(data):return hashlib.sha256(data).hexdigest()
def check(ok, msg):
    if not ok:raise RuntimeError(msg)

def package(locked, out, receipt):
    check(digest(locked.read_bytes())==PARENT_SHA, "Wrong locked 1.0.5.211 skin")
    with zipfile.ZipFile(locked) as src:
        check(src.testzip() is None, "Source ZIP CRC failed")
        names=src.namelist()
        check(len(names)==len(set(names)), "Duplicate ZIP path")
        check({n for n in names if n.endswith("/Custom_1193_InfinityBrowse.xml")}==PATHS, "Wrong responsive profiles")
        changed={}
        for path in sorted(PATHS):
            source=src.read(path).decode("utf-8-sig")
            check(source.count(BEFORE)==1, f"Unverified browse file {path}")
            node=ET.fromstring(source)
            panel=node.find('.//control[@type="panel"][@id="50"]')
            check(node.get("id")=="1193" and node.get("type")=="dialog" and panel is not None,
                  f"Dialog/controls changed in {path}")
            content=panel.find("content")
            check(content is not None and not content.attrib and content.text ==
                  "$INFO[Window(Home).Property(Infinity.BrowsePath)]", f"Source changed in {path}")
            update=source.replace(BEFORE, AFTER)
            new=ET.fromstring(update)
            new_content=new.find('.//control[@type="panel"][@id="50"]/content')
            check(new_content.attrib=={"target":"videos"}, f"No native videos target: {path}")
            new_content.attrib.clear()
            check(ET.tostring(node)==ET.tostring(new),f"Other UI delta: {path}")
            changed[path]=update.encode()
        manifest=ROOT+"addon.xml"
        old=src.read(manifest).decode("utf-8-sig")
        check('<addon id="skin.infinity.diggz" version="1.0.5.211"' in old, "Wrong addon manifest")
        new=old.replace('<addon id="skin.infinity.diggz" version="1.0.5.211"',
                        '<addon id="skin.infinity.diggz" version="1.0.5.213"',1)
        changed[manifest]=new.encode()
        check(len(changed)==14,"Wrong delta budget")
        out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(out,"w",allowZip64=True) as dst:
            for entry in src.infolist():
                dst.writestr(entry,changed.get(entry.filename,src.read(entry.filename)))
    with zipfile.ZipFile(locked) as src,zipfile.ZipFile(out) as dst:
        check(dst.testzip() is None and dst.namelist()==names,"Candidate ZIP layout/CRC changed")
        diff={n for n in names if src.read(n)!=dst.read(n)}
        check(diff==set(changed),"Unauthorized changed files")
        for n in names:
            a,b=src.getinfo(n),dst.getinfo(n)
            check(a.compress_type==b.compress_type and a.external_attr==b.external_attr,
                  f"ZIP member attributes changed: {n}")
        xmls=[n for n in names if n.startswith(ROOT) and n.endswith(".xml")]
        for n in xmls:ET.fromstring(dst.read(n))
    candidate=digest(out.read_bytes())
    check(candidate==CANDIDATE_SHA,"Candidate binary bytes differ from tested artifact")
    proof={
        "locked_parent":"skin.infinity.diggz 1.0.5.211","locked_parent_sha256":PARENT_SHA,
        "candidate":"skin.infinity.diggz 1.0.5.213 - Add-on Tile Selection RC1",
        "candidate_sha256":candidate,"candidate_size_bytes":out.stat().st_size,
        "zip_entries":len(names),"byte_identical":len(names)-len(changed),
        "changed_paths":sorted(changed),"profiles_verified":len(PROFILES),
        "all_xml_parsed":len(xmls),"zip_crc_clean":True,
        "other_ui_and_routes_identical":True,
        "native_apk_changed":False,"trakt_or_resume_hub_changed":False,
        "physical_addon_launch_verified":False,"locked":False
    }
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(proof,sort_keys=True,indent=2)+"\n")
    print(json.dumps(proof,sort_keys=True,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--locked",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    package(a.locked,a.out,a.receipt)
