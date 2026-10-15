#!/usr/bin/env python3
"""Stage the minimal native interpreter-retirement RC1 over the exact Rails RC02
and Stability Probe source lineage, then compile the complete matched Kodi engine.

No production baseline branch, APK asset, or user data is ever mutated.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

# Preserve the Rails driver's 'import patch_native' resolution. Importing our
# fix under the same generic name causes the upstream 3-file Rails patch to be
# accidentally replaced at runtime. Unique module identities are essential.
patch_native = module(HERE / 'patch_native.py', 'infinity_shutdown_order_native_patch')
test_source = module(HERE / 'test_source.py', 'infinity_shutdown_order_native_tests')

def stable():
    return module(ROOT/"repairs/stability-probe-2103377/native_ci.py", "stability_native_parent")

def source_root(stable_ci):
    return stable_ci.parent().previous().source_root()

def native_manifest(stable_ci):
    return stable_ci.parent().previous().rc3().import_rc2().wide().lifecycle().SCRATCH / "runtime/native/manifest.json"

def load(path):
    return json.loads(Path(path).read_text())

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2)+"\n")

def digests(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root/"xbmc").rglob("*") if p.is_file()}

def prepare(args):
    parent = stable()
    parent.prepare(args)  # Same locked Rails RC02 + RC5 + stabilization source.
    source = source_root(parent)
    stage_proof = load(ROOT/"checkpoint-build/STABILITY-PROBE-DELTA.json")
    python_rel = patch_native.PYTHON
    assert stage_proof["after"][python_rel] == hashlib.sha256((source/python_rel).read_bytes()).hexdigest()
    old = digests(source)
    delta = patch_native.apply(source, expected_python_sha=stage_proof["after"][python_rel])
    new = digests(source)
    changed = sorted(set(old) | set(new))
    changed = [name for name in changed if old.get(name) != new.get(name)]
    assert changed == delta["changed"], (changed, delta["changed"])
    assert delta["python_persistence_authorization_unmodified"]
    assert delta["reusable_script_path_unchanged"]
    assert delta["early_swig_module_clear_preserved"]
    assert delta["no_py_end_interpreter_bypass"]

    manifest_path = native_manifest(parent)
    manifest = load(manifest_path)
    manifest["after"].update(delta["after"])
    manifest["changed"] = sorted(set(manifest["changed"]) | set(changed))
    save(manifest_path, manifest)

    preservation = ROOT/"checkpoint-build/FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    original = load(preservation)
    assert original["final_termination_authorization_byte_identical"]
    assert original["final_required_save_and_database_seal_stages_byte_identical"]
    original["after"].update(delta["after"])
    original["changed"] = sorted(set(original["changed"]) | set(changed))
    original.update(
      python_311_thread_shutdown_order_correction=True,
      registered_python_callback_failure_blocks_clean_exit=True,
      all_17_required_checkpoint_owners_byte_identical=True,
      physical_device_verified=False,
      implementation_branch_only=True,
      installed_apk_unchanged=True,
    )
    save(preservation, original)
    delta["source_commit"] = os.environ.get("GITHUB_SHA", "local-preview")
    delta["parent_rails_hold_rc02_sha256"] = "17e2458552b7dbb8f14dad307015eafc2497a5ec6ddc4f7bb1707d975f37b906"
    delta["source_preserved_except_two_files"] = True
    save(ROOT/"checkpoint-build/THREAD-SHUTDOWN-ORDER-DELTA.json", delta)
    test_source.verify(source,ROOT/"checkpoint-build/THREAD-SHUTDOWN-ORDER-HOST-CHECKS.json")
    print("RC1 STAGED: native Python Close callback ordering only; all 17 owners unchanged.", flush=True)

def compile_engine():
    parent = stable()
    # Full native build uses exactly the source tree that prepare() staged.
    parent.compile_engine()
    build = ROOT/"checkpoint-build"
    proof = load(build/"ENGINE-PROOF.json")
    delta = load(build/"THREAD-SHUTDOWN-ORDER-DELTA.json")
    native = (build/"libkodi.so").read_bytes()
    assert proof["complete_native_engine_compiled"]
    assert proof["rc5_17_required_save_owners_unchanged"]
    assert delta["source_preserved_except_two_files"]
    for token in (
        b"registered_python_thread_shutdown_failed",
        b"python.runtime.threading_shutdown.begin",
        b"python.runtime.threading_shutdown.complete",
        b"python.runtime.threading_shutdown.failed",
        b"rc3.playlist_read_cancelled_in_poll",
        b"Infinity Rails hold: control=",
    ):
        assert token in native, ("Native C++ compile proof missing: ", token)
    proof.update(
        python_thread_shutdown_order_rc1_compiled=True,
        python_shutdown_order_source_commit=os.environ.get("GITHUB_SHA", "unknown"),
        changed_runtime_files=delta["changed"],
        persistence_checkpoint_owners_unchanged=True,
        release_signed=False,
        physical_device_verified=False,
        root_cause_fully_resolved=False,
        locked=False,
    )
    save(build/"ENGINE-PROOF.json",proof)
    print("PASS RC1 complete matched Kodi native engine; physical Fold acceptance PENDING.",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["prepare","compile"])
    for name in ("locked","previous","parent-proof"):
        parser.add_argument("--"+name,type=Path)
    arguments=parser.parse_args()
    if arguments.mode == "prepare": prepare(arguments)
    else: compile_engine()
