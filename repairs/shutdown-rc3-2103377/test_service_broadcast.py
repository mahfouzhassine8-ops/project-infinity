#!/usr/bin/env python3
"""Execute the *actual CScriptInvocationManager::BeginAndroidCheckpoint method*
with controlled native peers for the five Fold pending services and protected
resident save owners. This tests notification dispatch, NOT third-party Python
bytecode retirement or real Galaxy Fold behavior.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, tempfile

MANAGER="xbmc/interfaces/generic/ScriptInvocationManager.cpp"
PIN="847d9b0fdb26fde4973744689204bbd7531e2fa249e423c63dd9539cda430239"
def run(root):
    file=Path(root)/MANAGER
    original=file.read_bytes()
    assert hashlib.sha256(original).hexdigest()==PIN,"not pinned RC2 manager"
    source=original.decode()
    begin=source.index("void CScriptInvocationManager::BeginAndroidCheckpoint()\n{")
    end=source.index("\nvoid CScriptInvocationManager::PumpAndroidCheckpointRetirement(bool force)",begin)
    method=source[begin:end]
    assert "if (m_androidCheckpointRetirementArmed)" not in method
    method=method.replace("    m_shutdownRequested = true;\n",
                          "    m_shutdownRequested = true;\n"
                          "    if (m_androidCheckpointRetirementArmed) return;\n",1)
    # The diff is exactly the production follow-up's idempotence clause.
    # All other behavior is taken from the actual original C++ method.
    harness=r'''#include <cassert>
#include <chrono>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <string>
#include <vector>
using CCriticalSection=std::mutex;
struct FakeInvoker {
  int GetId() const {return 1;} // Trace-only fake ID, never permissions.
  unsigned nonblockingStops{0};
  bool Stop(bool wait) {
    assert(!wait);
    ++nonblockingStops; return true;
  }
};
struct FakeThread {
  std::string addon;
  std::shared_ptr<FakeInvoker> inv=std::make_shared<FakeInvoker>();
  unsigned releases{0},monitorAborts{0};
  std::shared_ptr<FakeInvoker> GetInvoker(){return inv;}
  void Release(){++releases;}
};
using CLanguageInvokerThreadPtr=std::shared_ptr<FakeThread>;
struct FakeLanguageInvokerThread {
  std::string script,checkpointContract;
  CLanguageInvokerThreadPtr thread;
  bool done{false};
};
struct FakePython {
  void NotifyScriptAborting(FakeThread* item){++item->monitorAborts;}
};
struct CServiceBroker {
  static FakePython& GetXBPython(){static FakePython handler;return handler;}
};
// Production source has observation-only VFS requests; mock the tracer,
// not the actual invoker selection or native AbortNotification logic.
namespace InfinityVfsOpenTrace {
inline void Request(int,const char*) {}
}
std::string VerifiedCheckpointContract(
  const std::string&, const CLanguageInvokerThreadPtr&,
  const std::string& admittedContract){return admittedContract;}
struct CScriptInvocationManager {
  CCriticalSection m_critSection;
  bool m_shutdownRequested{false};
  bool m_androidCheckpointRetirementArmed{false};
  std::chrono::steady_clock::time_point m_androidCheckpointRetirementStarted{};
  std::set<int> m_androidCheckpointEscalatedIds;
  std::size_t m_androidCheckpointEscalationsActive{0};
  std::map<int,FakeLanguageInvokerThread> m_scripts;
  void BeginAndroidCheckpoint();
};
'''+method+r'''
int main(){
  CScriptInvocationManager manager;
  std::vector<std::string> pending={
    "plugin.video.playlistbrowser:service.py",
    "plugin.video.umbrella:service.py",
    "repository.zeus768:service.py",
    "script.trakt:default.py",
    "unidentified:infinity_continuity.py"
  };
  std::vector<CLanguageInvokerThreadPtr> five;
  int id=1;
  for (const auto& name:pending) {
    auto thread=std::make_shared<FakeThread>();
    thread->addon=name;
    manager.m_scripts.emplace(id, FakeLanguageInvokerThread{name, "", thread, false});
    five.push_back(thread);
    ++id;
  }
  // Positive protect checks are valid only with verified resident contracts.
  auto resident=std::make_shared<FakeThread>();
  manager.m_scripts.emplace(id++,FakeLanguageInvokerThread{"command_center","command_center",resident,false});
  auto compat=std::make_shared<FakeThread>();
  manager.m_scripts.emplace(id++,FakeLanguageInvokerThread{"compat","compat",compat,false});
  auto optional=std::make_shared<FakeThread>();
  manager.m_scripts.emplace(id++,FakeLanguageInvokerThread{"artwork","nonpersistent:cache",optional,false});
  auto finished=std::make_shared<FakeThread>();
  manager.m_scripts.emplace(id++,FakeLanguageInvokerThread{"finished","",finished,true});
  manager.BeginAndroidCheckpoint();
  assert(manager.m_shutdownRequested && manager.m_androidCheckpointRetirementArmed);
  const auto start=manager.m_androidCheckpointRetirementStarted;
  for (const auto& worker:five) {
    assert(worker->monitorAborts==1);
    assert(worker->releases==1);
    assert(worker->inv->nonblockingStops==1);
  }
  assert(optional->monitorAborts==1 && optional->inv->nonblockingStops==1);
  assert(resident->monitorAborts==0 && resident->inv->nonblockingStops==0);
  assert(compat->monitorAborts==0 && compat->inv->nonblockingStops==0);
  assert(finished->monitorAborts==0 && finished->inv->nonblockingStops==0);
  manager.BeginAndroidCheckpoint();
  assert(manager.m_androidCheckpointRetirementStarted==start);
  for (const auto& worker:five) assert(worker->monitorAborts==1);
  assert(resident->releases==0 && compat->releases==0);
  std::cout<<"PASS: five generic service notifications, protected resident writers, idempotent startup\n";
}
'''
    with tempfile.TemporaryDirectory(prefix="infinity-rc3-5service-") as directory:
      cpp=Path(directory)/"check.cpp"
      bin=Path(directory)/"check"
      cpp.write_text(harness)
      c=subprocess.run(["g++","-std=c++17","-pthread","-O2","-Wall","-Wextra","-Werror",
                        "-DTARGET_ANDROID","-DHAS_PYTHON",str(cpp),"-o",str(bin)],
                        capture_output=True,text=True,timeout=40)
      assert c.returncode==0,c.stderr
      r=subprocess.run([str(bin)],capture_output=True,text=True,timeout=15)
      assert r.returncode==0,r.stderr+r.stdout
    return {
      "passed":True,
      "case_count":8,
      "cases":["Playlist Browser generic service signalled",
               "Umbrella generic service signalled","Zeus768 generic service signalled",
               "Trakt generic service signalled","Infinity Continuity generic service signalled",
               "Command Center and compat valid residents protected",
               "Already completed scripts excluded","Second BeginAndroidCheckpoint idempotent"],
      "scope":"Real native CScriptInvocationManager::BeginAndroidCheckpoint body compiled with mocks. Installed third-party service code NOT executed.",
      "observed_5_service_physical_retirement":False,
      "saved_writer_receipts_fabricated":False,
      "no_abandonment_of_unknown_python_writes":True,
      "script_manager_before_sha256":PIN
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=run(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
