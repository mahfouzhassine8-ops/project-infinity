#!/usr/bin/env python3
"""Real pinned CPython failure-path experiment, not an Android/Fold reproduction."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import sysconfig
import tempfile

HERE=Path(__file__).resolve().parent
PREFIX=r'''
#include <Python.h>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>
#include "interfaces/generic/InfinityStartupTrace.h"
constexpr int LOGERROR=1;
struct CLog{template<class...T>static void Log(T...){}template<class...T>static void LogF(T...) {}};
namespace InfinityScriptPersistence{inline void InitializationProgress(int,const char*,uint64_t=0){}}
inline int GetId(){return 42;}
static bool deny=false,denialObserved=false;
static int audit(const char* event,PyObject*,void*){
 if(deny && std::strcmp(event,"cpython.PyInterpreterState_New")==0){
   deny=false;denialObserved=true;PyErr_SetString(PyExc_RuntimeError,"controlled_host_initialization_denial");return -1;
 }return 0;
}
static PyThreadState* checkedNew(PyThreadState* expected){
 auto* result=Py_NewInterpreter(); // Real pinned API, never a fabricated NULL.
 if(!result){
   assert(denialObserved && PyThreadState_Get()==expected);
   assert(PyErr_ExceptionMatches(PyExc_RuntimeError));
   std::cout<<"audit_denial_and_retained_current_state_verified\n"<<std::flush;
 }return result;
}
static bool create(PyThreadState* owner,PyThreadState*& l_threadState,PyThreadState*& m_mainThreadState){
 bool m_invokerOwnsGil=false,newInterp=false;std::string m_sourceFile="host-fixture";
'''
SUFFIX=r'''
 (void)m_invokerOwnsGil;(void)newInterp;return true;
}
int main(int argc,char** argv){
 assert(argc==2);const std::string mode=argv[1];
 assert(std::strncmp(Py_GetVersion(),"3.11.7 ",7)==0);
 InfinityStartupTrace::hostInfinity=true;
 std::atomic<bool> stop{false};
 std::thread observer([&]{while(!stop){
   InfinityStartupTrace::Drain([](const InfinityStartupTrace::Event& e){
     std::cout<<InfinityStartupTrace::Name(e.stage)<<"\n"<<std::flush;
   });std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }});
 Py_Initialize();auto* main=PyThreadState_Get();assert(PySys_AddAuditHook(audit,nullptr)==0);
 if(mode=="denied"){
   deny=true;PyEval_SaveThread();PyThreadState *child=nullptr,*temporary=nullptr;
   const bool result=create(main,child,temporary);
   assert(!result && !child && !temporary);
   PyEval_RestoreThread(main);
   std::cout<<"controlled_failure_returned\n"<<std::flush;
 }
 // Real successful interpreter initialization and bytecode, repeated in one process.
 for(int i=0;i<3;++i){
   PyEval_SaveThread();PyThreadState *child=nullptr,*temporary=nullptr;
   assert(create(main,child,temporary));assert(child && temporary);
   PyEval_RestoreThread(child);assert(PyRun_SimpleString("assert sum([1, 2, 3]) == 6")==0);
   Py_EndInterpreter(child);PyThreadState_Swap(temporary);
   PyThreadState_Clear(temporary);PyThreadState_DeleteCurrent();PyEval_RestoreThread(main);
 }
 // Independent Python-thread progress after the tested cleanup.
 auto* next=PyThreadState_New(main->interp);assert(next);PyEval_SaveThread();
 std::thread python([&]{PyEval_RestoreThread(next);assert(PyRun_SimpleString("assert 7 * 6 == 42")==0);PyEval_SaveThread();});
 python.join();PyEval_RestoreThread(main);PyThreadState_Clear(next);PyThreadState_Delete(next);
 Py_Finalize();stop=true;observer.join();
 InfinityStartupTrace::Drain([](const InfinityStartupTrace::Event& e){std::cout<<InfinityStartupTrace::Name(e.stage)<<"\n";});
 std::cout<<"three_interpreters_and_independent_thread_passed\n";
}
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert sys.version_info[:3]==(3,11,7), 'Pinned CPython3.11.7 required; no version substitution'
    source=(HERE/'native/overlay/xbmc/interfaces/python/PythonInvoker.cpp').read_text()
    start=source.index('      m_mainThreadState = PyThreadState_New(owner->interp);')
    end=source.index('      newInterp = true;',start)+len('      newInterp = true;')
    original=source[start:end]
    redundant='        PyEval_RestoreThread(m_mainThreadState);\n        m_invokerOwnsGil = true;\n'
    assert original.count(redundant)==1
    comparison=original.replace(redundant,'',1)
    include=sysconfig.get_path('include');libdir=sysconfig.get_config_var('LIBDIR')
    results=[]
    with tempfile.TemporaryDirectory(prefix='infinity-py311-init-') as tmp:
        tmp=Path(tmp)
        for variant,block in [('unchanged_cleanup',original),('host_only_cleanup_comparison',comparison)]:
            assert block.count('l_threadState = Py_NewInterpreter();')==1
            observed=block.replace('l_threadState = Py_NewInterpreter();','l_threadState = checkedNew(m_mainThreadState);',1)
            cpp=tmp/(variant+'.cpp');cpp.write_text(PREFIX+observed+SUFFIX);binary=tmp/variant
            subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-DINFINITY_STARTUP_TRACE_QA','-DINFINITY_STARTUP_TRACE_HOST','-Wall','-Wextra','-Werror','-pthread','-I'+str(HERE/'native/overlay/xbmc'),'-I'+include,str(cpp),'-L'+libdir,'-Wl,-rpath,'+libdir,'-lpython3.11','-ldl','-lm','-o',str(binary)],check=True,timeout=60)
            for mode in ('success','denied'):
                try:
                    r=subprocess.run([str(binary),mode],capture_output=True,text=True,timeout=5)
                except subprocess.TimeoutExpired as e:
                    output=e.stdout.decode() if isinstance(e.stdout,bytes) else e.stdout or ''
                    assert variant=='unchanged_cleanup' and mode=='denied' and 'interpreter.failed' in output and 'audit_denial_and_retained_current_state_verified' in output,output
                    results.append(dict(variant=variant,case=mode,result='EXPECTED_BASELINE_SELF_DEADLOCK',trace=output.splitlines(),parent_killed_host_child=True))
                    continue
                assert r.returncode==0,(variant,mode,r.returncode,r.stderr,r.stdout)
                assert not (variant=='unchanged_cleanup' and mode=='denied'),'baseline defect did not reproduce'
                assert 'three_interpreters_and_independent_thread_passed' in r.stdout
                results.append(dict(variant=variant,case=mode,result='PASS_CONTROLLED_CPYTHON_EXECUTION',trace=r.stdout.splitlines(),parent_killed_host_child=False))
    report=dict(python=sys.version,source_block_sha256=hashlib.sha256(original.encode()).hexdigest(),
                controlled_trigger='Host-only native audit rejection of cpython.PyInterpreterState_New; not present in deployed observer',
                results=results,fold_failure_reproduced=False,production_cleanup_changed=False,
                conclusion='Real NULL-return self-deadlock reproduced; host-only two-line cleanup comparison restores progress; Fold attribution unresolved')
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
