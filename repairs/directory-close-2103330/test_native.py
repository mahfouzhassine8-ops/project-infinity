#!/usr/bin/env python3
"""Exercise actual result-wait/getter bodies with real threads; Kodi APIs are fakes."""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def function(text, signature):
    start=text.index(signature);a=text.index('{',start);depth=1;i=a+1
    while depth:
        depth += (text[i]=='{')-(text[i]=='}');i+=1
    return text[start:i]

PREFIX=r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
using namespace std::chrono_literals;
using CCriticalSection=std::recursive_mutex;
class Event {
 std::mutex m;std::condition_variable cv;bool set=false;
 public:
 void Set(){std::lock_guard<std::mutex> l(m);set=true;cv.notify_all();}
 void Reset(){std::lock_guard<std::mutex> l(m);set=false;}
 bool Wait(std::chrono::milliseconds t){std::unique_lock<std::mutex> l(m);return cv.wait_for(l,t,[&]{return set;});}
};
class CScriptInvocationManager {
 public:
 mutable CCriticalSection m_critSection;bool m_shutdownRequested=false;
 std::atomic<bool> running{true};std::atomic<int> stops{0};
 static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager m;return m;}
 bool IsShutdownRequested() const;
 bool IsRunning(int) const{return running;}
 void Stop(int){++stops;running=false;}
 void reset(){std::unique_lock<CCriticalSection> l(m_critSection);m_shutdownRequested=false;running=true;stops=0;}
 void shutdown(){std::unique_lock<CCriticalSection> l(m_critSection);m_shutdownRequested=true;}
};
namespace XbmcThreads {template<typename T=void>class EndTime{
 std::chrono::steady_clock::time_point end;
 public:template<class D>EndTime(D):end(std::chrono::steady_clock::now()+30ms){}
 bool IsTimePast(){return std::chrono::steady_clock::now()>=end;}
};}
struct Addon{std::string ID()const{return "plugin.test.directory";}};
struct Messenger{bool main=false;bool IsProcessThread()const{return main;}};
struct CGUIDialogProgress{bool WaitOnEvent(Event& e){return e.Wait(300ms);}};
struct WindowManager {bool IsModalDialogTopmost(int)const{return false;}
 template<class T>T* GetWindow(int){static T t;return &t;}};
struct GUI {WindowManager wm;WindowManager& GetWindowManager(){return wm;}};
struct CServiceBroker {static Messenger* GetAppMessenger(){static Messenger m;return &m;}
 static GUI* GetGUI(){static GUI g;return &g;}};
constexpr int WINDOW_DIALOG_PROGRESS=1,LOGDEBUG=0;
struct CLog {template<class...T>static void Log(T...) {}};
struct CGUIDialogBusy {static bool WaitOnEvent(Event& e,int){return e.Wait(300ms);}};
struct CRunningScriptObserver {CRunningScriptObserver(int,Event&){}void Abort(){}};
namespace InfinityShutdownTrace {inline std::atomic<int> records{0};
 template<class...T> void Event(T...){++records;}}
