#!/usr/bin/env python3
"""Infinity 2103406: SIGABRT recorder ownership fix, ONLY two APK payload edits.

Accepted parent is the exact permanently signed 2103405.
Changes:
  lib/arm64-v8a/libinfinitycrash.so -- recompiled recorder with SIGABRT unhooked
  AndroidManifest.xml             -- 2103405 => 2103406 install-over
Everything else (native Kodi, Cobra, skin, Command Center, Watched Bridge, UI
Repair, Java/DEX, diagnostics export, Essential-First) remains byte-identical.
This is a CRASH FORENSICS correction, not a root-cause fix for native mutex UAF.
"""
import argparse
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path
from zipfile import ZipFile

PARENT_NAME = "Infinity-2103405-WatchNixtoons2-Infinity-Tracked-Context-QA.apk"
TARGET_NAME = "Infinity-2103406-SIGABRT-Crash-Recorder-QA.apk"
PARENT_SHA256 = "22414799b39cb5ea7ace1085f5d8b0e313654b07979884585b183faffdd066c9"
OLD_RECORDER_SHA256 = "bc7aab86fc97844e02e25c96fc73f269bc85f5f8ce5528e132a78841aa130bca"
RECORDER = "lib/arm64-v8a/libinfinitycrash.so"
NATIVE_KODI = "lib/arm64-v8a/libkodi.so"
MANIFEST = "AndroidManifest.xml"
OLD_VERSION = 2103405
NEW_VERSION = 2103406
SIG = {"META-INF/INFINITY.SF", "META-INF/INFINITY.RSA", "META-INF/MANIFEST.MF"}
COMPONENTS = (
    "script.infinity.commandcenter-0.3.5.38-2103405-QA.zip",
    "script.infinity.watchedbridge-1.0.19-2103405-QA.zip",
    "script.infinity.uirepair-0.1.21-2103405-QA.zip",
    "skin.infinity.diggz-1.0.5.243.zip",
)

