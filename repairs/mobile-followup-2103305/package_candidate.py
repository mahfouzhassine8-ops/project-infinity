#!/usr/bin/env python3
"""Package only the evidenced route-installer correction over locked APK 304.

Reuse all native/asset/resource bytes and the permanent signer. This does not
claim the shutdown hang, the skin defects, or physical acceptance are resolved.
"""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INHERITED = HERE.parent / "mobile-regressions-2103304"
sys.path.insert(0, str(INHERITED))
from packaging_checks import (DEX, SIGNATURE, dex_contract, require, resource_ids,
                              run, sha, verify_manifest_pair)

spec = importlib.util.spec_from_file_location("package304", INHERITED / "package_candidate.py")
package304 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package304)

BASE_APK_SHA = "81884f5591d0912b031c6cc8dd6e8c6e198a84ddd95d03a878624fbb1e0425fa"
BASE_COMMIT = "dc102b4b13b2931a1eec9d9476a2038d1a4d5d2d"
BASE_NATIVE_SHA = "b6724bc5cff3f3e79c5035f82e77be331535a9e3a7bf33e7650b7ab1e95c0626"
BASE_SOURCE_COMMIT = "70309e66ab33d3f12df93b7a46ddb153f1f02f97"
CERT = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
TARGET = "tools/android/packaging/xbmc/src/InfinityPowerMenuRoutes.java.in"
ROUTE_SHA = "30091cc727a2fb4a477d286c7d7987af3e5cd683b53af3effe38401871661e6d"
VERSION_CODE = 2103305
RELEASE = "1.0.9-Power-Route-RC1"
PACKAGE = "com.projectinfinity.kodi"
APK_NAME = "Infinity-2103305-1.0.9-Power-Route-RC1.apk"


def manifest(source):
    return {p.relative_to(source).as_posix(): sha(p.read_bytes())
            for p in source.rglob("*") if p.is_file()}


def verify_source(source, proof, receipt, baseline_proof, source_commit):
    actual = manifest(source)
    require(baseline_proof["source_commit"] == BASE_SOURCE_COMMIT, "Wrong locked APK source proof")
    require(len(baseline_proof["files"]) == len(actual) == 250, "Wrong complete source count")
    require(receipt["parent_source_commit"] == BASE_SOURCE_COMMIT, "Wrong source parent")
    require(receipt["before"] == baseline_proof["files"], "Source parent differs from locked APK")
    require(actual == receipt["after"] == proof["files"], "Successful source manifest differs")
    require(proof["source_commit"] == source_commit, "Source evidence is not from this build commit")
    require(proof["weather_isolation_audit_passed"] is True, "Compiled weather isolation gate missing")
    changed = sorted(n for n in actual if actual[n] != receipt["before"][n])
    require(changed == receipt["changed"] == [TARGET], "Delta exceeds one route installer")
    require(actual[TARGET] == ROUTE_SHA, "Not the audited route correction")
    for key in ("native_changed", "skin_changed", "weather_changed", "shutdown_policy_changed"):
        require(receipt[key] is False, "Unexpected policy/payload change: " + key)
    return len(actual)


def merge(base, donor, output):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(donor) as b, zipfile.ZipFile(output, "w") as z:
        require(len(a.namelist()) == len(set(a.namelist())), "Duplicate baseline members")
        require(len(b.namelist()) == len(set(b.namelist())), "Duplicate Android donor members")
        require(a.testzip() is None and b.testzip() is None, "APK CRC failure")
        require(sha(a.read("lib/arm64-v8a/libkodi.so")) == BASE_NATIVE_SHA, "Wrong locked native engine")
        require(not any(n.startswith(("lib/", "assets/")) and not n.endswith("/")
                        for n in b.namelist()), "Native/assets appeared in Android-only donor")
        old_native, old_classes = dex_contract(a)
        new_native, new_classes = dex_contract(b)
        require(old_native == new_native, "JNI declarations changed despite native reuse")
        old_core = {n for n in old_classes if n.startswith("Lcom/projectinfinity/kodi/") and "$" not in n}
        require(old_core <= new_classes, "Existing core Java class lost")
        for info in a.infolist():
            if info.filename != "AndroidManifest.xml" and not DEX.fullmatch(info.filename) and not SIGNATURE.fullmatch(info.filename):
                z.writestr(copy.copy(info), a.read(info.filename))
        for info in b.infolist():
            if info.filename == "AndroidManifest.xml" or DEX.fullmatch(info.filename):
                z.writestr(copy.copy(info), b.read(info.filename))
    return len(old_native), len(old_core)


