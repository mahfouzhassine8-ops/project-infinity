#!/usr/bin/env python3
"""Re-sign previously user-tested 2103402 QA with exact newly compiled native owner.

Package content delta is *only* lib/arm64-v8a/libkodi.so. Android signing
entries are regenerated in the workflow with the original certificate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile

BASE = "Infinity-2103402-Functional-Corrective-QA.apk"
TARGET = "Infinity-2103402-Matching-Native-Ownership-QA.apk"
SO = "lib/arm64-v8a/libkodi.so"
SIG = {"META-INF/INFINITY.SF", "META-INF/INFINITY.RSA", "META-INF/MANIFEST.MF"}
COMPONENT_NAMES = [
    "script.infinity.commandcenter-0.3.5.36.zip",
    "script.infinity.uirepair-0.1.18.zip",
    "script.infinity.watchedbridge-1.0.16.zip",
    "skin.infinity.diggz-1.0.5.243.zip",
]
BASELINE_SO = "704834f42e49a2eea0a36ad41b5f79345f5e4108dcd339213899ea3c6ff045a0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def copy_apk(original, destination, new_so):
    with ZipFile(original) as previous:
        names = previous.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate signed QA ZIP member")
        if sha(previous.read(SO)) != BASELINE_SO:
            raise ValueError("Unexpected user-tested QA native image")
        candidate = new_so.read_bytes()
        if candidate[:4] != b"\x7fELF" or candidate[4] != 2 or candidate[18:20] != b"\xb7\x00":
            raise ValueError("Native output is not ARM64 ELF")
        if len(candidate) < 1_000_000 or sha(candidate) == BASELINE_SO:
            raise ValueError("Native code did not compile into a new valid engine")
        for marker in (
            b"1b0b2ae9da31cd4772463799d4a3d44d0fce0639ef514221d506f25d09efc10b",
            b"8cf3cfcab461d73d4e8bb625039d905478ffb52688f729252002b292ea87c429",
            b"b9059729493751dfc0be65801f73e41a06b604f3fdaf099963821b84f2b2e443",
            b"51fc63f6922885c8473277398e6f3569274eb42afe06be0148501d6ddc65bb23",
            b"0.3.5.36",
            b"Infinity.Search.Protocol",
            b"CHECKPOINT_FAILED",
        ):
            if marker not in candidate:
                raise ValueError("New native binary missing reviewed owner or protection: " + repr(marker))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(destination, "w", allowZip64=True) as out:
            for info in previous.infolist():
                if info.filename in SIG:
                    continue
                with out.open(copy.copy(info), "w", force_zip64=info.file_size >= 2**31) as target:
                    if info.filename == SO:
                        target.write(candidate)
                    else:
                        with previous.open(info, "r") as inp:
                            shutil.copyfileobj(inp, target, 1024 * 1024)
    print("Unsigned native-owner corrective staged, all previously accepted QA addon bytes retained")


def verify(original, candidate, packages):
    with ZipFile(original) as src, ZipFile(candidate) as dst:
        original_members=set(src.namelist())
        new_members=set(dst.namelist())
        if len(src.namelist())!=len(original_members) or len(dst.namelist())!=len(new_members):
            raise ValueError("Duplicate packaged member")
        if any(n for n in original_members ^ new_members if not n.startswith("META-INF/")):
            raise ValueError("Unexpected added/removed app component")
        changed=[]
        for name in src.namelist():
            if name in SIG:
                continue
            if name not in dst.namelist():
                raise ValueError("Required original APK member missing: " + name)
            with src.open(name) as a, dst.open(name) as b:
                ah=hashlib.sha256();bh=hashlib.sha256()
                for fileobj,h in ((a,ah),(b,bh)):
                    for chunk in iter(lambda: fileobj.read(1024*1024), b""):
                        h.update(chunk)
            if ah.digest()!=bh.digest():
                changed.append(name)
        if changed!=[SO]:
            raise ValueError("Native-only member boundary violated: " + repr(changed))
        if src.read("AndroidManifest.xml")!=dst.read("AndroidManifest.xml"):
            raise ValueError("APK manifest identity changed")
        for zname in COMPONENT_NAMES:
            with ZipFile(packages / zname) as part:
                if len(part.namelist())!=len(set(part.namelist())):
                    raise ValueError("Duplicate matching component ZIP")
                for member in part.namelist():
                    if member.endswith("/"):
                        continue
                    if part.read(member) != dst.read("assets/addons/" + member):
                        raise ValueError("On-disk component and signed APK bytes disagree: " + member)
    return changed


def receipt(args, changed):
    data={
        "baseline_signed_qa_run": 40144024130,
        "source_native_baseline_run": 40089463702,
        "version_code": 2103402,
        "ABI": "arm64-v8a",
        "modified_apk_content_members": changed,
        "all_other_QA_members_unchanged": True,
        "Cobra_native_or_resources_changed": False,
        "user_data_modified": False,
        "matching_command_center": "0.3.5.36",
        "matching_skin": "1.0.5.243",
        "all_five_user_passed_visual_changes_retained": True,
        "Search_compatibility": "NATIVE_OWNER_CORRECTED; ANDROID_RUNTIME_NOT_YET_PASSED",
        "TV_Continue_Playing": "REQUIRES_PHYSICAL_CONFIRMATION",
        "Home_return_posters": "STILL_UNRESOLVED",
        "Essential_First": "REQUIRES_ANDROID17_AND_FOLD_VERIFICATION",
        "Search_SIGBUS": "SEPARATE_UNRESOLVED_ISSUE"
    }
    (args.out / "NATIVE-OWNER-PACKAGE-RECEIPT.json").write_text(json.dumps(data,indent=2)+"\n")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["stage","verify"])
    p.add_argument("--qa",required=True,type=Path)
    p.add_argument("--compiled-so",type=Path)
    p.add_argument("--signed",type=Path)
    p.add_argument("--components",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    qa=a.qa / BASE
    if not qa.is_file():
        raise FileNotFoundError(qa)
    if a.mode=="stage":
        if not a.compiled_so:
            p.error("--compiled-so required")
        copy_apk(qa,a.out/"unsigned-native-ownership.apk",a.compiled_so)
        changed=verify(qa,a.out/"unsigned-native-ownership.apk",a.components)
    else:
        if not a.signed:
            p.error("--signed required")
        changed=verify(qa,a.signed,a.components)
    receipt(a,changed)
    print("PASS: only libkodi.so changed from physical Fold QA; all matching component ZIPs identical")


if __name__=="__main__":
    main()
