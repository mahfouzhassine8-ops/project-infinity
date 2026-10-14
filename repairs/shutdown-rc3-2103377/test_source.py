#!/usr/bin/env python3
"""Verify real RC3 source transformations against captured, pinned RC2 source.

Curl's actual injected C++ guards and the owner-gate header are compiled and
executed with minimal mock Kodi types. Full Kodi/Android compilation is a later
gate. This cannot prove device-level Curl cancellation or addon durability.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent

def imported(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+".py"))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def check(root):
    early=imported("early_local_snapshot")
    curlfix=imported("cancel_owned_curl")
    cases={}
    with tempfile.TemporaryDirectory(prefix="infinity-rc3-host-") as scratch:
        tmp=Path(scratch)
        for source in [
            early.SOURCE,
            curlfix.CURL,
            curlfix.CURL_H,
        ]:
            original=Path(root)/source
            assert original.is_file(),original
            target=tmp/source
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(original,target)
        er=early.apply(tmp)
        cr=curlfix.apply(tmp,include_invoker=False)
        assert er['early_snapshot_confers_durability_receipt'] is False
        assert cr['required_saves_waived'] is False
        cases['actual_pinned_source_transforms']=True
        original=(Path(root)/early.SOURCE).read_text()
        changed=(tmp/early.SOURCE).read_text()
        for originalGate in [
            'bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)',
            'if (!InfinityDatabaseBarrier::Seal(s.generation))',
            'Complete("python_services", true);',
            'Complete("native_databases", true);',
            's.phase = "SAFE_TO_TERMINATE";',
        ]:
            assert original.count(originalGate)==changed.count(originalGate)==1
        assert changed.index('rc3.early_local_snapshot')<changed.index('Operation("python_services");')
        assert changed.index('Operation("kodi_settings");') > changed.index('Operation("python_services");')
        assert changed.index('Operation("favourites");') > changed.index('Operation("python_services");')
        assert 'earlyLocalSnapshotAttempted=false;' in changed
        cases['early_save_before_python_with_final_barrier_retained']=True
        nativeCurl=(tmp/curlfix.CURL).read_text()
        assert nativeCurl.count('m_state->m_infinityHttpRead = false;')==1
        assert nativeCurl.count('m_state->m_infinityHttpRead = url.GetProtocol()')==1
        assert nativeCurl.count('m_cancelled = true;')>=1
        assert nativeCurl.count('rc3.playlist_read_cancelled_in_poll')==1
        assert nativeCurl.count('rc3.playlist_read_rejected_at_open')==1
        cases['http_read_only_write_api_excluded']=True
        # Extract inserted operational C++ statements exactly, rather than
        # writing a competing hand-coded model with weaker behavior.
        begin=nativeCurl.index('bool CCurlFile::Open(const CURL& url)\n{')
        end=nativeCurl.index('  INFINITY_VFS_STEP(CurlSetup);',begin)
        openPrefix=nativeCurl[begin:end]
        buf=nativeCurl.index('    if (!m_cancelled && m_infinityHttpRead')
        guardStart=nativeCurl.rindex('#if defined(TARGET_ANDROID)',0,buf)
        guardEnd=nativeCurl.index('      return FILLBUFFER_NO_DATA;',buf)+len('      return FILLBUFFER_NO_DATA;')
        fillBlock=nativeCurl[guardStart:guardEnd]
        writeBegin=nativeCurl.index('bool CCurlFile::OpenForWrite(')
        writeEnd=nativeCurl.index('  if(m_opened)',writeBegin)
        writePrefix=nativeCurl[writeBegin:writeEnd]
        root_include=tmp/'xbmc'
        mock=root_include/'platform/android/activity/InfinityAndroidCheckpoint.h'
        mock.parent.mkdir(parents=True,exist_ok=True)
        mock.write_text('''#pragma once
namespace InfinityAndroidCheckpoint {
extern bool checkpointActive;
inline bool IsActive() { return checkpointActive; }
}
''')
        harness=tmp/'rc3_gate_native.cpp'
        header='''#define TARGET_ANDROID 1
#include "filesystem/InfinityCloseNetworkGate.h"
#include <cassert>
#include <iostream>
#include <thread>
#include <atomic>
namespace InfinityAndroidCheckpoint { bool checkpointActive=false; }
namespace InfinityShutdownTrace { inline void Event(const char*,const char*) {} }
namespace InfinityVfsOpenTrace { inline void CancelFlagSeen() {} }
struct CURL {
  std::string proto;
  std::string GetProtocol() const { return proto; }
};
struct CReadState {
  bool m_infinityHttpRead=false;
  bool m_cancelled=false;
  int FillBuffer();
};
constexpr int FILLBUFFER_NO_DATA=0;
class CCurlFile {
public:
  CReadState m_value;
  CReadState* m_state=&m_value;
  bool Open(const CURL&);
  bool OpenForWrite(const CURL&,bool);
};
'''
        harness.write_text(header+openPrefix+"  return true;\n}\n"+writePrefix+
          "  (void)url; (void)bOverWrite; return true;\n}\n"+"int CReadState::FillBuffer(){\n"+fillBlock+
          "\n  return 1;\n}\n"+
          '''
int main() {
  // Normal operation must preserve every network request.
  {InfinityCloseNetworkGate::ScopedOwner context("plugin.video.playlistbrowser");
    CCurlFile file;
    assert(file.Open(CURL{"http"}));
    assert(file.Open(CURL{"https"}));
    assert(file.m_state->FillBuffer()==1);
  }
  InfinityAndroidCheckpoint::checkpointActive=true;
  // No global cancellation of Trakt, Umbrella or unidentified Python.
  for(const std::string owner:{"script.trakt","plugin.video.umbrella",""}) {
    InfinityCloseNetworkGate::ScopedOwner context(owner);
    CCurlFile file;
    assert(file.Open(CURL{"https"}));
    assert(file.m_state->FillBuffer()==1);
  }
  // Exact owned HTTP reads are blocked at open or returned at poll.
  {InfinityCloseNetworkGate::ScopedOwner context("plugin.video.playlistbrowser");
    CCurlFile file;
    assert(!file.Open(CURL{"http"}));
    assert(!file.Open(CURL{"https"}));
    assert(file.Open(CURL{"ftp"}));
    assert(file.OpenForWrite(CURL{"http"},true));
    assert(!file.m_state->m_infinityHttpRead);
    file.m_state->m_infinityHttpRead=true;
    assert(file.m_state->FillBuffer()==0);
    assert(file.m_state->m_cancelled);
  }
  // Nested identity must return to prior owner.
  {InfinityCloseNetworkGate::ScopedOwner context("script.trakt");
   {InfinityCloseNetworkGate::ScopedOwner nested("plugin.video.playlistbrowser");
    assert(InfinityCloseNetworkGate::CancelPlaylistBrowserRead());}
   assert(!InfinityCloseNetworkGate::CancelPlaylistBrowserRead());
  }
  std::atomic<bool> isolated{false};
  {InfinityCloseNetworkGate::ScopedOwner context("plugin.video.playlistbrowser");
   std::thread worker([&]{isolated=(!InfinityCloseNetworkGate::CancelPlaylistBrowserRead());});
   worker.join();
   assert(InfinityCloseNetworkGate::CancelPlaylistBrowserRead());
  }
  assert(isolated);
  assert(!InfinityCloseNetworkGate::CancelPlaylistBrowserRead());
  std::cout<<"PASS RC3 native Curl owner-specific cancellation and normal mode"<<std::endl;
}
''')
        bin=tmp/'rc3_gate_native'
        compiler=subprocess.run(['g++','-std=c++17','-O2','-pthread','-Wall','-Wextra','-Werror',
                                 '-I',str(root_include),str(harness),'-o',str(bin)],
                                capture_output=True,text=True,timeout=50)
        assert compiler.returncode==0,compiler.stderr
        result=subprocess.run([str(bin)],capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr+result.stdout
        cases['actual_curl_guard_compiled_and_executed']=True
        cases['normal_running_no_block_and_unknown_addons_fail_closed']=True
        cases['nested_and_cross_thread_identity_isolation']=True
        cases['curl_self_cancel_instead_of_cross_thread_kill']=True
        tests=dict(checks=cases,passed=len(cases),total=len(cases),source_hashes={
          'curl':hashlib.sha256((Path(root)/curlfix.CURL).read_bytes()).hexdigest(),
          'checkpoint':hashlib.sha256((Path(root)/early.SOURCE).read_bytes()).hexdigest()},
          scope="Host simulation with real injected Curl code, stub native API and exact RC2 source. Not a full Kodi/Android build.")
        return tests

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--source",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    result=check(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
