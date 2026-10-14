#!/usr/bin/env python3
"""Compile actual RC5 native classification + shutdown broadcast with mock peers.

No simulated 17/17 receipts or claims of physical Fold success. Validates both
exact native production methods, path/identity boundaries and unchanged gate.
"""
import argparse
import importlib.util
import json
import re
import subprocess
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("optional_shutdown",HERE/"optional_shutdown.py")
policy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

def compiled_cpp(body, scope):
    with tempfile.TemporaryDirectory(prefix="infinity-rc5-") as folder:
        path=Path(folder)/"test.cpp"
        exe=Path(folder)/"test"
        path.write_text(body)
        run=subprocess.run(["g++","-std=c++17","-O2","-pthread","-Wall","-Wextra",
            "-Werror","-DTARGET_ANDROID","-DHAS_PYTHON",str(path),"-o",str(exe)],
            capture_output=True,text=True,timeout=45)
        if run.returncode:
            raise RuntimeError(scope+" compile failed: "+run.stderr[-9000:])
        result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
        if result.returncode:
            raise RuntimeError(scope+" run failed: "+result.stdout+result.stderr)
        return result.stdout.strip()

def check(root):
    root=Path(root)
    c=(root/policy.CLASSIFIER).read_text()
    m=(root/policy.MANAGER).read_text()
    checkpoint=(root/"xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp").read_text()
    persistence=(root/"xbmc/platform/android/activity/InfinityScriptPersistence.h").read_text()
    cases={}

    assert c.count('return "stop-only:trakt-cloud-owned";')==1
    assert c.count('return "stop-only:continuity-diagnostic";')==1
    assert c.count('addon == "script.trakt"')==1
    assert c.count('script.trakt/default.py')==1
    assert all(q in c for q in (policy.CONTINUITY_211,policy.CONTINUITY_212))
    cases["strict_two_scope_source_contract"]=True

    required_match=re.search(r"constexpr const char\* REQUIRED\[\] = \{(.*?)\};",checkpoint,re.S)
    assert required_match
    required=re.findall(r'"([^"]+)"',required_match.group(1))
    assert len(required)==17 and len(set(required))==17
    assert "python_services" in required and "trakt" not in required and "continuity" not in required
    cases["seventeen_native_required_owners_preserved"]=True

    assert m.count('if (checkpointContract.empty())')>=3
    assert m.count("InfinityScriptPersistence::Admit(")==2
    assert 'contract.rfind("stop-only:", 0) == 0' in m
    assert "if (m_androidCheckpointRetirementArmed)" in m
    assert 'invoker->Stop(false);' in m and "NotifyScriptAborting(thread.get())" in m
    cases["stop_only_receives_monitor_and_nonblocking_stop"]=True

    assert "for (const auto& name : m_checkpointUnresolvedWriterLedger)" in m
    assert "if (checkpointContract.empty() && m_checkpointUnresolvedWriterLedger.size() < 8)" in m
    assert m.count("VerifiedCheckpointContract(")>=6
    cases["new_contracts_do_not_enter_foreign_writer_ledger"]=True

    assert "if (!s.writers.empty())return false;" in persistence
    assert "if(!found->second.observed)return;" in persistence
    assert "inline bool PollCommit()" in persistence
    assert "script_file_sync_or_identity_failed" in persistence
    cases["all_nonoptional_python_observer_and_durability_checks_intact"]=True

    assert 'if (!InfinityScriptPersistence::PollInventory())' in checkpoint
    assert 'if (!InfinityDatabaseBarrier::Seal(s.generation))' in checkpoint
    assert 'Complete("python_services", true);' in checkpoint
    assert 'bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)' in checkpoint
    cases["native_authorization_and_database_barrier_retained"]=True

    classification=c[c.index("std::string ClassifyScript("):c.index("} // namespace InfinityAndroidCheckpoint",c.index("std::string ClassifyScript("))]
    cpp=r'''
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>
#include <utility>
#include <vector>
static std::string continuityDigest;
static int digestReads=0;
namespace KODI {namespace UTILITY {namespace CDigest {enum class Type {SHA256};}}}
struct CSpecialProtocol {
  static std::string TranslatePath(const std::string& v) {
    const std::string home="special://home/addons/";
    const std::string system="special://xbmc/addons/";
    if(v.rfind(home,0)==0)return "/data/installed/addons/"+v.substr(home.size());
    if(v.rfind(system,0)==0)return "/system/xbmc/addons/"+v.substr(system.size());
    return v;
  }
};
struct CUtil {
  static std::string GetFileDigest(const std::string& path,KODI::UTILITY::CDigest::Type) {
    ++digestReads;
    if(path.find("infinity_continuity.py")!=std::string::npos)return continuityDigest;
    return "unreviewed";
  }
};
namespace InfinityAndroidCheckpoint {
struct Contract {const char* script;const char* addon;const char* owner;
  std::vector<std::pair<const char*,const char*>> source;};
const std::vector<Contract>& Contracts() {static const std::vector<Contract> c;return c;}
'''+classification+r'''
}
int main() {
  using InfinityAndroidCheckpoint::ClassifyScript;
  std::string home="/data/installed/addons/";
  std::string system="/system/xbmc/addons/";
  assert(ClassifyScript(home+"script.trakt/default.py","script.trakt")=="stop-only:trakt-cloud-owned");
  assert(ClassifyScript(system+"script.trakt/default.py","script.trakt")=="stop-only:trakt-cloud-owned");
  // No source hash dependence so future Trakt updates do not require RC5 repatching.
  assert(digestReads==0);
  for(auto id:{"","plugin.video.umbrella","script.trakt.fake","service.infinity.compat"})
    assert(ClassifyScript(home+"script.trakt/default.py",id).empty());
  for(auto path:{"/sdcard/script.trakt/default.py",
                 "/data/installed/addons/script.trakt/service.py",
                 "/data/installed/addons/script.trakt/resources/default.py",
                 "/data/installed/addons/script.trakt/../other/default.py"})
    assert(ClassifyScript(path,"script.trakt").empty());
  assert(ClassifyScript(home+"plugin.video.umbrella/service.py","plugin.video.umbrella").empty());
  std::string continuity=home+"skin.infinity.diggz/resources/lib/infinity_continuity.py";
  continuityDigest="a9a5477eec6ae1684d04d6b0a574be3f6b07172ca793240af82c8d26a421c9d1";
  assert(ClassifyScript(continuity,"")=="stop-only:continuity-diagnostic");
  continuityDigest="97469b505ffae522b31a5bf96ef4313b2b184d1abd5937ee52b65dd7fe96599a";
  assert(ClassifyScript(continuity,"skin.infinity.diggz")=="stop-only:continuity-diagnostic");
  continuityDigest="new-unknown-skin";
  assert(ClassifyScript(continuity,"").empty());
  continuityDigest="a9a5477eec6ae1684d04d6b0a574be3f6b07172ca793240af82c8d26a421c9d1";
  assert(ClassifyScript("/data/other/infinity_continuity.py","").empty());
  assert(ClassifyScript(continuity,"script.trakt").empty());
  assert(ClassifyScript(home+"skin.infinity.diggz/resources/lib/other.py","").empty());
  std::cout<<"PASS RC5 actual ClassifyScript: identity, update independence, source pins and fail closed\n";
}
'''
    output=compiled_cpp(cpp,"classifier")
    cases["real_cpp_classifier_compiles_executes"]=output.startswith("PASS RC5")
    cases["trakt_owned_entry_only"]=True
    cases["trakt_future_updates_source_independent"]=True
    cases["unrelated_addons_fail_closed"]=True
    cases["continuity_exact_skin_pin_only"]=True
    cases["spoofed_identity_or_path_rejected"]=True

    start=m.index("void CScriptInvocationManager::BeginAndroidCheckpoint()\n{")
    end=m.index("\nvoid CScriptInvocationManager::PumpAndroidCheckpointRetirement(",start)
    method=m[start:end]
    harness=r'''
#include <cassert>
#include <chrono>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <string>
#include <vector>
using CCriticalSection=std::mutex;
struct Invoker {unsigned calls=0;bool Stop(bool wait){assert(!wait);++calls;return true;}};
struct Thread {
  unsigned notifications=0,releases=0;
  std::shared_ptr<Invoker> inv=std::make_shared<Invoker>();
  std::shared_ptr<Invoker> GetInvoker(){return inv;}
  void Release(){++releases;}
};
using CLanguageInvokerThreadPtr=std::shared_ptr<Thread>;
struct Record {std::string script;CLanguageInvokerThreadPtr thread;bool done;std::string checkpointContract;};
struct Python {void NotifyScriptAborting(Thread* thread){++thread->notifications;}};
struct CServiceBroker {static Python& GetXBPython(){static Python p;return p;}};
std::string VerifiedCheckpointContract(const std::string&,
    const CLanguageInvokerThreadPtr&,const std::string& value){return value;}
struct CScriptInvocationManager {
  CCriticalSection m_critSection;
  bool m_shutdownRequested{false};
  bool m_androidCheckpointRetirementArmed{false};
  std::chrono::steady_clock::time_point m_androidCheckpointRetirementStarted{};
  std::set<int> m_androidCheckpointEscalatedIds;
  std::size_t m_androidCheckpointEscalationsActive{0};
  std::map<int,Record> m_scripts;
  void BeginAndroidCheckpoint();
};
'''+method+r'''
int main() {
  CScriptInvocationManager manager;
  std::vector<std::shared_ptr<Thread>> checks;
  auto add=[&](std::string entry,std::string contract,bool done=false){
    auto t=std::make_shared<Thread>();
    checks.push_back(t);
    manager.m_scripts.emplace(checks.size(),Record{entry,t,done,contract});
  };
  add("script.trakt/default.py","stop-only:trakt-cloud-owned");
  add("infinity_continuity.py","stop-only:continuity-diagnostic");
  add("plugin.video.umbrella/service.py","");
  add("script.infinity.commandcenter/service.py","command_center");
  add("service.infinity.compat/service.py","compat");
  add("service.infinity.refresh/service.py","reconstructible-cache:refresh-policy");
  add("already_done.py","",true);
  manager.BeginAndroidCheckpoint();
  assert(manager.m_shutdownRequested && manager.m_androidCheckpointRetirementArmed);
  for(int i:{0,1,2,5})assert(checks[i]->notifications==1 &&
    checks[i]->releases==1 && checks[i]->inv->calls==1);
  for(int i:{3,4,6})assert(checks[i]->notifications==0 &&
    checks[i]->releases==0 && checks[i]->inv->calls==0);
  manager.BeginAndroidCheckpoint();
  for(int i:{0,1,2,5})assert(checks[i]->notifications==1);
  std::cout<<"PASS RC5 real native BeginAndroidCheckpoint cooperative stop, preserved participants\n";
}
'''
    output=compiled_cpp(harness,"cooperative_stop")
    cases["real_cpp_begin_checkpoint_compiles_executes"]=output.startswith("PASS RC5")
    cases["nonblocking_close_stop_dispatched_to_both_optional_services"]=True
    cases["resident_save_participants_not_stopped"]=True
    cases["generic_unknown_services_still_stopped"]=True
    cases["duplicate_abort_notifications_prevented"]=True
    return {"scope":"RC5 real native source methods in compiled harness with mock Kodi peers; NO Fold shutdown assertion",
       "checks":cases,"passed":len(cases),"total":len(cases),
       "trakt_addon_source_modified":False,"trakt_disabled":False,
       "continuity_skin_modified":False,"unverified_foreign_writers_exempted":False,
       "physical_fold_17_receipts_verified":False,"locked":False}

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--source",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    opts=cli.parse_args()
    result=check(opts.source)
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
