#!/usr/bin/env python3
"""Execute approved and corrected Kodi Monitor methods with concurrent peers."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile
from cooperative_abort import PINS, transform


def method(text, marker):
    start = text.index(marker)
    opening = text.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


PEERS = r'''
#include <algorithm>
#include <atomic>
#include <chrono>
#include <memory>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <vector>
using CCriticalSection = std::recursive_mutex;
namespace InfinityAndroidCheckpoint {
std::atomic<bool> active{false};
bool IsActive() { return active.load(); }
}
namespace XBMCAddon { namespace xbmc {
struct Monitor {
  long id; std::atomic<bool> abort{false};
  explicit Monitor(long value):id(value){}
  long GetInvokerId() const { return id; }
  void AbortNotify() { abort.store(true); }
};
}}
struct ILanguageInvoker {
  long id; explicit ILanguageInvoker(long value):id(value){}
  long GetId() const { return id; }
};
struct MonitorCallbackList : std::vector<XBMCAddon::xbmc::Monitor*>, CCriticalSection {};
template<class T> bool check(MonitorCallbackList& list,T pointer) {
  std::lock_guard<CCriticalSection> lock(list);
  return std::find(list.begin(), list.end(), pointer)!=list.end();
}
#define XBMC_TRACE
#define LOCK_AND_COPY(type, target, source) type target; {std::lock_guard<CCriticalSection> lock(source); target.assign(source.begin(),source.end());}
#define CHECK_FOR_ENTRY(source,pointer) check(source,pointer)
struct XBPython {
  MonitorCallbackList m_vecMonitorCallbackList;
  std::set<long> m_checkpointAbortedInvokerIds;
  bool globalShutdown=false;
  bool IsShutdownRequested() const { return globalShutdown; }
  void RegisterPythonMonitorCallBack(XBMCAddon::xbmc::Monitor*);
  void NotifyScriptAborting(ILanguageInvoker*);
};
'''

CASES = r'''
int main(int argc,char** argv) {
  const std::string name=argv[1];
  XBPython python; ILanguageInvoker invoker(17);
  using XBMCAddon::xbmc::Monitor;
  InfinityAndroidCheckpoint::active = name != "normal_running";
  if (name=="normal_running") {
    Monitor monitor(17);python.RegisterPythonMonitorCallBack(&monitor);
    if(monitor.abort) return 3;
    python.NotifyScriptAborting(&invoker);
    if(!monitor.abort) return 3;
    Monitor later(17);python.RegisterPythonMonitorCallBack(&later);
    if(later.abort) return 3;
  } else if(name=="existing_monitor") {
    Monitor monitor(17);python.RegisterPythonMonitorCallBack(&monitor);
    python.NotifyScriptAborting(&invoker);if(!monitor.abort) return 3;
  } else if(name=="late_monitor" || name=="recreated_monitor") {
    if(name=="recreated_monitor") {
      Monitor first(17);python.RegisterPythonMonitorCallBack(&first);
      python.NotifyScriptAborting(&invoker);
      std::lock_guard<CCriticalSection> lock(python.m_vecMonitorCallbackList);
      python.m_vecMonitorCallbackList.clear();
    } else python.NotifyScriptAborting(&invoker);
    Monitor later(17);python.RegisterPythonMonitorCallBack(&later);
    if(!later.abort) return 3;
  } else if(name=="participants_remain_running") {
    python.NotifyScriptAborting(&invoker);
    Monitor target(17),commandcenter(18),compat(19);
    python.RegisterPythonMonitorCallBack(&target);
    python.RegisterPythonMonitorCallBack(&commandcenter);
    python.RegisterPythonMonitorCallBack(&compat);
    if(!target.abort || commandcenter.abort || compat.abort) return 3;
  } else if(name=="null_broadcast") {
    Monitor first(17),second(18);
    python.RegisterPythonMonitorCallBack(&first);python.RegisterPythonMonitorCallBack(&second);
    python.NotifyScriptAborting(nullptr);
    if(!first.abort || !second.abort) return 3;
    Monitor later(19);python.RegisterPythonMonitorCallBack(&later);
    if(later.abort) return 3;
  } else if(name=="global_shutdown") {
    python.globalShutdown=true;Monitor later(18);
    python.RegisterPythonMonitorCallBack(&later);if(!later.abort) return 3;
  } else if(name=="concurrent_registration") {
    for(int i=0;i<1000;i++) {
      XBPython instance;ILanguageInvoker target(i);Monitor monitor(i);
      std::atomic<bool> ready{false};
      std::thread registering([&] {
        while(!ready.load()) std::this_thread::yield();
        instance.RegisterPythonMonitorCallBack(&monitor);
      });
      std::thread aborting([&] {
        while(!ready.load()) std::this_thread::yield();
        instance.NotifyScriptAborting(&target);
      });
      ready=true;registering.join();aborting.join();
      if(!monitor.abort) return 3;
    }
  } else if(name=="inactive_latch") {
    python.NotifyScriptAborting(&invoker);InfinityAndroidCheckpoint::active=false;
    Monitor later(17);python.RegisterPythonMonitorCallBack(&later);
    if(later.abort) return 3;
  } else return 4;
  return 0;
}
'''


def verify(root, out):
    root, out = Path(root), Path(out)
    source = (root/'xbmc/interfaces/python/XBPython.cpp').read_text()
    assert hashlib.sha256(source.encode()).hexdigest() == PINS['xbmc/interfaces/python/XBPython.cpp']
    header = (root/'xbmc/interfaces/python/XBPython.h').read_bytes()
    assert hashlib.sha256(header).hexdigest() == PINS['xbmc/interfaces/python/XBPython.h']
    cases = ['normal_running','existing_monitor','late_monitor','recreated_monitor',
             'participants_remain_running','null_broadcast','global_shutdown',
             'concurrent_registration','inactive_latch']
    failures = {'late_monitor','recreated_monitor','participants_remain_running'}
    report = {'scope':'Actual compiled RegisterPythonMonitorCallBack and NotifyScriptAborting bodies with controlled native peers; not full Kodi or physical device verification.',
              'original_source_hashes':PINS,'cases':{},'shutdown_repaired':False,
              'complete_native_compilation':False,'new_android_run_claimed':False}
    with tempfile.TemporaryDirectory() as scratch:
        path=Path(scratch)
        for label,text in [('approved',source),('corrected',transform('xbmc/interfaces/python/XBPython.cpp',source))]:
            methods='\n'.join(method(text,s) for s in [
                'void XBPython::RegisterPythonMonitorCallBack(',
                'void XBPython::NotifyScriptAborting('])
            cpp=path/(label+'.cpp');cpp.write_text(PEERS+methods+CASES)
            binary=path/label
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Wno-unused-parameter',
                            '-Werror','-pthread','-DTARGET_ANDROID',str(cpp),'-o',str(binary)],check=True)
            results={name:subprocess.run([str(binary),name],timeout=30).returncode for name in cases}
            if label=='approved':
                assert all(results[name]==3 for name in failures),results
                assert all(results[name]==0 for name in set(cases)-failures-{'concurrent_registration'}),results
            else:
                assert all(value==0 for value in results.values()),results
            report['cases'][label]=results
    report['passed']=True
    report['corrected_cases']=len(cases)
    report['concurrent_interleavings']=1000
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS: three deterministic late-registration failures reproduced; nine corrected cases passed, including 1000 concurrent registration/abort interleavings. Not an end-to-end shutdown proof.')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();verify(args.source,args.out)
