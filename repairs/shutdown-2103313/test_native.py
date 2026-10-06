#!/usr/bin/env python3
"""Compile production shutdown methods with explicit host dependency fakes.

Real C++ locks, threads and a five-second clock exercise the observed serial
wait class. Python C API and Android are fakes: this is not a device test.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path
import native_patch as patch


def function(text, signature):
    start = text.index(signature)
    end = text.index('\n}', start) + 2
    return text[start:end] + '\n'


def no_includes(text):
    return '\n'.join(x for x in text.splitlines() if not x.startswith(('#include', '#pragma once')))


PREFIX = r'''
#include <algorithm>
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <functional>
#include <future>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <utility>
#include <vector>
using namespace std::chrono_literals;
using CCriticalSection = std::recursive_mutex;
enum { LOGDEBUG, LOGINFO, LOGWARNING, LOGERROR };
struct CLog { template<class... T> static void Log(int,const char*,T&&...) {}
  template<class... T> static void LogF(int,const char*,T&&...) {} };
struct Event {
  std::mutex mutex; std::condition_variable cv; bool signaled{false};
  bool Wait(std::chrono::milliseconds t) {
    std::unique_lock<std::mutex> l(mutex); return cv.wait_for(l,t,[&]{return signaled;});
  }
  void Set() { std::lock_guard<std::mutex> l(mutex); signaled=true; cv.notify_all(); }
};
namespace XBMCAddon { namespace xbmc {
struct Monitor { std::atomic<int> notices{0}; Event event;
  void AbortNotify() { ++notices; event.Set(); }
};
}}
template<class T> struct LockableType: public T, public CCriticalSection {};
using MonitorCallbackList=LockableType<std::vector<XBMCAddon::xbmc::Monitor*>>;
#define XBMC_TRACE
class XBPython {
public:
  void RegisterPythonMonitorCallBack(XBMCAddon::xbmc::Monitor*);
  void BeginShutdown(); bool ShutdownGraceExpired() const;
  bool IsShutdownRequested() const { return m_shutdownDeadlineMs.load()!=0; }
  MonitorCallbackList m_vecMonitorCallbackList;
  std::atomic<int64_t> m_shutdownDeadlineMs{0};
};
struct Messenger { int pulses{0}; bool IsProcessThread(){return true;}
  void ProcessMessages(){ ++pulses; }
};
struct CServiceBroker {
  static XBPython python; static Messenger messenger;
  static XBPython& GetXBPython(){ return python; }
  static Messenger* GetAppMessenger(){return &messenger;}
};
XBPython CServiceBroker::python; Messenger CServiceBroker::messenger;
namespace ADDON { struct Addon {}; using AddonPtr=std::shared_ptr<Addon>; }
class ILanguageInvoker { public: virtual ~ILanguageInvoker()=default; void Reset() {} };
using LanguageInvokerPtr=std::shared_ptr<ILanguageInvoker>;
struct ILanguageInvocationHandler {
  void Initialize(){} void Uninitialize(){} void Process(){}
  ILanguageInvoker* CreateInvoker(){ return new ILanguageInvoker; }
};
class CScriptInvocationManager;
class CLanguageInvokerThread {
public:
  CLanguageInvokerThread(LanguageInvokerPtr p,CScriptInvocationManager*,bool): invoker(p){}
  LanguageInvokerPtr invoker; int id{-1}; int stops{0};
  std::function<void()> stopping;
  static std::function<void()> dispatch;
  bool Reuseable(const std::string&){return false;}
  void Release(){} LanguageInvokerPtr GetInvoker(){return invoker;}
  void SetAddon(const ADDON::AddonPtr&){} void SetId(int v){id=v;} int GetId(){return id;}
  void Execute(const std::string&,const std::vector<std::string>&){if(dispatch)dispatch();}
  bool Stop(bool){++stops;if(stopping)stopping();return true;}
};
std::function<void()> CLanguageInvokerThread::dispatch;
struct CFileUtils { static bool Exists(const std::string&,bool=true){return true;} };
struct URIUtils { static std::string GetExtension(const std::string&){return ".py";} };
struct StringUtils {
  static void ToLower(std::string&){}
  static bool StartsWithNoCase(const std::string& a,const std::string& b){return a.rfind(b,0)==0;}
};
namespace KODI { namespace TIME {
  void Sleep(std::chrono::milliseconds t){std::this_thread::sleep_for(t);}
}}
'''

INVOKER_STUB = r'''
struct Interpreter;
struct PyObject {};
PyObject exceptionObject; PyObject* PyExc_SystemExit=&exceptionObject;
struct PyThreadState { Interpreter* interp; PyObject* async_exc{nullptr}; };
struct Interpreter { PyThreadState* head{nullptr}; };
std::atomic<int> gilAcquires{0}, injected{0};
PyThreadState* currentState=nullptr;
PyThreadState* PyThreadState_New(Interpreter* i){return new PyThreadState{i};}
void PyEval_RestoreThread(PyThreadState* p){currentState=p;++gilAcquires;}
void PyThreadState_Clear(PyThreadState*){}
void PyThreadState_DeleteCurrent(){delete currentState;currentState=nullptr;}
PyThreadState* PyInterpreterState_ThreadHead(Interpreter* i){return i->head;}
PyThreadState* PyThreadState_Next(PyThreadState*){return nullptr;}
void Py_XDECREF(PyObject*){} void Py_XINCREF(PyObject*){++injected;}
struct CSingleExit { CCriticalSection& lock;
  CSingleExit(CCriticalSection& l):lock(l){lock.unlock();} ~CSingleExit(){lock.lock();}
};
namespace XbmcThreads {
template<class T=void> struct EndTime {
  std::chrono::steady_clock::time_point end;
  EndTime(std::chrono::milliseconds t):end(std::chrono::steady_clock::now()+t){}
  bool IsTimePast(){return std::chrono::steady_clock::now()>=end;}
  auto GetTimeLeft(){return std::max(0ms,std::chrono::duration_cast<std::chrono::milliseconds>(end-std::chrono::steady_clock::now()));}
};
}
#define PYTHON_SCRIPT_TIMEOUT 5000ms
enum { InvokerStateRunning,InvokerStateStopping,InvokerStateExecutionDone,InvokerStateFailed };
class CPythonInvoker {
public:
  CCriticalSection m_critical; bool m_stop{false}; int state{InvokerStateRunning};
  Interpreter interpreter; PyThreadState thread{&interpreter}; PyThreadState* m_threadState{&thread};
  bool m_addon{true}; std::string m_sourceFile{"service.py"}; Event m_stoppedEvent;
  int notifications{0}; CPythonInvoker(){interpreter.head=&thread;}
  bool IsRunning(){return state==InvokerStateRunning;} void setState(int v){state=v;}
  int GetId(){return 7;} void AbortNotification(){++notifications;}
  void pulseGlobalEvent(){} bool stop(bool);
};
'''

SERVICE_STUB = r'''
namespace ADDON {
struct Events { template<class T> void Unsubscribe(T*) {} };
struct CAddonMgr { ADDON::Events events; ADDON::Events& Events(){return events;}
  ADDON::Events& UnloadEvents(){return events;}
};
class CServiceAddonManager {
public:
  CAddonMgr m_addonMgr; CCriticalSection m_criticalSection; std::map<std::string,int> m_services;
  void Stop(); void Stop(const std::string&);
  void Stop(const std::map<std::string,int>::value_type&);
};
}
'''

TESTS = r'''
bool anotherThreadCanLock(CCriticalSection& lock) {
  return std::async(std::launch::async,[&]{bool ok=lock.try_lock();if(ok)lock.unlock();return ok;}).get();
}
auto install(CScriptInvocationManager& m,int id) {
  auto t=std::make_shared<CLanguageInvokerThread>(std::make_shared<ILanguageInvoker>(),&m,false);
  t->SetId(id);std::string path=std::to_string(id)+".py";
  m.m_scripts[id]={t,path,false};m.m_scriptPaths[path]=id;return t;
}
int main(){
  auto& m=CScriptInvocationManager::GetInstance();
  auto reset=[&]{m.m_scripts.clear();m.m_scriptPaths.clear();m.m_lastInvokerThread.reset();m.m_shutdownRequested=false;};
  // Both Stop overloads must allow worker callbacks to take the registry lock.
  for(bool byPath:{false,true}) {
    reset();auto t=install(m,1);t->stopping=[&]{assert(anotherThreadCanLock(m.m_critSection));};
    assert(byPath?m.Stop(std::string("1.py"),true):m.Stop(1,true));assert(t->stops==1);
  }
  // Real reentrant Process() removes the next item while stopping the first.
  reset();auto a=install(m,1),b=install(m,2);
  a->stopping=[&]{m.OnExecutionDone(2);m.Process();};
  m.StopRunningScripts();assert(a->stops==1&&b->stops==1);assert(m.m_scripts.count(2)==0);
  // Service registry must also be unlocked during script callbacks.
  for(bool single:{false,true}) {
    reset();auto t=install(m,3);ADDON::CServiceAddonManager services;services.m_services["service"]=3;
    t->stopping=[&]{assert(anotherThreadCanLock(services.m_criticalSection));assert(anotherThreadCanLock(m.m_critSection));};
    if(single)services.Stop(std::string("service"));else services.Stop();
    assert(t->stops==1&&services.m_services.empty());
  }
  // Dispatch already admitted must finish before the shutdown gate closes.
  reset();std::promise<void> entered,release;auto allow=release.get_future().share();
  CLanguageInvokerThread::dispatch=[&]{entered.set_value();allow.wait();};
  auto launch=std::async(std::launch::async,[&]{return m.ExecuteAsync("live.py",std::make_shared<ILanguageInvoker>());});
  entered.get_future().wait();
  auto closing=std::async(std::launch::async,[&]{m.BeginShutdown();});
  assert(closing.wait_for(30ms)==std::future_status::timeout);
  release.set_value();assert(launch.get()>=0);closing.get();CLanguageInvokerThread::dispatch=nullptr;
  assert(!m.GetLanguageInvoker("new.py"));
  assert(m.ExecuteAsync("new.py",std::make_shared<ILanguageInvoker>())==-1);
  assert(m.ExecuteAsync("new.py",ADDON::AddonPtr())==-1);reset();
  // All monitors are signaled before waiting; late registrations cannot miss it.
  auto& py=CServiceBroker::python;XBMCAddon::xbmc::Monitor monitors[8];
  for(int i=0;i<7;++i)py.RegisterPythonMonitorCallBack(&monitors[i]);
  py.BeginShutdown();const auto deadline=py.m_shutdownDeadlineMs.load();
  for(int i=0;i<7;++i)assert(monitors[i].event.Wait(0ms));
  py.RegisterPythonMonitorCallBack(&monitors[7]);assert(monitors[7].event.Wait(0ms));
  std::this_thread::sleep_for(20ms);py.BeginShutdown();assert(py.m_shutdownDeadlineMs.load()==deadline);
  // Execute the actual production stop loop for seven non-cooperating invokers.
  // The old implementation spends 35s here; the new one shares one 5s deadline.
  const auto started=std::chrono::steady_clock::now();
  CPythonInvoker invokers[7];
  for(auto& inv:invokers){assert(inv.stop(false));assert(inv.notifications==0);}
  const auto elapsed=std::chrono::steady_clock::now()-started;
  assert(elapsed>=4500ms&&elapsed<6500ms);assert(injected==7);assert(gilAcquires==7);
  assert(CServiceBroker::messenger.pulses>0);
  // The accepted individual-stop path still delivers its own abort notification.
  py.m_shutdownDeadlineMs.store(0);assert(!py.ShutdownGraceExpired());
  CPythonInvoker individual;individual.m_stoppedEvent.Set();
  assert(individual.stop(false));assert(individual.notifications==1);
  py.m_vecMonitorCallbackList.clear();reset();
  std::cout<<"PASS: production registry stop/join unlock, reentrant snapshot, service unlock, admission race, late monitor, shared seven-script grace, ordinary abort; elapsed_ms="
           <<std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count()<<"\n";
}
'''


def run(source):
    parent = {n: (source/n).read_text() for n in patch.ALLOWED}
    for name, text in parent.items():
        assert patch.digest(text.encode()) == patch.PREIMAGES[name], name
    changed = {n: patch.transform(n, text) for n, text in parent.items()}
    # Retain final native cleanup/saves and the previously accepted GIL teardown.
    for marker in ('bool CApplication::Stop(int exitCode)',):
        assert changed[patch.APP].split(marker,1)[1] == parent[patch.APP].split(marker,1)[1]
    for signature in ('void CPythonInvoker::onExecutionDone()', 'void CPythonInvoker::onExecutionFailed()'):
        assert function(changed[patch.INVOKER],signature)==function(parent[patch.INVOKER],signature)
    assert changed[patch.APP].index('GetSettings()->Save();', changed[patch.APP].index('PrepareAndroidShutdownScripts')) < changed[patch.APP].index('GetInstance().BeginShutdown();')
    header = no_includes(changed[patch.MANAGER_H]).replace('protected:', 'public:').replace('private:', 'public:')
    code = PREFIX + header + no_includes(changed[patch.MANAGER])
    for sig in ('void XBPython::BeginShutdown()', 'bool XBPython::ShutdownGraceExpired() const',
                'void XBPython::RegisterPythonMonitorCallBack('):
        code += function(changed[patch.PYTHON], sig)
    code += INVOKER_STUB + function(changed[patch.INVOKER], 'bool CPythonInvoker::stop(bool abort)')
    code += SERVICE_STUB
    for sig in ('void CServiceAddonManager::Stop()', 'void CServiceAddonManager::Stop(const std::string& addonId)',
                'void CServiceAddonManager::Stop(const std::map<std::string, int>::value_type& service)'):
        code += 'namespace ADDON {\n' + function(changed[patch.SERVICE],sig) + '}\n'
    code += TESTS
    with tempfile.TemporaryDirectory(prefix='infinity-shutdown-') as tmp:
        cpp=Path(tmp)/'production_shutdown.cpp';cpp.write_text(code)
        binary=Path(tmp)/'shutdown_test'
        subprocess.run(['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror',
                        '-Wno-unused-parameter',str(cpp),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True,timeout=15)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    run(p.parse_args().source)
