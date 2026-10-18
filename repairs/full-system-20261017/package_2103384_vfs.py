#!/usr/bin/env python3
"""Fast, permanent-signature APK 2103384 from exact installed Infinity 2103383.

Never recompile the native engine at signing time. Reject any unverified native
output, unexpected APK change, missing permanent signing identity or failure of
the Essential-First/TEST3 preservation receipts.
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
CODE=2103384
PARENT_CODE=2103383
PACKAGE="com.projectinfinity.kodi"
PARENT_NAME="1.0.9-Close-Durability-Repair-T1"
NAME="1.0.9-Optional-VFS-SaveFix-TEST1"
ENGINE="lib/arm64-v8a/libkodi.so"
PARENT_SHA="a07700f41e434b1aaa7d192bd718417d1028bb6bff0887ba170562adb3d94377"
PARENT_ENGINE_SHA="6ba8900869787666257d6e3e5b03eb37d73689e87dc710cbb4b05285af55b069"
NATIVE_COMMIT="3795b1b03731cba567e091913299c1888805373c"
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
SIGNATURE=re.compile(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))",re.I)
REVIEWED={
 "xbmc/platform/android/activity/InfinityScriptPersistence.h":"69f722917abd3aba5e86293b083b3ae6c32acbd06325faf0ed0585eddad7e62e",
 "xbmc/platform/android/activity/InfinityProtectedWrites.h":"580a884e002bd95cbdd10a5c439b9052b7bdebebaf9473613da588c11f50cc9e",
 "xbmc/interfaces/python/InfinityPythonPersistence.h":"abf7ee47395a998bd983dc95fbe66deeb8f91d79be0ebb7db8224191098d754e",
 "xbmc/interfaces/python/InfinityPythonPersistenceSource.h":"f2ef91219be97cb9c2eacc9d0517483d03f4ab952246fd98a2d5e77211f8f53b",
}

def require(yes,why):
    if not yes: raise RuntimeError("Infinity signing refused: "+why)
def sha(data):return hashlib.sha256(data).hexdigest()
def data(path):return json.loads(Path(path).read_text())
def output(*args):return subprocess.check_output([str(x) for x in args],text=True,stderr=subprocess.STDOUT)
def verify_signed(path,bt):
    cert=output(bt/"apksigner","verify","--verbose","--print-certs",path)
    require(CERT in cert.lower(),"Permanent Infinity release signer mismatch")
    for version in (1,2,3):
        require(re.search(r"Verified using v"+str(version)+r" scheme[^\n]*:\s*true",cert,re.I),
                "APK v"+str(version)+" signature not verified")
def library_exports(path):
    return {w[-1].split("@")[0] for line in output("readelf","--dyn-syms","--wide",path).splitlines()
            if len(w:=line.split())>=8 and w[4:6]==["GLOBAL","DEFAULT"] and w[6]!="UND"}
def needed(path):
    return sorted(re.findall(r"\(NEEDED\).*?\[(.*?)\]",output("readelf","-d","-W",path)))

def package(parent,native,dest):
    require(PARENT_CODE<CODE and len(NAME)==len(PARENT_NAME),"APK version code/name invalid")
    require(parent.is_file() and sha(parent.read_bytes())==PARENT_SHA,
            "Not the exact signed user-installed 2103383 input")
    for key in ("INFINITY_KEYSTORE_B64","INFINITY_STORE_PASSWORD",
                "INFINITY_KEY_PASSWORD","INFINITY_KEY_ALIAS"):
        require(os.environ.get(key),"Permanent signing secret missing: "+key)
    delta=data(native/"INFINITY-WRITE-ERROR-SCOPE-DELTA.json")
    old=data(native/"INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json")
    watch=data(native/"WATCHED-TOUCH-SOURCE-DELTA.json")
    deadlock=data(native/"FOLD-DEADLOCK-SOURCE-DELTA.json")
    maps=data(native/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    locked=data(native/"LOCKED-TEST4-SOURCE-PRESERVATION.json")
    proof=data(native/"ENGINE-PROOF.json")
    require(set(delta["changed"])==set(REVIEWED) and delta["before"]==REVIEWED and
            all(maps["after"].get(k)==delta["after"].get(k) for k in REVIEWED),
            "Unreviewed four-file native write correction")
    for tag in ("actual_native_vfs_write_lease_required","no_class_wide_advisory_exemptions",
                "opaque_fatal_writes_remain_fatal","native_sqlite_and_essential_protection_unchanged"):
        require(delta.get(tag) is True,"Missing strict optional error invariant: "+tag)
    require(old["after"].get("xbmc/platform/android/activity/InfinityProtectedWrites.h")==
            REVIEWED["xbmc/platform/android/activity/InfinityProtectedWrites.h"] and
            watch.get("native_shutdown_and_write_admission_unchanged") is True and
            deadlock.get("shutdown_coordinator_unchanged") is True,
            "2103383/TEST3 approved correction not retained")
    checkpoint="xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
    require(locked["after"].get(checkpoint)==maps["after"].get(checkpoint) and
            maps.get("original_test4_source_untouched") is True and
            maps.get("essential_first_coordinator_unchanged") is True,
            "TEST4 locked shutdown coordinator or original source changed")
    for tag in ("complete_native_engine_compiled","fold_callback_retirement_compiled",
                "watched_presentation_bridge_compiled","browse_touch_preselection_compiled",
                "independent_close_installer_durability_compiled",
                "verified_optional_vfs_error_lease_scope_compiled",
                "opaque_vfs_and_essential_write_errors_still_block"):
        require(proof.get(tag) is True,"Native build did not prove "+tag)
    require(proof.get("shutdown_policy")=="essential_first_process_exit_v1" and
            proof.get("source_commit")==delta.get("source_provenance")==NATIVE_COMMIT,
            "Native engine source is not the exact approved 2103384 source")
    require(proof.get("locked") is False and proof.get("physical_fold_verified") is False,
            "Build claims physical acceptance before Fold testing")
    engine=native/"libkodi.so"
    require(engine.is_file() and engine.stat().st_size>100_000_000 and
            sha(engine.read_bytes())==proof["native_sha256"],
            "Reused native engine bytes do not match compiled proof")
    bt=Path(os.environ["ANDROID_HOME"])/"build-tools/34.0.0"
    ndk=Path(os.environ["ANDROID_HOME"])/"ndk/21.4.7075529"/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    verify_signed(parent,bt)
    dest.mkdir(parents=True,exist_ok=True)
    compiled=dest/"new-engine.so"
    shutil.copyfile(engine,compiled)
    output(ndk/"llvm-strip","--strip-unneeded",compiled)
    spec=importlib.util.spec_from_file_location("infinity_manifest",ROOT/"repairs/critical-preview-2103376/manifest_patch.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PARENT_CODE=PARENT_CODE
    module.CODE=CODE
    module.PARENT_NAME=PARENT_NAME
    results=[]
    with zipfile.ZipFile(parent) as src:
        require(src.testzip() is None and len(src.namelist())==len(set(src.namelist())),
                "Original Infinity APK corrupt or has duplicate files")
        require(sha(src.read(ENGINE))==PARENT_ENGINE_SHA,
                "Original native engine is not exact signed 2103383")
        original=dest/"old-engine.so"
        original.write_bytes(src.read(ENGINE))
        require(not (library_exports(original)-library_exports(compiled)) and
                needed(original)==needed(compiled),
                "Native exported symbols or dependencies changed")
        for restore in (False,True):
            filename=("Infinity-2103384-2103383-Compatibility-Return.apk" if restore
                      else "Infinity-2103384-Optional-VFS-Shutdown-TEST1.apk")
            module.NAME=PARENT_NAME if restore else NAME
            xml,edits=module.patch(src.read("AndroidManifest.xml"))
            require({x["field"] for x in edits}=={"versionCode","versionName"},
                    "Android manifest changed beyond two version fields")
            unsigned=dest/("unsigned-"+filename)
            with zipfile.ZipFile(unsigned,"w") as target:
                for info in src.infolist():
                    if SIGNATURE.fullmatch(info.filename):continue
                    payload=(xml if info.filename=="AndroidManifest.xml" else
                             compiled.read_bytes() if info.filename==ENGINE and not restore else
                             src.read(info.filename))
                    target.writestr(copy.copy(info),payload)
            final=dest/filename
            subprocess.run(["bash",str(ROOT/"scripts/sign-infinity71.sh"),str(unsigned),str(final)],check=True)
            verify_signed(final,bt)
            output(bt/"zipalign","-c","-p","4",final)
            badge=output(bt/"aapt","dump","badging",final)
            require(f"package: name='{PACKAGE}' versionCode='{CODE}'" in badge and
                    f"versionName='{module.NAME}'" in badge and "application-label:'Infinity'" in badge and
                    "application-debuggable" not in badge,
                    "APK package identity/manifest invalid")
            with zipfile.ZipFile(final) as end:
                require(end.testzip() is None and set(end.namelist())==set(src.namelist()),
                        "APK contents dropped")
                changed=sorted(n for n in src.namelist() if not SIGNATURE.fullmatch(n) and
                               src.read(n)!=end.read(n))
                require(changed==(["AndroidManifest.xml"] if restore else
                                 ["AndroidManifest.xml",ENGINE]),
                        "Unexpected APK payload changes: "+repr(changed))
                results.append(dict(name=filename,sha256=sha(final.read_bytes()),
                                    bytes=final.stat().st_size,
                                    versionCode=CODE,
                                    changed_unsigned_payload=changed,
                                    native_sha256=sha(end.read(ENGINE)),
                                    signed_by_original_infinity_certificate=True,
                                    restore_previous_engine=restore))
            unsigned.unlink()
    original.unlink()
    compiled.unlink()
    receipt=dict(status="EXPERIMENTAL, REQUIRES PHYSICAL FOLD ACCEPTANCE",
                 actual_app_package=PACKAGE,prior_signed_2103383_sha256=PARENT_SHA,
                 reused_native_run=39088360171,
                 native_source_commit=NATIVE_COMMIT,
                 signing_workflow_commit=os.environ.get("GITHUB_SHA"),
                 verified_essential_first_shutdown_preserved=True,
                 no_other_apk_components_modified=True,
                 user_data_changed=False,
                 physical_fold_verified=False,
                 final_lock_authorized=False,
                 artifacts=results)
    (dest/"INFINITY-2103384-SIGNED-EXPERIMENTAL.json").write_text(json.dumps(receipt,indent=2)+"\n")
    (dest/"SHA256SUMS").write_text("".join(f"{row['sha256']}  {row['name']}\n" for row in results))
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arg in ("parent","native","out"):p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    package(a.parent,a.native,a.out)
