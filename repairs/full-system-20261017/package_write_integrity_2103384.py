#!/usr/bin/env python3
"""Fast, permanent signing from one already-built full Infinity native engine.

Never installs stock Kodi, swaps certificates, rebuilds native code, modifies
user data, or silently promotes a candidate to a Fold-accepted release.
"""
import argparse
import copy
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
PACKAGE="com.projectinfinity.kodi"
PARENT_CODE=2103383
CODE=2103384
PARENT_NAME="1.0.9-Close-Durability-Repair-T1"
NAME="1.0.9-Write-Integrity-Repair-RC1"
PARENT_SHA256="a07700f41e434b1aaa7d192bd718417d1028bb6bff0887ba170562adb3d94377"
PARENT_ENGINE_SHA256="6ba8900869787666257d6e3e5b03eb37d73689e87dc710cbb4b05285af55b069"
PERMANENT_SIGNER="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
NATIVE_SOURCE_REF="__PINNED_NATIVE_SOURCE_COMMIT__"
SIGNATURE=re.compile(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))",re.I)
SCOPE_NAMES=(
  "xbmc/interfaces/python/InfinityPythonPersistenceSource.h",
  "xbmc/interfaces/python/InfinityPythonPersistence.h",
  "xbmc/platform/android/activity/InfinityScriptPersistence.h",
  "xbmc/platform/android/activity/InfinityProtectedWrites.h",
)

def require(ok,message):
    if not ok:
        raise RuntimeError("Infinity Write-Integrity signed APK blocked: "+message)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def read(path):
    return json.loads(Path(path).read_text())
def run(*args):
    return subprocess.check_output(list(map(str,args)),text=True,stderr=subprocess.STDOUT)
def sig(apk,bt):
    text=run(bt/"apksigner","verify","--verbose","--print-certs",apk)
    require(PERMANENT_SIGNER in text.lower(),"wrong permanent Infinity signer")
    for v in (1,2,3):
        require(re.search(r"Verified using v"+str(v)+r" scheme[^\n]*:\s*true",text,re.I),
                "required APK signature scheme v"+str(v)+" not verified")
def exports(path):
    return {line.split()[-1].split("@")[0]
            for line in run("readelf","--dyn-syms","--wide",path).splitlines()
            if len(line.split())>=8 and line.split()[4:6]==["GLOBAL","DEFAULT"] and
            line.split()[6]!="UND"}
def needed(path):
    return sorted(re.findall(r"\(NEEDED\).*?\[(.*?)\]",run("readelf","-d","-W",path)))