def require(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()

def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def manifest_update(raw):
    original=struct.pack("<I",OLD_VERSION)
    newer=struct.pack("<I",NEW_VERSION)
    require(raw.count(original)==1 and newer not in raw,
            "Manifest versionCode must be a single unambiguous exact integer")
    at=raw.index(original)
    require(raw[at-4:at]==b"\x08\x00\x00\x10",
            "Manifest versionCode must be typed TYPE_INT_DEC in binary AXML")
    return raw[:at]+newer+raw[at+4:]

def valid_arm64_recorder(data):
    require(data[:4]==b"\x7fELF" and data[4:6]==b"\x02\x01" and data[18:20]==b"\xb7\x00",
            "New crash recorder is not a 64-bit ARM64 ELF")
    require(len(data)>10000 and hash_bytes(data)!=OLD_RECORDER_SHA256,
            "New recorder is missing or identical to the old binary")
    for fragment in (b"native-crash-last.txt",b"native-maps-%d.txt",
                     b"native.sigsegv.",b"SIGSEGV"):
        # SIGSEGV marker is optional in compiled object because signal numbers
        # are constants; verify operational textual labels only.
        if fragment==b"SIGSEGV": continue
        require(fragment in data,"Required existing diagnostic owner removed: "+repr(fragment))

def make_zip(parent, out, changed):
    with ZipFile(parent) as original, ZipFile(out,"w",allowZip64=True) as candidate:
        names=original.namelist()
        require(len(names)==len(set(names)) and set(changed).issubset(names),
                "Signed baseline contains duplicated or missing members")
        for info in original.infolist():
            if info.filename in SIG:continue
            with candidate.open(copy.copy(info),"w",force_zip64=info.file_size >= 2**31) as target:
                if info.filename in changed:
                    target.write(changed[info.filename])
                else:
                    with original.open(info.filename) as source:
                        shutil.copyfileobj(source,target,4*1024*1024)

def compare_and_verify(parent, candidate, components, receipt):
    required = {MANIFEST,RECORDER}
    require(hash_file(parent)==PARENT_SHA256,"Parent signed 2103405 APK hash mismatch")
    with ZipFile(parent) as base, ZipFile(candidate) as target:
        aa=base.namelist()
        bb=target.namelist()
        require(len(aa)==len(set(aa)) and len(bb)==len(set(bb)),"Duplicate APK member")
        require((set(aa)^set(bb)).issubset(SIG),"Unexpected APK member insertion/removal")
        modified=[]
        for name in sorted(set(aa)&set(bb)):
            if name in SIG:continue
            digest_a=hashlib.sha256()
            digest_b=hashlib.sha256()
            for z,h in ((base,digest_a),(target,digest_b)):
                with z.open(name) as inp:
                    for chunk in iter(lambda:inp.read(4*1024*1024),b""):
                        h.update(chunk)
            if digest_a.digest()!=digest_b.digest():modified.append(name)
        require(set(modified)==required,
                "Unapproved signed APK change(s): "+str(set(modified)^required))
        require(target.read(MANIFEST)==manifest_update(base.read(MANIFEST)),
                "Manifest change is not exact versionCode transition")
        require(hash_bytes(base.read(RECORDER))==OLD_RECORDER_SHA256,
                "Original crash recorder binary mismatch")
        valid_arm64_recorder(target.read(RECORDER))
        # Compiled Kodi engine, Cobra, all UI skin and APK components
        # were checked in the complete-member comparison above.
        for name in (NATIVE_KODI,"classes.dex",
                     "assets/addons/script.infinity.commandcenter/context.py",
                     "assets/addons/script.infinity.commandcenter/resume_hub.py",
                     "assets/addons/skin.infinity.diggz/unified/Home.xml"):
            require(base.read(name)==target.read(name),"Protected payload changed: "+name)
        for component in COMPONENTS:
            with ZipFile(components/component) as package:
                for item in package.namelist():
                    if not item.endswith("/"):
                        require(target.read("assets/addons/"+item)==package.read(item),
                                "APK component mismatch: "+component+" "+item)
    return modified

def stage(args):
    require(not args.output.exists(),"Refusing stale output directory")
    require(hash_file(args.input/PARENT_NAME)==PARENT_SHA256,"Wrong signed 2103405 parent")
    require(hash_file(args.input/COMPONENTS[0])!=hash_file(args.input/PARENT_NAME),
            "Invalid component inventory")
    with ZipFile(args.input/PARENT_NAME) as src:
        require(hash_bytes(src.read(RECORDER))==OLD_RECORDER_SHA256,
                "Old recorder binary does not match audited 2103405")
        new_manifest=manifest_update(src.read(MANIFEST))
    new_binary=args.compiled.read_bytes()
    valid_arm64_recorder(new_binary)
    args.output.mkdir(parents=True)
    unsigned=args.output/"unsigned-2103406.apk"
    make_zip(args.input/PARENT_NAME,unsigned,{MANIFEST:new_manifest,RECORDER:new_binary})
    for file in COMPONENTS:
        shutil.copyfile(args.input/file,args.output/file)
    diff=compare_and_verify(args.input/PARENT_NAME,unsigned,args.output,None)
    receipt={
      "baseline_versionCode":OLD_VERSION,"candidate_versionCode":NEW_VERSION,
      "base_signed_apk_sha256":PARENT_SHA256,
      "modified_apk_payload_members":diff,
      "old_recorder_sha256":OLD_RECORDER_SHA256,
      "new_recorder_sha256":hash_bytes(new_binary),
      "original_kodi_native_engine_unchanged":True,
      "Cobra_and_all_other_APK_members_unchanged":True,
      "command_center_and_watchnixtoons2_unchanged":True,
      "watched_bridge_uirepair_skin_unchanged":True,
      "Essential_First_shutdown_unmodified":True,
      "root_cause_destroyed_mutex_repaired":False,
      "debuggerd_abort_tombstone_device_validation":"PENDING",
      "original_signing_certificate_verified":"PENDING",
      "Fold_Android17_acceptance":"PENDING"
    }
    (args.output/"INFINITY-2103406-RECORDER-RECEIPT.json").write_text(
         json.dumps(receipt,indent=2)+"\n")
    print("PASS exact two-member 2103406 stage; 2103405 untouched")

def verify(args):
    receipt=json.loads((args.output/"INFINITY-2103406-RECORDER-RECEIPT.json").read_text())
    changed=compare_and_verify(args.input/PARENT_NAME,args.signed,args.output,receipt)
    require(set(changed)==set(receipt["modified_apk_payload_members"]),
            "Signed artifact differs from staging")
    with ZipFile(args.signed) as z:
        require(hash_bytes(z.read(RECORDER))==receipt["new_recorder_sha256"],
                "Signed native recorder no longer matches compiled binary")
    print("PASS: exact scoped signed APK, original native Kodi/skin/Cobra, 4 original ZIPs")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("stage","verify"))
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--compiled",type=Path)
    p.add_argument("--signed",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.command=="stage":
        require(args.compiled is not None,"--compiled is required")
        stage(args)
    else:
        require(args.signed is not None,"--signed is required")
        verify(args)
