#!/usr/bin/env python3
"""Compile targeted cooperative shutdown corrections on the exact green lineage."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import cooperative_abort
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shutdown-drain-2103377'))
import prune_optional_jobs

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'checkpoint-build'
LATEST_MAP='73792db364d0f8a1f802fb59aba7b28d3affb8f4ef4d487adabb6592cd86f112'
INVOKER='xbmc/interfaces/python/PythonInvoker.cpp'
INVOKER_SHA='38387c6eaa2839dc49d4f5eb2c15c714f8269f519b11a2db007b48f7784c3df2'
HEADER='xbmc/interfaces/python/InfinityServiceStartupWait.h'

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def digest(data):return hashlib.sha256(data).hexdigest()

def wide():
    folder=ROOT/'repairs/shutdown-wide-trace-2103377'
    sys.path.insert(0,str(folder))
    spec=importlib.util.spec_from_file_location('saved_wide_native',folder/'native_ci.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def prepare(args):
    saved=wide()
    original_run=saved.subprocess.run
    old_oracle=(ROOT/'repairs/shutdown-wide-trace-2103377/tests/verify_trace.py').resolve()
    def routed_run(argv,*positional,**keywords):
        if isinstance(argv,(list,tuple)) and len(argv)>1 and Path(argv[1]).resolve()==old_oracle:
            argv=[argv[0],str(HERE/'trace_oracle.py'),*argv[2:]]
        return original_run(argv,*positional,**keywords)
    saved.subprocess.run=routed_run
    try:
        saved.prepare(args)
    finally:
        saved.subprocess.run=original_run
    life=saved.lifecycle();source=life.SOURCE
    manifest_path=life.SCRATCH/'runtime/native/manifest.json'
    manifest=json.loads(manifest_path.read_text());before=manifest['after']
    assert len(before)==9393
    assert digest(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==LATEST_MAP
    assert before[INVOKER]==INVOKER_SHA and digest((source/INVOKER).read_bytes())==INVOKER_SHA
    subprocess.run([sys.executable,str(HERE/'test_cooperative_abort.py'),'--source',str(source),
                    '--out',str(OUT/'COOPERATIVE-ABORT-TESTS.json')],check=True)
    latch=cooperative_abort.apply(source,OUT/'COOPERATIVE-ABORT-SOURCE-DELTA.json')
    text=(source/INVOKER).read_text()
    text=cooperative_abort.once(text,'#include "PythonInvoker.h"\n',
        '#include "PythonInvoker.h"\n#if defined(TARGET_ANDROID)\n#include "InfinityServiceStartupWait.h"\n#endif\n')
    text=cooperative_abort.once(text,'  int m_Py_file_input = Py_file_input;',
        '  #if defined(TARGET_ANDROID)\n'
        '  if (InfinityServiceStartupWait::TryExecute(fp, script,\n'
        '      m_addon ? m_addon->ID() : std::string{}, moduleDict))\n'
        '    return;\n'
        '  #endif\n\n'
        '  int m_Py_file_input = Py_file_input;')
    (source/INVOKER).write_text(text)
    assert HEADER not in before and not (source/HEADER).exists()
    shutil.copyfile(HERE/Path(HEADER).name,source/HEADER)
    after=dict(before);after.update(latch['after'])
    after[INVOKER]=digest((source/INVOKER).read_bytes());after[HEADER]=digest((source/HEADER).read_bytes())
    rc2=prune_optional_jobs.apply(source)
    after.update(rc2['after'])
    changed=sorted(name for name in before if before[name]!=after[name])
    assert changed==sorted([*cooperative_abort.PINS,INVOKER,*rc2['changed']])
    write(OUT/'RC2-OPTIONAL-QUEUE-PRUNE.json',rc2)
    manifest.update(after=after,changed=sorted(set(manifest['changed'])|set(changed)),
                    added=sorted(set(manifest['added'])|{HEADER}))
    write(manifest_path,manifest)
    foundation=life.load_parent_driver().previous().foundation()
    foundation.runtime_delta.verify(source,after)
    host=json.loads((HERE/'STARTUP-WAIT-VERIFICATION.json').read_text())
    assert host['passed'] and host['actual_function_scenarios']==20 and host['source_guard_rejections']==12
    assert host['compiled_header_sha256']==digest((HERE/'InfinityServiceStartupWait.h').read_bytes())
    write(OUT/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json',{
        'source_commit':os.environ['GITHUB_SHA'],'before':before,'after':after,
        'changed':changed,'added':[HEADER],'unchanged_green_native_inputs':len(before)-len(changed),
        'save_and_termination_authority_byte_identical':True,
        'known_wait_source_hashes':{k:v['input_sha256'] for k,v in host['addons'].items()},
        'unknown_sources_retain_existing_behavior_and_writer_obligations':True,
        'in_process_threads_forcibly_killed':False,'shutdown_timeouts_changed':False,
        'playlist_browser_unchanged':True,'device_verified':False,
        'rc2_optional_queue_prune':rc2,
        'source_provenance':'rc2 exact three-file queue/pruning diff atop verified 2103377'})
    shutil.copyfile(HERE/'STARTUP-WAIT-VERIFICATION.json',OUT/'STARTUP-WAIT-VERIFICATION.json')

def compile_engine():
    saved=wide();saved.lifecycle().compile_engine()
    binary=(OUT/'libkodi.so').read_bytes()
    for token in [b'while waited < timeout and not',b'__import__(\'xbmc\').Monitor().waitForAbort(1)',
                  b'afcef67ec3552bf1aea81fa40825801dd8726f6ac9ec3c940fded868add215ce',
                  b'infinityPrepareNativeTask',b'capture.lane_limit',b'vfs.shutdown_operation_return']:
        assert token in binary,token
    proof=json.loads((OUT/'ENGINE-PROOF.json').read_text())
    assert b'jobs.optional_queued_pruned' in binary
    rc2=json.loads((OUT/'RC2-OPTIONAL-QUEUE-PRUNE.json').read_text())
    assert rc2['only_verified_optional_no_callback_queued']
    proof.update(purpose='Targeted cooperative shutdown repair test candidate',
                 final_shutdown_corrections_compiled=True,
                 checkpoint_monitor_abort_latched=True,
                 exact_loaded_byte_startup_wait_corrections=True,
                 original_shutdown_overflow_corrections_preserved=True,
                 original_save_and_termination_authority_preserved=True,
                 known_wait_addons=4, unknown_writers_abandoned=False,
                 native_entry_matches_saved_274_java=True,
                 in_process_threads_forcibly_killed=False,
                 shutdown_timeout_changed=False,
                 rc2_optional_queued_prune_compiled=True,
                 physical_shutdown_verified=False,
                 apk_packaged_or_signed=False,locked=False,device_accepted=False)
    write(OUT/'ENGINE-PROOF.json',proof)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','compile'])
    for name in ['locked','previous','parent-proof']:parser.add_argument('--'+name,type=Path)
    args=parser.parse_args();OUT.mkdir(exist_ok=True)
    if args.mode=='prepare':prepare(args)
    else:compile_engine()
