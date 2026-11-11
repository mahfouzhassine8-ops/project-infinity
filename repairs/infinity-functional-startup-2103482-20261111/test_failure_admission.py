#!/usr/bin/env python3
"""Selected native bookkeeping experiment; never executes a Python add-on.

Uses the existing lifetime fixture's peers, unchanged production method bodies,
and real persistence headers. See SELECTED-HOST-CHECK.md for limits.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = 'repairs/android-checkpoint-shutdown/runtime-tests/test_script_writer_lifetime.py'


def method(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


MAIN = r'''
int main(int argc, char** argv) {
  assert(argc==2);
  const std::string mode=argv[1];
  auto& manager=CScriptInvocationManager::GetInstance();
  Handler handler;manager.m_invocationHandlers[".py"]=&handler;
  const auto writer=std::make_shared<ADDON::Addon>();
  const int id=manager.ExecuteAsync("/fixture/service.py",writer,{});
  assert(id>=0 && InfinityScriptPersistence::Pending(id));
  // Synthetic audit records only: no filesystem mutation or library load.
  const char* events[]={"os.utime", "os.setxattr", "os.chmod", "ctypes.dlopen"};
  for(int repeat=0;repeat<233;++repeat)
    for(const auto* event:events)
      InfinityScriptPersistence::Fail(id,"external_or_opaque_writer_requires_explicit_participant",event);
  auto before=InfinityScriptPersistence::Snapshot();
  assert(before.blockers.size()==4 && !before.blockerOverflow);
  for(const auto& blocker:before.blockers)assert(blocker.count==233 && blocker.blocking);
  assert(before.active==1 && before.blockingCount==4 && !before.durable);
  assert(!manager.m_shutdownRequested && !manager.m_checkpointStartupAdmissionClosed);
  assert(!InfinityScriptPersistence::RejectOpaqueMutation("host_read_only_probe"));
  if(mode=="startup-gate")manager.BeginCheckpointStartupAdmission();
  else if(mode=="shutdown-gate")manager.BeginShutdown();
  else assert(mode=="failures-only");
  const auto dispatched=manager.m_scripts.size();
  const int status=RunScript(std::vector<std::string>{"script.fixture.local"});
  const bool admitted=manager.m_scripts.size()==dispatched+1;
  assert(status==0); // The real builtin discards the invocation return value.
  assert(admitted==(mode=="failures-only"));
  if(admitted) {
    const int newId=manager.m_nextId-1;
    assert(InfinityScriptPersistence::Pending(newId));
    assert(InfinityScriptPersistence::Get().writers.at(newId).failure.empty());
    // Registration alone must not claim interpreter initialization or execution.
    assert(!InfinityScriptPersistence::Get().writers.at(newId).observed);
  }
  auto after=InfinityScriptPersistence::Snapshot();
  assert(after.failure==before.failure && after.blockers.size()==4 && !after.durable);
  assert(checkpointStops==0 && forcedStops==0 && Test::aborted.empty());
  std::cout<<"{\"case\":\""<<mode<<"\",\"builtin_return\":"<<status
    <<",\"independent_dispatch_admitted\":"<<(admitted?"true":"false")
    <<",\"blocking_rows\":"<<after.blockers.size()
    <<",\"repetitions_per_row\":233,\"failure_preserved\":true,\"python_executed\":false}\n";
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve(strict=True)
    binding = json.loads((HERE/'RETAINED-SOURCE-CHECK.json').read_text())
    paths = ['xbmc/interfaces/generic/ScriptInvocationManager.cpp',
             'xbmc/interfaces/builtins/AddonBuiltins.cpp',
             'xbmc/platform/android/activity/InfinityScriptPersistence.h',
             'xbmc/platform/android/activity/InfinityProtectedWrites.h']
    hashes = {p: hashlib.sha256((runtime/p).read_bytes()).hexdigest() for p in paths}
    for path in paths[:2]:
        assert hashes[path] == binding[path]['sha256'], path
    # The retained source-map schema is recorded in the results. Exact header
    # hashes must occur next to their paths in that source evidence.
    source_map = json.loads(args.source_map.read_text())
    def find(obj, path, digest):
        if isinstance(obj, dict):
            if path in obj and (obj[path] == digest or
                              isinstance(obj[path], dict) and obj[path].get('sha256') == digest):
                return True
            return any(find(v, path, digest) for v in obj.values())
        if isinstance(obj, list):
            return any(find(v, path, digest) for v in obj)
        return False
    for path in paths:
        assert find(source_map, path, hashes[path]), ('source map mismatch', path)
    fixture = subprocess.check_output(['git', 'show', 'HEAD:'+FIXTURE], cwd=ROOT, text=True)
    peers = next(ast.literal_eval(n.value) for n in ast.parse(fixture).body
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PEERS' for t in n.targets))
    changes = [
        ('std::string ID()const{return "addon";}', 'std::string ID()const{return "addon";}std::string LibPath()const{return "/fixture/program.py";}'),
        ('struct Invoker{', 'struct Invoker{void Reset(){}'),
        (' void Release();', ' bool Reuseable(const std::string&)const{return false;}\n void Release();'),
        ('struct Handler{void Process(){}};', 'struct Handler{void Process(){}LanguageInvokerPtr CreateInvoker(){return std::make_shared<Invoker>();}};'),
        ('struct CServiceBroker {', '''enum class OnlyEnabled{CHOICE_YES};
enum class AddonType{SCRIPT,SCRIPT_WEATHER,SCRIPT_LYRICS,SCRIPT_LIBRARY};
using ADDON::AddonPtr;using ILanguageInvocationHandler=Handler;
struct AddonMgr{template<class...T>bool GetAddon(const std::string&,AddonPtr& a,T...){a=std::make_shared<ADDON::Addon>();return true;}};
struct CServiceBroker {static AddonMgr& GetAddonMgr(){static AddonMgr m;return m;}'''),
        ('struct URIUtils{', 'struct StringUtils{static void ToLower(std::string&){};};\nstruct URIUtils{static std::string GetExtension(const std::string&){return ".py";}'),
        ('constexpr int LOGERROR=1,LOGINFO=2;', 'constexpr int LOGERROR=1,LOGINFO=2,LOGDEBUG=3,LOGWARNING=4;'),
        ('std::map<int,Handler*>m_invocationHandlers;', 'std::map<std::string,Handler*>m_invocationHandlers;'),
        (' int ExecuteAsync(', ''' static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager instance;return instance;}
 void BeginShutdown();void BeginCheckpointStartupAdmission();
 LanguageInvokerPtr GetLanguageInvokerForAdmission(const std::string&,const ADDON::AddonPtr&,bool);
 int ExecuteAsync(const std::string&,const ADDON::AddonPtr&,const std::vector<std::string>&,bool=false,int=-1);
 int ExecuteAsync('''),
    ]
    for old, new in changes:
        peers = replace_once(peers, old, new)
    manager = (runtime/paths[0]).read_text()
    markers = [
        'void CScriptInvocationManager::BeginCheckpointStartupAdmission()',
        'void CScriptInvocationManager::BeginShutdown()',
        'LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvokerForAdmission(',
        'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const ADDON::AddonPtr&',
        'int CScriptInvocationManager::ExecuteAsync(\n    const std::string& script,\n    const LanguageInvokerPtr&',
    ]
    methods = '\n'.join(method(manager, marker) for marker in markers)
    builtin = method((runtime/paths[1]).read_text(), 'template<bool OnlyApple=false>\nstatic int RunScript(')
    code = '#include <iostream>\n#include "platform/android/activity/InfinityProtectedWrites.h"\n'+peers+methods+builtin+MAIN
    results = []
    with tempfile.TemporaryDirectory(prefix='infinity-startup-admission-') as name:
        folder = Path(name)
        cpp, binary = folder/'probe.cpp', folder/'probe'
        cpp.write_text(code)
        subprocess.run(['g++', '-std=c++17', '-DTARGET_ANDROID', '-Wall', '-Wextra', '-Werror', '-pthread', '-I', str(runtime/'xbmc'), str(cpp), '-o', str(binary)], check=True, timeout=60)
        for case in ['failures-only', 'startup-gate', 'shutdown-gate']:
            result = subprocess.run([str(binary), case], check=True, capture_output=True, text=True, timeout=5)
            results.append(json.loads(result.stdout))
    report = dict(schema=1, scope='host native admission and ledger only',
                  source_sha256=hashes, fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest(),
                  generated_cpp_sha256=hashlib.sha256(code.encode()).hexdigest(),
                  source_map_sha256=hashlib.sha256(args.source_map.read_bytes()).hexdigest(),
                  results=results, all_selected_assertions_passed=True,
                  actual_core_service_executed=False, android_tested=False,
                  fold_failure_reproduced=False, production_changed=False)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
