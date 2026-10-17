#!/usr/bin/env python3
"""Fail-closed identity gate for the signed Infinity APK, never stock Kodi.

APK preflight proves exact pinned file, package, permanent signer and ARM64 engine.
Phase mode accepts only reports from the unchanged real signed-APK Android probes.
Neither mode asserts feature completeness, physical Fold acceptance or final lock.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

PACKAGE = "com.projectinfinity.kodi"
CERTIFICATE = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
ENGINE = "lib/arm64-v8a/libkodi.so"
CASES = ("fresh", "cold", "core-initialized", "loaded")


class GateFailure(ValueError):
    pass


def require(value, message):
    if not value:
        raise GateFailure(message)


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_apk(apk, expected_sha, expected_code, aapt, apksigner):
    apk = Path(apk)
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha), "Unpinned APK digest")
    require(apk.is_file(), "Signed Infinity APK missing")
    actual_sha = digest_file(apk)
    require(actual_sha == expected_sha, "APK SHA-256 differs from pinned signed Infinity producer")

    with zipfile.ZipFile(apk) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), "APK has duplicate ZIP entries")
        require(z.testzip() is None, "APK is corrupt")
        require("AndroidManifest.xml" in names and "classes.dex" in names, "Missing actual Android APK payload")
        require(ENGINE in names, "Missing Infinity's ARM64 Kodi-derived native engine")
        native = z.read(ENGINE)
        require(len(native) > 64 and native[:5] == b"\x7fELF\x02", "Engine is not 64-bit ELF")
        require(int.from_bytes(native[18:20], "little") == 183, "Engine is not AArch64")
        native_sha = hashlib.sha256(native).hexdigest()

    badges = subprocess.check_output([str(aapt), "dump", "badging", str(apk)], text=True)
    m = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badges, re.M)
    require(m is not None, "Cannot prove APK package and version")
    require(m.group(1) == PACKAGE, "STOCK KODI OR WRONG APP PACKAGE: " + m.group(1))
    require(int(m.group(2)) == expected_code, "Unexpected Infinity versionCode")
    require("application-label:'Infinity'" in badges, "Not the Infinity application identity")
    require("application-debuggable" not in badges, "Debuggable APK cannot approve Infinity testing")

    signature = subprocess.check_output(
        [str(apksigner), "verify", "--verbose", "--print-certs", str(apk)], text=True)
    sig = re.search(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})", signature)
    require(sig is not None and sig.group(1).lower() == CERTIFICATE, "Wrong permanent Infinity signer")
    for version in (1, 2, 3):
        require(re.search(r"Verified using v" + str(version) + r" scheme[^\n]*:\s*true",
                          signature, re.I), "Missing required APK signing scheme v" + str(version))
    return {
        "product": "Infinity", "scope": "APK identity ONLY; not an end-to-end release approval",
        "package": PACKAGE, "apk_sha256": actual_sha, "version_code": int(m.group(2)),
        "version_name": m.group(3), "signer_sha256": sig.group(1).lower(),
        "native_engine_sha256": native_sha, "signed_infinity_apk_verified": True,
        "stock_kodi_eligible": False, "physical_fold_accepted": False,
        "final_lock_authorized": False,
    }


def check_phase(report_path, expected_sha, case):
    require(case in CASES, "Unknown Android probe phase")
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha), "Missing trusted APK hash")
    report = json.loads(Path(report_path).read_text())
    expected_report = "ANDROID-PROCESS-PROBE.json" if case == "fresh" else "OBSERVER-UPGRADE-PROBE.json"
    require(report.get("original_probe_report") == expected_report, "Wrong native Android probe type")
    require(report.get("case") == case, "Wrong native Android probe case")
    require(report.get("apk_sha256") == expected_sha, "Android tested a different APK")
    require(report.get("passed") is True, "Actual Infinity Android probe failed or was skipped")
    require(report.get("apk_deliverable") is False, "Probe improperly authorized release")
    require(report.get("physical_fold_accepted") is False, "Emulator falsely claims Fold acceptance")
    require(report.get("final_lock_authorized") is False, "Probe falsely claims final lock")
    return {
        "product": "Infinity", "case": case, "apk_sha256": expected_sha,
        "real_signed_android_probe_passed": True, "release_ready": False,
        "stock_kodi_eligible": False, "physical_fold_accepted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    apk = sub.add_parser("apk")
    apk.add_argument("--apk", type=Path, required=True)
    apk.add_argument("--expected-sha", required=True)
    apk.add_argument("--version-code", type=int, required=True)
    apk.add_argument("--aapt", required=True)
    apk.add_argument("--apksigner", required=True)
    phase = sub.add_parser("phase")
    phase.add_argument("--report", type=Path, required=True)
    phase.add_argument("--expected-sha", required=True)
    phase.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = (check_apk(args.apk, args.expected_sha, args.version_code, args.aapt, args.apksigner)
              if args.mode == "apk"
              else check_phase(args.report, args.expected_sha, args.case))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (GateFailure, OSError, ValueError, subprocess.CalledProcessError,
            zipfile.BadZipFile) as error:
        print("INFINITY-ONLY GATE BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(1)
