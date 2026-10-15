#!/usr/bin/env python3
"""Package isolated native-only RC1 over the exact user-locked Rails Hold RC02 APK.
No skin, helper, provider, Java, asset, or user-data changes are authorized.
The identical versionCode 2103377 permits reinstalling the original signed
Rails Hold RC02 APK as a normal in-place rollback, without uninstalling.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
ENGINE="lib/arm64-v8a/libkodi.so"
PARENT_SHA="17e2458552b7dbb8f14dad307015eafc2497a5ec6ddc4f7bb1707d975f37b906"
SIGNER="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
PARENT_NAME="1.0.9-Rails-Hold-Correction-RC02"
CANDIDATE_NAME="1.0.9-Python-Exit-Correction-RC1"
assert len(PARENT_NAME)==len(CANDIDATE_NAME)==32
SIGNATURE=re.compile(r"^META-INF/(?:MANIFEST.MF|[^/]+\.(?:SF|RSA|DSA|EC))$",re.I)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def run(*args):
    return subprocess.check_output([str(x) for x in args],text=True,stderr=subprocess.STDOUT)

def load(path):
    return json.loads(Path(path).read_text())

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def symbols(file):
    result=set()
    for line in run("readelf","--dyn-syms","--wide",file).splitlines():
        parts=line.split()
        if len(parts)>=8 and parts[4:6]==["GLOBAL","DEFAULT"] and parts[6]!="UND":
            result.add(parts[-1].split("@")[0])
    return result

def needed(file):
    return sorted(re.findall(r"\(NEEDED\).*?\[(.*?)\]",run("readelf","-d","-W",file)))

def package(args):
    assert sha(args.parent.read_bytes())==PARENT_SHA, "Refusing anything but locked Rails Hold RC02 APK"
    assert args.native.is_dir(), "Native evidence directory missing"
    n=args.native/"checkpoint-build"
    if not n.exists():
        n=args.native
    proof=load(n/"ENGINE-PROOF.json")
    delta=load(n/"THREAD-SHUTDOWN-ORDER-DELTA.json")
    source=load(n/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    tests=load(n/"THREAD-SHUTDOWN-ORDER-HOST-CHECKS.json")
    assert proof.get("complete_native_engine_compiled") and proof.get("python_thread_shutdown_order_rc1_compiled")
    assert proof.get("rc5_17_required_save_owners_unchanged")
    assert proof.get("physical_device_verified") is False and not proof.get("locked")
    assert source["all_17_required_checkpoint_owners_byte_identical"]
    assert source["final_required_save_and_database_seal_stages_byte_identical"]
    assert source["final_termination_authorization_byte_identical"]
    assert source["python_311_thread_shutdown_order_correction"]
    assert set(delta["changed"]) == {
        "xbmc/interfaces/python/PythonInvoker.cpp",
        "xbmc/interfaces/python/PythonInvoker.h",
    }
    assert tests["status"]=="source_contracts_passed" and all(tests["checks"].values())
    assert proof["python_shutdown_order_source_commit"]==args.native_source_commit
    assert sha((n/"libkodi.so").read_bytes())==proof["native_sha256"]
    args.out.mkdir(parents=True,exist_ok=True)
    ndk=Path(os.environ["ANDROID_HOME"])/"ndk"/os.environ["NDK_VER"]/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    bt=Path(os.environ["ANDROID_HOME"])/"build-tools/34.0.0"
    mod=module(ROOT/"repairs/critical-preview-2103376/manifest_patch.py","exact_binary_manifest")
    mod.PARENT_CODE=mod.CODE=2103377
    mod.PARENT_NAME=PARENT_NAME
    mod.NAME=CANDIDATE_NAME
    out_engine=args.out/"libkodi.so"
    shutil.copyfile(n/"libkodi.so",out_engine)
    run(ndk/"llvm-strip","--strip-unneeded",out_engine)
    pre=args.out/"unsigned-native-only.apk"
    parent_engine=args.out/"locked-rails-parent-engine.so"
    with zipfile.ZipFile(args.parent) as old,zipfile.ZipFile(pre,"w") as new:
        assert len(old.namelist())==len(set(old.namelist()))
        parent_engine.write_bytes(old.read(ENGINE))
        for info in old.infolist():
            if SIGNATURE.match(info.filename):
                continue
            item=old.read(info.filename)
            if info.filename==ENGINE:
                item=out_engine.read_bytes()
            elif info.filename=="AndroidManifest.xml":
                item,edits=mod.patch(item)
                assert {e["field"] for e in edits}=={"versionCode","versionName"}
            new.writestr(info,item)
    assert not symbols(parent_engine)-symbols(out_engine),"Removed required exported native ABI"
    assert needed(parent_engine)==needed(out_engine),"Changed required native dependencies"
    signed=args.out/"Infinity-2103377-Python-Retirement-RC1-Signed-Test.apk"
    subprocess.run(["bash",str(ROOT/"scripts/sign-infinity71.sh"),str(pre),str(signed)],check=True)
    cert=run(bt/"apksigner","verify","--verbose","--print-certs",signed)
    assert SIGNER in cert.lower(),"Signing certificate mismatch"
    for v in (2,3):
        assert re.search(r"Verified using v"+str(v)+r" scheme[^\n]+true",cert),"Signature scheme missing"
    run(bt/"zipalign","-c","-p","4",signed)
    badging=run(bt/"aapt","dump","badging",signed)
    assert "package: name='com.projectinfinity.kodi'" in badging
    assert "versionCode='2103377'" in badging and CANDIDATE_NAME in badging
    with zipfile.ZipFile(args.parent) as old,zipfile.ZipFile(signed) as new:
        a={p for p in old.namelist() if not SIGNATURE.match(p)}
        b={p for p in new.namelist() if not SIGNATURE.match(p)}
        assert a==b
        changed=sorted(p for p in a if old.read(p)!=new.read(p))
        assert changed==["AndroidManifest.xml",ENGINE],changed
        assert new.read(ENGINE)==out_engine.read_bytes()
        assert new.read("AndroidManifest.xml")==mod.patch(old.read("AndroidManifest.xml"))[0]
    result={
        "source_commit":os.environ.get("GITHUB_SHA","unknown"),
        "native_source_commit":args.native_source_commit,
        "parent_apk_sha256":PARENT_SHA,
        "signed_candidate":signed.name,
        "signed_candidate_sha256":sha(signed.read_bytes()),
        "permanent_signer_sha256":SIGNER,
        "package_id":"com.projectinfinity.kodi",
        "version_code":2103377,
        "version_name":CANDIDATE_NAME,
        "changed_apk_entries":changed,
        "android_assets_unchanged":True,
        "skin_1_0_5_223_unchanged":True,
        "rails_helper_0_2_5_unchanged":True,
        "existing_native_exports_and_dependencies_preserved":True,
        "checkpoint_17_owners_unchanged":True,
        "source_contracts_passed":len(tests["checks"]),
        "physical_fold_tested":False,
        "lock_authorized":False,
        "rollback":"Reinstall original signed Rails Hold RC02 APK with same versionCode 2103377; never clear data or uninstall",
    }
    (args.out/"SHUTDOWN-RC1-APK-PRESERVATION.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (args.out/"CERT-VERIFICATION.txt").write_text(cert)
    (args.out/"SHA256SUMS").write_text(result["signed_candidate_sha256"]+"  "+signed.name+"\n")
    for f in (pre,out_engine,parent_engine):
        f.unlink()
    print("PASS: signer verified, exact Rails Hold RC02 parent preserved; only native engine & binary manifest changed.")
    print("PHYSICAL DEVICE CLOSE STILL UNVERIFIED — THIS IS TEST ONLY.")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for name in ("parent","native","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--native-source-commit",required=True)
    package(parser.parse_args())
