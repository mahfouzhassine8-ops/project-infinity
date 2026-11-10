#!/usr/bin/env python3
"""Selected host checks of the actual final-save coordinator, not Android QA.

Reuse the existing controlled service peers without running their scenario list.
The coordinator, persistence ledger, database barrier and authorization are real.
Only disposable host files are touched. No APK, device, Close workflow or signer.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


HARNESS = r'''
#include "platform/android/activity/InfinityAndroidCheckpoint.cpp"
#include <cassert>
#include <fstream>
#include <iostream>
using namespace InfinityAndroidCheckpoint;
int main(int argc, char** argv)
{
  assert(argc == 4);
  const std::string mode = argv[1], root = argv[2];
  const bool baseline = std::string(argv[3]) == "baseline";
  Test::root = root;
  const auto profile = root + "/profile", cache = root + "/cache";
  std::filesystem::create_directories(profile);
  std::filesystem::create_directories(cache);
  const auto marker = profile + "/essential-sentinel.txt";
  std::ofstream(marker) << "existing-essential-bytes";
  const auto metadata = cache + "/optional.txt";
  std::ofstream(metadata) << "regenerable-cache";

  InfinityScriptPersistence::Admit(123, "service.host-fixture:service.py");
  InfinityScriptPersistence::Observed(123);
  // The existing native operation lease is real. This is NOT an assertion
  // that CPython audit-only metadata has acquired a completion adapter.
  const auto lease = InfinityScriptPersistence::BeginProtectedOperation(
      123, {metadata}, "metadata.chmod");
  assert(lease && ::chmod(metadata.c_str(), 0600) == 0);
  InfinityScriptPersistence::EndProtectedOperation(lease);
  if (mode != "optional-private")
  {
    InfinityScriptPersistence::Fail(123,
        "external_or_opaque_writer_requires_explicit_participant", "unknown-host-fixture-image");
    InfinityScriptPersistence::Retired(123);
    assert(InfinityScriptPersistence::Snapshot().active == 0);
    assert(InfinityScriptPersistence::Snapshot().blockingCount == 1);
  }
  assert(InfinityScriptPersistence::BeginWriteProtection(1, {profile}, {cache}));
  assert(InfinityScriptPersistence::CloseParticipantWrites(1));
  assert(InfinityDatabaseBarrier::Begin(1));

  auto& s = Get();
  s.active = true; s.requestReady = true; s.sealed = true;
  s.generation = 1; s.phase = "PERSISTING"; s.stage = 5;
  s.session = "11111111-1111-4111-8111-111111111111";
  s.owner = "22222222-2222-4222-8222-222222222222";
  s.pid = static_cast<int>(getpid()); s.started = Clock::now();
  s.expires = s.started + DEADLINE;
  // Earlier owner phases are controlled preconditions, not end-to-end proof.
  for (const char* name : REQUIRED)
  {
    auto& owner = s.owners[name];
    owner.complete = true; owner.dirty = false;
  }
  for (const char* name : {"native_admission", "native_databases", "deferred_dialog_state"})
  {
    s.owners[name].complete = false; s.owners[name].dirty = true;
  }
  RecordFailure("python_services", "optional-work-unfinished");
  assert(s.blockers.empty());
  if (mode == "deferred-save-fails") Test::deferredOk = false;
  if (mode == "settings-save-fails") Test::settingsOk = false;
  if (mode == "database-seal-fails")
  {
    // A real invalid second seal, not a boolean replacement of Seal().
    assert(InfinityDatabaseBarrier::Seal(1));
    s.stage = 6;
  }
  CApplication application;
  Pump(application);
  std::ifstream existing(marker);
  std::string bytes; std::getline(existing, bytes);
  assert(bytes == "existing-essential-bytes");
  assert(!s.owners["python_services"].complete);
  assert(!s.owners["python_services"].error.empty());

  if (mode == "optional-private")
  {
    assert(!baseline && InfinityScriptPersistence::Snapshot().active == 1);
    assert(s.phase == "SAFE_TO_TERMINATE");
    assert(s.owners["native_databases"].complete && s.owners["deferred_dialog_state"].complete);
    assert(InfinityScriptPersistence::EssentialWritesAuthorized(1));
    assert(AuthorizeTermination(s.session, s.owner, s.pid));
    assert(!AuthorizeTermination(s.session, s.owner, s.pid));
  }
  else
  {
    assert(s.phase == "CHECKPOINT_FAILED" && !s.authorized);
    assert(!AuthorizeTermination(s.session, s.owner, s.pid));
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(1));
    const bool databaseComplete = !baseline && mode != "database-seal-fails";
    const bool deferredComplete = !baseline && mode == "opaque-retired";
    assert(s.owners["native_databases"].complete == databaseComplete);
    assert(s.owners["deferred_dialog_state"].complete == deferredComplete);
    assert(!s.owners["native_admission"].complete);
  }
  std::cout << mode << ":PASS\n";
}
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source, runtime, peer_source, cases, baseline):
    spec = importlib.util.spec_from_file_location("existing_coordinator_peers", peer_source)
    peer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(peer)
    stubs = peer.STUBS.replace(
        "void UnPauseJobs(){};", "void UnPauseJobs(){}; void PruneCheckpointOptionalQueuedJobs(){};")
    stubs = stubs.replace("void BeginShutdown(){};",
                          "void BeginShutdown(){}; void BeginCheckpointStartupAdmission(){};")
    assert "void PruneCheckpointOptionalQueuedJobs()" in stubs
    assert "void BeginCheckpointStartupAdmission()" in stubs
    with tempfile.TemporaryDirectory(prefix="infinity-owner-receipts-") as folder:
        temp = Path(folder)
        real_files = [
            "platform/android/activity/InfinityAndroidCheckpoint.h",
            "platform/android/activity/InfinityScriptPersistence.h",
            "platform/android/activity/InfinityProtectedWrites.h",
            "platform/android/activity/InfinityShutdownTrace.h",
            "platform/android/activity/InfinityCheckpointFile.h",
            "dbwrappers/InfinityDatabaseBarrier.h",
            "utils/JobCheckpoint.h", "utils/Variant.h", "utils/Variant.cpp",
        ]
        for rel in real_files:
            target = temp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(runtime / "xbmc" / rel, target)
        cpp = temp / "platform/android/activity/InfinityAndroidCheckpoint.cpp"
        shutil.copy2(source, cpp)
        (temp / "stubs.h").write_text(stubs)
        boundaries = [
            "platform/android/activity/InfinityCheckpointXml.h",
            "platform/android/activity/InfinityPlaybackCheckpoint.h",
            "platform/android/activity/JNIMainActivity.h",
            "ServiceBroker.h", "addons/Skin.h", "application/Application.h",
            "application/ApplicationPlayer.h", "favourites/FavouritesService.h",
            "filesystem/Directory.h", "filesystem/SpecialProtocol.h",
            "interfaces/AnnouncementManager.h", "interfaces/generic/ScriptInvocationManager.h",
            "peripherals/Peripherals.h", "profiles/ProfileManager.h", "pvr/PVRManager.h",
            "pvr/addons/PVRClients.h", "settings/Settings.h", "settings/SettingsComponent.h",
            "utils/JSONVariantParser.h", "utils/JSONVariantWriter.h", "utils/JobManager.h",
        ]
        for rel in boundaries:
            target = temp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('#pragma once\n#include "stubs.h"\n')
        diagnostic = temp / "platform/android/activity/InfinityVfsOpenTrace.h"
        diagnostic.write_text('''#pragma once
namespace InfinityVfsOpenTrace {
struct CheckpointFlush { ~CheckpointFlush() {} };
template<class... T> void OwnerStatus(T&&...) {}
template<class... T> void CheckpointOutcome(T&&...) {}
template<class... T> void CheckpointBegin(T&&...) {}
}
''')
        (temp / "threads").mkdir()
        (temp / "threads/InfinityStabilityProbe.h").write_text(
            '#pragma once\nnamespace InfinityStabilityProbe { inline void CloseRequested() {} }\n')
        (temp / "platform/android/activity/InfinityInstalledModules.h").write_text('''#pragma once
#include <string>
namespace InfinityInstalledModules { inline bool Participant(const std::string&, unsigned, const std::string&) { return false; } }
''')
        (temp / "utils/log.h").write_text('''#pragma once
constexpr int LOGWARNING = 1;
struct CLog { template<class... T> static void Log(T&&...) {} };
''')
        (temp / "harness.cpp").write_text(HARNESS)
        common = ["g++", "-std=c++17", "-DTARGET_ANDROID", "-pthread", "-I", str(temp)]
        subprocess.run(common + ["-c", str(temp / "utils/Variant.cpp"), "-o", str(temp / "variant.o")], check=True)
        binary = temp / "receipts"
        subprocess.run(common + ["-Wall", "-Wextra", "-Werror", str(temp / "harness.cpp"),
                                str(temp / "variant.o"), "-o", str(binary)], check=True)
        result = []
        for case in cases:
            subprocess.run([str(binary), case, str(temp / case),
                            "baseline" if baseline else "candidate"], check=True, timeout=10)
            result.append({"case": case, "result": "PASS"})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--peer-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    task = Path(__file__).resolve().parent
    binding = json.loads((task / "BASELINE-SOURCE-BINDINGS.json").read_text())
    for rel, expected in binding["matched_native_sources"].items():
        assert digest(args.runtime / rel) == expected, "baseline source mismatch: " + rel
    baseline = args.runtime / "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
    candidate = task / "native/overlay/xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
    original = run(baseline, args.runtime, args.peer_source, ["opaque-retired"], True)
    cases = ["optional-private", "opaque-retired", "database-seal-fails", "deferred-save-fails", "settings-save-fails"]
    corrected = run(candidate, args.runtime, args.peer_source, cases, False)
    report = {"schema": 1, "scope": "HOST_CONTROLLED_FINAL_SAVE_BOUNDARY",
              "baseline_sha256": digest(baseline), "candidate_sha256": digest(candidate),
              "peer_source_sha256": digest(args.peer_source), "baseline_observation": original,
              "candidate_cases": corrected, "historical_checkpoint_failure": "RETAINED",
              "android_or_physical_test": "NOT_RUN", "python_metadata_adapter": "NOT_IMPLEMENTED",
              "signed_install_or_process_death_or_reopen": "NOT_RUN"}
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
