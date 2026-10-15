"""Full compile of diagnostic tracing; deliberately no shutdown-fix claim."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'checkpoint-build'
sys.path.insert(0,str(HERE))
import apply_trace

def lifecycle():
    spec=importlib.util.spec_from_file_location('saved_lifecycle',ROOT/'repairs/close-lifecycle-native-2103377/native_ci.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def prepare(args):
    saved=lifecycle();saved.prepare(args)
    path=saved.SCRATCH/'runtime/native/manifest.json'
    m=json.loads(path.read_text());before=m['after']
    after=apply_trace.apply(saved.SOURCE,before)
    m.update(after=after,changed=sorted(set(m['changed'])|set(apply_trace.FILES)),
             added=sorted(set(m['added'])|{apply_trace.HEADER}))
    write(path,m)
    foundation=saved.load_parent_driver().previous().foundation()
    foundation.runtime_delta.verify(saved.SOURCE,after)
    write(OUT/'VFS-TRACE-PRESERVATION.json',{
        'source_commit':os.environ['GITHUB_SHA'],'before':before,'after':after,
        'green_parent_manifest_sha256':apply_trace.GREEN_MAP_SHA,'changed':apply_trace.FILES,
        'added':[apply_trace.HEADER],'unchanged_green_inputs':len(before)-len(apply_trace.FILES),
        'observation_only':True,'shutdown_corrected':False,'device_verified':False,
        'saved_native_entry_wrapper_preserved':True})
    subprocess.run([sys.executable,str(HERE/'tests/verify_trace.py'),'--include',
                    str(saved.SOURCE/'xbmc/platform/android/activity'),'--out',str(OUT/'vfs-trace-tests')],check=True)
    # Pin all previously accepted candidate source/test bytes without rerunning
    # the unchanged 274-test checkpoint in this diagnostic-only job.
    accepted=json.loads((ROOT/'docs/verification/Infinity-2103377-Local-Android-274-20261013.json').read_text())
    for name,digest in accepted['provenance']['candidate_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    write(OUT/'SAVED-274-CANDIDATE-PRESERVATION.json',{
        'accepted_receipt':'12220187e6de5819651f7429bfdec43fcbaf3591',
        'candidate_files':accepted['provenance']['candidate_files'],
        'exact_hashes_preserved':True,'tests':274,'fresh_android_run_claimed':False,
        'diagnostic_apk_keeps_locked_2103376_dex':True})

def compile_engine():
    saved=lifecycle();saved.compile_engine()
    binary=(OUT/'libkodi.so').read_bytes()
    for token in [b'operation_start_monotonic_ns',b'vfs.shutdown.request',b'curl_cancel_callback_observed',b'vfs.python.interpreter_retired']:
        assert token in binary,token
    p=OUT/'ENGINE-PROOF.json';proof=json.loads(p.read_text())
    proof.update(purpose='Explicit VFS observation diagnostic; actual shutdown correction unresolved',
                 vfs_trace_header_sha256=hashlib.sha256((HERE/'InfinityVfsOpenTrace.h').read_bytes()).hexdigest(),
                 vfs_trace_compiled=True,observation_only=True,shutdown_corrected=False,
                 diagnostic_uses_locked_java=True,final_2103377_repair=False)
    write(p,proof)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','compile'])
    for name in ['locked','previous','parent-proof']:p.add_argument('--'+name,type=Path)
    a=p.parse_args();OUT.mkdir(exist_ok=True)
    if a.mode=='prepare':prepare(a)
    else:compile_engine()
