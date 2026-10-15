#!/usr/bin/env python3
"""Compile the three actual PVR lambdas with a contract-capturing job double.

This checks exact callsite annotations and callback captures. The production job
ledger and historical PVR owner predicates have separate tests.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from test_checked_sqlite import extract_function


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root / "xbmc/pvr"
    clients = (root / "addons/PVRClients.cpp").read_text()
    manager = (root / "PVRManager.cpp").read_text()
    bodies = "\n".join([
        extract_function(manager, "void CPVRManager::Init()"),
        extract_function(clients, "bool CPVRClients::RequestRestart("),
        extract_function(clients, "void CPVRClients::OnAddonEvent("),
    ])
    code = r'''
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <typeinfo>
#include <utility>
#include <vector>
namespace ADDON {
using AddonInstanceId = int;
enum class AddonType { PVRDLL };
struct AddonEvent { virtual ~AddonEvent() = default; std::string addonId; int instanceId=0; };
namespace AddonEvents {
struct Enabled : AddonEvent {}; struct Disabled : AddonEvent {};
struct UnInstalled : AddonEvent {}; struct ReInstalled : AddonEvent {};
struct InstanceAdded : AddonEvent {}; struct InstanceRemoved : AddonEvent {};
struct MetadataChanged : AddonEvent {};
}
}
using namespace ADDON;
struct Job { std::string owner, operation; std::function<bool()> run; };
struct Jobs {
  std::vector<Job> pending;
  template<class F> void SubmitForCheckpoint(const char* owner,const char* operation,F&& body) {
    pending.push_back({owner,operation,std::forward<F>(body)});
  }
};
struct AddonManager { bool pvr=true; bool HasType(const std::string&,AddonType) { return pvr; } };
struct CServiceBroker {
  static Jobs jobs; static AddonManager addons;
  static Jobs* GetJobManager() { return &jobs; }
  static AddonManager& GetAddonMgr() { return addons; }
};
Jobs CServiceBroker::jobs; AddonManager CServiceBroker::addons;
class CPVRClients {
public:
  int starts=0; std::vector<std::pair<std::string,int>> updates;
  void Start() { ++starts; }
  void UpdateClients(const std::string& addon,int instance) { updates.emplace_back(addon,instance); }
  bool RequestRestart(const std::string&, ADDON::AddonInstanceId, bool);
  void OnAddonEvent(const AddonEvent&);
};
class CPVRManager {
public:
  CPVRClients client; CPVRClients* Clients() { return &client; } void Init();
};
// @PRODUCTION@
void require(bool value,const char* text) { if(!value)throw std::runtime_error(text); }
Job take(const char* operation) {
  auto& pending=CServiceBroker::jobs.pending;
  require(pending.size()==1,"expected exactly one annotated lambda");
  Job job=std::move(pending.back()); pending.clear();
  require(job.owner=="pvr","lambda mapped to wrong persistence owner");
  require(job.operation==operation,"lambda lost its precise operation identity");
  return job;
}
int main() {
  CPVRManager manager;
  manager.Init(); require(manager.client.starts==0,"startup ran outside accepted job");
  require(take("pvr.initial_clients_start").run(),"startup callback failed");
  require(manager.client.starts==1,"startup callback changed");
  CPVRClients clients;
  require(clients.RequestRestart("pvr.example",7,true),"restart admission result changed");
  require(clients.updates.empty(),"restart ran outside accepted job");
  require(take("pvr.request_client_restart").run(),"restart callback failed");
  require(clients.updates.back()==std::make_pair(std::string("pvr.example"),7),"restart capture changed");
  AddonEvents::MetadataChanged metadata; clients.OnAddonEvent(metadata);
  require(CServiceBroker::jobs.pending.empty(),"irrelevant event scheduled private work");
  AddonEvents::Enabled enabled; enabled.addonId="pvr.event"; enabled.instanceId=9;
  CServiceBroker::addons.pvr=false; clients.OnAddonEvent(enabled);
  require(CServiceBroker::jobs.pending.empty(),"non-PVR addon scheduled private work");
  CServiceBroker::addons.pvr=true; clients.OnAddonEvent(enabled);
  require(take("pvr.addon_event_update_clients").run(),"addon callback failed");
  require(clients.updates.back()==std::make_pair(std::string("pvr.event"),9),"event capture changed");
  std::cout<<"PASS exact_three_pvr_lambda_contracts_and_unchanged_callback_scope\n";
}
'''
    with tempfile.TemporaryDirectory(prefix="infinity-pvr-lambdas-") as directory:
        source, binary = Path(directory) / "test.cpp", Path(directory) / "test"
        source.write_text(code.replace("// @PRODUCTION@", bodies))
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        "-Wno-unused-parameter", str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == "__main__":
    main()
