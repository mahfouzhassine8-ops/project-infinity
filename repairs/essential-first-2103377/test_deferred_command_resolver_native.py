#!/usr/bin/env python3
"""Native observer controls for the Android import.shutil bottleneck.

The controlled unavailable import reproduces the dependency, not Android timing.
The previous production source must fail and the correction must initialize all
41 real interpreters without attempting that unused import. Original child
resolution and genuine failed writes keep their independent fail-closed checks.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = 'e78c769d99b626b47292fb2bcac0d09661735fc6'
CODE = r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <iostream>
using namespace InfinityPythonPersistence;
namespace Ledger=InfinityScriptPersistence;
static bool rejectResolver=true;
static unsigned resolverAttempts=0;
static int resolverGate(const char* event,PyObject* args,void*) {
 if(std::strcmp(event,"import") || !PyTuple_Check(args) || PyTuple_GET_SIZE(args)<1)return 0;
 auto* name=PyTuple_GET_ITEM(args,0);
 if(!PyUnicode_Check(name) || std::strcmp(PyUnicode_AsUTF8(name),"shutil"))return 0;
 ++resolverAttempts;
 if(rejectResolver){PyErr_SetString(PyExc_RuntimeError,"controlled-shutil-unavailable");return -1;}
 return 0;
}
static void run(const char* code) {if(PyRun_SimpleString(code)!=0){PyErr_Print();std::_Exit(20);}}
static void originalResolverError() {
 assert(PyErr_ExceptionMatches(PyExc_RuntimeError));
 PyObject *type=nullptr,*value=nullptr,*trace=nullptr;PyErr_Fetch(&type,&value,&trace);
 assert(type==PyExc_RuntimeError && value && trace);
 auto* text=PyObject_Str(value);assert(text && std::strcmp(PyUnicode_AsUTF8(text),"controlled-shutil-unavailable")==0);
 Py_DECREF(text);Py_XDECREF(type);Py_XDECREF(value);Py_XDECREF(trace);
}
int main(int argc,char** argv) {
 assert(argc==3);const std::string mode=argv[1],root=argv[2];
 const bool legacy=mode=="legacy-dependency-41";
 const unsigned count=(legacy || mode=="deferred-41")?41:1;
 Py_Initialize();auto* main=PyThreadState_Get();assert(PySys_AddAuditHook(resolverGate,nullptr)==0);
 std::vector<PyThreadState*> bootstrap;std::vector<std::thread> workers;
 for(unsigned i=0;i<count;++i){Ledger::Admit(i+1,"fixture.resolver."+std::to_string(i+1));bootstrap.push_back(PyThreadState_New(main->interp));assert(bootstrap.back());}
 auto* saved=PyEval_SaveThread();
 for(unsigned i=0;i<count;++i)workers.emplace_back([&,i]{
  PyEval_AcquireThread(bootstrap[i]);auto* owner=Py_NewInterpreter();assert(owner);
  run("import sys,types\nvfs=types.ModuleType('xbmcvfs');vfs.File=object;sys.modules['xbmcvfs']=vfs\n");
  auto* context=Start(i+1,owner->interp);assert(context);
  if(legacy){
   assert(!context->observer && context->initializationStage=="python.import.shutil");originalResolverError();
  }else{
   assert(context->observer && context->connectionType && context->rawWrite && !PyErr_Occurred());
   assert(resolverAttempts==0); // No cold observer needs the command resolver.
   if(mode=="lookup-success"){
    rejectResolver=false;
    auto* result=PyRun_String("first=_which('sh')\nimport shutil\nassert first==shutil.which('sh')\nassert all(_which(name)==shutil.which(name) for name in ('sh','uname','no-such-infinity-command','/bin/sh'))\n",Py_file_input,context->globals,context->globals);
    assert(result && !PyErr_Occurred() && resolverAttempts>0);Py_DECREF(result);
   }else if(mode=="lookup-failure-before-child"){
    auto* result=PyRun_String("subprocess.Popen(['uname','-m'],stdout=subprocess.PIPE)",Py_file_input,context->globals,context->globals);
    assert(!result && resolverAttempts==1);originalResolverError();
    result=PyObject_GetAttrString(context->observer,"children");assert(result && PySet_Size(result)==0);Py_DECREF(result);
    assert(Ledger::Snapshot().paths==0);
   }else if(mode=="real-buffer-flush-failure"){
    auto* path=PyUnicode_FromString((root+"/profile/essential.txt").c_str());assert(path);
    assert(PyDict_SetItemString(context->globals,"fixture_path",path)==0);Py_DECREF(path);
    auto* result=PyRun_String("handle=open(fixture_path,'w')\nhandle.write('essential user state')\nos.close(handle.fileno())\ntry:\n handle.flush()\nexcept OSError:\n pass\nelse:\n raise AssertionError('real failed flush was swallowed')\n",Py_file_input,context->globals,context->globals);
    if(!result){PyErr_Print();std::_Exit(21);}Py_DECREF(result);
    assert(Ledger::Snapshot().blockingCount>0);
   }
  }
  PyEval_ReleaseThread(owner);
 });
 for(auto& worker:workers)worker.join();PyEval_RestoreThread(saved);
 const auto proof=Ledger::Snapshot();assert(proof.active==count && proof.observed==(legacy?0:count));
 assert(!Ledger::EssentialWritesAuthorized(23));
 if(legacy || mode=="real-buffer-flush-failure"){
  assert(proof.blockingCount>0);
  assert(Ledger::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));
  assert(Ledger::CloseParticipantWrites(23));assert(!Ledger::SealEssentialWrites(23));assert(!Ledger::EssentialWritesAuthorized(23));
 }else assert(proof.blockingCount==0);
 if(mode=="deferred-41")assert(resolverAttempts==0);
 std::cout<<"{\"case\":\""<<mode<<"\",\"passed\":true,\"active\":"<<proof.active<<",\"observed\":"<<proof.observed
          <<",\"resolver_import_attempts\":"<<resolverAttempts<<",\"blocking_count\":"<<proof.blockingCount<<",\"termination_authorized\":false}\n"<<std::flush;
 std::_Exit(0);
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python-prefix', type=Path, required=True)
    parser.add_argument('--sqlite-include', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    prefix = args.python_prefix.resolve()
    results = []
    with tempfile.TemporaryDirectory(prefix='infinity-deferred-resolver-') as temporary:
        folder = Path(temporary)
        cpp = folder/'test.cpp';cpp.write_text(CODE)
        legacy = folder/'legacy'
        shutil.copytree(HERE/'runtime/xbmc', legacy)
        rel = 'repairs/essential-first-2103377/runtime/xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
        (legacy/'interfaces/python/InfinityPythonPersistenceSource.h').write_bytes(
            subprocess.check_output(['git', 'show', BASELINE+':'+rel], cwd=ROOT))
        env = dict(os.environ, PYTHONHOME=str(prefix), LD_LIBRARY_PATH=str(prefix/'lib'), PYTHONDONTWRITEBYTECODE='1')
        for label, runtime, cases in (
            ('previous', legacy, ('legacy-dependency-41',)),
            ('corrected', HERE/'runtime/xbmc', ('deferred-41', 'lookup-success', 'lookup-failure-before-child', 'real-buffer-flush-failure')),
        ):
            binary = folder/label
            includes = [runtime, runtime/'interfaces/python', ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc', prefix/'include/python3.11', args.sqlite_include]
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation', '-pthread',
                *['-I'+str(p) for p in includes], str(cpp), '-L'+str(prefix/'lib'), '-lpython3.11', '-l:libsqlite3.so.0',
                '-ldl', '-lm', '-lcrypto', '-Wl,--export-dynamic', '-o', str(binary)], check=True)
            for mode in cases:
                case = folder/mode;case.mkdir();(case/'profile').mkdir();(case/'cache').mkdir()
                completed = subprocess.run([str(binary), mode, str(case)], env=env, capture_output=True, text=True, timeout=45)
                assert completed.returncode == 0, (mode, completed.returncode, completed.stderr)
                results.append(json.loads(completed.stdout));print(mode, 'PASS', flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dict(scope='Controlled dependency reproduction in real CPython3.11 subinterpreters; not Android timing or Fold acceptance',
        previous_production_source=BASELINE, results=results, all_passed=True, android_timing_verified=False,
        physical_fold_accepted=False, apk_deliverable=False), indent=2)+'\n')


if __name__ == '__main__':
    main()
