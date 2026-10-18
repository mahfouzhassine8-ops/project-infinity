#!/usr/bin/env python3
"""Recompile only the verified native VFS write-error scope delta.

Use exact proven TEST3/2103383 native reconstruction, preserving complete
player/PiP, Fold ANR, watched and touch code and protected TEST4. Signing is a
separate, fast reusable stage after the full native engine passes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/"checkpoint-build"

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    sys.modules[name]=result
    spec.loader.exec_module(result)
    return result

parent=load_module(HERE/"shutdown_native_ci.py","infinity_validated_2103383")
scope=load_module(HERE/"write_error_scope_patch.py","infinity_write_error_lease_scope")

def prepare(args):
    # Parent reconstructs exact locked TEST4, preserves full TEST3 delta and
    # applies only the verified 2103383 missing-installer-stage correction.
    parent.prepare(args)
    ancestor=parent.parent.parent.parent.parent
    manifest=ancestor.native_manifest(ancestor.stable())
    proof=scope.apply(ROOT/"kodi",OUT,manifest)
    assert len(proof["changed"])==4
    assert proof["no_class_wide_advisory_exemptions"]
    assert proof["actual_native_vfs_write_lease_required"]
    print("STAGED 2103383 source + 4 strictly enumerated native write-scope paths",flush=True)

def compile_engine():
    parent.compile_engine()
    original=json.loads((OUT/"ENGINE-PROOF.json").read_text())
    changed=json.loads((OUT/"INFINITY-WRITE-ERROR-SCOPE-DELTA.json").read_text())
    manifest=json.loads((OUT/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json").read_text())
    if not all(original.get(x) is True for x in
       ("complete_native_engine_compiled","fold_callback_retirement_compiled",
        "watched_presentation_bridge_compiled","browse_touch_preselection_compiled",
        "independent_close_installer_durability_compiled")):
        raise RuntimeError("Previously approved TEST3/2103383 native engine proof incomplete")
    if original.get("shutdown_policy")!="essential_first_process_exit_v1":
        raise RuntimeError("Original Essential-First policy replaced")
    if not (original.get("source_commit") == changed.get("source_provenance") == os.environ.get("GITHUB_SHA")):
        raise RuntimeError("Native source identity not established")
    for path,digest in changed["after"].items():
        actual=hashlib.sha256((ROOT/"kodi"/path).read_bytes()).hexdigest()
        if actual!=digest or manifest["after"].get(path)!=digest:
            raise RuntimeError("Unapproved native source changed after VFS repair: "+path)
    binary=OUT/"libkodi.so"
    if not binary.is_file() or binary.stat().st_size<100_000_000:
        raise RuntimeError("Full native binary not compiled")
    if hashlib.sha256(binary.read_bytes()).hexdigest()!=original["native_sha256"]:
        raise RuntimeError("Compiled ARM64 native proof mismatch")
    original.update(
        verified_optional_vfs_error_lease_scope_compiled=True,
        opaque_vfs_and_essential_write_errors_still_block=True,
        original_shutdown_coordinator_unchanged=True,
        original_fold_anr_and_watched_touch_preserved=True,
        write_error_scope_source_commit=os.environ.get("GITHUB_SHA"),
        write_error_scope_changed_source_paths=changed["changed"],
        signed_candidate_created=False,
        android_shutdown_verified=False,
        physical_fold_verified=False,
        locked=False,
    )
    (OUT/"ENGINE-PROOF.json").write_text(json.dumps(original,indent=2,sort_keys=True)+"\n")
    print("PASS native write-integrity correction; signed APK and Fold gates remain open",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["prepare","compile"])
    for key in ("locked","previous","parent-proof","rails-proof","test4-proof"):
        parser.add_argument("--"+key,type=Path)
    args=parser.parse_args()
    prepare(args) if args.mode=="prepare" else compile_engine()
