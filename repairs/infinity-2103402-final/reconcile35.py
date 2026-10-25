#!/usr/bin/env python3
"""2103402 companion-version correction using already compiled/signed native QA.

Only change exactly three APK payload members:
* Command Center manifest .36 -> .35, retaining all code and user-passed UI
* Watched Bridge hashes of three revised, user-passed Command Center sources
* one 64-character SHA256 string in the compiled engine's read-only .rodata

This is an explicit matched-component packaging repair, not a new native build.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path
from zipfile import ZipFile

APK = "Infinity-2103402-Matching-Native-Ownership-QA.apk"
FINAL = "Infinity-2103402-CommandCenter-03535-Matched-QA.apk"
CC = "assets/addons/script.infinity.commandcenter/"
WB = "assets/addons/script.infinity.watchedbridge/"
MANIFEST = CC+"addon.xml"
PINS = WB+"CONTROLLER-PREIMAGES.json"
SO = "lib/arm64-v8a/libkodi.so"
OLD_SO_HASH = "1d9758144623f5f1e9ba0743e58ec2b78a84f9d8067d8ef870f1748bc9b38615"
HASH_36 = "1b0b2ae9da31cd4772463799d4a3d44d0fce0639ef514221d506f25d09efc10b"
HASH_35 = "f6021a3f3c556a0a5377d462552a01c7f6fab463c495e7070c9a916451b379d2"
OLD_PINS_HASH = "56e743fe9683d7b650c5cc9d2bad0b33e4c16d51a295c542ca3c1cdc646a707e"
PINS_REVIEWED = {
 "information.py": ("c388b83353bff8e7687a545d3a00ea16691a208bd34b3a0a0678ff6441abb54e",
                    "8cf3cfcab461d73d4e8bb625039d905478ffb52688f729252002b292ea87c429"),
 "resources/skins/Default/1080i/InfinityInformation.xml":
                   ("bcfae57fcacc96a799e67f0c80cdfc22919a4a39fcb7f8ef9876eabf02f3a1e7",
                    "b9059729493751dfc0be65801f73e41a06b604f3fdaf099963821b84f2b2e443"),
 "service.py": ("ca9233507680c5d013468a38d4996bb54389ebe4d3e2410df8c241dd8340f6c5",
                "51fc63f6922885c8473277398e6f3569274eb42afe06be0148501d6ddc65bb23")
}
SIGNATURE_MEMBERS = {"META-INF/INFINITY.RSA", "META-INF/INFINITY.SF", "META-INF/MANIFEST.MF"}
SOURCE_COMPONENTS = {
 "script.infinity.commandcenter-0.3.5.36.zip":
    ("script.infinity.commandcenter-0.3.5.35-MATCHED-QA.zip", "script.infinity.commandcenter/addon.xml", MANIFEST),
 "script.infinity.watchedbridge-1.0.16.zip":
    ("script.infinity.watchedbridge-1.0.16-MATCHED-QA.zip",
     "script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json", PINS)
}
UNCHANGED_COMPONENTS = {
 "skin.infinity.diggz-1.0.5.243.zip", "script.infinity.uirepair-0.1.18.zip"
}


def check(test, why):
    if not test: raise RuntimeError(why)


def sha(blob): return hashlib.sha256(blob).hexdigest()


def section_at(data, offset):
    check(data[:4] == b'\x7fELF' and data[4:6] == b'\x02\x01'
          and data[18:20] == b'\xb7\x00', "Expected real 64-bit ARM64 ELF")
    start = struct.unpack_from('<Q', data, 0x28)[0]
    size, count, names = struct.unpack_from('<HHH', data, 0x3A)
    check(size==64 and 0<=names<count and start+size*count<=len(data),
          "Invalid native section table")
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, start+size*i)
                for i in range(count)]
    strtab = sections[names]
    strings = data[strtab[4]:strtab[4]+strtab[5]]
    for item in sections:
        if item[4] <= offset and offset+64 <= item[4]+item[5]:
            idx = item[0]
            end = strings.find(b'\0', idx)
            check(end>idx, "Invalid ELF section name")
            return strings[idx:end].decode(), item[2]
    raise RuntimeError("Replacement digest does not belong to an ELF section")


def new_native(original):
    check(sha(original)==OLD_SO_HASH, "Wrong previously compiled native engine")
    before, after = HASH_36.encode(), HASH_35.encode()
    check(original.count(before)==1, "Compiled 2103402 owner hash is not unique")
    offset=original.index(before)
    name,flags=section_at(original,offset)
    check(name=='.rodata' and flags & 2 and not flags & 1,
          "Owner literal isn't isolated in read-only .rodata")
    check(original[offset-1]==0 and original[offset+64]==0,
          "Owner SHA is not a standalone 64-character native constant")
    value=original[:offset]+after+original[offset+64:]
    check(len(value)==len(original) and
          value[:offset]==original[:offset] and
          value[offset+64:]==original[offset+64:] and
          value.count(before)==0 and value.count(after)==2,
          "Native patch touched unauthorized bytes")
    check(section_at(value,offset)==(name,flags),"ELF section metadata changed")
    return value


def required_edits(apk):
    with ZipFile(apk) as z:
        check(len(z.namelist())==len(set(z.namelist())),"Duplicate signed APK entries")
        existing=z.read(MANIFEST)
        check(sha(existing)==HASH_36 and existing.count(b'version="0.3.5.36"')==1,
              "Unexpected Command Center manifest source")
        manifest=existing.replace(b'version="0.3.5.36"',
                                  b'version="0.3.5.35"', 1)
        check(sha(manifest)==HASH_35,
              "Downgrade must change VERSION ONLY, retaining the exact .35 manifest")
        oldfile=z.read(PINS)
        check(sha(oldfile)==OLD_PINS_HASH,
              "Watched Bridge file pin inventory is not the approved input")
        current=json.loads(oldfile)
        check(len(current)==25 and current['addon.xml']==HASH_35,
              "Watched Bridge must validate 25 Command Center files")
        for name,(before,after) in PINS_REVIEWED.items():
            check(current.get(name)==before,
                  "Wrong old file pin: "+name)
            current[name]=after
            check(sha(z.read(CC+name))==after,
                  "User-approved source member changed: "+name)
        for name,want in current.items():
            raw = manifest if name=='addon.xml' else z.read(CC+name)
            check(sha(raw)==want, "Tracked member incompatible with reviewed source: "+name)
        wb_controller=z.read(WB+'controller.py')
        trakt=z.read(CC+'infinity_trakt.py')
        check(b'get("version") != "0.3.5.35"' in wb_controller,
              "Tracked controller version contract unexpectedly changed")
        check(b"'script.infinity.commandcenter','0.3.5.35'" in trakt,
              "Tracking menu expects different Command Center version")
        newpins=(json.dumps(current,indent=2,ensure_ascii=False)+'\n').encode()
        check(newpins!=oldfile, "Controller pin correction is empty")
        return {MANIFEST:manifest, PINS:newpins, SO:new_native(z.read(SO))}


def copy_zip(original,destination,edits,skip_signature=False):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(original) as source:
        names=source.namelist()
        check(len(names)==len(set(names)) and set(edits)<=set(names),
              "Duplicate/missing source entries")
        with ZipFile(destination,'w',allowZip64=True) as output:
            for info in source.infolist():
                if skip_signature and info.filename in SIGNATURE_MEMBERS:continue
                with output.open(copy.copy(info),'w',
                                 force_zip64=info.file_size>=2**31) as target:
                    if info.filename in edits:
                        target.write(edits[info.filename])
                    else:
                        with source.open(info) as old:
                            shutil.copyfileobj(old,target,1024*1024)


def verify(original,candidate,edits,signed=False):
    with ZipFile(original) as a,ZipFile(candidate) as b:
        x,y=set(a.namelist()),set(b.namelist())
        check(len(x)==len(a.namelist()) and len(y)==len(b.namelist()),
              "Duplicate ZIP member")
        if signed:
            check(all(name.startswith('META-INF/') for name in x^y),
                  "Unexpected removed/added application files")
        else:check(x==y,"Component ZIP member inventory mismatch")
        changes=[]
        for name in sorted(x&y):
            if name in SIGNATURE_MEMBERS:continue
            with a.open(name) as src,b.open(name) as dst:
                ah=hashlib.sha256();bh=hashlib.sha256()
                for stream,h in ((src,ah),(dst,bh)):
                    for block in iter(lambda:stream.read(1024*1024),b''):
                        h.update(block)
            if ah.digest()!=bh.digest():
                check(name in edits and bh.hexdigest()==sha(edits[name]),
                      "Unauthorized file changed in signed package: "+name)
                changes.append(name)
        check(set(changes)==set(edits),"Missing approved changes: "+str(set(edits)-set(changes)))
        return changes


def stage(args):
    original=args.input/APK
    check(original.is_file(),"Required signed native-owner QA APK is missing")
    edits=required_edits(original)
    target=args.out/'unsigned-cc03535.apk'
    copy_zip(original,target,edits,skip_signature=True)
    changed=verify(original,target,edits,signed=True)
    components=[]
    for original_name,(new_name,member,target_path) in SOURCE_COMPONENTS.items():
        old=args.input/original_name
        dest=args.out/new_name
        member_edits={member:edits[target_path]}
        copy_zip(old,dest,member_edits)
        verify(old,dest,member_edits)
        components.append(new_name)
    for oldname in UNCHANGED_COMPONENTS:
        shutil.copyfile(args.input/oldname,args.out/oldname)
        components.append(oldname)
    receipt={
       "source_signed_build":40149635167,
       "reused_compiled_native_engine":True,
       "native_rebuild":False,
       "native_modification":"Only one exact .rodata owner hash constant; machine instructions unchanged",
       "Command_Center_version":"0.3.5.35, newer validated code preserved",
       "Watched_Bridge":"1.0.16, matching three updated CC file hashes",
       "all_other_APK_contents":"byte-identical to user-tested native QA",
       "Cobra":"untouched",
       "signed_QA_modified_members":changed,
       "matching_ZIPs":sorted(components),
       "Fold_visual_passes":"all 5 preserved by byte identity",
       "Search_runtime":"NOT YET VERIFIED",
       "long_press_menu":"NOT YET VERIFIED",
       "TV_Continue_Playing":"NOT YET VERIFIED",
       "Home_return":"still incomplete",
       "known_Search_SIGBUS":"not in this scope",
       "installation":"Install-over APK, then explicitly reinstall matched CC .35 and WB .16 ZIPs; DO NOT uninstall or clear app data"
    }
    (args.out/'COMPATIBILITY-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print("PASS: Exact 3-member APK patch, two matching component updates, no native recompilation")


def verify_signed(args):
    check(args.signed is not None,"Signed APK path required")
    changes=verify(args.input/APK,args.signed,
                   required_edits(args.input/APK),signed=True)
    check(len(changes)==3,"Signed release requires exactly three changed app content members")
    print("PASS: signed APK matches exact new-version compatibility contract")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['stage','verify'])
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--signed',type=Path)
    args=parser.parse_args()
    if args.action=='stage':
        if args.out is None:parser.error('--out required')
        stage(args)
    else:verify_signed(args)
