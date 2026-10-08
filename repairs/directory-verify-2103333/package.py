#!/usr/bin/env python3
"""2103333: install-over verification repack of the successful 2103330 repair.

Reuses the exact 2103330 native build, source delta, Android reader and tests.
Only the installable version code/name change. No feature, skin, or native edits.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "directory-close-2103330"
sys.path.insert(0, str(SOURCE))
spec = importlib.util.spec_from_file_location("directory_close_330", SOURCE / "package.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

VERSION = 2103333
INSTALLED_ROLLBACK = 2103332
RELEASE = "1.0.9-Directory-Close-Verification-RC1"
REPAIRED_NATIVE_CANDIDATE = 2103330
REPAIRED_NATIVE_SOURCE = "16cb5ccebb2b85107132ca0a04a5e639208476e0"
REPAIRED_APK_SOURCE = "58ea53584f1998ce9a7b94e331f028bdc0bc61bf"
REPAIRED_NATIVE_RUN = "37709784725"
REPAIRED_APK_RUN = "37711193442"
PREVIOUS_APK = "Infinity-2103330-Directory-Close-RC1.apk"
OUTPUT_APK = "Infinity-2103333-Directory-Close-Verification-RC1.apk"
EXPECTED = core.EXPECTED

require = core.require
sha = core.sha
original_native = core.native

def native_3330_only(engine, out):
    """Keep the immutable 3330 ENGINE-PROOF contract while bumping Android."""
    proof = json.loads((engine / "ENGINE-PROOF.json").read_text())
    require(proof["candidate"] == REPAIRED_NATIVE_CANDIDATE and
            proof["source_commit"] == REPAIRED_NATIVE_SOURCE and
            proof["result_wait_cancellation"] is True and
            proof["final_worker_join_preserved"] is True and
            proof["script_owner_cleanup_preserved"] is True and
            proof["worker_force_stop_added"] is False,
            "Incorrect or unreviewed native engine")
    previous = core.VERSION
    try:
        core.VERSION = REPAIRED_NATIVE_CANDIDATE
        return original_native(engine, out)
    finally:
        core.VERSION = previous

core.native = native_3330_only
core.VERSION = VERSION
core.RELEASE = RELEASE

def verified_3330_report(root):
    proof_path = root / "parent3330" / "APK-VERIFICATION.json"
    prior = json.loads(proof_path.read_text())
    require(prior["candidate"] == REPAIRED_NATIVE_CANDIDATE and
            prior["source_commit"] == REPAIRED_APK_SOURCE and
            str(prior["validation_run"]) == REPAIRED_APK_RUN and
            prior["native_source_commit"] == REPAIRED_NATIVE_SOURCE and
            str(prior["native_validation_run"]) == REPAIRED_NATIVE_RUN and
            prior["skin_parent"] == "1.0.5.201" and
            prior["skin_candidate"] == "1.0.5.204" and
            prior["physical_device_verified"] is False and
            prior["locked"] is False,
            "2103330 receipt is not from the approved green run")
    return prior

def assert_preserved_apk(previous_apk, final_apk, previous_native):
    """Full unchanged-content proof against the already signed 3330 candidate."""
    with zipfile.ZipFile(previous_apk) as a, zipfile.ZipFile(final_apk) as b:
        require(a.testzip() is None and b.testzip() is None, "Bad APK ZIP")
        files_a, files_b = set(a.namelist()), set(b.namelist())
        require(files_a == files_b, "APK payload file set differs from 2103330")
        engine = core.base327.ENGINE
        require(sha(a.read(engine)) == previous_native and
                a.read(engine) == b.read(engine),
                "Packaged native engine differs from approved 2103330")
        ignored = lambda name: (name == "AndroidManifest.xml" or
                                core.base327.DEX.fullmatch(name) or
                                core.base327.SIGNATURE.fullmatch(name))
        for name in sorted(files_a):
            if not ignored(name):
                require(a.read(name) == b.read(name),
                        "Non-version payload changed against 2103330: " + name)

def prepare(base, build, out, engine):
    require(VERSION > INSTALLED_ROLLBACK, "Version code not installable over 2103332")
    prior = verified_3330_report(core.ROOT)
    require(os.environ["INFINITY_NATIVE_SOURCE_COMMIT"] == REPAIRED_NATIVE_SOURCE and
            os.environ["INFINITY_NATIVE_RUN_ID"] == REPAIRED_NATIVE_RUN,
            "Native validation run not pinned to green 2103330")
    core.prepare(base, build, out, engine)
    actual = json.loads((out / "SOURCE-PRESERVATION.json").read_text())
    require(actual["candidate"] == REPAIRED_NATIVE_CANDIDATE and
            actual["native_sha256"] == prior["native_sha256"],
            "Android source or native binding changed from tested 2103330")
    print("PASS: unchanged 2103330 repaired engine + Android source; 2103333 installable version prepared")

def package(base, build, out, engine):
    prior = verified_3330_report(core.ROOT)
    core.package(base, build, out, engine)  # Full signed 3330 preservation/suite checks at version 3333.
    previous_apk = core.ROOT / "base3330" / PREVIOUS_APK
    require(sha(previous_apk.read_bytes()) == prior["apk_sha256"],
            "Signed 2103330 parity APK does not match its successful run")
    from_path = out / PREVIOUS_APK
    to_path = out / OUTPUT_APK
    require(from_path.is_file() and not to_path.exists(), "Unexpected release artifact")
    assert_preserved_apk(previous_apk, from_path, prior["native_sha256"])
    report_path = out / "APK-VERIFICATION.json"
    result = json.loads(report_path.read_text())
    require(result["candidate"] == VERSION and result["version_name"] == RELEASE and
            result["native_sha256"] == prior["native_sha256"] and
            result["signer_certificate_sha256"] == prior["signer_certificate_sha256"] and
            result["android_source_delta"] == prior["android_source_delta"] and
            result["test_total"] >= prior["test_total"] and
            result["skin_and_assets_byte_identical"] is True and
            result["all_other_classes_behavior_identical"] is True and
            result["data_reset"] is False and
            result["locked"] is False,
            "2103333 differs from reviewed 2103330 beyond Android version metadata")
    from_path.rename(to_path)
    require(sha(to_path.read_bytes()) == result["apk_sha256"], "Renamed APK bytes changed")
    result.update(
        apk_filename=OUTPUT_APK,
        native_recompiled=False,
        packaged_native_unchanged_from_2103330=True,
        native_engine_source_candidate=2103330,
        native_engine_source_run=REPAIRED_NATIVE_RUN,
        repackaged_from_tested_apk_candidate=2103330,
        prior_apk_sha256=prior["apk_sha256"],
        prior_apk_run=REPAIRED_APK_RUN,
        installs_over_version=INSTALLED_ROLLBACK,
        preserved_rollback_apk=2103327,
        preserved_rollback_skin="1.0.5.201",
        skin_candidate="1.0.5.204",
        physical_device_verified=False,
        locked=False,
    )
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS: signed 2103333 APK, exact 2103330 repaired native & all other payloads; Fold verification pending")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "package"])
    for name in ("base", "build", "out", "engine"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (prepare if args.mode == "prepare" else package)(args.base, args.build, args.out, args.engine)
