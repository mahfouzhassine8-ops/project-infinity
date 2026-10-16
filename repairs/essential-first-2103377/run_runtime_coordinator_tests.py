#!/usr/bin/env python3
"""Compile the production coordinator plus the real persistence write barrier.

Reuses explicit Kodi peer adapters from the original host harness. The unchanged Kodi save peers remain adapters; production write admission and
sealing are compiled from runtime headers, without any coverage toggle.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import apply_runtime
import reconstruct_coordinator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OVERLAY = ROOT / "repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc"
PINS = {
    "utils/Variant.cpp": "a22b0af9ee844def08664b12f769a9119a3a00c8a02bf589cc6772e1c7c7293f",
    "utils/Variant.h": "18b9657ea27c4cf4eecf4e8eed66bc146e1a46e7f6847b79d4aa11308758ee3a",
}
CASES = ["optional-blocked", "optional-failed", "settings-failed", "profiles-failed",
         "first-party-missing", "first-party-failed", "compat-failed", "protected-writer",
         "native-transaction", "lease-lost", "deadline", "unobserved-writer", "protection-warning",
         "optional-repository", "repository-transaction", "repository-local-race",
         "repository-local-failure", "repository-late-local"]
MAIN = r'''
int main(int argc, char** argv) {
  assert(argc == 3);
  std::string mode = argv[1]; Test::root = argv[2]; CApplication app;
  const auto privateDir = Test::root + "/addon_data/plugin.video.optional";
  std::filesystem::create_directories(privateDir);
  const auto optionalPath = privateDir + "/cache.json";
  std::ofstream(optionalPath) << "cache";
  Test::foreign = {"plugin.video.optional:service.py"};
  InfinityScriptPersistence::Admit(42, Test::foreign.front());
  InfinityScriptPersistence::Observed(42);
  InfinityScriptPersistence::Touch(42, optionalPath);
  if (mode == "unobserved-writer") InfinityScriptPersistence::Admit(43, "unobserved:service.py");
  if (mode == "protection-warning") InfinityScriptPersistence::ProtectionFailure("test1_unresolved_protected_write_warning");
  if (mode == "optional-failed") InfinityScriptPersistence::Fail(42, "buffer_flush_failed");
  std::shared_ptr<CJobCheckpointRecord> repository;
  if (mode == "optional-repository" || mode == "repository-transaction")
    repository = JobCheckpoint::Admit(false, false, "native_databases", "repository_update",
        "CRepositoryUpdateJob", "callback", false, "test-repository");
  uint64_t pendingWrite = 0;
  if (mode == "protected-writer") {
    const auto path = Test::root + "/favourites.xml";
    std::ofstream(path) << "essential";
    pendingWrite = InfinityScriptPersistence::BeginProtectedOperation(42, {path}, "test.actual_write_extent");
    assert(pendingWrite);
  }
  assert(RegisterStartupOwner(OWNER, getpid(), Test::root));
  assert(PublishStartupOwner());
  std::unique_ptr<CheckpointWriteGuard> localRepository;
  if (mode == "repository-local-race" || mode == "repository-local-failure") {
    localRepository = std::make_unique<CheckpointWriteGuard>("optional-cache-work");
    assert(*localRepository);
  }
  assert(Request(SESSION, OWNER, getpid()));
  if (localRepository) {
    Pump(app); active(); Pump(app);
    assert(Get().phase == "QUIESCE" && Test::freezes == 0);
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    if (mode == "repository-local-failure")
      RecordFailure("native_databases", "genuine_admitted_repository_write_failed");
    localRepository.reset();
  }
  if (mode == "first-party-missing") {
    Pump(app); active(); Pump(app); Pump(app);
    assert(!Get().owners["command_center"].complete);
    assert(!Get().owners["kodi_settings"].complete);
    assert(!AuthorizeTermination(SESSION, OWNER, getpid())); return 0;
  }
  ready(app);
  if (mode == "first-party-failed") response("CHECKPOINT_FAILED");
  if (mode == "compat-failed") compatResponse("CHECKPOINT_FAILED");
  if (mode == "settings-failed") Test::settingsOk = false;
  if (mode == "profiles-failed") Test::profilesOk = false;
  int transactionOwner = 0;
  if (mode == "native-transaction" || mode == "repository-transaction")
    InfinityDatabaseBarrier::SetTransaction(&transactionOwner, true);
  Pump(app);
  if (mode == "native-transaction" || mode == "repository-transaction") {
    assert(Get().phase == "PERSISTING");
    assert(!Get().owners["kodi_settings"].complete);
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    InfinityDatabaseBarrier::SetTransaction(&transactionOwner, false);
    Pump(app);
  }
  if (mode == "protected-writer") {
    assert(Get().phase == "PERSISTING");
    assert(!InfinityScriptPersistence::EssentialWrites().blockers.empty());
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    if (pendingWrite) InfinityScriptPersistence::EndProtectedOperation(pendingWrite);
    return 0;
  }
  if (mode == "protection-warning" || mode == "unobserved-writer") {
    assert(Get().owners["kodi_settings"].complete);
    assert(Get().owners["profiles"].complete);
    assert(Get().owners["favourites"].complete);
    assert(Get().phase == "CHECKPOINT_FAILED");
    assert(!Get().owners["native_admission"].complete);
    assert(!InfinityScriptPersistence::EssentialWrites().blockers.empty());
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    return 0;
  }
  if (mode == "first-party-failed" || mode == "compat-failed" ||
      mode == "settings-failed" || mode == "profiles-failed" ||
      mode == "protected-writer" || mode == "unobserved-writer" || mode == "repository-local-failure") {
    assert(Get().phase == "CHECKPOINT_FAILED");
    assert(!AuthorizeTermination(SESSION, OWNER, getpid())); return 0;
  }
  assert(Get().phase == "SAFE_TO_TERMINATE");
  if (mode == "repository-late-local") {
    CheckpointWriteGuard refused("optional-cache-work");
    assert(!refused && Get().phase == "SAFE_TO_TERMINATE");
  }
  assert(Get().owners["kodi_settings"].complete);
  assert(Get().owners["profiles"].complete);
  assert(Get().owners["native_databases"].complete);
  assert(!Get().owners["python_services"].complete);
  assert(InfinityScriptPersistence::Snapshot().active == 1);
  const auto safe = Status(SESSION, OWNER, getpid());
  CVariant row; assert(CJSONVariantParser::Parse(safe, row));
  assert(row["owners"].size() == 17);
  assert(row["essential_owners"].size() == 16);
  if (repository) {
    assert(row["optional_unfinished_jobs"].size() == 1);
    assert(row["optional_unfinished_jobs"][0]["operation"].asString() == "repository_update");
    assert(!repository->resolved);
  }
  assert(!row["process_death_confirmed"].asBoolean());
  assert(!AuthorizeTermination(SESSION, "wrong-owner-00000000", getpid()));
  if (mode == "lease-lost") Test::ownLease = false;
  if (mode == "deadline") Get().expires = Clock::now();
  if (mode == "lease-lost" || mode == "deadline") {
    assert(!AuthorizeTermination(SESSION, OWNER, getpid())); return 0;
  }
  assert(AuthorizeTermination(SESSION, OWNER, getpid()));
  assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
  CheckpointWriteGuard late("kodi_settings"); assert(!late);
  std::cout << safe << '\n';
}
'''

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variant-source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    spec = importlib.util.spec_from_file_location("old_host", ROOT / "repairs/android-checkpoint-shutdown/runtime-tests/test_native_coordinator.py")
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    results = []
    with tempfile.TemporaryDirectory(prefix="essential-coordinator-") as work:
        work = Path(work); src = work / "xbmc"
        reconstruct_coordinator.reconstruct(work)
        source = work / apply_runtime.CHECKPOINT
        source.write_text(apply_runtime.checkpoint(source.read_text()))
        for rel in ["platform/android/activity/InfinityAndroidCheckpoint.h",
                    "platform/android/activity/InfinityCheckpointFile.h",
                    "platform/android/activity/InfinityScriptPersistence.h",
                    "dbwrappers/InfinityDatabaseBarrier.h", "utils/JobCheckpoint.h"]:
            dst = src / rel; dst.parent.mkdir(parents=True, exist_ok=True)
            runtime = HERE / "runtime/xbmc" / rel
            shutil.copyfile(runtime if runtime.exists() else OVERLAY / rel, dst)
        shutil.copyfile(HERE / "runtime/xbmc/platform/android/activity/InfinityProtectedWrites.h",
                        src / "platform/android/activity/InfinityProtectedWrites.h")
        for rel, digest in PINS.items():
            data = (args.variant_source / rel).read_bytes()
            assert hashlib.sha256(data).hexdigest() == digest, rel
            dst = src / rel; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(data)
        stubs = old.STUBS.replace("class CJobManager {public:", "class CJobManager {public:void PruneCheckpointOptionalQueuedJobs(){};")
        start = stubs.index(' static JobCheckpoint::Snapshot AndroidCheckpointSnapshot()')
        end = stubs.index('class CSettings ', start)
        stubs = stubs[:start] + ''' static JobCheckpoint::Snapshot AndroidCheckpointSnapshot(){return JobCheckpoint::GetSnapshot();}};
''' + stubs[end:]
        stubs = stubs.replace(' const std::string prefix="special://profile";',
            ' if(p=="special://masterprofile"){return Test::root;} if(p=="special://temp"){return Test::root+"/temp";} const std::string prefix="special://profile";')
        (src / "stubs.h").write_text(stubs)
        boundaries = ["ServiceBroker.h", "addons/Skin.h", "application/Application.h", "application/ApplicationPlayer.h",
            "favourites/FavouritesService.h", "filesystem/Directory.h", "filesystem/SpecialProtocol.h",
            "interfaces/AnnouncementManager.h", "interfaces/generic/ScriptInvocationManager.h", "peripherals/Peripherals.h",
            "profiles/ProfileManager.h", "pvr/PVRManager.h", "pvr/addons/PVRClients.h", "settings/Settings.h",
            "settings/SettingsComponent.h", "utils/JSONVariantParser.h", "utils/JSONVariantWriter.h", "utils/JobManager.h"]
        boundaries += ["platform/android/activity/" + name for name in ("InfinityCheckpointXml.h", "InfinityPlaybackCheckpoint.h", "JNIMainActivity.h")]
        for rel in boundaries:
            dst = src / rel; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text('#pragma once\n#include "stubs.h"\n')
        (src / "platform/android/activity/InfinityShutdownTrace.h").write_text('''#pragma once
namespace InfinityShutdownTrace { inline void Begin(){} template<class... T> void Event(T...){} struct Scope { explicit Scope(const char*){} }; }
''')
        (src / "platform/android/activity/InfinityVfsOpenTrace.h").write_text('''#pragma once
namespace InfinityVfsOpenTrace { struct CheckpointFlush { ~CheckpointFlush(){} }; template<class... T> void OwnerStatus(T...){} inline void CheckpointOutcome(unsigned long long,bool){} inline void CheckpointBegin(unsigned long long){} }
''')
        (src / "threads").mkdir()
        (src / "threads/InfinityStabilityProbe.h").write_text('#pragma once\nnamespace InfinityStabilityProbe { inline void CloseRequested(){} }\n')
        harness = old.HARNESS.split("int main(int argc,char**argv)", 1)[0] + MAIN
        (src / "test.cpp").write_text(harness)
        binary = work / "test"
        subprocess.run(["g++", "-std=c++17", "-DTARGET_ANDROID", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", "-pthread",
                        "-I", str(src), str(src / "test.cpp"), str(src / "utils/Variant.cpp"), "-o", str(binary)], check=True)
        for case in CASES:
            result = subprocess.run([str(binary), case, str(work / case)], capture_output=True, text=True, timeout=5)
            if case == "optional-blocked" and result.returncode == 0:
                fixture = json.loads(result.stdout)
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.with_name("runtime-native-safe-fixture.json").write_text(json.dumps(fixture, indent=2)+"\n")
            results.append({"case": case, "exit_code": result.returncode, "error": result.stderr})
            if result.returncode: print(result.stderr)
            print(case, "PASS" if result.returncode == 0 else "FAIL")
    report = {"scope": "production coordinator and persistence barrier; unchanged Kodi peers are adapters",
              "cases": results, "all_passed": all(r["exit_code"] == 0 for r in results),
              "actual_kodi_save_callbacks_executed": False, "simulated_hook_coverage_flag": False,
              "android_process_death_verified": False, "candidate_deliverable": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    assert report["all_passed"]

if __name__ == "__main__":
    main()
