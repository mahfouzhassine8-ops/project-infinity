#!/usr/bin/env python3
"""Stage RC5 optional service shutdown atop EXACT green RC3 native lineage.

Stage all original RC3 changes first, then make a two-file, hash-audited
classifier/dispatch delta. Compile full matched native engine; no native-only
APK splice without the exact green original dependency/artifact proofs.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import optional_shutdown

def rc3():
    path=ROOT/"repairs/shutdown-rc3-2103377/native_ci.py"
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location("green_rc3_native",path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load(path):
    return json.loads(Path(path).read_text())

def save(path, obj):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")

def source_root():
    return rc3().import_rc2().wide().lifecycle().SOURCE

def prepare(args):
    previous=rc3()
    previous.prepare(args)
    root=source_root()
    manifest_path=ROOT/"checkpoint-build/RC5-SOURCE-LEDGER.json"
    native_manifest=previous.import_rc2().wide().lifecycle().SCRATCH/"runtime/native/manifest.json"
    manifest=load(native_manifest)
    # No save-owner, Python persistence, database seal, or Java modifications.
    checkpoint_file=root/"xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
    script_persistence=root/"xbmc/platform/android/activity/InfinityScriptPersistence.h"
    checkpoint_before=checkpoint_file.read_bytes()
    script_before=script_persistence.read_bytes()
    delta=optional_shutdown.apply(root)
    after=dict(manifest["after"])
    after.update(delta["after"])
    manifest.update(after=after,
      changed=sorted(set(manifest["changed"]) | set(delta["changed"])))
    save(native_manifest, manifest)
    if checkpoint_file.read_bytes()!=checkpoint_before or script_persistence.read_bytes()!=script_before:
        raise AssertionError("RC5 touched locked save/transaction/native authorisation logic")
    previous.import_rc2().wide().lifecycle().load_parent_driver().previous().foundation().runtime_delta.verify(root,after)
    original=load(ROOT/"checkpoint-build/FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    assert original["final_termination_authorization_byte_identical"]
    assert original["final_required_save_and_database_seal_stages_byte_identical"]
    original["after"]=after
    original["changed"]=sorted(set(original["changed"])|set(delta["changed"]))
    original["source_commit"]=os.environ["GITHUB_SHA"]
    original.update(rc5_explicit_external_optional_script_classification=True,
                    rc5_17_required_save_owners_unchanged=True,
                    rc5_no_trakt_addon_edits=True,
                    rc5_infinity_continuity_is_optional_diagnostic=True,
                    rc5_trakt_infinity_checkpoint_receipt_required=False,
                    rc5_unclassified_writer_safety_preserved=True,
                    physical_shutdown_verified=False,
                    native_full_compilation_complete=False)
    save(ROOT/"checkpoint-build/FINAL-SHUTDOWN-SOURCE-PRESERVATION.json",original)
    save(ROOT/"checkpoint-build/RC5-OPTIONAL-STOP-DELTA.json",delta)
    save(manifest_path,{"rc5":delta,"original_checkpoint_sha256":hashlib.sha256(checkpoint_before).hexdigest(),
      "original_script_persistence_sha256":hashlib.sha256(script_before).hexdigest(),
      "purpose":"Source lineage and unrelated runtime preservation"})
    print("RC5 STAGED: optional Trakt/cloud-owned and pinned Continuity diagnostics stop-only; 17 final receipts unchanged.")

def compile_engine():
    previous=rc3()
    previous.compile_engine()
    build=ROOT/"checkpoint-build"
    binary=(build/"libkodi.so").read_bytes()
    for token in (
        b"stop-only:trakt-cloud-owned",
        b"stop-only:continuity-diagnostic",
        b"rc3.python_abort_requested_at_close",
        b"rc3.playlist_read_rejected_at_open",
        b"rc3.playlist_read_cancelled_in_poll"):
        if token not in binary:
            raise AssertionError("RC5 native binary lost approved behavior "+str(token))
    proof=load(build/"ENGINE-PROOF.json")
    delta=load(build/"RC5-OPTIONAL-STOP-DELTA.json")
    check=load(build/"RC5-OPTIONAL-HOST-TESTS.json")
    assert proof["complete_native_engine_compiled"]
    assert check["passed"]==check["total"] and check["total"]>=12
    assert delta["trakt_enabled_and_files_unchanged"] and delta["trakt_not_required_save_owner"]
    assert delta["other_foreign_writers_still_require_durability"]
    assert delta["all_17_required_owner_gates_unchanged"]
    proof.update(purpose="RC5 optional Trakt and Continuity native stop-only contract",
                 rc5_trakt_stop_only_compiled=True,
                 rc5_continuity_stop_only_compiled=True,
                 rc5_host_test_cases=check["passed"],
                 rc5_17_required_save_owners_unchanged=True,
                 rc5_unclassified_script_save_gate_unchanged=True,
                 rc5_trakt_files_touched=False,
                 rc5_automatic_trakt_disable=False,
                 rc5_shipped_skin_update=False,
                 rc5_full_loaded_fold_verified=False,
                 physical_shutdown_verified=False,
                 signed_apk_built=False,
                 device_accepted=False,
                 locked=False)
    save(build/"ENGINE-PROOF.json",proof)
    print("PASS RC5 FULL ENGINE: original RC3/native engine plus optional Trakt and Continuity stop-only. NOT physical Fold proof.")

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("mode",choices=("prepare","compile"))
    for item in ("locked","previous","parent-proof"):
        cli.add_argument("--"+item,type=Path)
    opts=cli.parse_args()
    if opts.mode=="prepare":prepare(opts)
    else:compile_engine()
