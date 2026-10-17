#!/usr/bin/env python3
"""Build forward from the exact TEST1 deadlock fix; bound presentation/touch delta."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "checkpoint-build"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


parent = module(ROOT / "repairs/fold-deadlock-20261017/native_ci.py", "watched_fold_parent")
patch = module(HERE / "native_patch.py", "watched_presentation_patch")
touch = module(HERE / "touch_patch.py", "touch_patch")
test_touch = module(HERE / "test_touch.py", "watched_touch_production_test")


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def prepare(args):
    parent.prepare(args)
    runtime = ROOT / "kodi"
    before = parent.digests(runtime)
    callback = "xbmc/guilib/listproviders/DirectoryProvider.cpp"
    assert before[callback] == "496d7b61c8425050e9f707cd28fa41f1e792abcf8892f49d7259bd71cee3506f"
    delta = patch.apply(runtime)
    touch_delta = touch.apply(runtime)
    after = parent.digests(runtime)
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    assert changed == sorted(patch.FILES + patch.ADDED + touch.FILES), changed
    assert before[callback] == after[callback], "Do not alter the completed native deadlock correction"
    # Existing Home hold body and dispatch remain exact, in addition to all
    # original shutdown, native writer and admission sources outside this list.
    prior_home = module(ROOT / "repairs/rails-hold-2103378/patch_native.py", "watched_original_home")
    assert prior_home.METHOD in (runtime / "xbmc/guilib/GUIBaseContainer.cpp").read_text()
    assert prior_home.DISPATCH in (runtime / "xbmc/input/InputManager.cpp").read_text()
    test_touch.verify(runtime, OUT / "BROWSE-TOUCH-PRODUCTION-HOST.json")
    binary = OUT / "watched-index-host"
    subprocess.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pthread", str(HERE / "test_native.cpp"), "-o", str(binary)], check=True)
    save(OUT / "WATCHED-INDEX-HOST.json", json.loads(subprocess.check_output([str(binary)], text=True)))
    changes = {**delta["after"], **touch_delta["after"]}
    ordering = parent.parent.parent.parent
    manifest_path = ordering.native_manifest(ordering.stable())
    manifest = json.loads(manifest_path.read_text())
    manifest["after"].update(changes)
    manifest["changed"] = sorted(set(manifest["changed"]) | set(patch.FILES) | set(touch.FILES))
    manifest["added"] = sorted(set(manifest.get("added", [])) | set(patch.ADDED))
    save(manifest_path, manifest)
    proof_path = OUT / "FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    proof = json.loads(proof_path.read_text())
    proof["after"].update(changes)
    proof["changed"] = sorted(set(proof["changed"]) | set(patch.FILES) | set(touch.FILES))
    proof["added"] = sorted(set(proof.get("added", [])) | set(patch.ADDED))
    proof.update(watched_readonly_presentation_delta=True, scoped_browse_touch_preselection=True, locked=False, physical_device_verified=False)
    save(proof_path, proof)
    prior = json.loads((OUT / "FOLD-DEADLOCK-SOURCE-DELTA.json").read_text())
    prior.update(scope="Completed callback-retirement stage before the separately enumerated watched/touch delta",
                 all_other_native_sources_byte_identical=False, additional_delta_report="WATCHED-TOUCH-SOURCE-DELTA.json")
    save(OUT / "FOLD-DEADLOCK-SOURCE-DELTA.json", prior)
    report = dict(schema=1, source_commit=os.environ.get("GITHUB_SHA", "local"),
        completed_deadlock_source="0c9b933c7916cce7d5e0f47a195751827fc41c28",
        completed_deadlock_callback_sha256=after[callback], changed=changed,
        before={name: before[name] for name in changed if name in before}, after=changes,
        complete_native_files_before=len(before), complete_native_files_after=len(after),
        all_other_native_sources_byte_identical=True, native_shutdown_and_write_admission_unchanged=True,
        provider_code_changed=False, command_center_code_changed=False, rails_helper_code_changed=False,
        original_home_rail_hold_unchanged=True, watched=delta, touch=touch_delta,
        physical_fold_verified=False, locked=False)
    save(OUT / "WATCHED-TOUCH-SOURCE-DELTA.json", report)


def compile_engine():
    parent.compile_engine()
    path = OUT / "ENGINE-PROOF.json"
    proof = json.loads(path.read_text())
    assert proof["complete_native_engine_compiled"] and proof["fold_callback_retirement_compiled"]
    proof.update(watched_presentation_bridge_compiled=True, browse_touch_preselection_compiled=True,
                 watched_touch_source_commit=os.environ.get("GITHUB_SHA", "local"),
                 physical_device_verified=False, locked=False)
    save(path, proof)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "compile"])
    for name in ("locked", "previous", "parent-proof", "rails-proof", "test4-proof"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    prepare(args) if args.mode == "prepare" else compile_engine()