def package(parent,native,out):
    require(NATIVE_SOURCE_REF != "__PINNED_NATIVE_SOURCE_COMMIT__",
            "Native source pin not set: do NOT sign an unverified engine")
    require(CODE>PARENT_CODE and len(NAME)==len(PARENT_NAME),
            "Android in-place update manifest identity/length mismatch")
    require(parent.is_file() and sha(parent.read_bytes())==PARENT_SHA256,
            "not the exact previously signed Infinity 2103383")
    for name in ("INFINITY_KEYSTORE_B64","INFINITY_STORE_PASSWORD",
                 "INFINITY_KEY_PASSWORD","INFINITY_KEY_ALIAS"):
        require(bool(os.environ.get(name)),"missing permanent signing secret "+name)
    scope=read(native/"INFINITY-WRITE-ERROR-SCOPE-DELTA.json")
    proof=read(native/"ENGINE-PROOF.json")
    preservation=read(native/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    original_stage=read(native/"INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json")
    watched=read(native/"WATCHED-TOUCH-SOURCE-DELTA.json")
    require(scope.get("source_provenance")==proof.get("source_commit") ==
            proof.get("write_error_scope_source_commit")==NATIVE_SOURCE_REF,
            "not the exact reviewed native source")
    require(set(scope.get("changed",[]))==set(SCOPE_NAMES) and
            len(scope["before"])==len(SCOPE_NAMES)==len(scope["after"]),
            "unexpected native source changes")
    require(scope.get("no_class_wide_advisory_exemptions") is True and
            scope.get("actual_native_vfs_write_lease_required") is True and
            scope.get("opaque_fatal_writes_remain_fatal") is True and
            scope.get("coordinator_unchanged") is True,
            "unverified optional failure classifier")
    for path in SCOPE_NAMES:
        require(scope["after"][path]==preservation["after"][path] and
                scope["after"][path]!=scope["before"][path],
                "signed source/overlay manifest mismatch "+path)
    require(original_stage.get("strict_protected_file_durability_not_weakened") is True and
            watched.get("native_shutdown_and_write_admission_unchanged") is True and
            proof.get("verified_optional_vfs_error_lease_scope_compiled") is True and
            proof.get("independent_close_installer_durability_compiled") is True and
            proof.get("fold_callback_retirement_compiled") is True and
            proof.get("watched_presentation_bridge_compiled") is True and
            proof.get("browse_touch_preselection_compiled") is True and
            proof.get("shutdown_policy")=="essential_first_process_exit_v1",
            "existing TEST3/2103383 or essential-save protections lost")
    require(proof.get("physical_fold_verified") is False and
            proof.get("locked") is False,
            "experimental native build incorrectly promoted")
    lib=native/"libkodi.so"
    require(proof.get("complete_native_engine_compiled") is True and
            lib.is_file() and sha(lib.read_bytes())==proof["native_sha256"],
            "missing full verified native engine bytes")
    out.mkdir(parents=True,exist_ok=True)
    sdk=Path(os.environ["ANDROID_HOME"])
    bt=sdk/"build-tools/34.0.0"
    ndk=sdk/"ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin"
    sig(parent,bt)
    newlib=out/"candidate-native.so"
    shutil.copyfile(lib,newlib)
    run(ndk/"llvm-strip","--strip-unneeded",newlib)
    manifest_path=ROOT/"repairs/critical-preview-2103376/manifest_patch.py"
    spec=importlib.util.spec_from_file_location("infinity_manifest",manifest_path)
    manifest=importlib.util.module_from_spec(spec);spec.loader.exec_module(manifest)
    manifest.PARENT_CODE=PARENT_CODE
    manifest.CODE=CODE
    manifest.PARENT_NAME=PARENT_NAME
    artifacts=[]
    with zipfile.ZipFile(parent) as original:
        require(original.testzip() is None and len(original.namelist())==len(set(original.namelist())),
                "original signed Infinity archive invalid")
        old_payload=original.read(ENGINE)
        require(sha(old_payload)==PARENT_ENGINE_SHA256,
                "parent 2103383 ARM64 native engine differs from lock")
        oldlib=out/"prior-native.so"
        oldlib.write_bytes(old_payload)
        require(not (exports(oldlib)-exports(newlib)),
                "previous native ABI export removed")
        require(needed(oldlib)==needed(newlib),
                "native library dependency set unexpectedly changed")
        for previous in (False,True):
            filename=("Infinity-2103384-2103383-Compatibility-Return.apk" if previous
                      else "Infinity-2103384-Write-Integrity-TEST1.apk")
            unsigned=out/("unsigned-"+filename)
            manifest.NAME=PARENT_NAME if previous else NAME
            data,edits=manifest.patch(original.read("AndroidManifest.xml"))
            require({entry["field"] for entry in edits}=={"versionCode","versionName"},
                    "changed Android manifest outside two version attributes")
            with zipfile.ZipFile(unsigned,"w") as dest:
                for info in original.infolist():
                    if SIGNATURE.fullmatch(info.filename):continue
                    value=original.read(info.filename)
                    if info.filename=="AndroidManifest.xml":value=data
                    elif info.filename==ENGINE and not previous:value=newlib.read_bytes()
                    dest.writestr(copy.copy(info),value)
            apk=out/filename
            subprocess.run(["bash",str(ROOT/"scripts/sign-infinity71.sh"),
                            str(unsigned),str(apk)],check=True)
            sig(apk,bt)
            run(bt/"zipalign","-c","-p","4",apk)
            badging=run(bt/"aapt","dump","badging",apk)
            require(f"package: name='{PACKAGE}' versionCode='{CODE}'" in badging and
                    f"versionName='{manifest.NAME}'" in badging and
                    "application-label:'Infinity'" in badging and
                    "application-debuggable" not in badging,"APK was not the same Infinity app")
            with zipfile.ZipFile(apk) as final:
                require(final.testzip() is None and
                        set(final.namelist())==set(original.namelist()),
                        "signed candidate dropped or added APK contents")
                changed=sorted(p for p in original.namelist()
                               if not SIGNATURE.fullmatch(p) and
                               original.read(p)!=final.read(p))
                expected=(["AndroidManifest.xml"] if previous else
                          ["AndroidManifest.xml",ENGINE])
                require(changed==expected,"changed unrelated APK payload: "+str(changed))
                artifacts.append(dict(filename=filename,sha256=sha(apk.read_bytes()),
                                      bytes=apk.stat().st_size,
                                      native_sha256=sha(final.read(ENGINE)),
                                      restored_original_native=previous,
                                      version_code=CODE,
                                      signer_sha256=PERMANENT_SIGNER,
                                      changed_unsigned_payload=changed))
            unsigned.unlink()
    oldlib.unlink();newlib.unlink()
    receipt=dict(schema=1,status="EXPERIMENTAL; PHYSICAL FOLD VALIDATION REQUIRED",
                 package_id=PACKAGE,native_source=NATIVE_SOURCE_REF,
                 signing_source=os.environ.get("GITHUB_SHA","unknown"),
                 parent_signed_apk_sha256=PARENT_SHA256,
                 accepted_test4_untouched=True,
                 exact_2103383_features_preserved=True,
                 no_new_app_or_uninstall=True,
                 user_data_untouched=True,
                 native_and_signing_provenance_verified=True,
                 physical_shutdown_verified=False,
                 startup_25_second_close_resolved=False,
                 final_lock_authorized=False,artifacts=artifacts)
    (out/"INFINITY-2103384-SIGNING-RECEIPT.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        f"{a['sha256']}  {a['filename']}\n" for a in artifacts))
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("parent","native","out"):p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args();package(a.parent,a.native,a.out)
