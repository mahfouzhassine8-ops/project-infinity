#!/usr/bin/env python3
"""Reproducible RC2 skin-only build from SHA-locked Infinity skin 1.0.5.211.
Do not change the approved RC5 APK or install/disable any add-ons.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from copy import deepcopy

SOURCE_HASH="460762f78ad2a1cb2d54639e973d20a5958de0c22575a0d7f228b7f1cdc73815"
OUTPUT_HASH="3b1d5b2bb2edf8ca79ed285804e6ef71de03dfa7bfaa3853a926334c6b8b45e1"
ROOT="skin.infinity.diggz/"
PROFILES=("16x9","20x9","5x6","6x5","portrait","responsive/base","responsive/landscape",
          "responsive/portrait","responsive/square","responsive/tall","responsive/ultrawide",
          "responsive/wide","unified")
BROWSE={ROOT+p+"/Custom_1193_InfinityBrowse.xml" for p in PROFILES}
PROPERTIES=("Infinity.BrowsePath","Infinity.BrowseTitle","Infinity.BrowseSubtitle")

def sha(data):return hashlib.sha256(data).hexdigest()
def require(ok,message):
    if not ok:raise AssertionError(message)
def swap(text,old,new,label):
    require(text.count(old)==1,f"Unexpected source at {label}, matches={text.count(old)}")
    return text.replace(old,new,1)
def change_browse(data,name):
    original=ET.fromstring(data)
    require(original.attrib=={"id":"1193","type":"dialog"},name+" dialog identity")
    panel=original.find('./controls/control[@type="panel"][@id="50"]')
    require(panel is not None and panel.find("content") is not None,name+" panel")
    old_content=panel.find("content")
    require(old_content.attrib=={} and old_content.text=="$INFO[Window(Home).Property(Infinity.BrowsePath)]",name+" source")
    back=original.find('./controls/control[@type="button"][@id="10"]/onclick')
    require(back is not None and back.text=="Close",name+" Back")
    require([a.text for a in original.findall("onunload")] ==
            ["ClearProperty("+p+",Home)" for p in PROPERTIES],name+" unload policy")
    text=data.decode("utf-8-sig")
    text=swap(text,'<window id="1193" type="dialog">','<window id="1193">',name+" root")
    text=swap(text,
       '<content>$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>',
       '<content target="videos">$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>',
       name+" native target")
    text=swap(text,'<onclick>Close</onclick>','<onclick>PreviousMenu</onclick>',name+" back")
    for p in PROPERTIES:
        text=swap(text,f'  <onunload>ClearProperty({p},Home)</onunload>\n','',name+" preserve path")
    after=ET.fromstring(text)
    require(after.attrib=={"id":"1193"} and not list(after.findall("onunload")),name+" must navigate as native window")
    canonical=deepcopy(after);canonical.attrib["type"]="dialog"
    canonical.find('./controls/control[@type="panel"][@id="50"]/content').attrib.clear()
    canonical.find('./controls/control[@type="button"][@id="10"]/onclick').text="Close"
    for index,p in enumerate(PROPERTIES):
        el=ET.Element("onunload");el.text=f"ClearProperty({p},Home)";canonical.insert(3+index,el)
    for tree in (original,canonical):
        for node in tree.iter():
            node.tail=None
            if node.text is not None and not node.text.strip():node.text=None
    require(ET.tostring(original)==ET.tostring(canonical),name+" unauthorized visual/control change")
    return text.encode()

def package(parent,out,receipt):
    require(sha(parent.read_bytes())==SOURCE_HASH,"Wrong locked parent ZIP hash")
    with zipfile.ZipFile(parent) as old:
        names=old.namelist()
        require(old.testzip() is None and len(names)==len(set(names)),"Corrupt or duplicate source")
        require({n for n in names if n.endswith("/Custom_1193_InfinityBrowse.xml")}==BROWSE,
                "Changed Browse profile inventory")
        before={n:old.read(n) for n in names}
        changed={name:change_browse(before[name],name) for name in BROWSE}
        skin=ROOT+"addon.xml"
        data=before[skin].decode("utf-8-sig")
        changed[skin]=swap(data,'<addon id="skin.infinity.diggz" version="1.0.5.211"',
                          '<addon id="skin.infinity.diggz" version="1.0.5.214"',skin).encode()
        require(len(changed)==14,"Wrong skin delta budget")
        out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(out,"w",allowZip64=True) as new:
            for item in old.infolist():
                new.writestr(item,changed.get(item.filename,before[item.filename]))
    with zipfile.ZipFile(out) as new,zipfile.ZipFile(parent) as old:
        require(new.testzip() is None and new.namelist()==names,"Candidate archive invalid")
        require({n for n in names if old.read(n)!=new.read(n)}==set(changed),
                "Altered unapproved file")
        for n in names:
            a,b=old.getinfo(n),new.getinfo(n)
            require((a.compress_type,a.external_attr,a.date_time)==
                    (b.compress_type,b.external_attr,b.date_time),n+" changed member identity")
        xmls=[n for n in names if n.startswith(ROOT) and n.endswith(".xml")]
        require(len(xmls)==2075,"Wrong skin XML inventory")
        for n in xmls:ET.fromstring(new.read(n))
        layouts={n[len(ROOT):-len('/Home.xml')] for n in names
                 if n.startswith(ROOT) and n.endswith("/Home.xml")}
        require(len(layouts)==14 and "fallback" in layouts and set(PROFILES).issubset(layouts),
                "Wrong total skin layout count")
        require(all(ROOT+d+"/AddonBrowser.xml" in names for d in layouts),
                "Other native add-on browsers changed")
    actual=sha(out.read_bytes())
    require(actual==OUTPUT_HASH,"Candidate hash is not exactly the pretested RC2 ZIP")
    proof={"parent_sha256":SOURCE_HASH,"candidate_sha256":actual,
       "candidate_size_bytes":out.stat().st_size,
       "candidate_skin_version":"1.0.5.214","total_layouts":len(layouts),
       "custom_browse_windows":len(BROWSE),"total_zip_files":len(names),
       "unchanged_files":len(names)-len(changed),"xmls_parsed":len(xmls),
       "changed_files":sorted(changed),"normal_window_instead_of_dialog":True,
       "video_target":True,"native_Back":True,"browse_path_survives_child_window":True,
       "locked_2103377_rc5_apk_changed":False,
       "skin_parent_1_0_5_211_overwritten":False,"device_verified":False,"locked":False}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(proof,sort_keys=True,indent=2)+"\n")
    print(json.dumps(proof,sort_keys=True,indent=2))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--receipt",required=True,type=Path)
    args=ap.parse_args();package(args.parent,args.out,args.receipt)
