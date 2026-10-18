#!/usr/bin/env python3
"""Replay EXACT green TEST3 native source, apply ONE independent Close correction.

The original full compiler still reconstructs and validates every inherited
source stage. No stock Kodi tree, new app ID, shortcut signing, or skipped gate.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "checkpoint-build"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


# The previous passed native driver is the only source of all inherited
# watched/touch/deadlock/Essential-First reconstruction and compiler gates.
parent = module(ROOT / "repairs/watched-bridge-20261017/native_ci.py",
                "preserved_full_test3_native_driver")
overlay = module(HERE / "shutdown_native_overlay.py", "independent_close_overlay")


def prepare(args):
    parent.prepare(args)
    ancestor = parent.parent.parent.parent
    source_manifest = ancestor.native_manifest(ancestor.stable())
    proof = overlay.apply(ROOT / "kodi", OUT, source_manifest)
    assert proof["changed"] == ["xbmc/platform/android/activity/InfinityProtectedWrites.h"]
    assert proof["parent_experimental_source"] == overlay.REFERENCE_SOURCE_COMMIT
    print("STAGED original signed TEST3 source + ONE reviewed durability correction; "
          "no installed user data touched.", flush=True)


def compile_engine():
    parent.compile_engine()
    proof_path = OUT / "ENGINE-PROOF.json"
    proof = json.loads(proof_path.read_text())
    expected = json.loads((OUT / "INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json").read_text())
    source = json.loads((OUT / "FINAL-SHUTDOWN-SOURCE-PRESERVATION.json").read_text())
    require = lambda x, m: x or (_ for _ in ()).throw(RuntimeError(m))
    native = (OUT / "libkodi.so")
    require(native.is_file() and native.stat().st_size > 100_000_000,
            "No full compiled ARM64 native engine")
    require(proof.get("complete_native_engine_compiled") is True and
            proof.get("fold_callback_retirement_compiled") is True and
            proof.get("watched_presentation_bridge_compiled") is True and
            proof.get("browse_touch_preselection_compiled") is True,
            "Original native TEST3 improvements did not compile")
    require(expected["source_provenance"] == os.environ.get("GITHUB_SHA") ==
            proof.get("source_commit"), "Native source commit mismatch")
    require(source["after"][overlay.NATIVE] == expected["after"][overlay.NATIVE] and
            hashlib.sha256((ROOT / "kodi" / overlay.NATIVE).read_bytes()).hexdigest() ==
            expected["after"][overlay.NATIVE], "Native source not compiled from reviewed correction")
    require(hashlib.sha256(native.read_bytes()).hexdigest() ==
            proof.get("native_sha256"), "Compiled engine proof invalid")
    require(proof.get("shutdown_policy") == "essential_first_process_exit_v1",
            "Original independent Infinity Essential-First coordinator was replaced")
    proof.update(
        independent_close_installer_durability_compiled=True,
        preservation_reference_test3=overlay.REFERENCE_SOURCE_COMMIT,
        original_test4_untouched=True,
        native_change_scope=[overlay.NATIVE],
        new_apk_built=False,
        apk_deliverable=False,
        android_close_verified=False,
        physical_device_verified=False,
        physical_fold_verified=False,
        locked=False,
    )
    proof_path.write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
    print("PASS: full tested TEST3 native engine + one durability correction; "
          "APK/physical gate still pending.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "compile"))
    for option in ("locked", "previous", "parent-proof", "rails-proof", "test4-proof"):
        parser.add_argument("--" + option, type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args)
    else:
        compile_engine()
