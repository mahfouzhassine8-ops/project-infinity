#!/usr/bin/env python3
"""Compile production admission/completion/Process/ledger methods with controlled peers.

Unlike interpreter liveness tests, proves a completed unknown admission cannot
vanish from the persistence obligations before a checkpoint request.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def method(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


PEERS = r'''
#include "platform/android/activity/InfinityScriptPersistence.h"
#include <algorithm>
#include <atomic>
#include <cassert>
#include <chrono>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <vector>
using CCriticalSection=std::recursive_mutex;
namespace ADDON {struct Addon {std::string ID()const{return "addon";}};using AddonPtr=std::shared_ptr<Addon>;}
inline std::atomic<int> checkpointStops{0};
inline std::atomic<int> forcedStops{0};
struct Invoker{bool Stop(bool abort){if(abort)++forcedStops;else ++checkpointStops;return true;}};using LanguageInvokerPtr=std::shared_ptr<Invoker>;
class CScriptInvocationManager;
struct CLanguageInvokerThread{
 LanguageInvokerPtr inv;ADDON::AddonPtr addon;int id=-1;
 CLanguageInvokerThread(const LanguageInvokerPtr&i,CScriptInvocationManager*,bool):inv(i){}
 LanguageInvokerPtr GetInvoker()const{return inv;}
 void SetAddon(const ADDON::AddonPtr&a){addon=a;} ADDON::AddonPtr GetAddon()const{return addon;}
 void SetId(int i){id=i;}int GetId()const{return id;}
 void Execute(const std::string&,const std::vector<std::string>&){}
 void Release();
 bool Stop(bool wait){Release();return inv->Stop(wait);}
};using CLanguageInvokerThreadPtr=std::shared_ptr<CLanguageInvokerThread>;
struct Handler{void Process(){}};
namespace Test {
inline std::vector<int> aborted;inline std::vector<int> released;
inline bool suppress=false;inline int quarantinedFailures=0;inline int quarantineSuccesses=0;
}
inline void CLanguageInvokerThread::Release(){Test::released.push_back(GetId());}
struct Python {void NotifyScriptAborting(CLanguageInvokerThread* t){Test::aborted.push_back(t->GetId());}};
struct CServiceBroker {static Python& GetXBPython(){static Python p;return p;}};
struct CFileUtils{static bool Exists(const std::string&,bool){return true;}};
struct URIUtils{static std::string GetFileName(const std::string&s){return s;}};
constexpr int LOGERROR=1,LOGINFO=2;struct CLog{template<class...T>static void Log(T...) {}};
namespace InfinityShutdownTrace {
inline void Event(const char*,const char*,long long=-1,unsigned long long=0,unsigned long long=0,
                  long long=0,const char*=nullptr,const char*="observed",const char*=nullptr) noexcept {}
}
namespace InfinityAndroidCheckpoint {
 inline bool active=false;inline int failures=0;inline std::string lastFailure;
 std::string ClassifyScript(const std::string&s,const std::string&){return s=="known.py"?"known":s=="ambient.py"?"nonpersistent:ambient-glass":std::string{};}
 bool IsActive(){return active;}void RecordFailure(const char*,const char* detail){++failures;lastFailure=detail;}
}
namespace InfinityAddonQuarantine {
 bool ShouldSuppress(const std::string&,const std::string&){return Test::suppress;}
 void RecordCleanFailure(const std::string&,const std::string&){++Test::quarantinedFailures;}
 void RecordCleanSuccess(const std::string&,const std::string&){++Test::quarantineSuccesses;}
}
std::string VerifiedCheckpointContract(const std::string&s,const CLanguageInvokerThreadPtr&,const std::string& c){return InfinityAndroidCheckpoint::ClassifyScript(s,"addon")==c?c:std::string{};}
class CScriptInvocationManager {public:
 struct LanguageInvokerThread{CLanguageInvokerThreadPtr thread;std::string script;bool done;std::string checkpointContract;};
 using LanguageInvokerThreadMap=std::map<int,LanguageInvokerThread>;
 LanguageInvokerThreadMap m_scripts;std::map<std::string,int>m_scriptPaths;
 std::map<int,Handler*>m_invocationHandlers;CLanguageInvokerThreadPtr m_lastInvokerThread;
 int m_lastPluginHandle=-1,m_nextId=0;mutable CCriticalSection m_critSection;bool m_shutdownRequested=false;
 std::chrono::steady_clock::time_point m_androidCheckpointRetirementStarted{};
 bool m_androidCheckpointRetirementArmed=false;
 std::set<int>m_androidCheckpointEscalatedIds;
 std::size_t m_androidCheckpointEscalationsActive=0;
 std::vector<std::string>m_checkpointUnresolvedWriterLedger;
 int ExecuteAsync(const std::string&,const LanguageInvokerPtr&,const ADDON::AddonPtr&,const std::vector<std::string>&,bool,int);
 std::vector<std::string>AndroidCheckpointUnresolvedWriters()const;
 std::size_t AndroidCheckpointEscalationsActive()const;
 void OnExecutionDone(int);void Process();void BeginAndroidCheckpoint();void PumpAndroidCheckpointRetirement(bool=false);
};
'''
TEST = r'''
int main(){
 auto addon=std::make_shared<ADDON::Addon>();
 CScriptInvocationManager m;
 Test::suppress=true;
 assert(m.ExecuteAsync("service.py",std::make_shared<Invoker>(),addon,{},false,-1)==-1);
 assert(m.AndroidCheckpointUnresolvedWriters().empty());
 Test::suppress=false;
 const int id=m.ExecuteAsync("unknown.py",std::make_shared<Invoker>(),addon,{},false,-1);
 assert(id>=0);assert(m.AndroidCheckpointUnresolvedWriters().size()==2);
 m.OnExecutionDone(id);assert(InfinityAndroidCheckpoint::failures==0);
 m.Process();assert(m.m_scripts.empty());
 auto unresolved=m.AndroidCheckpointUnresolvedWriters();assert(unresolved.size()==1);assert(unresolved[0]=="addon:unknown.py");
 // Reused unknown executions also cannot evade admission bookkeeping.
 m.ExecuteAsync("another.py",m.m_lastInvokerThread->GetInvoker(),addon,{},true,-1);
 assert(m.AndroidCheckpointUnresolvedWriters().size()==2);
 for(int n=0;n<100;++n){int i=m.ExecuteAsync("unknown.py",std::make_shared<Invoker>(),addon,{},false,-1);m.OnExecutionDone(i);m.Process();}
 assert(m.AndroidCheckpointUnresolvedWriters().size()==8);
 CScriptInvocationManager known;int k=known.ExecuteAsync("known.py",std::make_shared<Invoker>(),addon,{},false,-1);known.OnExecutionDone(k);known.Process();assert(known.AndroidCheckpointUnresolvedWriters().empty());
 CScriptInvocationManager closed;closed.m_shutdownRequested=true;assert(closed.ExecuteAsync("unknown.py",std::make_shared<Invoker>(),addon,{},false,-1)==-1);assert(closed.AndroidCheckpointUnresolvedWriters().empty());
 InfinityAndroidCheckpoint::active=true;int x=known.ExecuteAsync("unknown.py",std::make_shared<Invoker>(),addon,{},false,-1);known.OnExecutionDone(x);assert(InfinityAndroidCheckpoint::failures==1);
 assert(InfinityAndroidCheckpoint::lastFailure=="foreign_invoker_finished_without_persistence_receipt;id="+std::to_string(x)+";addon=addon;script=unknown.py");
 // A no-addon exact memory-only contract receives the checkpoint-safe stop signal, while
 // the canonical resident stays alive to complete its PREPARE/FINALIZE protocol.
 CScriptInvocationManager stopping;stopping.m_nextId=2000;
 const int resident=stopping.ExecuteAsync("known.py",std::make_shared<Invoker>(),addon,{},false,-1);
 const int ambient=stopping.ExecuteAsync("ambient.py",std::make_shared<Invoker>(),nullptr,{},false,-1);
 const int unknown=stopping.ExecuteAsync("other.py",std::make_shared<Invoker>(),addon,{},false,-1);
 assert(stopping.m_scripts[ambient].checkpointContract=="nonpersistent:ambient-glass");
 stopping.BeginAndroidCheckpoint();assert(stopping.m_shutdownRequested);
 assert(Test::aborted==std::vector<int>({ambient,unknown}));
 assert(checkpointStops==2);
 assert(Test::released==std::vector<int>({ambient,unknown}));
 assert(std::find(Test::released.begin(),Test::released.end(),resident)==Test::released.end());
 assert(stopping.m_scripts[resident].checkpointContract=="known");
 // Only the still-running FOREIGN writer is escalated. Verified resident and
 // nonpersistent contracts are never forced by the checkpoint escalation pass.
 stopping.PumpAndroidCheckpointRetirement(true);
 for(int n=0;n<200 && stopping.AndroidCheckpointEscalationsActive()!=0;++n)
   std::this_thread::sleep_for(std::chrono::milliseconds(1));
 assert(stopping.AndroidCheckpointEscalationsActive()==0);
 assert(forcedStops.load()==1);
 assert(stopping.m_androidCheckpointEscalatedIds.count(unknown)==1);
 assert(stopping.m_androidCheckpointEscalatedIds.count(resident)==0);
 assert(stopping.m_androidCheckpointEscalatedIds.count(ambient)==0);
 // Two Command Center default invocations overlap. Each completion must use
 // its own actual interpreter retirement, never the shared basename counter.
 CScriptInvocationManager concurrent;concurrent.m_nextId=1000;
 const int first=concurrent.ExecuteAsync("default.py",std::make_shared<Invoker>(),addon,{},false,-1);
 const int second=concurrent.ExecuteAsync("default.py",std::make_shared<Invoker>(),addon,{},false,-1);
 InfinityScriptPersistence::Observed(first);InfinityScriptPersistence::Retired(first);
 assert(!InfinityScriptPersistence::DurableRetirement("addon:default.py"));
 const int failureCount=InfinityAndroidCheckpoint::failures;
 concurrent.OnExecutionDone(first);assert(InfinityAndroidCheckpoint::failures==failureCount);
 assert(!InfinityScriptPersistence::TakeInterpreterRetirement(first)); // One-use manager receipt.
 InfinityScriptPersistence::Observed(second);InfinityScriptPersistence::Retired(second);
 concurrent.OnExecutionDone(second);assert(InfinityAndroidCheckpoint::failures==failureCount);
 // An unrelated writer's sticky failure blocks GLOBAL saving but does not
 // masquerade as a missing receipt in a healthy Command Center invocation.
 InfinityScriptPersistence::Admit(999,"ambient.py");
 InfinityScriptPersistence::Fail(999,"external_or_opaque_writer_requires_explicit_participant");
 const int healthy=concurrent.ExecuteAsync("default.py",std::make_shared<Invoker>(),addon,{},false,-1);
 InfinityScriptPersistence::Observed(healthy);InfinityScriptPersistence::Retired(healthy);
 concurrent.OnExecutionDone(healthy);
 assert(InfinityAndroidCheckpoint::lastFailure=="python_writer:external_or_opaque_writer_requires_explicit_participant");
 assert(!InfinityScriptPersistence::PollCommit());
 // A cleanly retired uncaught SERVICE failure may become a quarantine strike.
 CScriptInvocationManager quarantine;
 const int q=quarantine.ExecuteAsync("service.py",std::make_shared<Invoker>(),addon,{},false,-1);
 InfinityScriptPersistence::Observed(q);
 InfinityScriptPersistence::Fail(q,"uncaught_script_failure_before_persistence_receipt");
 InfinityScriptPersistence::Retired(q);
 quarantine.OnExecutionDone(q);
 assert(Test::quarantinedFailures==1);
 assert(Test::quarantineSuccesses==0);
 // A later clean service retirement clears a pending strike in the real policy.
 const int qs=quarantine.ExecuteAsync("service.py",std::make_shared<Invoker>(),addon,{},false,-1);
 InfinityScriptPersistence::Observed(qs);InfinityScriptPersistence::Retired(qs);
 quarantine.OnExecutionDone(qs);
 assert(Test::quarantineSuccesses==1);
 // Checkpoint-forced retirement is diagnostic evidence, not proof that a
 // quarantined service had a normal clean runtime. It must not auto-heal.
 const int qe=quarantine.ExecuteAsync("service.py",std::make_shared<Invoker>(),addon,{},false,-1);
 InfinityScriptPersistence::Observed(qe);InfinityScriptPersistence::Retired(qe);
 quarantine.m_androidCheckpointEscalatedIds.insert(qe);
 quarantine.OnExecutionDone(qe);
 assert(Test::quarantineSuccesses==1);
 assert(quarantine.m_androidCheckpointEscalatedIds.count(qe)==0);
 // Hard persistence uncertainty never becomes a quarantine excuse.
 const int qb=quarantine.ExecuteAsync("service.py",std::make_shared<Invoker>(),addon,{},false,-1);
 InfinityScriptPersistence::Observed(qb);
 InfinityScriptPersistence::Fail(qb,"external_or_opaque_writer_requires_explicit_participant");
 InfinityScriptPersistence::Retired(qb);
 quarantine.OnExecutionDone(qb);
 assert(Test::quarantinedFailures==1);

 // Re-admission clears stale invocation proof; missing retirement still fails.
 InfinityScriptPersistence::Admit(healthy,"addon:default.py");
 assert(!InfinityScriptPersistence::TakeInterpreterRetirement(healthy));
}
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True);args=parser.parse_args()
    source=(args.runtime/'xbmc/interfaces/generic/ScriptInvocationManager.cpp').read_text()
    python=(args.runtime/'xbmc/interfaces/python/PythonInvoker.cpp').read_text()
    assert 'if (!abort && InfinityAndroidCheckpoint::IsActive())' in python
    assert '(!m_stop || InfinityAndroidCheckpoint::IsActive())' in python
    checkpoint_branch=python.split('if (!abort && InfinityAndroidCheckpoint::IsActive())',1)[1].split('#endif',1)[0]
    assert 'PyExc_SystemExit' not in checkpoint_branch and 'm_stoppedEvent.Wait' not in checkpoint_branch
    assert 'script.module.slyguy' in source and 'seeded_fold_startup_error' in source
    assert 'record.failures >= 2' in source and 'RecordCleanSuccess' in source
    assert 'ConsumeProbeRequest' in source and 'registry.probation' in source
    assert 'restored_after_probation' in source and 'AndroidQuarantineSuppressErrorToast' in source
    assert 'scripts.checkpoint_escalation_start' in source and '!checkpointEscalated' in source
    methods=[method(source,'void CScriptInvocationManager::Process()'),
             method(source,'std::vector<std::string> CScriptInvocationManager::AndroidCheckpointUnresolvedWriters() const'),
             method(source,'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const LanguageInvokerPtr&'),
             method(source,'void CScriptInvocationManager::OnExecutionDone(int scriptId)'),
             method(source,'void CScriptInvocationManager::BeginAndroidCheckpoint()'),
             method(source,'void CScriptInvocationManager::PumpAndroidCheckpointRetirement(bool force)'),
             method(source,'std::size_t CScriptInvocationManager::AndroidCheckpointEscalationsActive() const')]
    with tempfile.TemporaryDirectory(prefix='script-lifetime-') as directory:
        directory=Path(directory);(directory/'test.cpp').write_text(PEERS+'\n'.join(methods)+TEST)
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-DHAS_PYTHON','-Wall','-Wextra','-Werror','-pthread','-I',str(args.runtime/'xbmc'),str(directory/'test.cpp'),'-o',str(directory/'test')],check=True)
        subprocess.run([str(directory/'test')],check=True)
    print('PASS: production script lifetime + bounded checkpoint escalation + persistence-gated quarantine')
if __name__=='__main__':main()
