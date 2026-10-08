#!/usr/bin/env python3
"""Check PVR startup leases and compile the actual retained-owner predicates."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from test_checked_sqlite import extract_function


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    base = args.source_root / "xbmc/pvr"
    clients = (base / "addons/PVRClients.cpp").read_text()
    manager = (base / "PVRManager.cpp").read_text()
    update = extract_function(clients, "void CPVRClients::UpdateClients(")
    latch = "m_androidCheckpointOwnerEncountered = true;"
    assert update.count(latch) == 1
    assert update.index("lock(m_critSection)") < update.index(latch)
    assert update.index(latch) < update.index("std::make_shared<CPVRClient>")
    assert "m_androidCheckpointOwnerEncountered = false" not in clients
    for source, signature in [
        (manager, "void CPVRManager::Start()"),
        (clients, "void CPVRClients::Start()"),
        (clients, "void CPVRClients::UpdateClients("),
    ]:
        function = extract_function(source, signature)
        body = function[function.index("{") + 1:]
        assert re.match(
            r'\s*#if defined\(TARGET_ANDROID\)\s*'
            r'(?://[^\n]*\n\s*)?'
            r'InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointStart\("pvr-start"\);\s*'
            r'if \(!checkpointStart\)\s*return;\s*#endif', body
        ), signature + " must hold its admission lease before any initialization"
        assert function.count('CheckpointWriteGuard checkpointStart("pvr-start")') == 1

    code = r'''
#include <algorithm>
#include <atomic>
#include <chrono>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <thread>
using CCriticalSection=std::recursive_mutex;
struct Client { bool ready=false; bool ReadyToUse() const { return ready; } };
class CPVRClients {
public:
  mutable CCriticalSection m_critSection;
  std::map<int,std::shared_ptr<Client>> m_clientMap;
  bool m_androidCheckpointOwnerEncountered=false;
  bool HasCreatedClients() const;
  bool HasAndroidCheckpointOwners() const;
};
// @PRODUCTION@
void require(bool value,const char* text){if(!value)throw std::runtime_error(text);}
int main(){
  CPVRClients clients;
  require(!clients.HasAndroidCheckpointOwners(),"empty owner inventory");
  clients.m_clientMap.emplace(1,std::make_shared<Client>());
  require(!clients.HasCreatedClients(),"fixture must represent not-ready client");
  require(clients.HasAndroidCheckpointOwners(),"not-ready private owner was ignored");
  clients.m_clientMap.at(1)->ready=true;
  require(clients.HasAndroidCheckpointOwners(),"ready private owner was ignored");
  std::atomic<bool> entered{false},returned{false};
  std::unique_lock<CCriticalSection> lock(clients.m_critSection);
  std::thread reader([&]{entered=true;clients.HasAndroidCheckpointOwners();returned=true;});
  while(!entered)std::this_thread::yield();
  std::this_thread::sleep_for(std::chrono::milliseconds(20));
  const bool held=!returned;
  lock.unlock();reader.join();
  require(held,"owner inventory did not synchronize with mutation lock");
  clients.m_clientMap.clear();
  require(!clients.HasAndroidCheckpointOwners(),"removed inventory remains present");
  clients.m_androidCheckpointOwnerEncountered=true;
  require(clients.HasAndroidCheckpointOwners(),"destroyed private owner history was forgotten");
  std::cout<<"PASS retained_and_initializing_pvr_owners_cannot_appear_inactive\n";
}
'''
    functions = "\n".join(extract_function(clients, signature) for signature in [
        "bool CPVRClients::HasCreatedClients() const",
        "bool CPVRClients::HasAndroidCheckpointOwners() const",
    ])
    with tempfile.TemporaryDirectory(prefix="infinity-pvr-owner-") as temp:
        cpp, binary = Path(temp) / "test.cpp", Path(temp) / "test"
        cpp.write_text(code.replace("// @PRODUCTION@", functions))
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
                        str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)
    print("PASS all_three_pvr_startup_entries_hold_full_scope_admission_leases_and_private_history_is_latched")


if __name__ == "__main__":
    main()