class CScriptRunner {
 public:
 Event m_scriptDone;std::atomic<bool> cancelled{false};bool successful=true;
 std::shared_ptr<Addon> GetAddon()const{return std::make_shared<Addon>();}
 bool IsCancelled()const{return cancelled;}bool IsSuccessful()const{return successful;}
 bool WaitOnScriptResult(int,const std::string&,const std::string&);
};
'''
TESTS=r'''
int main(int argc,char**argv){
 assert(argc==2);auto&m=CScriptInvocationManager::GetInstance();
 m.reset();CServiceBroker::GetAppMessenger()->main=false;
 // Reproduce a pending plugin result while its owner remains running. The
 // owner is deliberately released only after the job has returned, matching
 // the shutdown dependency that the parent result wait cannot resolve.
 CScriptRunner pending;
 auto result=std::async(std::launch::async,[&]{return pending.WaitOnScriptResult(7,"","test");});
 std::this_thread::sleep_for(30ms);m.shutdown();
 auto state=result.wait_for(200ms);
#ifdef EXPECT_PARENT
 assert(state==std::future_status::timeout);
 m.running=false;pending.m_scriptDone.Set();result.get();
 std::cout<<"PASS: exact parent reproduces blocking result wait after global shutdown\n";
#else
 assert(state==std::future_status::ready);assert(!result.get());
 assert(m.running && m.stops==0); // cancelling result does not terminate owner
 std::thread owner([&]{std::ofstream f(argv[1]);f<<"saved-by-owner";f.close();m.running=false;});
 owner.join();std::ifstream f(argv[1]);std::string saved;f>>saved;assert(saved=="saved-by-owner");
 assert(!m.running && m.stops==0);
 assert(InfinityShutdownTrace::records>=1);
 // Existing successful background results retain their normal outcome.
 m.reset();CScriptRunner ok;ok.m_scriptDone.Set();assert(ok.WaitOnScriptResult(8,"","test"));
 assert(m.stops==0);
 // A script's finished-but-unsuccessful result remains unsuccessful.
 m.reset();CScriptRunner failed;failed.successful=false;failed.m_scriptDone.Set();
 assert(!failed.WaitOnScriptResult(9,"","test"));
 // Existing user cancellation outside global shutdown still uses Stop.
 m.reset();CScriptRunner cancel;cancel.cancelled=true;
 assert(!cancel.WaitOnScriptResult(10,"","test"));assert(m.stops==1);
 // The second grace loop must also respond to global shutdown.
 m.reset();CScriptRunner grace;grace.cancelled=true;
 auto g=std::async(std::launch::async,[&]{return grace.WaitOnScriptResult(11,"","test");});
 m.shutdown();assert(g.wait_for(200ms)==std::future_status::ready);assert(!g.get());assert(m.stops==0);
 // Main-thread GUI result behavior is preserved, including global shutdown.
 m.reset();m.shutdown();CServiceBroker::GetAppMessenger()->main=true;
 CScriptRunner gui;gui.m_scriptDone.Set();assert(gui.WaitOnScriptResult(12,"","test"));assert(m.stops==0);
 CServiceBroker::GetAppMessenger()->main=false;
 // Never publish a successful result after global shutdown races a completion.
 m.reset();m.shutdown();CScriptRunner late;late.m_scriptDone.Set();
 assert(!late.WaitOnScriptResult(13,"","test"));assert(m.running && m.stops==0);
 std::cout<<"PASS: 7 real-thread result/owner/GUI/cancellation cases; owner persistence and join preserved\n";
#endif
}
'''

def run(source):
    manager=(source/'xbmc/interfaces/generic/ScriptInvocationManager.cpp').read_text()
    runner=(source/'xbmc/interfaces/generic/ScriptRunner.cpp').read_text()
    getter=function(manager,'bool CScriptInvocationManager::IsShutdownRequested() const')
    body=function(runner,'bool CScriptRunner::WaitOnScriptResult(')
    import re
    old=re.sub(r'#if defined\(TARGET_ANDROID\).*?#endif\n','',body,flags=re.S)
    old=old.replace('    {\n    }','      ;')
    proof=json.loads((HERE/'test-parent.json').read_text())
    assert hashlib.sha256(old.encode()).hexdigest()==proof['wait_body_sha256']
    for forbidden in ('SetDone(', '.detach(', 'Uninitialize(', 'm_scripts.erase', 'exit('):
        assert forbidden not in body
    assert body.count('if (shutdownResultCancelled())')==4
    directory=(source/'xbmc/guilib/listproviders/DirectoryProvider.cpp').read_text()
    bodydir=function(directory,'  bool DoWork() override')
    assert bodydir.count('ShouldCancel(')==3
    assert bodydir.index('ShouldCancel(')<bodydir.index('CDirectory::GetDirectory(')
    assert 'static_cast<unsigned int>(limit)' in bodydir
    for name,digest in proof['protected'].items():
        assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
    with tempfile.TemporaryDirectory(prefix='infinity-result-wait-') as tmp:
        t=Path(tmp)
        for baseline, method in [(True,old),(False,body)]:
            cpp=t/('parent.cpp' if baseline else 'repair.cpp')
            cpp.write_text(PREFIX+getter+'\n'+method+'\n'+TESTS)
            exe=cpp.with_suffix('')
            cmd=['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-DTARGET_ANDROID']
            if baseline:cmd+=['-DEXPECT_PARENT']
            subprocess.run(cmd+[str(cpp),'-o',str(exe)],check=True)
            subprocess.run([str(exe),str(t/'state.txt')],check=True,timeout=5)
    print('PASS: exact parent reproduced; tested five-file delta; protected finalization paths unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    run(p.parse_args().source)