def verify_bytes(base, final):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
        kept = {n for n in a.namelist() if n != "AndroidManifest.xml"
                and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected = kept | {"AndroidManifest.xml"} | {n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(set(b.namelist()) == expected and len(b.namelist()) == len(expected), "Unexpected final payload")
        for name in kept:
            require(a.read(name) == b.read(name), "Protected locked APK entry changed: " + name)
        require(dex_contract(a)[0] == dex_contract(b)[0], "Final JNI contract differs")
        require(b.testzip() is None, "Final APK CRC failure")
        return {"native_files_byte_identical": sum(n.startswith("lib/") and not n.endswith("/") for n in kept),
                "asset_files_byte_identical": sum(n.startswith("assets/") and not n.endswith("/") for n in kept),
                "android_resources_byte_identical": True, "protected_entries": len(kept)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "source-proof", "source-receipt", "baseline-dir", "build-dir", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    source, baseline, build, out = [q.resolve() for q in (a.source, a.baseline_dir, a.build_dir, a.out)]
    base = baseline / "Infinity-2103304-1.0.9-Responsive-Repair-RC1.apk"
    require(sha(base.read_bytes()) == BASE_APK_SHA, "Not the exact locked APK 2103304")
    old_proof = json.loads((baseline / "ANDROID-SOURCE-PROOF.json").read_text())
    proof = json.loads(a.source_proof.read_text())
    receipt = json.loads(a.source_receipt.read_text())
    source_count = verify_source(source, proof, receipt, old_proof, os.environ["GITHUB_SHA"])
    out.mkdir(parents=True, exist_ok=True)
    # Retain the verified 304 Android build factory. Only its output identity and
    # exact APK parent change; no native preparation or 304 native merge is called.
    package304.BASE_APK_SHA256 = BASE_APK_SHA
    package304.VERSION_CODE = VERSION_CODE
    package304.RELEASE = RELEASE
    ids = package304.prepare(source, base, build, out)
    env = dict(os.environ, KODI_ANDROID_KEY_ALIAS="androiddebugkey", KODI_ANDROID_KEY_PASSWORD="android",
               KODI_ANDROID_STORE_PASSWORD="android", KODI_ANDROID_STORE_FILE=str(Path.home() / ".android/debug.keystore"))
    run("./gradlew", "--no-daemon", "--console=plain", ":xbmc:assembleRelease", cwd=build, env=env)
    run("./gradlew", "--no-daemon", "--console=plain", ":xbmc:dependencies", "--configuration",
        "releaseRuntimeClasspath", cwd=build, env=env, output=out / "android-dependencies.txt")
    donor = build / "xbmc/build/outputs/apk/release/xbmc-release.apk"
    bt = Path(os.environ["ANDROID_HOME"]) / "build-tools/34.0.0"
    require(ids == resource_ids(bt / "aapt2", donor, out / "compiled-resources.txt"), "Android resource IDs drifted")
    unsigned = out / "Infinity-2103305-unsigned.apk"
    natives, core = merge(base, donor, unsigned)
    compiled_manifest = run(bt / "aapt", "dump", "xmltree", unsigned, "AndroidManifest.xml", output=out / "manifest.txt")
    base_manifest = run(bt / "aapt", "dump", "xmltree", base, "AndroidManifest.xml", output=out / "base-manifest.txt")
    verify_manifest_pair(base_manifest, compiled_manifest)
    for name in ("INFINITY_KEYSTORE_B64", "INFINITY_STORE_PASSWORD", "INFINITY_KEY_PASSWORD", "INFINITY_KEY_ALIAS"):
        require(bool(os.environ.get(name)), "Missing permanent signing configuration: " + name)
    final = out / APK_NAME
    run("bash", ROOT / "scripts/sign-infinity71.sh", unsigned, final)
    cert = run(bt / "apksigner", "verify", "--verbose", "--print-certs", final, output=out / "signing-verification.txt")
    require(CERT in cert.lower(), "Permanent signer differs from locked APK")
    badging = run(bt / "aapt", "dump", "badging", final, output=out / "badging.txt")
    require(f"package: name='{PACKAGE}' versionCode='{VERSION_CODE}' versionName='{RELEASE}'" in badging, "Wrong candidate identity")
    require("sdkVersion:'21'" in badging and "targetSdkVersion:'35'" in badging, "Android API contract changed")
    require("application-label:'Infinity'" in badging and "application-debuggable" not in badging, "Branding/debuggability drift")
    require(len(re.findall(r"^launchable-activity:", badging, re.M)) == 1, "Launcher count changed")
    preserved = verify_bytes(base, final)
    report = {"schema": 1, "source_commit": os.environ["GITHUB_SHA"], "base_source_commit": BASE_COMMIT,
              "base_run": 37194819014, "base_apk_sha256": BASE_APK_SHA, "base_native_sha256": BASE_NATIVE_SHA,
              "apk": final.name, "apk_sha256": sha(final.read_bytes()), "version_code": VERSION_CODE,
              "version_name": RELEASE, "signer_certificate_sha256": CERT,
              "existing_jni_declarations_preserved": natives, "jni_additions": [],
              "core_java_classes_preserved": core, "resource_id_map_verified": len(ids),
              "verified_source_files": source_count, "source_built_android_layer": True,
              "native_recompiled": False, "packaged_native_sha256": BASE_NATIVE_SHA, "smali_used": False,
              "skin_id": "skin.infinity.diggz", "required_skin_version": "1.0.5.195",
              "skin_modified": False, "weather_modified": False, "shutdown_policy_changed": False,
              "shutdown_hang_resolved": False, "umbrella_back_freeze_resolved": False,
              "idle_takeover_resolved": False, "full_repair_brief_complete": False,
              "deferred_movie_video_framing_changed": False, "runtime_device_tested": False,
              "accepted": False, **preserved}
    (out / "APK-AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for src in (a.source_proof, a.source_receipt):
        shutil.copy2(src, out / src.name)
    for name in ("ENGINE-PROOF.json", "native-source-manifest.json"):
        shutil.copy2(baseline / name, out / name)
    shutil.copy2(HERE / "DEVICE-TEST.md", out / "DEVICE-TEST.md")
    unsigned.unlink()
    print("PASS Java-only Power route candidate; ALL native/assets/resources preserved; not device accepted")


if __name__ == "__main__":
    main()
