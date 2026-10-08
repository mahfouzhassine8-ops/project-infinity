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
#include <cassert>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
using CCriticalSection=std::recursive_mutex;
namespace ADDON {struct Addon {std::string ID()const{return "addon";}};using AddonPtr=std::shared_ptr<Addon>;}
struct Invoker{};using LanguageInvokerPtr=std::shared_ptr<Invoker>;
class CScriptInvocationManager;
struct CLanguageInvokerThread{
 LanguageInvokerPtr inv;ADDON::AddonPtr addon;int id=-1;
 CLanguageInvokerThread(const LanguageInvokerPtr&i,CScriptInvocationManager*,bool):inv(i){}
 LanguageInvokerPtr GetInvoker()const{return inv;}
 void SetAddon(const ADDON::AddonPtr&a){addon=a;} ADDON::AddonPtr GetAddon()const{return addon;}
 void SetId(int i){id=i;}int GetId()const{return id;}
 void Execute(const std::string&,const std::vector<std::string>&){}
};using CLanguageInvokerThreadPtr=std::shared_ptr<CLanguageInvokerThread>;
struct Handler{void Process(){}};
struct CFileUtils{static bool Exists(const std::string&,bool){return true;}};
struct URIUtils{static std::string GetFileName(const std::string&s){return s;}};
constexpr int LOGERROR=1;struct CLog{template<class...T>static void Log(T...) {}};
namespace InfinityAndroidCheckpoint {
 inline bool active=false;inline int failures=0;
 std::string ClassifyScript(const std::string&s,const std::string&){return s=="known.py"?"known":std::string{};}
 bool IsActive(){return active;}void RecordFailure(const char*,const char*){++failures;}
}
std::string VerifiedCheckpointContract(const std::string&s,const CLanguageInvokerThreadPtr&,const std::string& c){return InfinityAndroidCheckpoint::ClassifyScript(s,"addon")==c?c:std::string{};}
class CScriptInvocationManager {public:
 struct LanguageInvokerThread{CLanguageInvokerThreadPtr thread;std::string script;bool done;std::string checkpointContract;};
 using LanguageInvokerThreadMap=std::map<int,LanguageInvokerThread>;
 LanguageInvokerThreadMap m_scripts;std::map<std::string,int>m_scriptPaths;
 std::map<int,Handler*>m_invocationHandlers;CLanguageInvokerThreadPtr m_lastInvokerThread;
 int m_lastPluginHandle=-1,m_nextId=0;mutable CCriticalSection m_critSection;bool m_shutdownRequested=false;
 std::vector<std::string>m_checkpointUnresolvedWriterLedger;
 int ExecuteAsync(const std::string&,const LanguageInvokerPtr&,const ADDON::AddonPtr&,const std::vector<std::string>&,bool,int);
 std::vector<std::string>AndroidCheckpointUnresolvedWriters()const;
 void OnExecutionDone(int);void Process();
};
'''
TEST = r'''
int main(){
 auto addon=std::make_shared<ADDON::Addon>();
 CScriptInvocationManager m;
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
}
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True);args=parser.parse_args()
    source=(args.runtime/'xbmc/interfaces/generic/ScriptInvocationManager.cpp').read_text()
    methods=[method(source,'void CScriptInvocationManager::Process()'),
             method(source,'std::vector<std::string> CScriptInvocationManager::AndroidCheckpointUnresolvedWriters() const'),
             method(source,'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const LanguageInvokerPtr&'),
             method(source,'void CScriptInvocationManager::OnExecutionDone(int scriptId)')]
    with tempfile.TemporaryDirectory(prefix='script-lifetime-') as directory:
        directory=Path(directory);(directory/'test.cpp').write_text(PEERS+'\n'.join(methods)+TEST)
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-pthread',str(directory/'test.cpp'),'-o',str(directory/'test')],check=True)
        subprocess.run([str(directory/'test')],check=True)
    print('PASS: production admission/completion/removal/ledger methods retain unknown lifetime obligations')
if __name__=='__main__':main()
