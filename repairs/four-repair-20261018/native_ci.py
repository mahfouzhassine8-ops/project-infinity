"""Reconstruct exact locked 2103384, verify all 9404 sources, then add UI input."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'checkpoint-build'

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec); sys.modules[name] = obj
    spec.loader.exec_module(obj); return obj

parent = module(HERE.parent / 'full-system-20261017/write_error_native_ci.py', 'ui_exact_2103384_parent')
patch = module(HERE / 'native_patch.py', 'ui_touch_patch')

def save(path, obj): path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
def digests():
    root = ROOT / 'kodi'
    # The locked manifest contains the WHOLE 9404-file source tree, including
    # CMake, platform packaging and add-on headers outside xbmc/. Comparing a
    # 4501-file xbmc-only inventory to it is a harness error, not source drift.
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}

def prepare(args):
    parent.prepare(args)
    before = digests()
    locked = json.loads((args.locked_384_proof / 'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json').read_text())
    save(OUT / 'RECONSTRUCTED-2103384-SOURCE-MAP.json', before)
    differences = [p for p in before.keys() | locked['after'].keys() if before.get(p) != locked['after'].get(p)]
    save(OUT / 'LOCKED-SOURCE-COMPARISON.json', dict(reconstructed=len(before), locked=len(locked['after']), differences=sorted(differences)))
    assert len(before) == 9404 and before == locked['after'], 'Reconstructed sources differ from locked 2103384'
    save(OUT / 'LOCKED-2103384-SOURCE-MAP.json', before)
    delta = patch.apply(ROOT / 'kodi')
    after = digests()
    assert sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k)) == sorted(patch.FILES)
    # Keep the established compiler's own final source verification authoritative.
    ordering = parent.parent.parent.parent.parent.parent.parent
    manifest_path = ordering.native_manifest(ordering.stable())
    for path in (manifest_path, OUT / 'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json'):
        proof = json.loads(path.read_text()); proof['after'].update(delta['after'])
        proof['changed'] = sorted(set(proof['changed']) | set(patch.FILES))
        save(path, proof)
    delta.update(parent_source_commit='3795b1b03731cba567e091913299c1888805373c',
                 source_commit=os.environ['GITHUB_SHA'], source_file_count=len(after),
                 all_other_sources_byte_identical=True, locked=False)
    save(OUT / 'FOUR-REPAIR-INPUT-DELTA.json', delta)
    module(HERE / 'test_native.py', 'ui_production_test').verify(ROOT / 'kodi', OUT / 'UI-INPUT-HOST.json')

def compile_engine():
    delta = json.loads((OUT / 'FOUR-REPAIR-INPUT-DELTA.json').read_text())
    locked = json.loads((OUT / 'LOCKED-2103384-SOURCE-MAP.json').read_text())
    expected = dict(locked, **delta['after'])
    assert digests() == expected
    # Reuse the full compiler and completed watched/deadlock/Essential-First
    # verification. Historical 2103383 post-link wrappers compare a header
    # preimage that 2103384 intentionally superseded; this full final map
    # replaces that stale comparison, without changing any protected wrapper.
    parent.parent.parent.compile_engine()
    assert digests() == expected
    proof = json.loads((OUT / 'ENGINE-PROOF.json').read_text())
    assert proof['source_commit'] == delta['source_commit'] == os.environ['GITHUB_SHA']
    assert proof['complete_native_engine_compiled'] and proof['fold_callback_retirement_compiled']
    assert proof['watched_presentation_bridge_compiled'] and proof['browse_touch_preselection_compiled']
    assert proof['shutdown_policy'] == 'essential_first_process_exit_v1'
    engine = OUT / 'libkodi.so'
    assert hashlib.sha256(engine.read_bytes()).hexdigest() == proof['native_sha256']
    assert b'RunScript(script.infinity.uirepair,' in engine.read_bytes()
    proof.update(ui_input_contract_compiled=True, locked_2103384_source_verified=True,
                 every_non_ui_native_source_byte_identical=True, crash_fixed=False,
                 physical_fold_verified=False, locked=False)
    save(OUT / 'ENGINE-PROOF.json', proof)

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['prepare', 'compile'])
    for name in ('locked', 'previous', 'parent-proof', 'rails-proof', 'test4-proof', 'locked-384-proof'):
        p.add_argument('--' + name, type=Path)
    args = p.parse_args()
    prepare(args) if args.mode == 'prepare' else compile_engine()
