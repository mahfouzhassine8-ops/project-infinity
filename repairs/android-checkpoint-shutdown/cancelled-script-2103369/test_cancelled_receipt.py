#!/usr/bin/env python3
"""Production observer/ledger under real CPython; compare old cancellation gap.

No cancellation-only receipt, writer whitelist, native shutdown or live user data.
The early attach block is extracted from the actual CPythonInvoker source.
"""
import argparse
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import sysconfig
import tempfile

HARNESS=r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <iostream>

int main(int argc,char** argv) {
  assert(argc==3);
  const std::string mode=argv[1];
  Py_Initialize();
  auto* main=PyThreadState_Get();auto* owner=Py_NewInterpreter();assert(owner);
  const int id=54;
  InfinityScriptPersistence::Admit(id,"plugin.program.iagl:addon.py");
  PyThreadState* m_threadState=owner;
  void* m_infinityPersistenceObserver=nullptr;
  auto GetId=[](){return 54;};
  // The production pre-bytecode observer block (or no block in old source).
  __EARLY_ATTACH__
  const bool stopping=mode=="cancelled" || mode=="old-gap";
  const bool fileOpened=mode!="missing-file";
  if(!stopping && fileOpened) {
    // Stock 2103368 attaches only here. Repaired source has one early attach.
    __LATE_ATTACH__
  }
  auto* context=static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver);
  if(mode=="old-gap") {
    assert(context==nullptr);
    auto* interpreter=owner->interp;
    Py_EndInterpreter(owner);InfinityPythonPersistence::End(context,interpreter);
    PyThreadState_Swap(main);
    assert(InfinityScriptPersistence::Pending(id));
    assert(!InfinityScriptPersistence::TakeInterpreterRetirement(id));
    std::cout<<"REPRODUCED: interpreter ended; admitted cancelled writer has no retirement receipt\n";
    Py_FinalizeEx();return 0;
  }
  assert(context);
  PyObject* globals=PyDict_New();
  PyDict_SetItemString(globals,"__builtins__",PyEval_GetBuiltins());
  PyObject* directory=PyUnicode_FromString(argv[2]);
  PyDict_SetItemString(globals,"directory",directory);Py_DECREF(directory);
  const char* code="pass";
  if(mode=="checked-write")code="import os\np=os.path.join(directory,'saved.xml')\nf=open(p,'w');f.write('saved');f.close()\n";
  if(mode=="pending-transaction")code="import sqlite3,os\nc=sqlite3.connect(os.path.join(directory,'state.db'))\nc.execute('CREATE TABLE t(v)');c.commit()\nc.execute('INSERT INTO t VALUES(42)')\n";
  if(mode=="opaque-writer")code="import ctypes\nctypes.CDLL('/definitely-unreviewed-native-writer.so')\n";
  if(!stopping && fileOpened) {
    auto* result=PyRun_String(code,Py_file_input,globals,globals);
    if(result)Py_DECREF(result);else PyErr_Clear();
  }
  if(mode=="observer-error")PyErr_SetString(PyExc_RuntimeError,"injected finalization failure");
  InfinityPythonPersistence::Finish(context,owner);
  if(PyErr_Occurred())PyErr_Clear();
  const bool mustBlock=mode=="pending-transaction" || mode=="opaque-writer" || mode=="observer-error";
  if(mustBlock) {
    assert(!context->finalized || !InfinityScriptPersistence::Failure().empty());
    assert(InfinityScriptPersistence::Pending(id));
    assert(!InfinityScriptPersistence::TakeInterpreterRetirement(id));
  } else {
    assert(context->finalized);
    // Finalized observer alone is insufficient. Actual interpreter retirement follows.
    assert(InfinityScriptPersistence::Pending(id));
    assert(!InfinityScriptPersistence::TakeInterpreterRetirement(id));
  }
  Py_DECREF(globals);
  auto* interpreter=owner->interp;
  // For blocked cases this is test teardown, not authorized normal shutdown.
  Py_EndInterpreter(owner);InfinityPythonPersistence::End(context,interpreter);
  PyThreadState_Swap(main);
  if(mustBlock) {
    assert(!InfinityScriptPersistence::TakeInterpreterRetirement(id));
    assert(!InfinityScriptPersistence::DurableRetirement("plugin.program.iagl:addon.py"));
  } else {
    assert(!InfinityScriptPersistence::Pending(id));
    assert(InfinityScriptPersistence::TakeInterpreterRetirement(id));
    assert(!InfinityScriptPersistence::TakeInterpreterRetirement(id));
    assert(InfinityScriptPersistence::DurableRetirement("plugin.program.iagl:addon.py"));
  }
  std::cout<<"PASS "<<mode<<" proof="<<(mustBlock?"blocked":"checked-retirement")<<"\n";
  Py_FinalizeEx();
}
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--expect-old-gap',action='store_true');parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    invoker=(args.runtime/'xbmc/interfaces/python/PythonInvoker.cpp').read_text()
    call='m_infinityPersistenceObserver = InfinityPythonPersistence::Start(GetId(), m_threadState->interp);'
    assert invoker.count(call)==1
    before=invoker.index(call)<invoker.index('// we need to check if we was asked to abort')
    if args.expect_old_gap:assert not before
    else:
        assert before
        assert invoker.index(call)<invoker.index('_Py_fopen_obj(pyRealFilename')
        assert invoker.index('m_threadState = l_threadState')<invoker.index(call)
        assert invoker.index('onInitialization();')<invoker.index(call)
    # Extract exactly the shipped attach statement, preserving the production call.
    early=call if before else ''
    late='' if before else call
    source=HARNESS.replace('__EARLY_ATTACH__',early).replace('__LATE_ATTACH__',late)
    modes=['old-gap'] if args.expect_old_gap else ['cancelled','missing-file','normal-readonly','checked-write','pending-transaction','opaque-writer','observer-error']
    include=Path(sysconfig.get_path('include'));libfolder=Path(sysconfig.get_config_var('LIBDIR'))
    library=libfolder/sysconfig.get_config_var('LDLIBRARY')
    if not library.exists():library=libfolder/(sysconfig.get_config_var('LDLIBRARY')+'.1.0')
    if not library.exists():libfolder=Path(sys.prefix)/'lib';library=libfolder/sysconfig.get_config_var('LDLIBRARY')
    if not library.exists():library=libfolder/(sysconfig.get_config_var('LDLIBRARY')+'.1.0')
    assert library.exists()
    results=[]
    with tempfile.TemporaryDirectory(prefix='cancelled-native-proof-') as d:
        d=Path(d);cpp=d/'test.cpp';cpp.write_text(source);binary=d/'test'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-I',str(include),'-I',str(args.runtime/'xbmc'),
            '-I',str(args.runtime/'xbmc/interfaces/python'),str(cpp),str(library),'-ldl','-lm','-lcrypto','-o',str(binary)],check=True)
        env=dict(os.environ,PYTHONHOME=sys.prefix,LD_LIBRARY_PATH=str(libfolder))
        for mode in modes:
            folder=d/mode;folder.mkdir()
            process=subprocess.run([str(binary),mode,str(folder)],env=env,text=True,capture_output=True,timeout=20)
            print(process.stdout,end='')
            if process.returncode:print(process.stderr,file=sys.stderr)
            assert process.returncode==0,(mode,process.returncode)
            results.append({'case':mode,'passed':True,'detail':process.stdout.strip()})
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps({'scope':'Actual production observer/ledger and extracted attach placement; host CPython, not Galaxy Fold acceptance.','old_source_reproduction':args.expect_old_gap,'cases':results},indent=2)+'\n')

if __name__=='__main__':main()
