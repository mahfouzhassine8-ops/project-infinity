#!/usr/bin/env python3
"""Observe real pending imports through the production native stage bridge.

The import pause releases the existing GIL and never changes admission. These
host controls do not reproduce Android timing or grant physical acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CODE = r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <condition_variable>
#include <iostream>
using namespace InfinityPythonPersistence;
namespace Ledger=InfinityScriptPersistence;
struct Gate {
 std::mutex mutex;std::condition_variable changed;std::set<int> arrivals;
 bool released{false};std::string module;
};
static Gate gate;
static int pauseImport(const char* event,PyObject* args,void*) {
 if(std::strcmp(event,"import") || !PyTuple_Check(args) || PyTuple_GET_SIZE(args)<1)return 0;
 auto* name=PyTuple_GET_ITEM(args,0);
 if(!PyUnicode_Check(name) || gate.module!=PyUnicode_AsUTF8(name))return 0;
 const auto found=Contexts().find(PyThreadState_Get()->interp);
 if(found==Contexts().end())return 0;
 std::unique_lock<std::mutex> lock(gate.mutex);
 if(!gate.arrivals.insert(found->second->id).second)return 0;
 gate.changed.notify_all();auto* saved=PyEval_SaveThread();
 gate.changed.wait(lock,[]{return gate.released;});lock.unlock();PyEval_RestoreThread(saved);
 return 0;
}
static void run(const char* code) {if(PyRun_SimpleString(code)!=0){PyErr_Print();std::_Exit(20);}}
static void pendingProof(unsigned count,const std::string& expected) {
 const auto proof=Ledger::Snapshot();
 assert(proof.active==count && proof.observed==0 && proof.blockingCount==0 && proof.paths==0);
 assert(!Ledger::EssentialWritesAuthorized(23));
 const auto rows=Ledger::Snapshot().initialization;assert(rows.size()==count);
 std::set<uint64_t> identities;
 for(const auto& row:rows) {
  assert(row.writerId>0 && static_cast<unsigned>(row.writerId)<=count);
  assert(row.writer=="fixture.live."+std::to_string(row.writerId)+":service.py");
  assert(row.current.stage==expected && !row.observed && row.pid==getpid() && row.current.nativeTid>0);
  assert(row.current.interpreterIdentity && identities.insert(row.current.interpreterIdentity).second);
 }
}
int main(int argc,char** argv) {
 assert(argc==3);const std::string mode=argv[1],root=argv[2];
 Py_Initialize();auto* main=PyThreadState_Get();
 if(mode=="callback-original-error" || mode=="audit-compile-exec") {
  Context context;context.id=1;context.interpreterIdentity=reinterpret_cast<uintptr_t>(main->interp);
  Contexts()[main->interp]=&context;Ledger::Admit(1,"fixture.live.1:service.py");
  if(mode=="callback-original-error") {
   auto* capsule=PyCapsule_New(&context,"Infinity.Persistence.Observer",nullptr);assert(capsule);
   auto* stage=PyUnicode_FromString("python.import.shutil");assert(stage);
   PyErr_SetString(PyExc_RuntimeError,"original-callback-sentinel");
   PyObject *type=nullptr,*value=nullptr,*trace=nullptr;PyErr_Fetch(&type,&value,&trace);
   PyErr_Restore(type,value,trace);errno=E2BIG;
   auto* result=ReportPythonInitializationStage(capsule,stage);assert(result==Py_None && errno==E2BIG);Py_DECREF(result);
   PyObject *afterType=nullptr,*afterValue=nullptr,*afterTrace=nullptr;PyErr_Fetch(&afterType,&afterValue,&afterTrace);
   assert(afterType==type && afterValue==value && afterTrace==trace);PyErr_Restore(afterType,afterValue,afterTrace);PyErr_Clear();
   pendingProof(1,"python.import.shutil");
   Context foreign;auto* foreignCapsule=PyCapsule_New(&foreign,"Infinity.Persistence.Observer",nullptr);assert(foreignCapsule);
   auto* ignored=PyUnicode_FromString("python.import.foreign");assert(ignored);
   result=ReportPythonInitializationStage(foreignCapsule,ignored);assert(result==Py_None && !PyErr_Occurred());Py_DECREF(result);
   pendingProof(1,"python.import.shutil");
   Py_DECREF(ignored);Py_DECREF(foreignCapsule);Py_DECREF(stage);Py_DECREF(capsule);
  } else {
   assert(PySys_AddAuditHook(Audit,nullptr)==0);
   context.globals=PyDict_New();assert(context.globals);
   InitializationStage(&context,"python.source");
   auto* result=PyRun_String("answer=42",Py_file_input,context.globals,context.globals);assert(result && !PyErr_Occurred());Py_DECREF(result);
   assert(PyLong_AsLong(PyDict_GetItemString(context.globals,"answer"))==42);
   pendingProof(1,"python.source.execute");
   auto rows=Ledger::Snapshot().initialization;
   bool compiled=false,executed=false;
   for(const auto& step:rows[0].steps) {
    if(step.stage=="python.source.compile")compiled=true;
    if(step.stage=="python.source.execute"){assert(compiled);executed=true;}
   }
   assert(compiled && executed);
   InitializationStage(&context,"python.import.shutil");
   result=PyRun_String("answer+=1",Py_file_input,context.globals,context.globals);assert(result && !PyErr_Occurred());Py_DECREF(result);
   assert(PyLong_AsLong(PyDict_GetItemString(context.globals,"answer"))==43);
   pendingProof(1,"python.import.shutil");
  }
  Contexts().erase(main->interp);
 } else {
  const bool failure=mode=="source-original-failure";
  const unsigned count=mode=="paused-sqlite3-37"?37:1;
  gate.module=mode=="paused-ctypes"?"ctypes":"sqlite3";
  if(!failure)assert(PySys_AddAuditHook(pauseImport,nullptr)==0);
  std::vector<PyThreadState*> bootstrap;std::vector<std::thread> workers;
  for(unsigned i=0;i<count;++i) {
   Ledger::Admit(static_cast<int>(i+1),"fixture.live."+std::to_string(i+1)+":service.py");
   bootstrap.push_back(PyThreadState_New(main->interp));assert(bootstrap.back());
  }
  auto* saved=PyEval_SaveThread();
  for(unsigned i=0;i<count;++i)workers.emplace_back([&,i] {
   PyEval_AcquireThread(bootstrap[i]);auto* owner=Py_NewInterpreter();assert(owner);
   run("import sys, types\nvfs=types.ModuleType('xbmcvfs');vfs.File=object;sys.modules['xbmcvfs']=vfs\n");
   if(failure) {
    auto* globals=PyModule_GetDict(PyImport_AddModule("__main__"));auto* path=PyUnicode_FromString(root.c_str());assert(path);
    assert(PyDict_SetItemString(globals,"fixture_root",path)==0);Py_DECREF(path);
    run("sys.path.insert(0,fixture_root)\n");
   }
   auto* context=Start(static_cast<int>(i+1),owner->interp);assert(context);
   if(failure) {
    assert(!context->observer && PyErr_ExceptionMatches(PyExc_RuntimeError));
    assert(context->initializationStage=="python.import.sqlite3");
    PyObject *type=nullptr,*value=nullptr,*trace=nullptr;PyErr_Fetch(&type,&value,&trace);
    assert(type==PyExc_RuntimeError && value && trace);
    auto* text=PyObject_Str(value);assert(text && std::strcmp(PyUnicode_AsUTF8(text),"live-source-original-sentinel")==0);Py_DECREF(text);
    PyErr_Restore(type,value,trace);PyErr_Clear();
   } else assert(context->observer && context->rawWrite && !PyErr_Occurred());
   PyEval_ReleaseThread(owner);
  });
  if(!failure) {
   std::unique_lock<std::mutex> lock(gate.mutex);
   assert(gate.changed.wait_for(lock,std::chrono::seconds(20),[&]{return gate.arrivals.size()==count;}));
   pendingProof(count,"python.import."+gate.module);
   gate.released=true;gate.changed.notify_all();
  }
  for(auto& worker:workers)worker.join();PyEval_RestoreThread(saved);
  const auto proof=Ledger::Snapshot();assert(proof.active==count && proof.observed==(failure?0:count));
  assert(!Ledger::EssentialWritesAuthorized(23));
  if(failure) {
   assert(proof.blockingCount==1);
   const auto& detail=proof.blockers[0].detail;
   assert(detail.find("stage=python.import.sqlite3")!=std::string::npos);
   assert(detail.find("python_stage=python.import.sqlite3")!=std::string::npos);
   assert(detail.find("exception=RuntimeError")!=std::string::npos);
   assert(detail.find("live-source-original-sentinel")!=std::string::npos);
   assert(Ledger::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));
   assert(Ledger::CloseParticipantWrites(23));assert(!Ledger::SealEssentialWrites(23));
   assert(!Ledger::EssentialWritesAuthorized(23));
  } else {
   assert(proof.blockingCount==0);
   for(const auto& row:Ledger::Snapshot().initialization) {
    assert(row.current.stage=="complete" && row.observed);
    assert(row.stepsOverflow); // Auxiliary history cap never caps current stage or observer proof.
   }
  }
 }
 std::cout<<"{\"case\":\""<<mode<<"\",\"passed\":true,\"authorized\":false}\n"<<std::flush;
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
    runtime = HERE/'runtime/xbmc'
    source = (HERE/'runtime/observer.py').read_text()
    expected = '#pragma once\n// Generated from runtime/observer.py; verified by the source gate.\ninline constexpr const char* INFINITY_PYTHON_PERSISTENCE_SOURCE = R"infinity_source('+source+')infinity_source";\n'
    assert (runtime/'interfaces/python/InfinityPythonPersistenceSource.h').read_text() == expected
    # No native callback is required by standalone observer execution.
    standalone = {}
    exec(compile(source, 'standalone-observer.py', 'exec'), standalone)
    assert standalone['_INFINITY_INITIALIZATION_STAGE'] == 'python.define_observer'
    assert '_INFINITY_NATIVE_INITIALIZATION_STAGE' not in standalone
    results = [dict(case='standalone-optional-callback', passed=True)]
    with tempfile.TemporaryDirectory(prefix='infinity-live-init-') as temporary:
        folder = Path(temporary)
        cpp, binary = folder/'test.cpp', folder/'test'
        cpp.write_text(CODE)
        base = ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'
        includes = [runtime, runtime/'interfaces/python', base, prefix/'include/python3.11', args.sqlite_include]
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation', '-pthread',
                        *['-I'+str(p) for p in includes], str(cpp), '-L'+str(prefix/'lib'), '-lpython3.11',
                        '-l:libsqlite3.so.0', '-ldl', '-lm', '-lcrypto', '-Wl,--export-dynamic', '-o', str(binary)], check=True)
        env = dict(os.environ, PYTHONHOME=str(prefix), LD_LIBRARY_PATH=str(prefix/'lib'), PYTHONDONTWRITEBYTECODE='1')
        for mode in ('paused-sqlite3', 'paused-ctypes', 'paused-sqlite3-37', 'source-original-failure',
                     'callback-original-error', 'audit-compile-exec'):
            case = folder/mode;case.mkdir();(case/'profile').mkdir();(case/'cache').mkdir()
            if mode == 'source-original-failure':
                (case/'sqlite3.py').write_text("raise RuntimeError('live-source-original-sentinel')\n")
            completed = subprocess.run([str(binary), mode, str(case)], env=env, capture_output=True, text=True, timeout=45)
            assert completed.returncode == 0, (mode, completed.returncode, completed.stderr)
            result = json.loads(completed.stdout)
            results.append(result);print(mode, 'PASS', flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dict(scope='Production live observer-stage bridge in pinned CPython3.11.7 with host Kodi VFS peer',
        results=results, all_passed=True, physical_fold_verified=False, android_timing_reproduced=False,
        android_process_death_verified=False, apk_deliverable=False), indent=2)+'\n')


if __name__ == '__main__':
    main()
