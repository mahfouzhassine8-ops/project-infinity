#!/usr/bin/env python3
"""Check PVR startup leases and compile actual manager/client owner predicates."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from test_checked_sqlite import extract_function


def manager_api_fixture(header, manager):
    """Retain production access labels and predicate bodies in a small host class."""
    clean_header = re.sub(r'/\*.*?\*/|//[^\n]*', '', header, flags=re.S)
    wrapper_signature = "bool IsStoppedForAndroidCheckpoint() const"
    private_signature = "bool IsStopped() const"

    def member_access(signature):
        assert clean_header.count(signature) == 1, signature
        access = re.findall(r'^\s*(public|protected|private)\s*:',
                            clean_header[:clean_header.index(signature)], flags=re.M)
        assert access, "Missing production access label for " + signature
        return access[-1]

    wrapper_access = member_access(wrapper_signature)
    predicate_access = member_access(private_signature)
    assert wrapper_access == "public", "Checkpoint manager query must be public"
    assert predicate_access == "private", "Original stopped predicate must remain private"
    wrapper = extract_function(clean_header, wrapper_signature)
    assert re.search(r'#if\s+defined\(TARGET_ANDROID\)\s*' + re.escape(wrapper) +
                     r'\s*#endif', clean_header), "Checkpoint query must remain Android-only"
    predicate = extract_function(clean_header, private_signature)
    states = extract_function(clean_header, "enum class ManagerState")
    state_names = re.findall(r'\bSTATE_[A-Z]+\b', states)
    assert state_names == ["STATE_ERROR", "STATE_STOPPED", "STATE_STARTING", "STATE_STOPPING",
                           "STATE_INTERRUPTED", "STATE_STARTED"], "Review any new manager states"
    setters = "\n".join('if (state == "' + name + '") m_managerState = ManagerState::' + name + ';'
                        for name in state_names)
    return r'''
class CPVRManager {
public:
  void SetStateForTest(const std::string& state) {
    std::unique_lock<CCriticalSection> lock(m_managerStateMutex);
    // @STATE_SETTERS@
  }
// @WRAPPER_ACCESS@:
#if defined(TARGET_ANDROID)
  // @WRAPPER@
#endif
private:
  // @STATES@;
// @PREDICATE_ACCESS@:
  // @PREDICATE@
  ManagerState GetState() const;
  mutable CCriticalSection m_managerStateMutex;
  ManagerState m_managerState = ManagerState::STATE_STOPPED;
};
// @GET_STATE@
'''.replace("// @STATE_SETTERS@", setters).replace("// @WRAPPER_ACCESS@", wrapper_access).replace(
        "// @WRAPPER@", wrapper).replace("// @STATES@", states).replace(
        "// @PREDICATE_ACCESS@", predicate_access).replace("// @PREDICATE@", predicate).replace(
        "// @GET_STATE@", extract_function(manager, "CPVRManager::ManagerState CPVRManager::GetState() const"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    base = args.source_root / "xbmc/pvr"
    clients = (base / "addons/PVRClients.cpp").read_text()
    manager = (base / "PVRManager.cpp").read_text()
    manager_header = (base / "PVRManager.h").read_text()
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
#include <string>
#include <thread>
using CCriticalSection=std::recursive_mutex;
// @MANAGER_API@
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
  CPVRManager manager;
  const CPVRManager& constManager = manager;
  for (const char* state : {"STATE_ERROR", "STATE_STOPPED", "STATE_STARTING", "STATE_STOPPING",
                            "STATE_INTERRUPTED", "STATE_STARTED"}) {
    manager.SetStateForTest(state);
    require(constManager.IsStoppedForAndroidCheckpoint() == (std::string(state) == "STATE_STOPPED"),
            "checkpoint manager query accepted a non-stopped state or rejected stopped state");
  }
  std::cout<<"PASS public_android_manager_query_preserves_all_six_stopped_state_cases\n";
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
        cpp.write_text(code.replace("// @PRODUCTION@", functions).replace(
            "// @MANAGER_API@", manager_api_fixture(manager_header, manager)))
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread", "-DTARGET_ANDROID",
                        str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)
    print("PASS all_three_pvr_startup_entries_hold_full_scope_admission_leases_and_private_history_is_latched")


if __name__ == "__main__":
    main()
