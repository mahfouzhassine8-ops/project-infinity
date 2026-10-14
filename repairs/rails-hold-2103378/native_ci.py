#!/usr/bin/env python3
"""Reconstruct the existing RC5 engine, then apply only the three-file rail delta."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import patch_native

def previous():
    path=ROOT/'repairs/shutdown-rc5-2103377/native_ci.py'
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('rails_parent_native',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def read(p): return json.loads(p.read_text())
def save(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

def prepare(args):
    parent=previous();parent.prepare(args)
    root=parent.source_root()
    manifest_path=parent.rc3().import_rc2().wide().lifecycle().SCRATCH/'runtime/native/manifest.json'
    manifest=read(manifest_path)
    # Record the complete reconstructed parent before touching any source file.
    before={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root/'xbmc').rglob('*') if p.is_file()}
    delta=patch_native.apply(root)
    after={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in (root/'xbmc').rglob('*') if p.is_file()}
    changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
    assert changed==sorted(delta['changed']), changed
    manifest['after'].update(delta['after'])
    manifest['changed']=sorted(set(manifest['changed'])|set(changed))
    save(manifest_path,manifest)
    parent.rc3().import_rc2().wide().lifecycle().load_parent_driver().previous().foundation().runtime_delta.verify(root,manifest['after'])
    delta.update(source_commit=os.environ['GITHUB_SHA'],parent_source_hashes=before,
                 exact_three_file_delta_verified=True)
    save(ROOT/'checkpoint-build/RAILS-NATIVE-DELTA.json',delta)
    import test_native
    test_native.verify(root,ROOT/'checkpoint-build')

def compile_engine():
    parent=previous();parent.verify_source();parent.compile_engine()
    build=ROOT/'checkpoint-build'
    proof=read(build/'ENGINE-PROOF.json')
    binary=(build/'libkodi.so').read_bytes()
    assert b'Infinity Rails hold: control=' in binary
    assert b'RunScript(script.infinity.rails,options,' in binary
    assert proof['complete_native_engine_compiled']
    assert proof['rc5_17_required_save_owners_unchanged']
    proof.update(rails_native_hold_compiled=True,rails_source_commit=os.environ['GITHUB_SHA'],
                 rails_physical_fold_accepted=False,locked=False)
    save(build/'ENGINE-PROOF.json',proof)

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mode',choices=['prepare','compile'])
    for name in ['locked','previous','parent-proof']:cli.add_argument('--'+name,type=Path)
    args=cli.parse_args()
    if args.mode=='prepare':prepare(args)
    else:compile_engine()
