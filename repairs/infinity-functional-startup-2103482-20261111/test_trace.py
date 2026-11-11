#!/usr/bin/env python3
"""Compile exact QA trace call sites with controlled native peers; no Android claim."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OVERLAY=HERE/'native/overlay'

PEERS=r'''
#include <algorithm>
#include <atomic>
#include <cassert>
#include <condition_variable>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include "interfaces/generic/InfinityStartupTrace.h"
using CCriticalSection=std::recursive_mutex;
namespace Test {inline bool missing=false,quarantine=false;inline int dispatched=0,checks=0,stops=0,initialized=0;}
namespace ADDON {struct Addon{std::string ID()const{return "script.fixture";}std::string LibPath()const{return "/fixture/secret-not-logged.py";}};using AddonPtr=std::shared_ptr<Addon>;}
using ADDON::AddonPtr;
enum class OnlyEnabled{CHOICE_YES};
enum class AddonType{SCRIPT,SCRIPT_WEATHER,SCRIPT_LYRICS,SCRIPT_LIBRARY};
struct AddonMgr{template<class...T>bool GetAddon(const std::string&,AddonPtr& a,T...){a=std::make_shared<ADDON::Addon>();return true;}};
struct CServiceBroker{static AddonMgr& GetAddonMgr(){static AddonMgr a;return a;}};
struct URIUtils{static std::string GetFileName(const std::string& s){return s;}static std::string GetExtension(const std::string&){return ".py";}};
struct StringUtils{static void ToLower(std::string&) {}};
struct CFileUtils{static bool Exists(const std::string&,bool=false){return !Test::missing;}};
constexpr int LOGERROR=1,LOGINFO=2,LOGDEBUG=3,LOGWARNING=4;
struct CLog{template<class...T>static void Log(T...) {}};
struct Invoker{int id=-1;int GetId()const{return id;}void Reset(){}};
using LanguageInvokerPtr=std::shared_ptr<Invoker>;
struct Handler{LanguageInvokerPtr CreateInvoker(){return std::make_shared<Invoker>();}};
using ILanguageInvocationHandler=Handler;
class CScriptInvocationManager;
struct CLanguageInvokerThread{
 LanguageInvokerPtr invoker;AddonPtr addon;int id=-1;
 CLanguageInvokerThread(LanguageInvokerPtr i,CScriptInvocationManager*,bool):invoker(i){}
 bool Reuseable(const std::string&)const{return false;}void Release(){}
 LanguageInvokerPtr GetInvoker()const{return invoker;}void SetAddon(AddonPtr a){addon=a;}
 void SetId(int i){id=i;invoker->id=i;}int GetId()const{return id;}
 void Execute(const std::string&,const std::vector<std::string>&){++Test::dispatched;}
};
using CLanguageInvokerThreadPtr=std::shared_ptr<CLanguageInvokerThread>;
namespace InfinityShutdownTrace{inline void Event(const char*,const char*){}}
namespace InfinityAndroidCheckpoint{inline std::string ClassifyScript(const std::string&,const std::string&){return {};}}
namespace InfinityAddonQuarantine{inline bool ShouldSuppress(const std::string&,const std::string&){++Test::checks;return Test::quarantine;}}
namespace InfinityScriptPersistence{inline void Admit(int,const std::string&){}inline void RegisterParticipant(int){}}
class CScriptInvocationManager{public:
 struct Row{CLanguageInvokerThreadPtr thread;std::string script;bool done;std::string checkpointContract;};
 using LanguageInvokerThread=Row;
 std::map<int,Row>m_scripts;std::map<std::string,int>m_scriptPaths;
 std::map<std::string,Handler*>m_invocationHandlers;
 CLanguageInvokerThreadPtr m_lastInvokerThread;int m_nextId=0,m_lastPluginHandle=-1;
 CCriticalSection m_critSection;bool m_shutdownRequested=false,m_checkpointStartupAdmissionClosed=false;
 std::vector<std::string>m_checkpointUnresolvedWriterLedger;
 static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager m;return m;}
 bool CanAdmitCheckpointStartupLocked(const std::string&,const AddonPtr&,bool,const LanguageInvokerPtr& = {})const{return false;}
 void BeginShutdown();void BeginCheckpointStartupAdmission();
 LanguageInvokerPtr GetLanguageInvokerForAdmission(const std::string&,const AddonPtr&,bool);
 int ExecuteAsync(const std::string&,const AddonPtr&,const std::vector<std::string>&,bool=false,int=-1);
 int ExecuteAsync(const std::string&,const LanguageInvokerPtr&,const AddonPtr&,const std::vector<std::string>&,bool,int);
};
#define XBMC_TRACE
struct ILanguageInvoker {int GetId()const{return 41;}};
struct CAddonPythonInvoker {static void GlobalInitializeModules(){}};
inline void Py_Initialize(){++Test::initialized;}
inline void* PyEval_SaveThread(){return reinterpret_cast<void*>(1);}
struct XBPython{CCriticalSection m_critSection;int m_iDllScriptCounter=0;bool m_bInitialized=false;void* m_mainThreadState=nullptr;bool OnScriptInitialized(ILanguageInvoker*);};
'''

MAIN=r'''
int main(int argc,char** argv){
 assert(argc==2);const std::string mode=argv[1];
#if defined(INFINITY_STARTUP_TRACE_HOST)
 InfinityStartupTrace::hostInfinity=mode!="foreign-process";
#endif
 auto& manager=CScriptInvocationManager::GetInstance();Handler handler;manager.m_invocationHandlers[".py"]=&handler;
 using S=InfinityStartupTrace::Stage;
 std::vector<InfinityStartupTrace::Event> events;
 const auto collect=[&]{InfinityStartupTrace::Drain([&](const InfinityStartupTrace::Event& e){events.push_back(e);});};
 const auto contains=[&](S s){return std::any_of(events.begin(),events.end(),[&](auto& e){return e.stage==s;});};
 if(mode=="startup-gate")manager.BeginCheckpointStartupAdmission();
 if(mode=="shutdown-gate")manager.BeginShutdown();
 if(mode=="missing-file")Test::missing=true;
 if(mode=="missing-handler")manager.m_invocationHandlers.clear();
 if(mode=="quarantine")Test::quarantine=true;
 if(mode=="delayed-runtime"){
   XBPython runtime;ILanguageInvoker invoker;
   std::unique_lock<CCriticalSection> held(runtime.m_critSection);
   std::atomic<bool> completed{false};
   std::thread worker([&]{assert(runtime.OnScriptInitialized(&invoker));completed=true;});
   for(unsigned i=0;i<200 && !contains(S::RuntimeWait);++i){collect();std::this_thread::sleep_for(std::chrono::milliseconds(1));}
   assert(contains(S::RuntimeWait) && !contains(S::RuntimeLocked) && !completed);
   held.unlock();worker.join();collect();
   assert(contains(S::RuntimeLocked) && contains(S::RuntimeInitialized) && completed);
   assert(Test::initialized==1);assert(runtime.OnScriptInitialized(&invoker));collect();
   assert(contains(S::RuntimeReused) && Test::initialized==1);
 }else{
   const int builtin=RunScript(std::vector<std::string>{"script.fixture","token=DO_NOT_LOG"});
   assert(builtin==0);
   const bool rejected=mode=="startup-gate" || mode=="shutdown-gate" || mode=="missing-file" || mode=="missing-handler" || mode=="quarantine";
   assert(Test::dispatched==(rejected?0:1));collect();
   if(InfinityStartupTrace::Enabled()){
     assert(contains(S::BuiltinResult));
     const auto result=*std::find_if(events.begin(),events.end(),[](auto& e){return e.stage==S::BuiltinResult;});
     assert(result.value==(rejected?-1:0));
     if(mode=="startup-gate")assert(contains(S::StartupClosed));
     if(mode=="shutdown-gate")assert(contains(S::ShutdownClosed));
     if(mode=="missing-file")assert(contains(S::MissingScript));
     if(mode=="missing-handler")assert(contains(S::MissingHandler));
     if(mode=="quarantine")assert(contains(S::Quarantined) && Test::checks==1);
     if(!rejected)assert(contains(S::FreshDispatch));
     assert(result.request!=0);
   }else assert(events.empty());
 }
 if(mode=="capacity"){
#if defined(INFINITY_STARTUP_TRACE_HOST)
   for(unsigned i=0;i<InfinityStartupTrace::CAPACITY+50;++i)InfinityStartupTrace::Record(S::ExecuteEnter,23);
   auto previous=events.size();collect();assert(events.size()-previous<=InfinityStartupTrace::DRAIN_BATCH+1);
   assert(contains(S::Overflow));
   while(InfinityStartupTrace::drained<InfinityStartupTrace::CAPACITY){previous=events.size();collect();assert(events.size()-previous<=InfinityStartupTrace::DRAIN_BATCH);}
   assert(events.size()<=InfinityStartupTrace::CAPACITY+1);
   auto count=events.size();collect();assert(events.size()==count);
   // Exceptions in diagnostic sinks cannot propagate into application control.
   InfinityStartupTrace::Drain([](const InfinityStartupTrace::Event&){throw 1;});
#endif
 }
 std::cout<<"{\"case\":\""<<mode<<"\",\"dispatched\":"<<Test::dispatched<<",\"trace_records\":"<<events.size()<<",\"stages\":[";
 bool comma=false;for(auto& e:events){if(comma)std::cout<<",";comma=true;std::cout<<"\""<<InfinityStartupTrace::Name(e.stage)<<"\"";if(mode=="capacity")break;}
 std::cout<<"],\"assertions_passed\":true}\n";
}
'''


def method(source, marker):
    start=source.index(marker);end=source.index('{',start)+1;depth=1
    while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    manager=(OVERLAY/'xbmc/interfaces/generic/ScriptInvocationManager.cpp').read_text()
    markers=['void CScriptInvocationManager::BeginCheckpointStartupAdmission()',
             'void CScriptInvocationManager::BeginShutdown()',
             'LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvokerForAdmission(',
             'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const ADDON::AddonPtr&',
             'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const LanguageInvokerPtr&']
    code=PEERS+'\n'.join(method(manager,m) for m in markers)
    code+=method((OVERLAY/'xbmc/interfaces/builtins/AddonBuiltins.cpp').read_text(),'template<bool OnlyApple=false>\nstatic int RunScript(')
    code+=method((OVERLAY/'xbmc/interfaces/python/XBPython.cpp').read_text(),'bool XBPython::OnScriptInitialized(')+MAIN
    cases=['success','startup-gate','shutdown-gate','missing-file','missing-handler','quarantine','delayed-runtime','foreign-process','capacity']
    results=[]
    with tempfile.TemporaryDirectory(prefix='infinity-trace-host-') as tmp:
        tmp=Path(tmp);cpp=tmp/'probe.cpp';cpp.write_text(code)
        for enabled in (True,False):
            binary=tmp/('qa' if enabled else 'disabled')
            defines=['-DINFINITY_STARTUP_TRACE_QA','-DINFINITY_STARTUP_TRACE_HOST'] if enabled else []
            subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-pthread',*defines,'-I'+str(OVERLAY/'xbmc'),str(cpp),'-o',str(binary)],check=True,timeout=60)
            for case in cases if enabled else ['success','startup-gate','shutdown-gate','missing-file','missing-handler','quarantine']:
                result=subprocess.run([str(binary),case],capture_output=True,text=True,check=True,timeout=5)
                assert 'DO_NOT_LOG' not in result.stdout and '/fixture/' not in result.stdout
                results.append(dict(trace_compiled=enabled,**json.loads(result.stdout)))
    report=dict(scope='Exact native call sites with controlled peers; no CPython or Android execution',
                generated_cpp_sha256=hashlib.sha256(code.encode()).hexdigest(),results=results,
                all_selected_assertions_passed=True,fold_failure_reproduced=False)
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
