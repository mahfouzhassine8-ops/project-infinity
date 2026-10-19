#!/usr/bin/env python3
"""Sign 2103391 experimental ALL-IN-ONE using exact 2103390 signed parent.

Requires genuine source-matched rebuilt ARM64 libkodi.so plus source manifest
and permanent Infinity signing secrets. No fallback/debug keystore allowed.

Combines: Group1 (except explicitly deferred task19), Group2, Group3,
Group4, Group5 stale recorder identity only (NOT fault-139 root cause),
Group6 Silent Mode. Feature freeze AFTER this experimental candidate.
Cobra, Essential-First shutdown, and all nonallowlisted APK entries unchanged.
This program cannot and does not prove physical Fold acceptance.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

import stage_all_in_one as allsource
import final_native_identity_patch as nativeidentity

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CODE=2103391
NAME="1.0.9-All-In-One-Bugfix-TEST0001"
PARENT_NAME="1.0.9-UI-Restoration-Fold-TEST06"
FILENAME="Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk"
MANIFEST="AndroidManifest.xml"
ENGINE="lib/arm64-v8a/libkodi.so"
RECORDER="lib/arm64-v8a/libinfinitycrash.so"
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
SIGNATURE=re.compile(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))",re.I)
SIGNED_PARENT_SHA256=allsource.PARENT_SHA256


def require(cond,reason):
    if not cond:raise RuntimeError("INFINITY 2103391 EXPERIMENTAL BUILD REFUSED: "+reason)


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_exact_native(original_engine:bytes,new_engine:bytes,proof:dict):
    require(proof.get("complete_native_engine_compiled") is True,
            "Full source-matched native Kodi compilation receipt missing")
    require(proof.get("rc5_17_required_save_owners_unchanged",True) is True,
            "Protected Essential-First durable owners changed")
    require(proof.get("shutdown_policy")=="essential_first_process_exit_v1",
            "Protected Essential-First Close policy replaced")
    require(proof.get("native_sha256")==sha(new_engine),
            "Native engine bytes do not match full compilation receipt")
    require(proof.get("physical_fold_verified") is not True and
            proof.get("crash_fixed") is not True,
            "CI cannot invent physical Fold/native crash qualifications")
    require(sha(original_engine)==nativeidentity.BASE_PACKAGED_ENGINE_SHA,
            "Signed 2103390 native engine identity changed")
    require(sha(new_engine)!=sha(original_engine),
            "Unmodified original engine would drop approved native fixes")
    require(len(new_engine)>90_000_000,
            "Full Kodi native engine missing or replaced by stub")
    sections=nativeidentity.elf_sections(new_engine)
    require(".text" in sections,
            "Rebuilt native ARM64 ELF code section missing")
    for literal in (
        b"RunScript(script.infinity.uirepair,option-b,",
        b"Skin.HasSetting(Infinity.SilentMode)",
        b"Hide from this browser (not Disable)",
    ):
        require(literal in new_engine,
                "Compiled Group2/3/6 native behavior absent: "+repr(literal[:50]))


def native_export_compatibility(original_engine:bytes,new_engine:bytes):
    with tempfile.TemporaryDirectory(prefix="native_abi_") as t:
        old=Path(t)/"old-libkodi.so"
        new=Path(t)/"new-libkodi.so"
        old.write_bytes(original_engine);new.write_bytes(new_engine)
        deps=lambda p: sorted(re.findall(r"\(NEEDED\).*?\[(.*?)\]",
            subprocess.check_output(["readelf","-d","-W",str(p)],text=True)))
        a,b=deps(old),deps(new)
        require(a==b,"Kodi native dynamic dependency list changed: "+str((a,b)))
        # ABI-visible symbol additions for guarded new methods are permitted;
        # all original exports needed by existing code must remain.
        def exports(p):
            lines=subprocess.check_output(["readelf","--dyn-syms","--wide",str(p)],text=True)
            return {words[-1].split("@")[0] for line in lines.splitlines()
                    if len(words:=line.split())>=8 and words[4:6]==["GLOBAL","DEFAULT"] and
                    words[6]!="UND"}
        prior=exports(old);after=exports(new)
        missing=prior-after
        require(not missing,"Existing native Kodi ABI exports removed: "+repr(sorted(missing)[:15]))
        return {"needed":a,"old_exports":len(prior),"new_exports":len(after),
                "previous_exports_preserved":True}


def source_and_manifest(parent:Path,native:bytes,proof:dict):
    require(sha(parent.read_bytes())==SIGNED_PARENT_SHA256,
            "User's signed original 2103390 not pinned")
    scripts,added,source_receipt=allsource.staged_sources(parent)
    with zipfile.ZipFile(parent) as archive:
        old_engine=archive.read(ENGINE)
        old_recorder=archive.read(RECORDER)
        verify_exact_native(old_engine,native,proof)
        compatibility=native_export_compatibility(old_engine,native)
        patched_recorder=nativeidentity.patch(native,old_recorder)
        manifest=load_module("infinity_g7_exact_manifest",
                        ROOT/"repairs/critical-preview-2103376/manifest_patch.py")
        manifest.PARENT_CODE=2103390;manifest.CODE=CODE
        manifest.PARENT_NAME=PARENT_NAME;manifest.NAME=NAME
        require(len(NAME)==len(PARENT_NAME),
                "Binary manifest versionName must remain exactly the same length")
        patched_manifest,edits=manifest.patch(archive.read(MANIFEST))
        require({x["field"] for x in edits}=={"versionCode","versionName"},
                "Only version identity changes in binary manifest")
    # The user's currently installed Group1 and Groups2–6 aren't inferred:
    # every target derives directly from the original signed base.
    modified={p:b for p,(_,b) in scripts.items()}
    for n,payload in ((ENGINE,native),(RECORDER,patched_recorder),
                      (MANIFEST,patched_manifest)):
        require(n not in modified,"Unexpected overlap with signed native target")
        modified[n]=payload
    require(len(modified)==128 and len(added)==2,
            "Unexpected all-in-one original + native + manifest member count")
    require(not any("cobra" in n.lower() or "shutdown" in n.lower()
                for n in set(modified)|set(added)),
            "Protected Cobra or shutdown APK path mutated")
    full_source=dict(source_receipt,
       original_original_modified=len(modified),
       group5_recorder_identity_sha=sha(native),
       parent_native_sha256=nativeidentity.BASE_PACKAGED_ENGINE_SHA,
       compiled_native_sha256=sha(native),
       group5_native_crash_fixed=False,
       group1_task19_fixed=False,
       new_version_code=CODE,new_version_name=NAME,
       proposed_member_additions=list(sorted(added)),
       native_abi=compatibility,
       native_proof_verified=True)
    return modified,added,full_source


def build(parent:Path,compiled:Path,out:Path,proof_path:Path,sign:bool):
    parent=parent.resolve();compiled=compiled.resolve();out=out.resolve()
    require(sign,"User asked for install-over APK; test/debug or unsigned package not permitted")
    require(all(os.environ.get(name) for name in
              ("INFINITY_KEYSTORE_B64","INFINITY_STORE_PASSWORD",
               "INFINITY_KEY_PASSWORD","INFINITY_KEY_ALIAS")),
            "Permanent Infinity signing secrets missing; no ephemeral debug signing")
    require(parent.is_file() and compiled.is_file() and proof_path.is_file(),
            "Exact signed parent, compiled native and source proof all required")
    proof=json.loads(proof_path.read_text())
    native=compiled.read_bytes()
    targets,added,receipt=source_and_manifest(parent,native,proof)
    out.mkdir(parents=True,exist_ok=True)
    unsigned=out/("unsigned-"+FILENAME)
    signed=out/FILENAME
    with zipfile.ZipFile(parent) as original:
        original_names=original.namelist()
        require(len(original_names)==7430 and len(set(original_names))==7430,
                "Unexpected original 2103390 member count")
        require(not set(added)&set(original_names),
                "New member unexpectedly exists already")
        require(set(targets).issubset(original_names),
                "Approved modification targets absent from signed original")
        with zipfile.ZipFile(unsigned,"w",allowZip64=True) as target:
            for info in original.infolist():
                name=info.filename
                if SIGNATURE.fullmatch(name):
                    continue
                payload=targets[name] if name in targets else original.read(info)
                target.writestr(copy.copy(info),payload)
            for name in sorted(added):
                target.writestr(name,added[name],
                                compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
        with zipfile.ZipFile(unsigned) as z:
            require(z.testzip() is None,"Unsigned APK ZIP integrity failed")
            require(set(z.namelist())==(set(original_names) -
                    {n for n in original_names if SIGNATURE.fullmatch(n)})|set(added),
                    "Unapproved removed or added member after staging")
            require(all(z.read(n)==targets[n] for n in targets),
                    "Staged member bytes drifted")
            require(all(z.read(n)==original.read(n)
                        for n in original_names
                        if n not in targets and not SIGNATURE.fullmatch(n)),
                    "Unrelated original APK bytes changed in all-in-one assembly")

    subprocess.run(["bash",str(ROOT/"scripts/sign-infinity71.sh"),
                    str(unsigned),str(signed)],check=True)
    require(signed.is_file(),"No signed experimental APK produced")
    android_bt=Path(os.environ["ANDROID_HOME"])/"build-tools/34.0.0"
    text=subprocess.check_output(
        [str(android_bt/"apksigner"),"verify","--verbose","--print-certs",str(signed)],
        text=True,stderr=subprocess.STDOUT)
    require(CERT in text.lower(),"Permanent signer identity mismatch")
    for i in (1,2,3):
        require(re.search(r"Verified using v"+str(i)+r" scheme[^\n]*:\s*true",text,re.I),
                "APK signature v"+str(i)+" failed")
    subprocess.run([str(android_bt/"zipalign"),"-c","-p","4",str(signed)],check=True)
    badge=subprocess.check_output([str(android_bt/"aapt"),"dump","badging",str(signed)],
                                  text=True,stderr=subprocess.STDOUT)
    require("package: name='com.projectinfinity.kodi' versionCode='2103391'" in badge,
            "Signed APK invalid package or version code")
    require("versionName='"+NAME+"'" in badge and "application-debuggable" not in badge,
            "Signed version name or production flags mismatch")
    with zipfile.ZipFile(signed) as final,zipfile.ZipFile(parent) as original:
        names=final.namelist()
        require(final.testzip() is None and len(set(names))==len(names),
                "Signed APK ZIP contains duplicate/corrupt members")
        before=set(original.namelist());now=set(names)
        unsigned_old={n for n in before if not SIGNATURE.fullmatch(n)}
        unsigned_new={n for n in now if not SIGNATURE.fullmatch(n)}
        require(unsigned_new-unsigned_old==set(added),
                "Unexpected extra APK resources")
        require(unsigned_old-unsigned_new==set(),
                "Original features/resources lost")
        changes=[n for n in unsigned_old if original.read(n)!=final.read(n)]
        require(set(changes)==set(targets),"Signed APK changed protected member")
        require(all(final.read(n)==targets[n] for n in targets),
                "Signed replacement member hash mismatch")
        require(all(final.read(n)==added[n] for n in added),
                "Signed new first-party modal differs")
    unsigned.unlink()
    receipt.update(
       artifact=signed.name,apk_sha256=sha(signed.read_bytes()),
       original_apk_sha256=SIGNED_PARENT_SHA256,
       original_apk_members=7430,changed_existing_apk_members=len(targets),
       new_first_party_apk_members=len(added),
       signed_permanently=True,signer_sha256=CERT,
       android_emulator_accepted=False,physical_fold_accepted=False,
       actual_SIGSEGV_139_root_cause_fixed=False,
       protected_cobra_and_shutdown_apk_members_byte_identical=True,
       user_final_LOCK=False,
       experimental_only=True,
       next_phase="ANDROID_TEST_AND_USER_FOLD_ACCEPTANCE",
       feature_freeze_after_this_apk="NO_NEW_FEATURES_BUG_FIXES_ONLY")
    (out/"INFINITY-2103391-SIGNED-EXPERIMENTAL.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--proof",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--sign",action="store_true")
    x=p.parse_args()
    receipt=build(x.parent,x.native,x.out,x.proof,x.sign)
    print(json.dumps({key:receipt[key] for key in
        ("artifact","apk_sha256","signed_permanently","changed_existing_apk_members",
         "new_first_party_apk_members","user_final_LOCK","experimental_only")},
         indent=2))
