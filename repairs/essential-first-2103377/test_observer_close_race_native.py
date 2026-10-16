#!/usr/bin/env python3
"""Reproduce Fold ctypes initialization overlapping the real Close barrier.

The test pauses real CPython dlopen(None) audit events before the production
audit hook runs. No guard, loader, observer or durability result is mocked.
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
#include <chrono>
#include <condition_variable>
#include <sstream>
#include <sys/syscall.h>
struct Gate {
  std::mutex mutex;
  std::condition_variable changed;
  std::set<int> arrivals;
  bool released{false};
};
static Gate gate;
static int pauseAtProcessHandle(const char* event,PyObject* args,void*) {
  if(std::strcmp(event,"ctypes.dlopen") || !PyTuple_Check(args) ||
     PyTuple_GET_SIZE(args)!=1 || PyTuple_GET_ITEM(args,0)!=Py_None)return 0;
  const auto found=InfinityPythonPersistence::Contexts().find(PyThreadState_Get()->interp);
  if(found==InfinityPythonPersistence::Contexts().end())return 0;
  auto* context=found->second;
  if(context->initializationStage!="python.observer.construct")return 0;
  std::unique_lock<std::mutex> lock(gate.mutex);
  if(!gate.arrivals.insert(context->id).second)return 0;
  gate.changed.notify_all();
  auto* saved=PyEval_SaveThread();
  gate.changed.wait(lock,[]{return gate.released;});
  lock.unlock();PyEval_RestoreThread(saved);
  return 0;
}
static void run(const char* code) {
  if(PyRun_SimpleString(code)!=0) {PyErr_Print();std::_Exit(20);}
}
static std::string json(const std::string& input) {
  const char* hex="0123456789abcdef";
  std::string result="\"";
  for(unsigned char c:input) {
    if(c=='"' || c=='\\') {result+='\\';result+=c;}
    else if(c<32) {result+="\\u00";result+=hex[c>>4];result+=hex[c&15];}
    else result+=c;
  }
  return result+'"';
}
int main(int argc,char** argv) {
  assert(argc==5);
  const std::string mode=argv[1],root=argv[2],output=argv[3];
  const bool expectedUnfixed=std::string(argv[4])=="unfixed";
  const bool beforeStart=mode=="closed-before-start-37";
  const bool early=mode!="loaded-close-37";
  const unsigned count=beforeStart || mode=="early-close-37" || !early?37:1;
  const bool expectedFailure=beforeStart || (early && expectedUnfixed);
  Py_Initialize();auto* main=PyThreadState_Get();
  // Registered before production Audit so Close can begin at the exact real
  // ctypes/PyDLL(None) boundary shown in the physical Fold traceback.
  assert(PySys_AddAuditHook(pauseAtProcessHandle,nullptr)==0);
  std::vector<PyThreadState*> bootstrap;
  std::vector<std::thread> workers;
  std::vector<std::string> exceptions(count);
  for(unsigned i=0;i<count;++i) {
    bootstrap.push_back(PyThreadState_New(main->interp));
    InfinityScriptPersistence::Admit(static_cast<int>(i+1),"fold.race.fixture."+std::to_string(i+1)+":service.py");
  }
  if(beforeStart) {
    // Counterexample: closing mutation admission before the native coordinator
    // has observed installation can reject required stdlib native imports.
    assert(InfinityScriptPersistence::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));
    gate.released=true;
  }
  auto* saved=PyEval_SaveThread();
  for(unsigned i=0;i<count;++i)workers.emplace_back([&,i] {
    PyEval_AcquireThread(bootstrap[i]);
    auto* owner=Py_NewInterpreter();assert(owner);
    auto* globals=PyModule_GetDict(PyImport_AddModule("__main__"));
    auto* path=PyUnicode_FromString(root.c_str());assert(path);
    assert(PyDict_SetItemString(globals,"fixture_root",path)==0);Py_DECREF(path);
    run("import sys, types\nvfs=types.ModuleType('xbmcvfs'); vfs.File=object; sys.modules['xbmcvfs']=vfs\n");
    auto* context=InfinityPythonPersistence::Start(static_cast<int>(i+1),owner->interp);assert(context);
    if(expectedFailure) {
      assert(!context->observer && PyErr_ExceptionMatches(context->admissionError));
      PyObject *type=nullptr,*value=nullptr,*trace=nullptr;PyErr_Fetch(&type,&value,&trace);
      auto* text=PyObject_Str(value);assert(text);
      exceptions[i]=PyUnicode_AsUTF8(text);Py_DECREF(text);
      assert(exceptions[i]==(beforeStart?"Infinity protected write admission is closed":"Infinity shutdown closed native mutation admission"));
      PyErr_Restore(type,value,trace);PyErr_Clear();
    } else {
      assert(context->observer && context->rawWrite && !PyErr_Occurred());
      if(mode=="early-native-guards")run(R"guards(
import ctypes
for action in (lambda: ctypes.CDLL('libc.so.6'),
               lambda: ctypes.pythonapi.open,
               lambda: sys.audit('ctypes.dlopen', None, None),
               lambda: open(fixture_root+'/profile/late-write','w')):
 try: action()
 except PermissionError: pass
 else: raise AssertionError('Unproven native capability or real write crossed Close')
assert not __import__('os').path.exists(fixture_root+'/profile/late-write')
)guards");
    }
    PyEval_ReleaseThread(owner);
  });
  if(!beforeStart) {
    std::unique_lock<std::mutex> lock(gate.mutex);
    assert(gate.changed.wait_for(lock,std::chrono::seconds(30),[&]{return gate.arrivals.size()==count;}));
    if(early)assert(InfinityScriptPersistence::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));
    gate.released=true;gate.changed.notify_all();
  }
  for(auto& worker:workers)worker.join();
  PyEval_RestoreThread(saved);
  if(!early)assert(InfinityScriptPersistence::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));
  const auto proof=InfinityScriptPersistence::Snapshot();
  assert(proof.active==count && proof.observed==(expectedFailure?0:count));
  assert(proof.blockingCount==(expectedFailure?count:0));
  assert(InfinityScriptPersistence::CloseParticipantWrites(23));
  const bool sealed=InfinityScriptPersistence::SealEssentialWrites(23);
  const bool authorized=InfinityScriptPersistence::EssentialWritesAuthorized(23);
  assert(sealed==!expectedFailure && authorized==!expectedFailure);
  if(expectedFailure)for(const auto& item:proof.blockers) {
    assert(item.reason=="checked_python_observer_initialization_failed");
    if(beforeStart)assert(item.detail.find("exception=WriteAdmissionClosed")!=std::string::npos);
    else {
      assert(item.detail.find("python_stage=python.import.ctypes")!=std::string::npos);
      assert(item.detail.find("ctypes/__init__.py:376:__init__")!=std::string::npos);
    }
  }
  std::ostringstream report;
  report<<"{\"active\":"<<proof.active<<",\"observed\":"<<proof.observed
        <<",\"paused_at_actual_dlopen_none\":"<<gate.arrivals.size()
        <<",\"blocking_count\":"<<proof.blockingCount<<",\"essential_sealed\":"<<(sealed?"true":"false")
        <<",\"authorized\":"<<(authorized?"true":"false")<<",\"exception\":"<<json(exceptions[0])<<",\"blockers\":[";
  bool first=true;
  for(const auto& item:proof.blockers) {
    if(!first)report<<',';
    first=false;
    report<<"{\"writer_id\":"<<item.writerId<<",\"writer\":"<<json(item.writer)
          <<",\"reason\":"<<json(item.reason)<<",\"detail\":"<<json(item.detail)<<'}';
  }
  report<<"]}\n";
  const auto bytes=report.str();
  const int fd=::open(output.c_str(),O_CREAT|O_EXCL|O_WRONLY,0600);assert(fd>=0);
  assert(syscall(SYS_write,fd,bytes.data(),bytes.size())==static_cast<long>(bytes.size()));assert(::close(fd)==0);
  std::_Exit(0); // Host race/durability proof only; never Android death evidence.
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python-prefix', type=Path, required=True)
    parser.add_argument('--sqlite-include', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expect-unfixed', action='store_true', help='Record the unchanged guard negative control; never used by acceptance CI')
    args = parser.parse_args()
    prefix = args.python_prefix.resolve()
    results = []
    with tempfile.TemporaryDirectory(prefix='infinity-observer-close-') as folder:
        folder = Path(folder)
        source, binary = folder/'test.cpp', folder/'test'
        source.write_text(CODE)
        runtime = HERE/'runtime/xbmc'
        includes = [runtime, runtime/'interfaces/python', ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc', prefix/'include/python3.11', args.sqlite_include]
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', *['-I'+str(p) for p in includes], str(source), '-L'+str(prefix/'lib'), '-lpython3.11', '-l:libsqlite3.so.0', '-ldl', '-lm', '-lcrypto', '-Wl,--export-dynamic', '-o', str(binary)], check=True)
        env = dict(os.environ, PYTHONHOME=str(prefix), LD_LIBRARY_PATH=str(prefix/'lib'), PYTHONDONTWRITEBYTECODE='1')
        for case in ['early-close-1', 'early-close-37', 'loaded-close-37', 'early-native-guards', 'closed-before-start-37']:
            root = folder/case
            (root/'profile').mkdir(parents=True); (root/'cache').mkdir()
            output = root/'result.json'
            completed = subprocess.run([str(binary), case, str(root), str(output), 'unfixed' if args.expect_unfixed else 'fixed'], env=env, capture_output=True, text=True, timeout=60)
            assert completed.returncode == 0, (case, completed.returncode, completed.stderr)
            result = json.loads(output.read_text())
            results.append(dict(case=case, expected_refusal_control=case=='closed-before-start-37', **result))
            print(case, 'PASS', result['active'], result['observed'], result['authorized'], flush=True)
    report = dict(scope='Production observer and real Close barrier, pinned CPython 3.11.7, deterministic interleaving at actual ctypes.dlopen(None)', unchanged_guard_negative_control=args.expect_unfixed, results=results, all_passed=True, physical_fold_verified=False, actual_diggz_services_executed=False, android_process_death_verified=False, apk_deliverable=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
