#!/usr/bin/env python3
"""Compile native audit + ledger against an actual CPython subinterpreter."""
import argparse
import os
import re
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

HARNESS = r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <chrono>
#include <iostream>
int main(int argc,char** argv) {
  assert(argc==3);
  const std::string mode=argv[1];
  Py_Initialize();auto* main=PyThreadState_Get();auto* owner=Py_NewInterpreter();
  assert(owner);
  InfinityScriptPersistence::Admit(1,"provider:service.py");
  assert(PyRun_SimpleString("import _io\ncached_raw_open = _io.open\n")==0);
  auto* context=InfinityPythonPersistence::Start(1,owner->interp);
  if(PyErr_Occurred())PyErr_Print();
  assert(context && InfinityScriptPersistence::Failure().empty());
  PyErr_SetString(PyExc_RuntimeError,"pending caller exception");
  auto* evidencePath=PyUnicode_FromString("/diagnostic-only");
  const auto diagnostic=InfinityPythonPersistence::OpenEvidence(evidencePath,O_WRONLY);
  Py_DECREF(evidencePath);
  assert(PyErr_ExceptionMatches(PyExc_RuntimeError) && diagnostic.find("/diagnostic-only")!=std::string::npos);
  PyErr_Clear();
  auto* root=PyUnicode_FromString(argv[2]);
  PyDict_SetItemString(PyModule_GetDict(PyImport_AddModule("__main__")),"root",root);Py_DECREF(root);
  const char* script=nullptr;
  if(mode=="committed")script="import sqlite3\nc=sqlite3.connect(root+'/state.db')\nc.execute('create table state (value)')\nc.execute('insert into state values (42)')\nc.commit()\nc.close()\nf=open(root+'/state.json','w');f.write('saved')\n";
  if(mode=="pending")script="import sqlite3\nc=sqlite3.connect(root+'/state.db')\nc.execute('create table state (value)')\nc.execute('insert into state values (42)')\n";
  if(mode=="raw-open")script="import _io\nf=cached_raw_open(root+'/raw.json','w');f.write('saved');f.close()\n";
  if(mode=="layered-raw")script="import io\nr=io.FileIO(root+'/layered.txt','w')\nb=io.BufferedWriter(r)\nf=io.TextIOWrapper(b)\nf.write('saved layers')\n";
  if(mode=="layered-failure")script="import io\nr=io.FileIO('/dev/full','w')\nb=io.BufferedWriter(r)\nf=io.TextIOWrapper(b)\nf.write('unsaved layers')\n";
  if(mode=="checked-raw")script="import _io\nf=_io.open(root+'/raw.json','w');f.write('saved')\nf.close()\nr=_io.FileIO(root+'/raw.bin','w');r.write(b'raw');r.close()\n";
  if(mode=="raw-write-failure")script="import _io\nr=_io.FileIO('/dev/full','w')\ntry: r.write(b'unsaved')\nexcept OSError: pass\nr.close()\n";
  if(mode=="import-cache")script="with open(root+'/fresh.py','w') as f: f.write('answer=42\\n')\nimport sys\nsys.path.insert(0,root)\nimport fresh\nassert fresh.answer==42\n";
  if(mode=="direct-sqlite")script="import _sqlite3\nc=_sqlite3.connect(root+'/direct.db');c.close()\n";
  if(mode=="external")script="import subprocess\nsubprocess.run(['/bin/true'],check=True)\n";
  if(mode=="workers")script="import threading\ne=threading.Event()\nt=threading.Thread(target=e.wait);t.start()\n";
  if(mode=="nested")script="from pathlib import Path\np=Path(root)/'health'/'sessions'/'session'/'state.json'\np.parent.mkdir(parents=True,exist_ok=True)\np.write_text('saved')\n";
  if(mode=="readonly-child")script="import subprocess,tempfile\nwith tempfile.TemporaryFile(dir=root) as output:\n subprocess.run(['/bin/echo','infinity-diagnostic-fixture'],stdout=output,stderr=subprocess.PIPE,check=True)\n output.seek(0)\n result=output.read()\nwith open(root+'/diagnostic.txt','wb') as f: f.write(result)\n";
  if(mode=="system-exit" || mode=="system-exit-pending" || mode=="abort-callback-error") {
    script=mode=="system-exit-pending" ?
      "import sqlite3\nc=sqlite3.connect(root+'/state.db')\nc.execute('create table state (value)')\nc.execute('insert into state values (42)')\nraise SystemExit\n" :
      "f=open(root+'/state.json','w');f.write('saved')\nraise SystemExit\n";
    auto* globals=PyModule_GetDict(PyImport_AddModule("__main__"));
    auto* executed=PyRun_String(script,Py_file_input,globals,globals);
    assert(!executed && PyErr_ExceptionMatches(PyExc_SystemExit));
    HandleProductionAbort(mode=="abort-callback-error");
    if(mode=="abort-callback-error") {
      assert(PyErr_ExceptionMatches(PyExc_RuntimeError));
      InfinityScriptPersistence::Fail(1,"python_cleanup_failed_before_save_retirement");
      PyErr_Clear();
    } else assert(!PyErr_Occurred());
  } else assert(script && PyRun_SimpleString(script)==0);
  InfinityPythonPersistence::Finish(context,owner);
  if(PyErr_Occurred())PyErr_Print();
  if(mode=="layered-failure") {
    assert(context->preservePending && !context->finalized);
    assert(PyRun_SimpleString("assert not f.closed and not b.closed and not r.closed\n")==0);
  }
  if(mode=="layered-raw") {
    assert(PyRun_SimpleString("assert f.closed and b.closed and r.closed\nassert open(root+'/layered.txt').read()=='saved layers'\n")==0);
  }
  if(mode=="pending" || mode=="system-exit-pending") {
    assert(context->preservePending && !context->finalized);
    assert(!InfinityScriptPersistence::PollCommit());
    assert(!InfinityScriptPersistence::Failure().empty());
    assert(PyRun_SimpleString("assert c.in_transaction\nassert c.execute('select value from state').fetchall()==[(42,)]\nc.rollback()\nc.close()\n")==0);
    // Explicit test cleanup does not grant a receipt for the failed session.
  }
  if(mode=="workers") {
    assert(context->waitingWorkers && !context->finalized);
    assert(InfinityScriptPersistence::Failure().empty());
    assert(!InfinityScriptPersistence::PollCommit());
    assert(PyRun_SimpleString("e.set();t.join()\n")==0);
    InfinityPythonPersistence::Finish(context,owner);
    assert(!context->waitingWorkers && context->finalized);
  }
  const bool expected=mode=="committed" || mode=="workers" || mode=="nested" || mode=="readonly-child" || mode=="system-exit" || mode=="import-cache" || mode=="checked-raw" || mode=="layered-raw";
  if(expected && !InfinityScriptPersistence::Failure().empty())std::cerr<<mode<<": "<<InfinityScriptPersistence::Failure()<<std::endl;
  if(expected)assert(InfinityScriptPersistence::Failure().empty());
  else {
    assert(!InfinityScriptPersistence::Failure().empty());
    const auto first=InfinityScriptPersistence::Snapshot();
    assert(first.failureWriterId==1 && first.failureWriter=="provider:service.py");
    InfinityScriptPersistence::Admit(2,"other:service.py");
    InfinityScriptPersistence::Fail(2,"later_failure");
    const auto second=InfinityScriptPersistence::Snapshot();
    assert(second.failureWriterId==1 && second.failureWriter==first.failureWriter);
    assert(second.failure==first.failure && second.failureDetail==first.failureDetail);
    if(mode=="raw-open") {
      assert(first.failureDetail.find("raw.json")!=std::string::npos);
      assert(first.failureDetail.find("frame=<string>")!=std::string::npos);
    }
  }
  auto* interpreter=owner->interp;
  Py_EndInterpreter(owner);
  InfinityPythonPersistence::End(context,interpreter);
  PyThreadState_Swap(main);
  if(expected) {
    assert(InfinityScriptPersistence::DurableRetirement("provider:service.py"));
    for(int i=0;i<1000 && !InfinityScriptPersistence::PollCommit();++i)
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    assert(InfinityScriptPersistence::PollCommit());
  } else {
    assert(!InfinityScriptPersistence::DurableRetirement("provider:service.py"));
    assert(!InfinityScriptPersistence::PollCommit());
  }
  Py_FinalizeEx();
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).with_name('observer.py').read_text()
    header = args.runtime / 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
    expected = '#pragma once\n// Generated from writers/observer.py; verified by the source gate.\ninline constexpr const char* INFINITY_PYTHON_PERSISTENCE_SOURCE = R"infinity_source(' + source + ')infinity_source";\n'
    if header.read_text() != expected:
        raise RuntimeError('Embedded Python observer differs from reviewed source')
    include = Path(sysconfig.get_path('include'))
    library_folder = Path(sysconfig.get_config_var('LIBDIR'))
    library = library_folder / sysconfig.get_config_var('LDLIBRARY')
    if not library.exists():
        library = library_folder / (sysconfig.get_config_var('LDLIBRARY') + '.1.0')
    if not library.exists():
        library_folder = Path(sys.prefix) / 'lib'
        library = library_folder / sysconfig.get_config_var('LDLIBRARY')
        if not library.exists():
            library = library_folder / (sysconfig.get_config_var('LDLIBRARY') + '.1.0')
    if not library.exists():
        raise RuntimeError('Actual CPython shared library required')
    with tempfile.TemporaryDirectory(prefix='native-python-save-') as directory:
        directory = Path(directory)
        invoker = (args.runtime / 'xbmc/interfaces/python/PythonInvoker.cpp').read_text()
        branch = invoker.split('else if (PyErr_ExceptionMatches(PyExc_SystemExit))', 1)[1].split('\n  else\n', 1)[0]
        branch = re.sub(r'    CLog::Log[^\n]*\n', '', branch)
        abort = '\n#define TARGET_ANDROID\nvoid HandleProductionAbort(bool callbackError) {\n bool m_systemExitThrown=false; int stateToSet=0; constexpr int InvokerStateFailed=1;\n auto onAbort=[&](){if(callbackError)PyErr_SetString(PyExc_RuntimeError,"real abort cleanup error");};\n' + branch + '\n (void)m_systemExitThrown;(void)stateToSet;\n}\n'
        code = HARNESS.replace('int main(int argc,char** argv) {', abort + 'int main(int argc,char** argv) {')
        (directory / 'test.cpp').write_text(code)
        binary = directory / 'test'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-I', str(include), '-I', str(args.runtime / 'xbmc'),
                        '-I', str(args.runtime / 'xbmc/interfaces/python'),
                        str(directory / 'test.cpp'), str(library), '-ldl', '-lm',
                        '-o', str(binary)], check=True)
        environment = dict(os.environ, PYTHONHOME=sys.prefix,
                           LD_LIBRARY_PATH=str(library_folder))
        for mode in ('committed', 'pending', 'raw-open', 'direct-sqlite', 'external', 'workers', 'nested', 'readonly-child', 'system-exit', 'system-exit-pending', 'abort-callback-error', 'import-cache', 'checked-raw', 'raw-write-failure', 'layered-raw', 'layered-failure'):
            folder = directory / mode
            folder.mkdir()
            subprocess.run([str(binary), mode, str(folder)], env=environment, check=True, timeout=15)
    print('PASS: real subinterpreter saves, retained transactions, worker retirement and bypass refusal')


if __name__ == '__main__':
    main()
