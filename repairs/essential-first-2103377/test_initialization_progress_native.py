#!/usr/bin/env python3
"""Native progress controls; evidence only, never an observer/save receipt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import apply_runtime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OVERLAY = ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'
LEGACY_INVOKER_SHA = '8f86218be8134e4dfe32cac40b98d209abcb2e9ee1ae32db72973105d3d71fba'
PEERS = r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <condition_variable>
#include <filesystem>
#include <iostream>
#include <set>
namespace InfinityAndroidCheckpoint {bool IsPersistingOnThisThread(){return false;}}
namespace Ledger=InfinityScriptPersistence;
static std::string mode;
static void stage(const char* expected) {
  auto proof=Ledger::Snapshot();assert(proof.initialization.size()==1);
  assert(proof.initialization[0].current.stage==expected);
  assert(proof.observed==0 && proof.blockingCount==0);
}
struct CFileUtils {static bool Exists(const std::string&) {
  stage("native.execute.file_exists");return mode!="execute-file-failed";
}};
struct CSpecialProtocol {static std::string TranslatePath(const std::string& p){return p;}};
constexpr int LOGERROR=1;
struct CLog {template<class...T>static void Log(T...){};};
struct ILanguageInvoker {bool Execute(const std::string&,const std::vector<std::string>&) {
  stage("native.handler.initialized");return true;
}};
class CPythonInvoker:public ILanguageInvoker {
public:
 int GetId()const{return 1;}
 bool onExecutionInitialized(){stage("native.handler.initialize");return mode!="execute-handler-failed";}
 bool Execute(const std::string&,const std::vector<std::string>&);
};
'''
MAIN = r'''
int main(int argc,char**argv) {
  assert(argc==3);mode=argv[1];const std::string root=argv[2];
  if(mode.rfind("execute-",0)==0) {
    Ledger::Admit(1,"fixture.execute:service.py");
    CPythonInvoker invoker;
    const bool result=invoker.Execute(mode=="execute-empty"?"":"service.py",{});
    assert(result==(mode=="execute-success"));
    if(mode=="execute-empty")stage("native.execute.enter");
    if(mode=="execute-file-failed")stage("native.execute.file_exists");
    if(mode=="execute-handler-failed")stage("native.handler.initialize");
    // A successful CPython dispatch is not successful observer installation.
    assert(Ledger::Snapshot().observed==0);
  } else if(mode=="pending-37") {
    std::mutex gate;std::condition_variable condition;unsigned arrived=0;bool release=false;
    std::vector<std::thread> workers;
    for(int id=1;id<=37;++id)Ledger::Admit(id,"fixture.pending."+std::to_string(id)+":service.py");
    for(int id=1;id<=37;++id)workers.emplace_back([&,id] {
      errno=ERANGE;
      assert(Ledger::InitializationProgress(id,"native.interpreter.create",1000+id));
      assert(errno==ERANGE);
      std::unique_lock<std::mutex> lock(gate);++arrived;condition.notify_all();
      condition.wait(lock,[&]{return release;});
      assert(Ledger::InitializationProgress(id,"complete"));
    });
    {
      std::unique_lock<std::mutex> lock(gate);condition.wait(lock,[&]{return arrived==37;});
      const auto proof=Ledger::Snapshot();assert(proof.active==37 && proof.observed==0 && proof.blockingCount==0);
      assert(proof.initialization.size()==37);std::set<int64_t> tids;
      for(const auto& row:proof.initialization) {
        assert(row.writer=="fixture.pending."+std::to_string(row.writerId)+":service.py");
        assert(row.pid==getpid() && row.current.nativeTid>0);
        assert(row.current.nativeTid!=static_cast<int64_t>(syscall(SYS_gettid)));
        assert(row.current.interpreterIdentity==static_cast<uint64_t>(1000+row.writerId));
        assert(row.current.stage=="native.interpreter.create" && !row.observed);
        assert(row.elapsedMs>=row.current.elapsedMs && row.steps.size()==1);
        tids.insert(row.current.nativeTid);
      }
      assert(tids.size()==37);release=true;condition.notify_all();
    }
    for(auto& worker:workers)worker.join();
    // Stage text cannot grant coverage or authorize unobserved writes.
    assert(Ledger::Snapshot().observed==0);
    assert(Ledger::BeginWriteProtection(17,{root+"/profile"},{root+"/cache"}));
    assert(Ledger::CloseParticipantWrites(17));
    assert(!Ledger::SealEssentialWrites(17));
    assert(!Ledger::EssentialWritesAuthorized(17));
  } else if(mode=="bounded-failure") {
    errno=EACCES;assert(!Ledger::InitializationProgress(404,"unknown"));assert(errno==EACCES);
    assert(Ledger::Snapshot().active==0);
    Ledger::Admit(1,"fixture.failure:service.py");
    Ledger::Fail(1,"protected_durability_failed","original-user-data-write");
    for(int i=0;i<40;++i)assert(Ledger::InitializationProgress(1,("step."+std::to_string(i)).c_str()));
    auto proof=Ledger::Snapshot();assert(proof.initialization.size()==1);
    const auto& row=proof.initialization[0];assert(row.current.stage=="step.39");
    assert(row.steps.size()==32 && row.stepsOverflow);
    assert(proof.blockingCount==1 && proof.blockers[0].detail=="original-user-data-write");
    assert(proof.observed==0 && !Ledger::EssentialWritesAuthorized(17));
  } else {
    const bool bad=mode=="observer-failed";
    assert(bad || mode=="observer-success");Ledger::Admit(1,"fixture.observer:service.py");
    Py_Initialize();auto* state=PyThreadState_Get();
    assert(PyRun_SimpleString(bad?
      "import sys,types\nvfs=types.ModuleType('xbmcvfs')\nsys.modules['xbmcvfs']=vfs\n":
      "import sys,types\nvfs=types.ModuleType('xbmcvfs')\nvfs.File=object\nsys.modules['xbmcvfs']=vfs\n")==0);
    auto* context=InfinityPythonPersistence::Start(1,state->interp);assert(context);
    const auto proof=Ledger::Snapshot();assert(proof.initialization.size()==1);
    const auto& row=proof.initialization[0];std::set<std::string> stages;
    for(const auto& step:row.steps)stages.insert(step.stage);
    assert(row.current.nativeTid==static_cast<int64_t>(syscall(SYS_gettid)));
    assert(row.current.interpreterIdentity==reinterpret_cast<uintptr_t>(state->interp));
    for(const auto* expected:{"native.observer.entry","native.sqlite_vfs.install","native.audit.install",
                             "native.hooks.install","python.source","python.import.xbmcvfs","python.observer.construct"})
      assert(stages.count(expected)==1);
    if(bad) {
      assert(proof.observed==0 && proof.blockingCount>0 && PyErr_Occurred());
      assert(row.current.stage=="failed:python.install.xbmcvfs");
      assert(proof.failureDetail.find("stage=python.install.xbmcvfs")!=std::string::npos);
      assert(proof.failureDetail.find("exception=AttributeError")!=std::string::npos);
      PyObject *type=nullptr,*value=nullptr,*trace=nullptr;PyErr_Fetch(&type,&value,&trace);
      assert(type==PyExc_AttributeError && value && trace);PyErr_Restore(type,value,trace);
      assert(Ledger::BeginWriteProtection(17,{root+"/profile"},{root+"/cache"}));
      assert(Ledger::CloseParticipantWrites(17));assert(!Ledger::SealEssentialWrites(17));
      assert(!Ledger::EssentialWritesAuthorized(17));
    } else assert(proof.observed==1 && proof.blockingCount==0 && row.current.stage=="complete" && !PyErr_Occurred());
  }
  std::cout<<mode<<" PASS\n"<<std::flush;
  std::_Exit(0); // Host scope only; never evidence of Android process death.
}
'''


def method(source):
    start=source.index('bool CPythonInvoker::Execute(')
    end=source.index('bool CPythonInvoker::execute(',start)
    return source[start:end]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--python-prefix',type=Path,required=True)
    parser.add_argument('--sqlite-include',type=Path,required=True)
    parser.add_argument('--invoker-source',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();prefix=args.python_prefix.resolve()
    source=args.invoker_source or OVERLAY/'interfaces/python/PythonInvoker.cpp'
    text=source.read_text();original_sha=hashlib.sha256(text.encode()).hexdigest()
    if not args.invoker_source:
        assert original_sha==LEGACY_INVOKER_SHA
        text=apply_runtime.python_invoker(text)
    assert text.count('InfinityScriptPersistence::InitializationProgress')==13
    required=['native.interpreter.main_state','native.interpreter.thread_state','native.interpreter.acquire_gil',
              'native.interpreter.create','native.interpreter.created','native.interpreter.restore_gil',
              'native.kodi_module.initialize','native.kodi_module.initialized','native.observer.before_start']
    assert all(text.count('"'+stage+'"')==1 for stage in required)
    assert text.index('"native.interpreter.create"')<text.index('l_threadState = Py_NewInterpreter();')
    assert text.index('"native.kodi_module.initialize"')<text.index('    onInitialization();')<text.index('"native.kodi_module.initialized"')
    cases=['execute-empty','execute-file-failed','execute-handler-failed','execute-success','pending-37',
           'bounded-failure','observer-success','observer-failed']
    results=[]
    with tempfile.TemporaryDirectory(prefix='infinity-progress-') as temporary:
        work=Path(temporary);cpp=work/'test.cpp';binary=work/'test'
        cpp.write_text(PEERS+method(text)+MAIN)
        includes=[HERE/'runtime/xbmc',HERE/'runtime/xbmc/interfaces/python',OVERLAY,prefix/'include/python3.11',args.sqlite_include]
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-pthread',
                        *['-I'+str(p) for p in includes],str(cpp),'-L'+str(prefix/'lib'),'-lpython3.11',
                        '-l:libsqlite3.so.0','-ldl','-lm','-lcrypto','-Wl,--export-dynamic','-o',str(binary)],check=True)
        environment=dict(os.environ,PYTHONHOME=str(prefix),LD_LIBRARY_PATH=str(prefix/'lib'),PYTHONDONTWRITEBYTECODE='1')
        for case in cases:
            root=work/case
            for child in ('profile','cache'):(root/child).mkdir(parents=True)
            result=subprocess.run([str(binary),case,str(root)],env=environment,capture_output=True,text=True,timeout=30)
            assert result.returncode==0,(case,result.returncode,result.stdout,result.stderr)
            results.append(dict(case=case,passed=True));print(case,'PASS',flush=True)
    report=dict(scope='native progress ledger, actual CPython Execute method with explicit Kodi peers, real observer initialization in CPython3.11.7',
                source_sha256=original_sha,staged_invoker_tested=bool(args.invoker_source),results=results,all_passed=True,
                android_shutdown_verified=False,physical_fold_verified=False,save_or_termination_authority_changed=False)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
