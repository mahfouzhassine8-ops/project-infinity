#!/usr/bin/env python3
"""Host checks for the source-only diagnostic; needs Python 3.9+, g++, and git.

Kodi/CPython/Android runtime boundaries are stubs. These checks are not a native
Android build, a historical PID 32099 reproduction, or device acceptance.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import platform
import shutil
import sys
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepare_delta',ROOT/'prepare_delta.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def without_new_android_blocks(text: str) -> list[str]:
    lines=[];skipping=False
    for line in text.splitlines():
        if line=='#if defined(TARGET_ANDROID)':
            if skipping: raise ValueError('Unexpected nested diagnostic guard')
            skipping=True;continue
        if skipping:
            if line=='#endif':skipping=False
            continue
        if line.strip():lines.append(line.rstrip())
    if skipping:raise ValueError('Unclosed diagnostic guard')
    return lines

def run_checks() -> dict:
    if not sys.platform.startswith('linux'):
        raise RuntimeError('These native host tests require Linux (SYS_gettid); this is not a macOS or phone installer')
    compiler=shutil.which('g++');git=shutil.which('git')
    if not compiler or not git:raise RuntimeError('g++ and git must be installed for host tests')
    result={'schema':1,'kind':'HOST_ONLY_DIAGNOSTIC_TESTS','platform':platform.platform(),
            'python':platform.python_version(),'android_cross_compile':False,
            'physical_device_tested':False,'historical_anr_reproduced':False,
            'root_cause_fixed':False,'checks':[],'host_runs':[]}
    def add(name):result['checks'].append({'name':name,'passed':True})
    with tempfile.TemporaryDirectory(prefix='infinity-diagnostic-test-') as tmp:
        work=Path(tmp);parent=work/'parent';shutil.copytree(ROOT/'parent',parent)
        prepared=work/'prepared';receipt=module.prepare(parent,prepared)
        if not receipt['original_tree_unchanged']:raise AssertionError('Parent tree changed')
        add('exact_two_file_parent_hashes_and_source_tree_unchanged')
        for name in module.EXPECTED:
            a=(parent/name).read_text();b=(prepared/name).read_text()
            if without_new_android_blocks(b)!=[line.rstrip() for line in a.splitlines() if line.strip()]:
                raise AssertionError('Original nonblank source lines changed: '+name)
        add('all_original_nonblank_source_lines_preserved_in_order')
        # Wrong source is refused before creating any prepared output.
        broken=work/'wrong-parent';shutil.copytree(parent,broken)
        p=broken/module.CPP;p.write_bytes(p.read_bytes()+b'\n// drift\n')
        try: module.prepare(broken,work/'must-not-exist')
        except ValueError: pass
        else: raise AssertionError('Wrong parent accepted')
        if (work/'must-not-exist').exists():raise AssertionError('Output created for wrong source')
        add('wrong_parent_refused_before_output_creation')
        try: module.prepare(parent,prepared)
        except FileExistsError: pass
        else: raise AssertionError('Overwrite accepted')
        try: module.prepare(parent,parent/'nested')
        except ValueError: pass
        else: raise AssertionError('Nested output accepted')
        add('existing_output_and_source_nested_output_refused')
        applytree=work/'patch-check';shutil.copytree(parent,applytree)
        subprocess.run([git,'apply','--check',str(prepared/'diagnostic-only.patch')],cwd=applytree,check=True,timeout=10,capture_output=True)
        subprocess.run([git,'apply',str(prepared/'diagnostic-only.patch')],cwd=applytree,check=True,timeout=10,capture_output=True)
        for name in receipt['after']:
            if (applytree/name).read_bytes()!=(prepared/name).read_bytes():raise AssertionError('Patch output mismatch')
        add('git_apply_exact_round_trip_in_temporary_tree')
        generic=prepared/'xbmc/interfaces/generic';stubs=ROOT/'tests/stubs'
        flags=[compiler,'-std=c++17','-Wall','-Wextra','-Werror','-O1','-pthread','-I'+str(generic),'-I'+str(stubs)]
        result['compiler']=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]
        cmd=flags+['-DTARGET_ANDROID',str(generic/'LanguageInvokerThread.cpp'),str(ROOT/'tests/test_target.cpp'),'-o',str(work/'test-target')]
        built=subprocess.run(cmd,capture_output=True,text=True,timeout=45,check=True)
        result['compile_output']=built.stdout+built.stderr
        add('actual_transformed_cpp_compiles_with_android_guard_and_mocked_boundaries')
        for index in range(3):
            tested=subprocess.run([str(work/'test-target')],capture_output=True,text=True,timeout=20,check=True)
            if tested.stdout.count('PASS ')!=8:raise AssertionError('Unexpected scenario count')
            result['host_runs'].append({'iteration':index+1,'exit_code':tested.returncode,'stdout':tested.stdout,'stderr':tested.stderr})
        add('eight_real_host_thread_scenarios_pass_three_repetitions')
        subprocess.run(flags+['-c',str(generic/'LanguageInvokerThread.cpp'),'-o',str(work/'nonandroid.o')],capture_output=True,text=True,timeout=45,check=True)
        add('non_android_guard_path_compiles_with_mocked_boundaries')
        # The inherited critical-stream predicate selects scripts.* by prefix.
        if not all(p.startswith('scripts.') for p in receipt['new_trace_phases']):raise AssertionError('Wrong phase class')
        add('new_phases_use_existing_scripts_critical_stream_prefix')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'HOST-TEST-RESULTS.json')
    args=parser.parse_args()
    try:result=run_checks()
    except (OSError,RuntimeError,ValueError,AssertionError,subprocess.SubprocessError) as error:
        parser.exit(1,f'FAILED: {error}\n')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks_passed':len(result['checks']),'scenarios_per_run':8,'repetitions':3,
                     'host_only':True,'result':str(args.out)},indent=2))
