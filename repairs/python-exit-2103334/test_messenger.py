#!/usr/bin/env python3
"""Execute exact Messenger bodies with real producer/drain threads and stub GUI.

A ThreadMessage move-constructor barrier schedules Stop+Cleanup between the
existing fast check and queue admission without editing either tested body.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess
import native_repair as repair
HERE=Path(__file__).resolve().parent

def function(text,signature):
    start=text.index(signature);pos=text.index('{',start);i=pos+1;depth=1
    while depth:depth+=(text[i]=='{')-(text[i]=='}');i+=1
    return text[start:i]

PREFIX=r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>
using namespace std::chrono_literals;
using CCriticalSection=std::recursive_mutex;
struct Barrier {
 std::mutex mutex;std::condition_variable cv;bool enabled=false,arrived=false,released=false;
 void pause(){std::unique_lock<std::mutex> l(mutex);if(!enabled)return;arrived=true;cv.notify_all();cv.wait(l,[&]{return released;});}
 void reached(){std::unique_lock<std::mutex> l(mutex);assert(cv.wait_for(l,3s,[&]{return arrived;}));}
 void release(){std::lock_guard<std::mutex> l(mutex);released=true;cv.notify_all();}
} barrier;
std::atomic<int> waiting{0},liveMessages{0};
struct CEvent {
 std::mutex m;std::condition_variable cv;bool signalled=false;
 explicit CEvent(bool){}
 void Wait(){std::unique_lock<std::mutex> l(m);++waiting;cv.wait(l,[&]{return signalled;});--waiting;}
 void Set(){std::lock_guard<std::mutex> l(m);signalled=true;cv.notify_all();}
};
struct CThread {static std::thread::id GetCurrentThreadId(){return std::this_thread::get_id();}};
struct CWinSystemBase {int GetGfxContext(){return 0;}};
struct CServiceBroker {static CWinSystemBase* GetWinSystem(){static CWinSystemBase w;return &w;}};
struct CSingleExit {explicit CSingleExit(int){}};
namespace InfinityShutdownTrace {template<class...T>void Event(T...) {}}
constexpr uint32_t TMSG_GUI_MESSAGE=123;
struct ThreadMessage {
 uint32_t dwMessage;std::shared_ptr<CEvent> waitEvent;std::shared_ptr<int> result;
 explicit ThreadMessage(uint32_t id):dwMessage(id){++liveMessages;}
 ThreadMessage(ThreadMessage&& other):dwMessage(other.dwMessage),waitEvent(std::move(other.waitEvent)),result(std::move(other.result)){++liveMessages;barrier.pause();}
 ~ThreadMessage(){--liveMessages;}
 void SetResult(int n){if(result)*result=n;}
};
class CApplicationMessenger {
 public:
 std::queue<ThreadMessage*> m_vecMessages,m_vecWindowMessages;
 CCriticalSection m_critSection;
 std::thread::id m_guiThreadId=std::this_thread::get_id();
 STOP_TYPE m_bStop{false};
 std::atomic<int> dispatched{0};
 int SendMsg(ThreadMessage&&,bool);void Cleanup();void ProcessMessages();void ProcessWindowMessages();
 void Stop(){m_bStop=true;}
 void ProcessMessage(ThreadMessage* m){++dispatched;m->SetResult(42);}
};
'''
TESTS=r'''
void awaitWait(){for(int i=0;i<1000 && waiting.load()==0;++i)std::this_thread::sleep_for(1ms);assert(waiting.load()>0);}
int main(int argc,char**argv){
 assert(argc==3);bool parent=std::string(argv[1])=="parent";std::string test=argv[2];
 CApplicationMessenger app;bool window=test.find("window")!=std::string::npos;
 uint32_t id=window?TMSG_GUI_MESSAGE:17;
 if(test.find("late")==0){
   bool wait=test.find("post")==std::string::npos;barrier.enabled=true;
   auto r=std::async(std::launch::async,[&]{return app.SendMsg(ThreadMessage(id),wait);});
   barrier.reached();app.Stop();app.Cleanup();barrier.release();
   if(parent){
     if(wait)assert(r.wait_for(100ms)==std::future_status::timeout);
     else {assert(r.wait_for(3s)==std::future_status::ready);assert(r.get()==-1);}
     {std::lock_guard<CCriticalSection> l(app.m_critSection);assert(app.m_vecMessages.size()+app.m_vecWindowMessages.size()==1);}
     app.Cleanup(); // Test-only rescue; never used to manufacture a repair pass.
     if(wait){assert(r.wait_for(3s)==std::future_status::ready);assert(r.get()==-1);}
   }else{assert(r.wait_for(3s)==std::future_status::ready);assert(r.get()==-1);}
   assert(app.dispatched==0);
 }else if(test.find("queued")==0){
   auto r=std::async(std::launch::async,[&]{return app.SendMsg(ThreadMessage(id),true);});
   awaitWait();app.Stop();app.Cleanup();assert(r.wait_for(3s)==std::future_status::ready);assert(r.get()==-1);assert(app.dispatched==0);
 }else if(test.find("normal")==0){
   auto r=std::async(std::launch::async,[&]{return app.SendMsg(ThreadMessage(id),true);});
   awaitWait();if(window)app.ProcessWindowMessages();else app.ProcessMessages();
   assert(r.wait_for(3s)==std::future_status::ready && r.get()==42 && app.dispatched==1);
   // Same-thread synchronous route is untouched.
   assert(app.SendMsg(ThreadMessage(id),true)==42 && app.dispatched==2);
 }else if(test=="already-stopped"){
   app.Stop();auto r=std::async(std::launch::async,[&]{return app.SendMsg(ThreadMessage(id),true);});
   assert(r.wait_for(3s)==std::future_status::ready && r.get()==-1 && app.dispatched==0);
 }else assert(false);
 assert(app.m_vecMessages.empty() && app.m_vecWindowMessages.empty());assert(liveMessages==0 && waiting==0);
 std::cout<<"PASS "<<argv[1]<<" "<<test<<" (GUI dependencies stubbed, producer/consumer threads real)\n";
}
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    source=(a.source/repair.MESSENGER).read_text();header=(a.source/repair.MESSENGER_H).read_text()
    proof=json.loads((HERE/'native-delta.json').read_text())
    assert repair.sha(source.encode())==proof['before'][repair.MESSENGER]
    assert repair.sha(header.encode())==proof['before'][repair.MESSENGER_H]
    assert 'void Stop() { m_bStop = true; }' in header
    signatures=['void CApplicationMessenger::Cleanup()', 'int CApplicationMessenger::SendMsg(ThreadMessage&& message, bool wait)', 'void CApplicationMessenger::ProcessMessages()', 'void CApplicationMessenger::ProcessWindowMessages()']
    cases=['late-regular','late-window','late-post-regular','late-post-window','queued-regular','queued-window','normal-regular','normal-window','already-stopped']
    results=[]
    for mode in ('parent','repair'):
        text=source if mode=='parent' else repair.transform(repair.MESSENGER,source)
        bodies='\n'.join(function(text,s) for s in signatures)
        prefix=PREFIX.replace('STOP_TYPE','bool' if mode=='parent' else 'std::atomic<bool>')
        cpp=a.out/(mode+'.cpp');cpp.write_text(prefix+bodies+TESTS);exe=a.out/mode
        subprocess.run(['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror','-DTARGET_ANDROID',str(cpp),'-o',str(exe)],check=True)
        for case in cases:
            r=subprocess.run([str(exe),mode,case],capture_output=True,text=True,timeout=5)
            print(r.stdout,end='');assert r.returncode==0,r.stdout+r.stderr
            results.append(dict(mode=mode,case=case,passed=True))
    report=dict(candidate=2103334,exact_function_bodies=True,parent_orphaned_wait_reproduced=True,
        changed_queue_gate=True,normal_dispatch_preserved=True,tests=results,physical_device_verified=False)
    (a.out/'MESSENGER-TESTS.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
