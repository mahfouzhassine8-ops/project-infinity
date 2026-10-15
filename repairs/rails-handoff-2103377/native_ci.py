#!/usr/bin/env python3
"""Add one Rails directory fix atop the *identical* Python Retirement RC1 source.
The RC1 native and 17-save-owner checks are run first, never bypassed.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    sys.modules[name]=result
    spec.loader.exec_module(result)
    return result

parent=module(ROOT/"repairs/python-shutdown-order-2103377/native_ci.py","infinity_rc1_parent_driver")
patch=module(HERE/"patch_native.py","infinity_rails_handoff_patch")
# The host harness imports patch_native by name, so its directory takes precedence.
sys.path.insert(0,str(HERE))
tests=module(HERE/"test_native.py","infinity_rails_handoff_test")

def load(path):
    return json.loads(Path(path).read_text())

def save(path,data):
    Path(path).write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")

def prepare(args):
    parent.prepare(args)
    stable=parent.stable()
    source=parent.source_root(stable)
    old=parent.digests(source)
    delta=patch.apply(source)
    new=parent.digests(source)
    changed=sorted(name for name in set(old)|set(new) if old.get(name)!=new.get(name))
    assert changed==delta["changed"],changed
    assert delta["all_17_shutdown_owner_gates_preserved"]
    manifest=parent.native_manifest(stable)
    info=load(manifest)
    info["after"].update(delta["after"])
    info["changed"]=sorted(set(info["changed"])|set(changed))
    save(manifest,info)
    base=ROOT/"checkpoint-build"
    preservation=base/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    p=load(preservation)
    assert p["all_17_required_checkpoint_owners_byte_identical"]
    assert p["final_termination_authorization_byte_identical"]
    assert p["final_required_save_and_database_seal_stages_byte_identical"]
    p["after"].update(delta["after"])
    p["changed"]=sorted(set(p["changed"])|set(changed))
    p.update(infinity_rails_handoff_correction=True,physical_device_verified=False,
             installed_apk_unchanged=True)
    save(preservation,p)
    delta["source_commit"]=os.environ.get("GITHUB_SHA","local")
    delta["candidate_scope"]="one DirectoryProvider.cpp, no other runtime files"
    save(base/"RAILS-HANDOFF-SOURCE-DELTA.json",delta)
    tests.verify(source,base/"RAILS-HANDOFF-HOST.json")
    print("PASS staged RC1 shutdown + one targeted Rails directory callback/priority correction",flush=True)

def compile_engine():
    parent.compile_engine()
    build=ROOT/"checkpoint-build"
    proof=load(build/"ENGINE-PROOF.json")
    delta=load(build/"RAILS-HANDOFF-SOURCE-DELTA.json")
    import hashlib
    lib=(build/"libkodi.so").read_bytes()
    assert proof["complete_native_engine_compiled"]
    assert proof["rc5_17_required_save_owners_unchanged"]
    assert delta["changed"]==[patch.SOURCE]
    assert b"Infinity rails: stale job discarded" in lib
    assert b"python.runtime.threading_shutdown.complete" in lib
    assert b"Infinity Rails hold: control=" in lib
    assert hashlib.sha256(lib).hexdigest()==proof["native_sha256"]
    proof.update(rails_handoff_native_compiled=True,
       rails_handoff_source_commit=os.environ.get("GITHUB_SHA","unknown"),
       changed_runtime_files=sorted(set(proof["changed_runtime_files"])|set(delta["changed"])),
       all_17_required_checkpoint_owners_unchanged=True,
       physical_device_verified=False,locked=False)
    save(build/"ENGINE-PROOF.json",proof)
    print("PASS matched complete native engine; no physical Fold claim",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["prepare","compile"])
    for name in ("locked","previous","parent-proof"):
        parser.add_argument("--"+name,type=Path)
    args=parser.parse_args()
    if args.mode=="prepare": prepare(args)
    else: compile_engine()
