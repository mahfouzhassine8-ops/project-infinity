#!/usr/bin/env python3
"""Compile native audit + ledger against an actual CPython subinterpreter."""
import argparse
import os
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
  auto* context=InfinityPythonPersistence::Start(1,owner->interp);
  if(PyErr_Occurred())PyErr_Print();
  assert(context && InfinityScriptPersistence::Failure().empty());
  auto* root=PyUnicode_FromString(argv[2]);
  PyDict_SetItemString(PyModule_GetDict(PyImport_AddModule("__main__")),"root",root);Py_DECREF(root);
  const char* script=nullptr;
  if(mode=="committed")script="import sqlite3\nc=sqlite3.connect(root+'/state.db')\nc.execute('create table state (value)')\nc.execute('insert into state values (42)')\nc.commit()\nc.close()\nf=open(root+'/state.json','w');f.write('saved')\n";
  if(mode=="pending")script="import sqlite3\nc=sqlite3.connect(root+'/state.db')\nc.execute('create table state (value)')\nc.execute('insert into state values (42)')\n";
  if(mode=="raw-open")script="import _io\nf=_io.open(root+'/raw.json','w');f.write('saved');f.close()\n";
  if(mode=="direct-sqlite")script="import _sqlite3\nc=_sqlite3.connect(root+'/direct.db');c.close()\n";
  if(mode=="external")script="import subprocess\nsubprocess.run(['/bin/true'],check=True)\n";
  if(mode=="workers")script="import threading\ne=threading.Event()\nt=threading.Thread(target=e.wait);t.start()\n";
  assert(script && PyRun_SimpleString(script)==0);
  InfinityPythonPersistence::Finish(context,owner);
  if(PyErr_Occurred())PyErr_Print();
  if(mode=="pending") {
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
  const bool expected=mode=="committed" || mode=="workers";
  if(expected)assert(InfinityScriptPersistence::Failure().empty());
  else assert(!InfinityScriptPersistence::Failure().empty());
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
        (directory / 'test.cpp').write_text(HARNESS)
        binary = directory / 'test'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-I', str(include), '-I', str(args.runtime / 'xbmc'),
                        '-I', str(args.runtime / 'xbmc/interfaces/python'),
                        str(directory / 'test.cpp'), str(library), '-ldl', '-lm',
                        '-o', str(binary)], check=True)
        environment = dict(os.environ, PYTHONHOME=sys.prefix,
                           LD_LIBRARY_PATH=str(library_folder))
        for mode in ('committed', 'pending', 'raw-open', 'direct-sqlite', 'external', 'workers'):
            folder = directory / mode
            folder.mkdir()
            subprocess.run([str(binary), mode, str(folder)], env=environment, check=True, timeout=15)
    print('PASS: real subinterpreter saves, retained transactions, worker retirement and bypass refusal')


if __name__ == '__main__':
    main()
