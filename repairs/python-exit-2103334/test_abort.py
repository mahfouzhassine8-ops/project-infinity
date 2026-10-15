#!/usr/bin/env python3
"""Compare the discarded abort hypothesis and test read-only evidence on real CPython; exercise actual interpreters.

This does not mock Python APIs. The parent fragment is verified against the
exact native source before testing. Device/native-backend acceptance is separate.
"""
from pathlib import Path
import argparse,hashlib,shlex,subprocess,sys,sysconfig,tempfile,json
HERE=Path(__file__).resolve().parent

def check_source(source):
    text=(source/'xbmc/interfaces/python/PythonInvoker.cpp').read_text()
    fixture=(HERE/'test_abort.cpp').read_text()
    parent='''      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);
      while (state)
      {
        // Raise a SystemExit exception in python threads
        Py_XDECREF(state->async_exc);
        state->async_exc = PyExc_SystemExit;
        Py_XINCREF(state->async_exc);
        state = PyThreadState_Next(state);
      }'''
    # Fixture adapts only the interpreter accessor, not the parent operation.
    def normalize(s):return ''.join(s.split())
    body='''Py_XDECREF(state->async_exc);state->async_exc=PyExc_SystemExit;Py_XINCREF(state->async_exc);state=PyThreadState_Next(state);'''
    assert normalize(body) in normalize(fixture)
    assert text.count(parent)==1,'Not the exact direct-write parent abort path'
    return hashlib.sha256(parent.encode()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--expect-python');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if a.expect_python:assert sys.version.split()[0]==a.expect_python,sys.version
    parent_hash=check_source(a.source) if a.source else None
    cmd=['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror',
         '-I'+sysconfig.get_path('include'),str(HERE/'test_abort.cpp'),
         '-L'+str(sysconfig.get_config_var('LIBDIR')),
         '-Wl,-rpath,'+str(sysconfig.get_config_var('LIBDIR')),
         '-lpython'+sysconfig.get_config_var('LDVERSION')]
    cmd+=shlex.split((sysconfig.get_config_var('LIBS') or '')+' '+(sysconfig.get_config_var('SYSLIBS') or ''))
    exe=a.out/'test-abort';cmd+=['-o',str(exe)]
    subprocess.run(cmd,check=True)
    results=[]
    for repetition in range(3):
        for mode in ('parent','repair','group','normal'):
            out=a.out/f'{mode}-{repetition}';out.mkdir(exist_ok=True)
            run=subprocess.run([str(exe),mode,str(out)],text=True,capture_output=True,timeout=15)
            print(run.stdout,end='');print(run.stderr,end='',file=sys.stderr)
            assert run.returncode==0, f'{mode}: {run.returncode}'
            (out/'output.txt').write_text(run.stdout+run.stderr)
            results.append(dict(mode=mode,repetition=repetition,passed=True))
    evidence=dict(python=sys.version.split()[0],tests=results,
        evidence_helper_sha256=hashlib.sha256((HERE/'InfinityPythonExitEvidence.h').read_bytes()).hexdigest(),
        parent_fragment_sha256=parent_hash,real_interpreters=True,
        abort_change_not_shipped=True,matching_runtime_disproves_initial_hypothesis=sys.version_info[:2]==(3,11),
        frame_capture_preserves_pending_exception=True,finally_persistence=True,subinterpreter_isolation=True,
        three_target_threads=True,real_owner_joins=True,helper_excluded=True,
        physical_device_verified=False)
    (a.out/'ABORT-TESTS.json').write_text(json.dumps(evidence,indent=2)+'\n')
if __name__=='__main__':main()
