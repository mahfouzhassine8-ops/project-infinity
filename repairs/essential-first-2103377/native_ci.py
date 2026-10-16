#!/usr/bin/env python3
"""Full ARM64 compile of the shutdown-only delta, without APK release authority."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT/'checkpoint-build'

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value

parent = module(ROOT/'repairs/rails-handoff-2103377/native_ci.py', 'essential_locked_rails_parent')
# Parent loaders use their own import paths. Bind this patch by an exact path.
patch = module(HERE/'apply_runtime.py', 'essential_runtime_patch')

def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def prepare(args):
    parent.prepare(args)  # All original lineage checks execute before this delta.
    source = ROOT/'kodi'
    preservation = OUT/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json'
    original = json.loads(preservation.read_text())
    published = json.loads((args.rails_proof/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json').read_text())
    assert original['after'] == published['after'], 'Not the complete locked Rails Handoff RC1 source map'
    save(OUT/'LOCKED-RAILS-SOURCE-PRESERVATION.json', original)
    delta = patch.apply(source, preservation)
    manifest_path = parent.parent.native_manifest(parent.parent.stable())
    manifest = json.loads(manifest_path.read_text())
    manifest['after'].update(delta['after'])
    manifest['changed'] = sorted(set(manifest['changed']) | set(delta['changed']))
    manifest['added'] = sorted(set(manifest.get('added', [])) | (set(delta['after'])-set(delta['before'])))
    save(manifest_path, manifest)
    original['after'].update(delta['after'])
    original['changed'] = sorted(set(original['changed']) | set(delta['changed']))
    original.update(all_17_required_checkpoint_owners_byte_identical=False,
        final_termination_authorization_byte_identical=False,
        final_required_save_and_database_seal_stages_byte_identical=False,
        diagnostic_owners_retained=17,essential_owners_required=16,
        optional_retirement_required=False,physical_device_verified=False,locked=False)
    save(preservation, original)
    delta.update(source_commit=os.environ.get('GITHUB_SHA','local'),
                 locked_commit='7d3aca64b34d00520908cf4afd531a4687124525')
    save(OUT/'ESSENTIAL-FIRST-SOURCE-DELTA.json', delta)
    print('Staged shutdown-only production adapters; all unrelated locked source hashes retained.',flush=True)

def compile_engine():
    # The original complete compiler and dependency verification are reused.
    # Higher historical wrappers assert mandatory 17/17 retirement, which is
    # intentionally superseded by the user-approved essential-first policy.
    life = module(ROOT/'repairs/close-lifecycle-native-2103377/native_ci.py','essential_native_compiler')
    life.compile_engine()
    path = OUT/'ENGINE-PROOF.json'
    proof = json.loads(path.read_text())
    binary = (OUT/'libkodi.so').read_bytes()
    for token in (b'essential_first_process_exit_v1', b'protected_write_seal_not_durable',
                  b'sqlite.vfs.write', b'Infinity protected write admission is closed',
                  b'Infinity Rails hold: control=', b'Infinity rails: stale job discarded',
                  b'python.runtime.threading_shutdown.complete', b'python_persistence_observer_initialization',
                  b'application_startup_initialization_failed'):
        assert token in binary, token
    assert hashlib.sha256(binary).hexdigest() == proof['native_sha256']
    proof.update(purpose='Essential-first shutdown production integration; not an accepted APK',
                 shutdown_policy='essential_first_process_exit_v1',
                 diagnostic_owners=17,essential_owners=16,optional_retirement_required=False,
                 android_validator_must_be_recompiled=True,
                 android_process_death_verified=False,apk_deliverable=False,locked=False)
    save(path, proof)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['prepare','compile'])
    for name in ('locked','previous','parent-proof','rails-proof'):
        p.add_argument('--'+name, type=Path)
    args = p.parse_args()
    if args.mode == 'prepare': prepare(args)
    else: compile_engine()
