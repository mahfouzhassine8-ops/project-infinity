#!/usr/bin/env python3
"""2103407 Search-overload-only install-over packaging from EXACT signed 2103406.

Changes are limited to the Search source, matching addon version and mutual
integrity pins, verified read-only native SHA constants, and Android version
code. No native executable instructions or unrelated player/Cobra changes.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import struct
from pathlib import Path
from zipfile import ZipFile

PARENT_NAME="Infinity-2103406-SIGABRT-Crash-Recorder-QA.apk"
OUTPUT_NAME="Infinity-2103407-Search-Single-Flight-SIGNED-QA.apk"
PARENT_SHA="a388be6cbcda5a2fb9b740300fde09e247519d9a23552ead30e84080fd9852cf"
PREFIX="assets/addons/"
CC="script.infinity.commandcenter/"
WB="script.infinity.watchedbridge/"
UI="script.infinity.uirepair/"
SKIN="skin.infinity.diggz/"
NATIVE="lib/arm64-v8a/libkodi.so"
RECORDER="lib/arm64-v8a/libinfinitycrash.so"
SIGNATURE={"META-INF/INFINITY.SF","META-INF/INFINITY.RSA","META-INF/MANIFEST.MF"}
V={
  CC:("0.3.5.38","0.3.5.39"),
  WB:("1.0.19","1.0.20"),
  UI:("0.1.21","0.1.22"),
}
PARENT_COMPONENTS={
  CC:"script.infinity.commandcenter-0.3.5.38-2103405-QA.zip",
  WB:"script.infinity.watchedbridge-1.0.19-2103405-QA.zip",
  UI:"script.infinity.uirepair-0.1.21-2103405-QA.zip",
  SKIN:"skin.infinity.diggz-1.0.5.243.zip",
}
TARGET_COMPONENTS={
  CC:"script.infinity.commandcenter-0.3.5.39-2103407-QA.zip",
  WB:"script.infinity.watchedbridge-1.0.20-2103407-QA.zip",
  UI:"script.infinity.uirepair-0.1.22-2103407-QA.zip",
  SKIN:"skin.infinity.diggz-1.0.5.243.zip",
}
CHANGES=frozenset({
  "AndroidManifest.xml",
  NATIVE,
  PREFIX+CC+"infinity_search.py",
  PREFIX+CC+"addon.xml",
  PREFIX+CC+"infinity_trakt.py",
  PREFIX+WB+"addon.xml",
  PREFIX+WB+"controller.py",
  PREFIX+WB+"CONTROLLER-PREIMAGES.json",
  PREFIX+UI+"addon.xml",
  PREFIX+UI+"CONTROLLER-PREIMAGES.json",
})

def require(ok, message):
    if not ok:raise RuntimeError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as inp:
        for chunk in iter(lambda:inp.read(4*1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def replace_once(body,before,after,where):
    require(body.count(before)==1,
            where+": expected exactly one occurrence of "+repr(before[:80]))
    return body.replace(before,after,1)

def addon_version(body,prefix):
    old,new=V[prefix]
    return replace_once(body,('version="'+old+'"').encode(),
                        ('version="'+new+'"').encode(),prefix+" addon version")

def manifest_version(body):
    before=struct.pack("<I",2103406)
    after=struct.pack("<I",2103407)
    require(body.count(before)==1 and after not in body,"Unexpected manifest versionCode")
    i=body.index(before)
    require(body[i-4:i]==b"\x08\x00\x00\x10","versionCode is not typed integer AXML")
    return body[:i]+after+body[i+4:]

def hash_readonly_offsets(native,old):
    """Allow hash replacement only in read-only allocated ELF .rodata."""
    require(native[:4]==b"\x7fELF" and native[4:6]==b"\x02\x01"
            and native[18:20]==b"\xb7\x00","Native ELF is not ARM64")
    offset=struct.unpack_from("<Q",native,0x28)[0]
    entsize,count,string_index=struct.unpack_from("<HHH",native,0x3a)
    require(entsize==64 and 0<=string_index<count and
            offset+count*entsize<=len(native),"Unexpected ELF section inventory")
    sections=[struct.unpack_from("<IIQQQQIIQQ",native,offset+64*i)
              for i in range(count)]
    sec=sections[string_index]
    names=native[sec[4]:sec[4]+sec[5]]
    out=[]
    at=0
    while True:
        i=native.find(old,at)
        if i<0:break
        require(i>0 and i+64<len(native) and native[i-1]==0 and native[i+64]==0,
                "Hash slot not a bounded immutable C literal")
        matching=[]
        for section in sections:
            start,size=section[4],section[5]
            if start<=i and i+64<=start+size:
                end=names.find(b"\0",section[0])
                label=names[section[0]:end]
                matching.append((label,section[2]))
        require(len(matching)==1 and matching[0][0]==b".rodata"
                and matching[0][1]&2 and not matching[0][1]&1,
                "Native owner hash outside immutable .rodata")
        out.append(i)
        at=i+64
    return out

def native_pin_update(native,old_new):
    copy=bytearray(native)
    touched={}
    for filename,(before,after) in old_new.items():
        slots=hash_readonly_offsets(native,before.encode())
        expected=2 if filename=="addon.xml" else 1
        require(len(slots)==expected,"Native hash slots unexpected for "+filename)
        for i in slots:copy[i:i+64]=after.encode()
        touched[filename]=slots
    for filename,(before,after) in old_new.items():
        for i in touched[filename]:copy[i:i+64]=before.encode()
    require(bytes(copy)==native,"Readonly hash patches not reversible")
    for filename,(before,after) in old_new.items():
        for i in touched[filename]:copy[i:i+64]=after.encode()
    # No code, Cobra, JNI, or other native data modified. Verified by reverse.
    return bytes(copy),touched

def write_archive(source,dest,edits,strip_signature=False):
    with ZipFile(source) as reader,ZipFile(dest,"w",allowZip64=True) as writer:
        original=reader.namelist()
        require(len(original)==len(set(original)),"Duplicate archive names")
        require(set(edits).issubset(original),"Archive missing intended changed member")
        for info in reader.infolist():
            n=info.filename
            if strip_signature and n in SIGNATURE:continue
            with writer.open(copy.copy(info),"w",force_zip64=info.file_size>=2**31) as output:
                if n in edits: output.write(edits[n])
                else:
                    with reader.open(info) as inp:shutil.copyfileobj(inp,output,4*1024*1024)

def construct_changes(base,source):
    cc_search=base.read(PREFIX+CC+"infinity_search.py")
    require(sha(cc_search)=="a5640a725d07440e914fd5f8d83a29196ea9cbb1104686f1929b5140040b2c44",
            "Wrong signed 2103406 Search base")
    patched=source.read_bytes()
    require(sha(patched)=="bb6e8791ca7644ca9d370b5871d69ded71790557069b56535e920baa6cf50531",
            "Wrong reviewed 2103407 Search correction")
    compile(patched.decode(),"infinity_search.py","exec")
    require(b"Infinity Tracked" in base.read(PREFIX+CC+"addon.xml"),
            "Protected WatchNixtoons2 native menu missing from parent")
    cc_edits={
      "infinity_search.py":patched,
      "addon.xml":addon_version(base.read(PREFIX+CC+"addon.xml"),CC),
    }
    bridge={
      "addon.xml":addon_version(base.read(PREFIX+WB+"addon.xml"),WB),
      "controller.py":replace_once(base.read(PREFIX+WB+"controller.py"),
                                   b"0.3.5.38",b"0.3.5.39",
                                   "Watched Bridge CC owner version"),
    }
    # Match protected reciprocal installed watchedbridge contract.
    original_trakt=base.read(PREFIX+CC+"infinity_trakt.py")
    bridge_line=re.search(rb"BRIDGE_PINS\s*=\s*(\{[^\n]+\})",original_trakt)
    require(bridge_line is not None,"Watched Bridge reciprocal pins absent")
    pins=ast.literal_eval(bridge_line.group(1).decode())
    require(len(pins)>=4,"Watched Bridge pin inventory damaged")
    trakt=original_trakt
    for n,raw in bridge.items():
        before=pins[n].encode()
        actual=sha(base.read(PREFIX+WB+n)).encode()
        require(actual==before,"Existing watched bridge contract not pinned: "+n)
        trakt=replace_once(trakt,before,sha(raw).encode(),"CC reciprocal bridge pin "+n)
    trakt=replace_once(trakt,b"'1.0.19'",b"'1.0.20'","CC Watched Bridge version")
    trakt=replace_once(trakt,b"'0.3.5.38'",b"'0.3.5.39'","CC self version")
    # The original uses single quotes in the verified-component version arguments.
    compile(trakt.decode(),"infinity_trakt.py","exec")
    cc_edits["infinity_trakt.py"]=trakt
    changed={PREFIX+CC+n:c for n,c in cc_edits.items()}
    changed.update({PREFIX+WB+n:c for n,c in bridge.items()})
    changed[PREFIX+UI+"addon.xml"]=addon_version(base.read(PREFIX+UI+"addon.xml"),UI)
    for prefix in (WB,UI):
        path=PREFIX+prefix+"CONTROLLER-PREIMAGES.json"
        pins=json.loads(base.read(path))
        require(len(pins)==25,"Controller pin inventory is not 25: "+prefix)
        for n,content in cc_edits.items():
            require(pins[n]==sha(base.read(PREFIX+CC+n)),
                    "Controller pin differs from original for "+prefix+n)
            pins[n]=sha(content)
        for n,pin in pins.items():
            actual=changed.get(PREFIX+CC+n,base.read(PREFIX+CC+n))
            require(sha(actual)==pin,"Inconsistent helper pin "+prefix+n)
        changed[path]=(json.dumps(pins,indent=2,ensure_ascii=False)+"\n").encode()
    original_native=base.read(NATIVE)
    source_hashes={}
    for n,c in cc_edits.items():
        source_hashes[n]=(sha(base.read(PREFIX+CC+n)),sha(c))
    changed[NATIVE],locations=native_pin_update(original_native,source_hashes)
    changed["AndroidManifest.xml"]=manifest_version(base.read("AndroidManifest.xml"))
    require(set(changed)==CHANGES,"Unexpected packaging member scope")
    return changed,locations

def compare_parent(parent,candidate,components,expected=None):
    require(hash_file(parent)==PARENT_SHA,"Signed 2103406 parent SHA mismatch")
    with ZipFile(parent) as before,ZipFile(candidate) as after:
        names=set(before.namelist())
        newnames=set(after.namelist())
        require((names^newnames).issubset(SIGNATURE),
                "Signed candidate added/removed a protected APK member")
        differences=[]
        for n in sorted(names&newnames):
            if n in SIGNATURE:continue
            if sha(before.read(n))!=sha(after.read(n)):differences.append(n)
        require(set(differences)==CHANGES,
                "Unapproved APK content change: "+str(set(differences)^CHANGES))
        require(after.read("AndroidManifest.xml")==manifest_version(before.read("AndroidManifest.xml")),
                "Manifest version delta differs from exact requested install-over")
        require(before.read(RECORDER)==after.read(RECORDER),
                "SIGABRT recorder changed unexpectedly")
        require(before.read("classes.dex")==after.read("classes.dex"),
                "Native Search UI/DEX changed unexpectedly")
        require(before.read(PREFIX+CC+"context.py")==after.read(PREFIX+CC+"context.py"),
                "WatchNixtoons2 context handler changed")
        require(before.read(PREFIX+SKIN+"unified/Home.xml")==
                after.read(PREFIX+SKIN+"unified/Home.xml"),
                "Protected skin altered")
        old_so=before.read(NATIVE)
        new_so=after.read(NATIVE)
        require(len(old_so)==len(new_so),"Native engine file size changed")
        hashed={}
        for n in ("addon.xml","infinity_search.py","infinity_trakt.py"):
            hashed[n]=(sha(before.read(PREFIX+CC+n)),sha(after.read(PREFIX+CC+n)))
        expected_so,locations=native_pin_update(old_so,hashed)
        require(expected_so==new_so,"Native executable or unrelated data changed")
        for prefix,out_name in TARGET_COMPONENTS.items():
            with ZipFile(components/out_name) as sub:
                for name in sub.namelist():
                    if name.endswith("/"):continue
                    require(after.read(PREFIX+name)==sub.read(name),
                            "APK/component mismatch: "+out_name+" "+name)
        if expected is not None:
            require(set(expected["modified_members"])==set(differences),
                    "Signed diff does not match reviewed staging receipt")
    return sorted(differences)

def stage(args):
    parent=args.input/PARENT_NAME
    require(hash_file(parent)==PARENT_SHA,"Wrong parent or modified 2103406 APK")
    require(not args.output.exists(),"Refusing to overwrite staging output")
    with ZipFile(parent) as base:
        changed,locations=construct_changes(base,args.source)
    args.output.mkdir(parents=True)
    unsigned=args.output/"unsigned-2103407.apk"
    write_archive(parent,unsigned,changed,strip_signature=True)
    for prefix,source_name in PARENT_COMPONENTS.items():
        old=args.input/source_name
        destination=args.output/TARGET_COMPONENTS[prefix]
        require(old.is_file(),"Missing exact component ZIP "+str(old))
        require(prefix!=SKIN or hash_file(old)=="0adfed89f1d5384a3fa3a023152c7c2a094ef2edb6dd60129f336fe3b7cb9ef9",
                "Original unchanged skin SHA mismatch")
        changes={n[len(PREFIX):]:value for n,value in changed.items()
                 if n.startswith(PREFIX+prefix)}
        if prefix==SKIN:
            require(not changes,"Protected skin must not have edits")
            shutil.copyfile(old,destination)
        else:
            write_archive(old,destination,changes)
    differences=compare_parent(parent,unsigned,args.output)
    receipt={
      "release_versionCode":2103407,
      "parent_versionCode":2103406,
      "parent_sha256":PARENT_SHA,
      "modified_members":differences,
      "new_command_center_version":V[CC][1],
      "new_watched_bridge_version":V[WB][1],
      "new_ui_repair_version":V[UI][1],
      "unchanged_skin_version":"1.0.5.243",
      "preserved_sigabrt_recorder":True,
      "native_executable_instructions_unchanged":True,
      "native_immutable_hash_slot_offsets":locations,
      "Cobra_all_unrelated_members_untouched":True,
      "WatchNixtoons2_Infinity_Tracked_unchanged":True,
      "shutdown_essential_first_unchanged":True,
      "Android17_physical_stress_acceptance":"PENDING",
      "SIGSEGV_root_cause_proven":"NO",
      "signing":"PENDING",
    }
    (args.output/"INFINITY-2103407-SEARCH-INTEGRATION-RECEIPT.json").write_text(
       json.dumps(receipt,indent=2)+"\n")
    print("PASS: exact reviewed Search scope, matched mutual integrity and native read-only owner hashes")
    print("MODIFIED:",differences)

def verify(args):
    receipt=json.loads((args.output/"INFINITY-2103407-SEARCH-INTEGRATION-RECEIPT.json").read_text())
    differences=compare_parent(args.input/PARENT_NAME,args.signed,args.output,receipt)
    with ZipFile(args.signed) as archive:
        require(sha(archive.read(PREFIX+CC+"infinity_search.py"))==
                "bb6e8791ca7644ca9d370b5871d69ded71790557069b56535e920baa6cf50531",
                "Signed Search source drifted from corrected host-tested source")
    print("PASS signed candidate byte audit:",differences)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("stage","verify"))
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--source",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--signed",type=Path)
    args=parser.parse_args()
    if args.action=="stage":
        require(args.source is not None,"--source required")
        stage(args)
    else:
        require(args.signed is not None,"--signed required")
        verify(args)
