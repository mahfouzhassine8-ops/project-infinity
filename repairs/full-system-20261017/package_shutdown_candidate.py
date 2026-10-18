#!/usr/bin/env python3
"""Signed update OVER the existing Infinity TEST3, not a new Android app.

Package only a fully rebuilt, preservation-proved ARM64 native engine plus
version metadata. Preserve the whole 2103382 TEST3 application and ship a
same-code compatibility rollback without wiping user data.
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

ROOT = Path(__file__).resolve().parents[2]
ENGINE = "lib/arm64-v8a/libkodi.so"
PACKAGE = "com.projectinfinity.kodi"
PARENT_SHA = "6e28bfea7cdb5e497ee21601a714e738db7a57edc3c5c0d29a9c19d461031854"
PARENT_ENGINE_SHA = "9c2259ac06dde7a6b6788e9971dc1c9a6f67ad316ce16d379dc9d7b3861d7f3d"
SIGNER_SHA = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
SOURCE_BASE = "093323fbc0ae87cbe2fa2a21abab0c357fdaf754"
PARENT_CODE = 2103382
CODE = 2103383
PARENT_NAME = "1.0.9-Watched-Touch-Bridge-TEST3"
NAME = "1.0.9-Close-Durability-Repair-T1"
SIGNATURE = re.compile(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))", re.I)


def require(ok, why):
    if not ok:
        raise RuntimeError("Infinity signed candidate blocked: " + why)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True, stderr=subprocess.STDOUT)


def exports(path):
    result = set()
    for line in run("readelf", "--dyn-syms", "--wide", path).splitlines():
        words = line.split()
        if len(words) >= 8 and words[4:6] == ["GLOBAL", "DEFAULT"] and words[6] != "UND":
            result.add(words[-1].split("@")[0])
    return result


def needed(path):
    return sorted(re.findall(r"\(NEEDED\).*?\[(.*?)\]", run("readelf", "-d", "-W", path)))


def verify_signature(apk, tools):
    output = run(tools / "apksigner", "verify", "--verbose", "--print-certs", apk)
    require(SIGNER_SHA in output.lower(), "wrong permanent Infinity certificate")
    for v in (1, 2, 3):
        require(re.search(r"Verified using v" + str(v) + r" scheme[^\n]*:\s*true",
                          output, re.I), "APK signature scheme v" + str(v) + " invalid")


def package(parent, native, destination):
    require(PARENT_CODE < CODE, "No in-place higher code")
    require(len(PARENT_NAME) == len(NAME), "Manifest version string length changed")
    require(parent.is_file() and sha(parent.read_bytes()) == PARENT_SHA,
            "Wrong 2103382 TEST3 signed APK")
    require(native.is_dir(), "Full native engine proof absent")
    for key in ("INFINITY_KEYSTORE_B64", "INFINITY_STORE_PASSWORD",
                "INFINITY_KEY_PASSWORD", "INFINITY_KEY_ALIAS"):
        require(os.environ.get(key), "Permanent signing secret missing: " + key)
    delta = read(native / "INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json")
    watched = read(native / "WATCHED-TOUCH-SOURCE-DELTA.json")
    prior = read(native / "FOLD-DEADLOCK-SOURCE-DELTA.json")
    source = read(native / "FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    proof = read(native / "ENGINE-PROOF.json")
    require(delta["changed"] == ["xbmc/platform/android/activity/InfinityProtectedWrites.h"],
            "Native patch is not one strictly scoped file")
    name = delta["changed"][0]
    require(delta["before"][name] == "a0a50a78e24fc5da8c9af65bc894ee47af4e61139af9d89cf014207d177e92f1" and
            source["after"][name] == delta["after"][name],
            "Untested or mismatched protected write correction")
    require(delta.get("strict_protected_file_durability_not_weakened") is True and
            delta.get("original_locked_test4_unmodified") is True,
            "Durability / original lock contract invalid")
    require(watched.get("all_other_native_sources_byte_identical") is True and
            watched.get("native_shutdown_and_write_admission_unchanged") is True and
            prior.get("shutdown_coordinator_unchanged") is True,
            "Previous native corrections/source not preserved")
    require(proof.get("complete_native_engine_compiled") is True and
            proof.get("watched_presentation_bridge_compiled") is True and
            proof.get("browse_touch_preselection_compiled") is True and
            proof.get("fold_callback_retirement_compiled") is True and
            proof.get("independent_close_installer_durability_compiled") is True and
            proof.get("shutdown_policy") == "essential_first_process_exit_v1",
            "Native engine lacks preserved features or corrected durability header")
    require(proof.get("native_sha256") == sha((native / "libkodi.so").read_bytes()),
            "Compiled native proof SHA mismatch")
    require(proof.get("physical_device_verified") is False and
            proof.get("locked") is False,
            "Experimental native proof falsely promoted")
    require(proof.get("source_commit") == delta.get("source_provenance") ==
            os.environ.get("GITHUB_SHA"), "Native build is from a different commit")
    destination.mkdir(parents=True, exist_ok=True)
    bt = Path(os.environ["ANDROID_HOME"]) / "build-tools/34.0.0"
    ndk = Path(os.environ["ANDROID_HOME"]) / "ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin"
    verify_signature(parent, bt)
    new_native = destination / "candidate-engine.so"
    shutil.copyfile(native / "libkodi.so", new_native)
    run(ndk / "llvm-strip", "--strip-unneeded", new_native)
    with zipfile.ZipFile(parent) as base:
        require(base.testzip() is None and len(set(base.namelist())) == len(base.namelist()),
                "Original TEST3 APK corrupt or has duplicate names")
        require(sha(base.read(ENGINE)) == PARENT_ENGINE_SHA, "Unexpected TEST3 ARM64 engine payload")
        old_native = destination / "parent-engine.so"
        old_native.write_bytes(base.read(ENGINE))
        require(not (exports(old_native) - exports(new_native)), "Previously exported ABI symbol removed")
        require(needed(old_native) == needed(new_native), "Native dependency set changed")
        manifest_path = ROOT / "repairs/critical-preview-2103376/manifest_patch.py"
        spec = importlib.util.spec_from_file_location("infinity_manifest_patch", manifest_path)
        manifest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manifest)
        manifest.PARENT_CODE = PARENT_CODE
        manifest.CODE = CODE
        manifest.PARENT_NAME = PARENT_NAME
        produced = []
        for rollback in (False, True):
            filename = ("Infinity-2103383-TEST3-Compatibility-Return.apk" if rollback else
                        "Infinity-2103383-Close-Durability-TEST1.apk")
            unsigned = destination / ("unsigned-" + filename)
            manifest.NAME = PARENT_NAME if rollback else NAME
            patched, edits = manifest.patch(base.read("AndroidManifest.xml"))
            require({x["field"] for x in edits} == {"versionCode", "versionName"},
                    "Android manifest changed beyond two version fields")
            with zipfile.ZipFile(unsigned, "w") as out:
                for info in base.infolist():
                    if SIGNATURE.fullmatch(info.filename):
                        continue
                    payload = base.read(info.filename)
                    if info.filename == "AndroidManifest.xml":
                        payload = patched
                    elif info.filename == ENGINE and not rollback:
                        payload = new_native.read_bytes()
                    out.writestr(copy.copy(info), payload)
            finished = destination / filename
            subprocess.run(["bash", str(ROOT / "scripts/sign-infinity71.sh"),
                            str(unsigned), str(finished)], check=True)
            verify_signature(finished, bt)
            run(bt / "zipalign", "-c", "-p", "4", finished)
            badges = run(bt / "aapt", "dump", "badging", finished)
            require(f"package: name='{PACKAGE}' versionCode='{CODE}'" in badges and
                    f"versionName='{manifest.NAME}'" in badges and
                    "application-label:'Infinity'" in badges and
                    "application-debuggable" not in badges, "APK package/brand mismatch")
            with zipfile.ZipFile(finished) as zipped:
                require(zipped.testzip() is None and set(zipped.namelist()) == set(base.namelist()),
                        "APK preservation violated")
                changed = sorted(name for name in base.namelist()
                                 if not SIGNATURE.fullmatch(name) and
                                 zipped.read(name) != base.read(name))
                require(changed == (["AndroidManifest.xml"] if rollback else
                                    ["AndroidManifest.xml", ENGINE]),
                        "Unapproved APK payload entries changed: " + repr(changed))
                produced.append({
                    "filename": filename, "sha256": sha(finished.read_bytes()),
                    "bytes": finished.stat().st_size,
                    "native_packaged_sha256": sha(zipped.read(ENGINE)),
                    "previous_TEST3_engine_restored": rollback,
                    "changed_unsigned_payload": changed,
                    "permanent_signer_sha256": SIGNER_SHA,
                    "version_code": CODE, "physical_fold_verified": False,
                })
            unsigned.unlink()
    old_native.unlink()
    new_native.unlink()
    receipt = {
        "scope": "Experimental in-place Infinity 2103383 from signed TEST3 2103382",
        "parent_signed_test3_sha256": PARENT_SHA, "parent_native_sha256": PARENT_ENGINE_SHA,
        "native_commit": os.environ.get("GITHUB_SHA"),
        "no_other_app_or_package_created": True, "user_data_untouched": True,
        "skin_rails_commandcenter_preserved": True,
        "all_test3_native_features_retained": True,
        "strict_essential_durability_checks_preserved": True,
        "runtime_android_close_verified": False,
        "physical_fold_verified": False, "final_lock_authorized": False,
        "artifacts": produced,
    }
    (destination / "INFINITY-2103383-SIGNED-EXPERIMENTAL.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    (destination / "SHA256SUMS").write_text(
        "".join(f"{item['sha256']}  {item['filename']}\n" for item in produced))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--native", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    package(a.parent, a.native, a.out)
