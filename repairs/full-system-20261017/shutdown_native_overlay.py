#!/usr/bin/env python3
"""ONE verified durability correction on top of the complete signed TEST3 source.

Reuse the unchanged TEST4 Essential-First controller, TEST3 Fold deadlock
correction, watched state, and touch fixes. Never create a second coordinator,
waive unfinished essential writes, or change another native component.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_BUILD = ROOT / "checkpoint-build"
NATIVE = "xbmc/platform/android/activity/InfinityProtectedWrites.h"
TEST4_TEST3_HEADER_SHA256 = "a0a50a78e24fc5da8c9af65bc894ee47af4e61139af9d89cf014207d177e92f1"
REFERENCE_SOURCE_COMMIT = "093323fbc0ae87cbe2fa2a21abab0c357fdaf754"
PROTECTED = (
    "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp",
    "xbmc/platform/android/activity/InfinityAndroidCheckpoint.h",
    "xbmc/platform/android/activity/InfinityScriptPersistence.h",
    "xbmc/dbwrappers/InfinityDatabaseBarrier.h",
    "xbmc/interfaces/python/PythonInvoker.cpp",
    "xbmc/interfaces/python/XBPython.cpp",
    "xbmc/utils/JobManager.cpp",
    "xbmc/addons/AddonInstaller.cpp",
    "xbmc/guilib/listproviders/DirectoryProvider.cpp",
    "xbmc/input/InputManager.cpp",
    "xbmc/guilib/GUIBaseContainer.cpp",
    "xbmc/guilib/GUIBaseContainer.h",
    "xbmc/GUIInfoManager.cpp",
    "xbmc/interfaces/builtins/GUIBuiltins.cpp",
    "xbmc/profiles/ProfileManager.cpp",
    "xbmc/guilib/InfinityWatchedIndex.h",
    "xbmc/guilib/InfinityWatchedPresentation.h",
)


def require(check, message):
    if not check:
        raise RuntimeError("Infinity source-preservation gate: " + message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def apply(source, build, manifest_path):
    source, build, manifest_path = Path(source), Path(build), Path(manifest_path)
    header = source / NATIVE
    corrected = ROOT / "repairs/essential-first-2103377/runtime" / NATIVE
    require(header.is_file() and corrected.is_file(), "missing original/corrected native header")
    previous = digest(header)
    require(previous == TEST4_TEST3_HEADER_SHA256,
            "NOT exact pre-correction TEST3: " + previous)
    replacement = corrected.read_bytes()
    require(b"SyncRemovedInstallerStage" in replacement and
            b"InstallerStageRoot" in replacement and
            b"protected_durability_failed:" not in replacement,
            "unexpected installer-stage correction payload")
    corrected_sha = hashlib.sha256(replacement).hexdigest()
    require(corrected_sha != previous, "the correction was not applied")

    manifest = read_json(manifest_path)
    preservation_path = build / "FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    preservation = read_json(preservation_path)
    locked = read_json(build / "LOCKED-TEST4-SOURCE-PRESERVATION.json")
    watched = read_json(build / "WATCHED-TOUCH-SOURCE-DELTA.json")
    deadlock = read_json(build / "FOLD-DEADLOCK-SOURCE-DELTA.json")
    require(manifest["after"].get(NATIVE) == previous and
            preservation["after"].get(NATIVE) == previous and
            locked["after"].get(NATIVE) == previous,
            "TEST4/TEST3 protected-write source identity mismatch")
    require(watched.get("native_shutdown_and_write_admission_unchanged") is True and
            watched.get("all_other_native_sources_byte_identical") is True,
            "TEST3 watched/touch stage not preserved")
    require(deadlock.get("shutdown_coordinator_unchanged") is True and
            deadlock.get("protected_write_admission_unchanged") is True,
            "TEST3 deadlock stage not preserved")
    require(set(PROTECTED).issubset(manifest["after"]), "missing protected feature sources")

    for path in PROTECTED:
        expected = manifest["after"][path]
        require(digest(source / path) == expected,
                "previously validated feature or shutdown source changed: " + path)
        require(preservation["after"][path] == expected,
                "original preservation manifest disagrees: " + path)

    # The only write to Kodi's native source tree is this exact header.
    header.write_bytes(replacement)
    require(digest(header) == corrected_sha, "correction bytes did not land")
    for path in PROTECTED:
        require(digest(source / path) == manifest["after"][path],
                "protected feature changed while staging: " + path)
    manifest["after"][NATIVE] = corrected_sha
    manifest["changed"] = sorted(set(manifest.get("changed", [])) | {NATIVE})
    preservation["after"][NATIVE] = corrected_sha
    preservation["changed"] = sorted(set(preservation.get("changed", [])) | {NATIVE})
    preservation.update(
        fold_deadlock_source_preserved=True,
        watched_touch_source_preserved=True,
        essential_first_coordinator_unchanged=True,
        safe_missing_installer_stage_durability_correction=True,
        original_locked_test4_unmodified=True,
        physical_device_verified=False, locked=False
    )

    # These records describe the new experimental build, never rewrite the
    # historical exact TEST4 evidence file.
    save_json(manifest_path, manifest)
    save_json(preservation_path, preservation)
    proof = {
        "schema": 1,
        "scope": "Single TEST3 native source correction; no independent Android app",
        "parent_experimental_source": REFERENCE_SOURCE_COMMIT,
        "changed": [NATIVE],
        "before": {NATIVE: previous},
        "after": {NATIVE: corrected_sha},
        "test4_reference_header_sha256": locked["after"][NATIVE],
        "strict_protected_file_durability_not_weakened": True,
        "missing_essential_profile_database_symlink_still_fatal": True,
        "source_provenance": os.environ.get("GITHUB_SHA", "local"),
        "shutdown_coordinator_sha256": manifest["after"][PROTECTED[0]],
        "prior_test3_native_features_preserved": list(PROTECTED),
        "blocked_future_job_admission_existing_coordinator_preserved": True,
        "optional_producers_not_authorized_to_bypass_essential_saves": True,
        "physical_fold_verified": False,
        "apk_built": False,
        "final_lock_authorized": False,
    }
    save_json(build / "INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json", proof)
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source, args.build, args.manifest), indent=2))
