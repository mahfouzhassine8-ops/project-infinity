#!/usr/bin/env python3
"""Byte-level preservation of green 2103364 APK for Android-only candidate."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "repairs/mobile-regressions-2103304"))
from packaging_checks import DEX, SIGNATURE, dex_contract, require

def compare(old, new):
    a = old.namelist()
    b = new.namelist()
    require(len(a) == len(set(a)) and len(b) == len(set(b)), "Duplicate APK entries")
    require(old.testzip() is None and new.testzip() is None, "APK ZIP integrity failure")
    old_names = {name for name in a if not SIGNATURE.fullmatch(name)}
    new_names = {name for name in b if not SIGNATURE.fullmatch(name)}
    require(old_names == new_names, "APK inventory changed from green 2103364")
    allowed = {name for name in old_names if name == "AndroidManifest.xml" or DEX.fullmatch(name)}
    protected = sorted(old_names - allowed)
    for name in protected:
        require(old.read(name) == new.read(name), "Protected payload changed: " + name)
    native = "lib/arm64-v8a/libkodi.so"
    require(native in protected, "Green ARM64 engine absent")
    old_jni, old_classes = dex_contract(old)
    new_jni, new_classes = dex_contract(new)
    require(old_jni == new_jni, "Protected JNI declaration changed")
    # Changed Android code may modify synthetic lambda classes; all existing
    # top-level classes, and all classes outside reviewed Android owners survive.
    reviewed_prefixes = (
        "Lcom/projectinfinity/kodi/Main$",
        "Lcom/projectinfinity/kodi/InfinityCloseGuardService$",
    )
    removed = old_classes - new_classes
    unexpected = sorted(c for c in removed if not c.startswith(reviewed_prefixes))
    require(not unexpected, "Unreviewed Android class removed: " + repr(unexpected))
    return {
        "baseline_version": 2103364,
        "protected_entries_byte_identical": len(protected),
        "native_sha256": hashlib.sha256(new.read(native)).hexdigest(),
        "java_top_level_and_unrelated_classes_preserved": True,
        "jni_declarations_preserved": True,
        "changed_android_entries_only": sorted(allowed),
        "physical_fold_verified": False,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.baseline) as left, zipfile.ZipFile(args.candidate) as right:
        result = compare(left, right)
    args.report.parent.mkdir(exist_ok=True, parents=True)
    args.report.write_text(json.dumps(result, indent=2)+"\n")
    print("PASS: Android-only candidate preserves exact green 2103364 native/scripts/skin and JNI")
