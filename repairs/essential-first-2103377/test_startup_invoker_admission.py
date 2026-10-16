#!/usr/bin/env python3
"""Compile production manager gates + real path/SHA classifier with explicit peers."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import apply_runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'

TEST=r'''
static std::string service(const char* addon,const char* name="service.py") {
 return std::string("special://home/addons/")+addon+"/"+name;
}
static ADDON::AddonPtr addon(const char* name) {auto a=std::make_shared<ADDON::Addon>();a->name=name;return a;}
static int start(CScriptInvocationManager& m,const std::string& script,const ADDON::AddonPtr& a,bool reusable=false) {
 return m.ExecuteAsync(script,a,{},reusable,-1);
}
int main(int argc,char**argv) {
 assert(argc==4);const std::string mode=argv[1],root=argv[3];
 std::ifstream input(argv[2]);std::string path,digest;while(input>>path>>digest)Test::digests[path]=digest;
 CScriptInvocationManager manager;Handler handler;manager.m_invocationHandlers[".py"]=&handler;
 auto cc=addon("script.infinity.commandcenter"),compat=addon("service.infinity.compat"),foreign=addon("service.observerprobe.writer01");
 const auto ccScript=service("script.infinity.commandcenter"),compatScript=service("service.infinity.compat","runtime_service.py");
 assert(InfinityAndroidCheckpoint::ClassifyScript(ccScript,cc->ID())=="command_center");
 assert(InfinityAndroidCheckpoint::ClassifyScript(compatScript,compat->ID())=="compat");
 if(mode=="normal-37") {
   for(int i=0;i<37;++i)assert(start(manager,"/foreign/service"+std::to_string(i)+".py",foreign)>=0);
   assert(manager.m_scripts.size()==37 && InfinityScriptPersistence::Snapshot().active==37);
   return 0;
 }
 if(mode=="concurrent-inflight-37") {
   std::mutex mutex;std::condition_variable condition;unsigned arrived=0;bool release=false;
   std::vector<std::thread> workers;std::atomic<unsigned> refused{0};
   for(int index=0;index<37;++index)workers.emplace_back([&,index] {
     const auto script="/foreign/inflight"+std::to_string(index)+".py";
     auto invoker=manager.GetLanguageInvokerForAdmission(script,foreign,false);assert(invoker);
     {std::unique_lock<std::mutex> lock(mutex);++arrived;condition.notify_all();condition.wait(lock,[&]{return release;});}
     if(manager.ExecuteAsync(script,invoker,foreign,{},false,-1)==-1)++refused;
   });
   {std::unique_lock<std::mutex> lock(mutex);condition.wait(lock,[&]{return arrived==37;});
     InfinityAndroidCheckpoint::active=true;manager.BeginCheckpointStartupAdmission();release=true;condition.notify_all();}
   for(auto& worker:workers)worker.join();
   assert(refused==37 && manager.m_scripts.empty() && InfinityScriptPersistence::Snapshot().active==0);
   assert(Test::quarantineChecks==0 && checkpointStops==0 && forcedStops==0);
   return 0;
 }
 int existing=-1;LanguageInvokerPtr retained;
 if(mode=="retained-owner" || mode=="real-write-failed" || mode=="unobserved-existing" ||
    mode=="direct-retained-alias" || mode=="map-owned-alias" || mode=="erased-old-alias") {
   existing=start(manager,"/foreign/existing.py",foreign,true);assert(existing>=0);
   retained=manager.m_lastInvokerThread->GetInvoker();
 }
 if(mode=="map-owned-alias")assert(start(manager,"/foreign/another.py",foreign,false)>=0);
 if(mode=="erased-old-alias") {
   retained->id=existing;manager.m_scripts.clear();manager.m_lastInvokerThread.reset();
 }
 LanguageInvokerPtr inFlight;
 if(mode=="inflight-dispatch") {
   inFlight=manager.GetLanguageInvokerForAdmission("/foreign/inflight.py",foreign,false);assert(inFlight);
 }
 InfinityAndroidCheckpoint::active=true;
 manager.BeginCheckpointStartupAdmission();assert(!manager.m_shutdownRequested);
 const int allocations=createdInvokers.load(),resets=resetInvokers.load(),quarantineChecks=Test::quarantineChecks;
 const auto releases=Test::released.size();
 if(mode=="early-37-and-required") {
   for(int i=0;i<37;++i)assert(start(manager,"/foreign/service"+std::to_string(i)+".py",foreign)==-1);
   assert(createdInvokers==allocations && manager.m_scripts.empty());
   assert(start(manager,ccScript,cc)>=0);assert(start(manager,compatScript,compat)>=0);
   assert(manager.m_scripts.size()==2 && InfinityScriptPersistence::Snapshot().active==2);
   assert(InfinityScriptPersistence::Snapshot().observed==0);
   assert(InfinityScriptPersistence::Get().protection.participants.size()==2);
 } else if(mode=="duplicate-resident") {
   assert(start(manager,ccScript,cc)>=0);const int made=createdInvokers;
   assert(start(manager,ccScript,cc)==-1 && createdInvokers==made);
   assert(manager.ExecuteAsync(ccScript,std::make_shared<Invoker>(),cc,{},false,-1)==-1);
   assert(manager.m_scripts.size()==1 && InfinityScriptPersistence::Snapshot().active==1);
 } else if(mode=="identity-and-source") {
   assert(start(manager,ccScript,addon("wrong.addon"))==-1);
   assert(start(manager,"/arbitrary/script.infinity.commandcenter/service.py",cc)==-1);
   const auto dependency=service("script.infinity.commandcenter","checkpoint_runtime.py");
   Test::digests[dependency]="changed";
   assert(start(manager,ccScript,cc)==-1);
   assert(createdInvokers==allocations && InfinityScriptPersistence::Snapshot().active==0);
 } else if(mode=="contract-types") {
   assert(start(manager,service("script.infinity.commandcenter","plugin.py"),cc)==-1);
   assert(start(manager,service("service.infinity.compat","layout_service.py"),compat)==-1);
   assert(start(manager,service("service.infinity.compat","theme_contract.py"),compat)==-1);
   assert(start(manager,ccScript,cc,true)==-1);
   assert(manager.ExecuteAsync(ccScript,std::make_shared<Invoker>(),cc,{},true,-1)==-1);
   assert(createdInvokers==allocations && InfinityScriptPersistence::Snapshot().active==0);
 } else if(mode=="hard-shutdown" || mode=="window-closed") {
   if(mode=="hard-shutdown")manager.BeginShutdown();
   else InfinityAndroidCheckpoint::startupAdmission=false;
   assert(start(manager,ccScript,cc)==-1 && start(manager,compatScript,compat)==-1);
   assert(createdInvokers==allocations && InfinityScriptPersistence::Snapshot().active==0);
 } else if(mode=="inflight-dispatch") {
   assert(manager.ExecuteAsync("/foreign/inflight.py",inFlight,foreign,{},false,-1)==-1);
   assert(manager.m_scripts.empty() && InfinityScriptPersistence::Snapshot().active==0);
   assert(Test::quarantineChecks==quarantineChecks);
 } else if(mode=="direct-retained-alias" || mode=="map-owned-alias" || mode=="erased-old-alias") {
   assert(manager.ExecuteAsync(ccScript,retained,cc,{},false,-1)==-1);
   assert(manager.ExecuteAsync(compatScript,retained,compat,{},false,-1)==-1);
   assert(Test::quarantineChecks==quarantineChecks && createdInvokers==allocations);
   assert(InfinityScriptPersistence::Get().protection.participants.empty());
   assert(InfinityScriptPersistence::Snapshot().active==(mode=="map-owned-alias"?2:1));
   if(mode!="erased-old-alias") {
     assert(manager.m_scripts[existing].checkpointContract.empty());
     assert(manager.m_scripts[existing].thread->GetAddon()==foreign);
   }
 } else if(mode=="retained-owner") {
   assert(!manager.GetLanguageInvoker("/foreign/new.py"));
   assert(start(manager,"/foreign/new.py",foreign)==-1);
   assert(manager.ExecuteSync("/foreign/new.py",foreign,{},0,false)==-1);
   assert(manager.GetReusablePluginHandle("/foreign/existing.py")==-1);
   assert(createdInvokers==allocations && resetInvokers==resets && Test::released.size()==releases);
   assert(manager.m_scripts.size()==1 && manager.m_scripts[existing].thread->GetInvoker()==retained);
   assert(InfinityScriptPersistence::Snapshot().active==1);
 } else if(mode=="unobserved-existing" || mode=="real-write-failed") {
   assert(start(manager,"/foreign/new.py",foreign)==-1);
   if(mode=="real-write-failed") {
     InfinityScriptPersistence::Observed(existing);
     const auto token=InfinityScriptPersistence::BeginProtectedOperation(existing,{root+"/profile/settings.xml"},"write");assert(token);
     std::ofstream(root+"/profile/settings.xml")<<"retained-user-data";
     InfinityScriptPersistence::ProtectionFailure("genuine_user_data_write_sync_failed");
     InfinityScriptPersistence::EndProtectedOperation(token);
   }
   assert(InfinityScriptPersistence::BeginWriteProtection(11,{root+"/profile"},{root+"/cache"}));
   assert(InfinityScriptPersistence::CloseParticipantWrites(11));
   assert(!InfinityScriptPersistence::SealEssentialWrites(11));
   assert(!InfinityScriptPersistence::EssentialWritesAuthorized(11));
   assert(InfinityScriptPersistence::Snapshot().active==1);
 } else assert(false);
 assert(checkpointStops==0 && forcedStops==0); // Admission never aborts existing owners.
 return 0;
}
'''


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--runtime',type=Path)
    p.add_argument('--installed-addons',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location('lifetime_peer',ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/test_script_writer_lifetime.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    source=(a.runtime/'xbmc/interfaces/generic/ScriptInvocationManager.cpp' if a.runtime else BASE/'interfaces/generic/ScriptInvocationManager.cpp').read_text()
    if not a.runtime:source=apply_runtime.manager(source)
    classifier=(a.runtime/'xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp' if a.runtime else BASE/'platform/android/activity/InfinityScriptCheckpointContracts.cpp').read_text()
    peers=old.PEERS
    peers=peers.replace('std::string ID()const{return "addon";}', 'std::string name="addon";std::string ID()const{return name;}')
    peers=peers.replace('struct Invoker{', 'inline std::atomic<int> createdInvokers{0},resetInvokers{0};\nstruct Invoker{void Reset(){++resetInvokers;}')
    peers=peers.replace('CLanguageInvokerThread(const LanguageInvokerPtr&i,CScriptInvocationManager*,bool):inv(i){}', 'bool reusable=false;std::string lastScript;CLanguageInvokerThread(const LanguageInvokerPtr&i,CScriptInvocationManager*,bool r):inv(i),reusable(r){}\n bool Reuseable(const std::string& s)const{return reusable && s==lastScript;}')
    peers=peers.replace('void Execute(const std::string&,const std::vector<std::string>&){}', 'void Execute(const std::string& s,const std::vector<std::string>&){lastScript=s;}')
    peers=peers.replace('struct Handler{void Process(){}};', 'struct Handler{void Process(){};LanguageInvokerPtr CreateInvoker(){++createdInvokers;return std::make_shared<Invoker>();}};')
    peers=peers.replace('inline bool suppress=false;', 'inline int quarantineChecks=0;inline bool suppress=false;')
    peers=peers.replace('return Test::suppress;', '++Test::quarantineChecks;return Test::suppress;')
    peers=peers.replace('struct CServiceBroker {', 'using ILanguageInvocationHandler=Handler;\nstruct CServiceBroker {')
    peers=peers.replace('struct URIUtils{', 'struct StringUtils{static void ToLower(std::string&){};};\nstruct URIUtils{static std::string GetExtension(const std::string&){return ".py";}')
    peers=peers.replace('constexpr int LOGERROR=1,LOGINFO=2;', 'constexpr int LOGERROR=1,LOGINFO=2,LOGDEBUG=3;')
    peers=peers.replace('bool IsStartupParticipantAdmissionOpen(){return false;}', 'inline bool startupAdmission=true;bool IsStartupParticipantAdmissionOpen(){return startupAdmission;}')
    peers=peers.replace(' std::string ClassifyScript(const std::string&s,const std::string&){return s=="known.py"?"known":s=="ambient.py"?"nonpersistent:ambient-glass":std::string{};}', ' std::string ClassifyScript(const std::string&,const std::string&);')
    peers=peers.replace('bool CanAdmitCheckpointStartupLocked(const std::string&,const ADDON::AddonPtr&,bool,const LanguageInvokerPtr& = LanguageInvokerPtr())const{return false;}', 'bool CanAdmitCheckpointStartupLocked(const std::string&,const ADDON::AddonPtr&,bool,const LanguageInvokerPtr& = LanguageInvokerPtr())const;')
    peers=peers.replace('std::map<int,Handler*>m_invocationHandlers;', 'using LanguageInvocationHandlerMap=std::map<std::string,Handler*>;LanguageInvocationHandlerMap m_invocationHandlers;')
    peers=peers.replace(' int ExecuteAsync(', ''' LanguageInvokerPtr GetLanguageInvoker(const std::string&);
 LanguageInvokerPtr GetLanguageInvokerForAdmission(const std::string&,const ADDON::AddonPtr&,bool);
 int GetReusablePluginHandle(const std::string&);void BeginShutdown();void BeginCheckpointStartupAdmission();
 int ExecuteAsync(const std::string&,const ADDON::AddonPtr&,const std::vector<std::string>&,bool,int);
 int ExecuteSync(const std::string&,const ADDON::AddonPtr&,const std::vector<std::string>&,uint32_t,bool);
 int ExecuteSync(const std::string&s,const LanguageInvokerPtr&i,const ADDON::AddonPtr&a,const std::vector<std::string>&v,uint32_t,bool){return ExecuteAsync(s,i,a,v,false,-1);}
 int ExecuteAsync(''')
    markers=['void CScriptInvocationManager::BeginCheckpointStartupAdmission()',
             'bool CScriptInvocationManager::CanAdmitCheckpointStartupLocked(',
             'void CScriptInvocationManager::BeginShutdown()',
             'int CScriptInvocationManager::GetReusablePluginHandle(',
             'LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvoker(',
             'LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvokerForAdmission(',
             'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const ADDON::AddonPtr&',
             'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const LanguageInvokerPtr&',
             'int CScriptInvocationManager::ExecuteSync(\n    const std::string& script,\n    const ADDON::AddonPtr&']
    methods='\n'.join(old.method(source,m) for m in markers)
    cases=['normal-37','early-37-and-required','duplicate-resident','identity-and-source','contract-types',
           'hard-shutdown','window-closed','inflight-dispatch','concurrent-inflight-37','retained-owner',
           'direct-retained-alias','map-owned-alias','erased-old-alias','unobserved-existing','real-write-failed']
    results=[]
    with tempfile.TemporaryDirectory(prefix='startup-admission-') as name:
        work=Path(name)
        headers={'InfinityAndroidCheckpoint.h':'#pragma once\n',
                 'utils/Digest.h':'#pragma once\nnamespace KODI {namespace UTILITY {class CDigest {public: enum class Type{SHA256};};}}\n',
                 'Util.h':'#pragma once\n#include "utils/Digest.h"\n#include <map>\n#include <string>\nnamespace Test {inline std::map<std::string,std::string> digests;}\nclass CUtil {public:static std::string GetFileDigest(const std::string& p,KODI::UTILITY::CDigest::Type){return Test::digests[p];}};\n',
                 'filesystem/SpecialProtocol.h':'#pragma once\n#include <string>\nclass CSpecialProtocol {public:static std::string TranslatePath(const std::string& p){return p;}};\n'}
        for rel,data in headers.items():
            path=work/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data)
        files={}
        roots=[a.installed_addons] if a.installed_addons else [ROOT/'repairs/android-checkpoint-shutdown/installed/parent',ROOT/'repairs/android-checkpoint-shutdown/installed/overlay']
        for root in roots:
            for path in root.rglob('*'):
                if path.is_file() and path.suffix in ('.py','.xml'):files[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        mapping=work/'digests';mapping.write_text(''.join(alias+rel+' '+digest+'\n' for rel,digest in files.items() for alias in ['special://home/addons/','special://xbmc/addons/']))
        cpp=work/'test.cpp';cpp.write_text('#include "platform/android/activity/InfinityProtectedWrites.h"\n#include <fstream>\n#include <condition_variable>\n'+peers+'\n'+classifier+'\n'+methods+'\n'+TEST)
        binary=work/'test'
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-pthread','-I'+str(work),'-I'+str(HERE/'runtime/xbmc'),'-I'+str(HERE/'runtime/xbmc/platform/android/activity'),'-I'+str(BASE),str(cpp),'-o',str(binary)],check=True)
        for case in cases:
            root=work/case
            for child in ('profile','cache'):(root/child).mkdir(parents=True)
            result=subprocess.run([str(binary),case,str(mapping),str(root)],capture_output=True,text=True,timeout=15)
            assert result.returncode==0,(case,result.returncode,result.stdout,result.stderr)
            results.append(dict(case=case,passed=True));print(case,'PASS',flush=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(dict(scope='production manager admission methods and actual source classifier; explicit invoker/handler and startup-state peers',
        classifier_sha256=hashlib.sha256(classifier.encode()).hexdigest(),staged_manager_tested=bool(a.runtime),results=results,all_passed=True,
        actual_python_interpreters_started=False,android_shutdown_verified=False,physical_fold_verified=False),indent=2)+'\n')


if __name__=='__main__':main()
