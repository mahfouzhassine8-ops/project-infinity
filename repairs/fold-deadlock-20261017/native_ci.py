#!/usr/bin/env python3
"""Replay exact TEST4 lineage, apply the callback delta, reuse full native build."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "checkpoint-build"
sys.path.insert(0, str(HERE))
import native_patch
import test_lock_retirement


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


# Its unchanged production patch imports sibling stage_experiment, just as
# when the original driver is invoked directly from its own directory.
sys.path.insert(0, str(ROOT / "repairs/essential-first-2103377"))
parent = module(ROOT / "repairs/essential-first-2103377/native_ci.py", "fold_test4_parent")


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def digests(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root / "xbmc").rglob("*") if p.is_file()}


def prepare(args):
    parent.prepare(args)
    root = ROOT / "kodi"
    path = OUT / "FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    proof = json.loads(path.read_text())
    locked = json.loads((args.test4_proof / path.name).read_text())
    assert proof["after"] == locked["after"], "Not the exact TEST4 native source map"
    save(OUT / "LOCKED-TEST4-SOURCE-PRESERVATION.json", proof)
    before = digests(root)
    original = (root / native_patch.SOURCE).read_text()
    (OUT / "TEST4-DirectoryProvider.cpp").write_text(original)
    delta = native_patch.apply(root, locked["after"][native_patch.SOURCE])
    after = digests(root)
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    assert changed == [native_patch.SOURCE], changed
    test_lock_retirement.verify(original, (root / native_patch.SOURCE).read_text(), OUT / "fold-lock-host")
    ordering = parent.parent.parent
    manifest_path = ordering.native_manifest(ordering.stable())
    manifest = json.loads(manifest_path.read_text())
    manifest["after"].update(delta["after"])
    save(manifest_path, manifest)
    proof["after"].update(delta["after"])
    proof.update(fold_callback_retirement_delta=True, physical_device_verified=False, locked=False)
    save(path, proof)
    delta.update(source_commit=os.environ.get("GITHUB_SHA", "local"),
                 exact_test4_native_source="f5e3d9434d8a8c0918d1f4cc6758cf3704eb873c",
                 complete_xbmc_file_count=len(before), all_other_native_sources_byte_identical=True,
                 shutdown_coordinator_unchanged=True, protected_write_admission_unchanged=True)
    save(OUT / "FOLD-DEADLOCK-SOURCE-DELTA.json", delta)


def compile_engine():
    parent.compile_engine()
    path = OUT / "ENGINE-PROOF.json"
    proof = json.loads(path.read_text())
    assert proof["complete_native_engine_compiled"]
    proof.update(fold_callback_retirement_compiled=True,
                 fold_correction_source_commit=os.environ.get("GITHUB_SHA", "local"),
                 physical_device_verified=False, locked=False)
    save(path, proof)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "compile"])
    for name in ("locked", "previous", "parent-proof", "rails-proof", "test4-proof"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    prepare(args) if args.mode == "prepare" else compile_engine()
