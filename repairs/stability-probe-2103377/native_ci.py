"""Reconstruct locked RC02, then stage bounded observations and full native build."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import patch_native,run_tests
def parent():
    p=ROOT/'repairs/rails-hold-2103378/native_ci.py';sys.path.insert(0,str(p.parent))
    spec=importlib.util.spec_from_file_location('locked_rails_native',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def prepare(args):
    p=parent();p.prepare(args);p.previous().verify_source();root=p.previous().source_root()
    # Full source manifest still covers every unchanged file, not just named gates.
    native_manifest=p.previous().rc3().import_rc2().wide().lifecycle().SCRATCH/'runtime/native/manifest.json'
    manifest=json.loads(native_manifest.read_text())
    before={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'xbmc').rglob('*') if f.is_file()}
    delta=patch_native.apply(root)
    after={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'xbmc').rglob('*') if f.is_file()}
    changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k));assert changed==delta['changed']
    manifest['after'].update(delta['after']);manifest['changed']=sorted(set(manifest['changed'])|set(changed));save(native_manifest,manifest)
    preservation=ROOT/'checkpoint-build/FINAL-SHUTDOWN-SOURCE-PRESERVATION.json'
    proof=json.loads(preservation.read_text());proof['after'].update(delta['after']);proof['changed']=sorted(set(proof['changed'])|set(changed));save(preservation,proof)
    delta.update(source_commit=os.environ['GITHUB_SHA'],parent_native_commit='99b3dd0c98b9991138163f4042b7f41825d1a23a',exact_delta_verified=True)
    save(ROOT/'checkpoint-build/STABILITY-PROBE-DELTA.json',delta)
    run_tests.verify(root,ROOT/'checkpoint-build/stability-probe-host')
    p.previous().verify_source()
def compile_engine():
    p=parent();p.compile_engine();build=ROOT/'checkpoint-build';proof=json.loads((build/'ENGINE-PROOF.json').read_text())
    assert proof['complete_native_engine_compiled'] and proof['rc5_17_required_save_owners_unchanged']
    proof.update(stability_probe_source_commit=os.environ['GITHUB_SHA'],observations_only=True,root_cause_fixed=False,physical_capture_required=True)
    save(build/'ENGINE-PROOF.json',proof)
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mode',choices=['prepare','compile'])
    for n in ['locked','previous','parent-proof']:cli.add_argument('--'+n,type=Path)
    args=cli.parse_args();prepare(args) if args.mode=='prepare' else compile_engine()
