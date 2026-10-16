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
         "repository-local-failure", "repository-late-local", "startup-admission-negative",
         "startup-early-close", "startup-write-pending", "startup-write-failed", "startup-deadline",
         "startup-failed", "startup-first-party-missing", "startup-without-close", "startup-late-scope",
         "entry-early-close", "entry-create-failure", "entry-gui-failure", "entry-initialize-failure", "entry-without-close"]
CASES += ["startup-observer-pending", "startup-observer-failed"]
ENTRY_PEERS = r'''
namespace Test { inline std::string entryMode; }
CApplication g_application;
class CMessagePrinter {public: static void DisplayError(const char*){};};
class CXBMCApp {public: static CXBMCApp&Get(){static CXBMCApp app;return app;}
 void Initialize(){} void Deinitialize(){} };
bool CApplication::Create() {
  assert(Get().startupInProgress);
  std::filesystem::create_directories(Test::root);
  assert(RegisterStartupOwner(OWNER,getpid(),Test::root)); assert(PublishStartupOwner());
  if(Test::entryMode!="entry-without-close")assert(Request(SESSION,OWNER,getpid()));
  return Test::entryMode!="entry-create-failure";
}
bool CApplication::CreateGUI() {
  // The actual entry has not completed core initialization yet. These are
  // the same production directory guards that refused keyboard-layout reads.
  CheckpointWriteGuard directory("directory-work"); assert(directory);
  CheckpointWriteGuard jobs("jobs"); assert(jobs);
  return Test::entryMode!="entry-gui-failure";
}
bool CApplication::Initialize() {
  if(Test::entryMode=="entry-initialize-failure")return false;
  return true; // The original GUI_MSG_UI_READY is queued, not dispatched yet.
}
int CApplication::Run() {
  if(Test::entryMode=="entry-without-close") {
    Test::initialized=true;
  } else Process(); // Compile and execute the actual checkpoint branch below.
  assert(!Get().startupInProgress);
  if(Test::entryMode!="entry-without-close")assert(Get().requestReady && IsWriteAdmissionActive());
  return 77;
}
bool CApplication::Stop(int){return false;}
void CApplication::Cleanup(){}
constexpr int EXITCODE_QUIT=0;
'''
MAIN = r'''
int main(int argc, char** argv) {
  assert(argc == 3);
  std::string mode = argv[1]; Test::root = argv[2]; CApplication app;
  if (mode.rfind("entry-",0)==0) {
    Test::entryMode=mode;Test::initialized=false;
    const int result=XBMC_Run(true);
    if(mode=="entry-without-close")assert(result==77 && !IsActive() && !Get().startupInProgress);
    else if(mode=="entry-early-close")assert(result==77 && Get().requestReady && !Get().startupInProgress);
    else assert(result==-1 && Get().phase=="CHECKPOINT_FAILED" && !Get().requestReady);
    assert(!AuthorizeTermination(SESSION,OWNER,getpid())); // Entry completion is never a save receipt.
    return 0;
  }
  if (mode == "startup-admission-negative") {
    Test::initialized = false;
    std::filesystem::create_directories(Test::root);
    assert(RegisterStartupOwner(OWNER, getpid(), Test::root));
    assert(PublishStartupOwner());
    assert(Request(SESSION, OWNER, getpid()));
    CheckpointWriteGuard directory("directory-work");
    assert(!directory);
    Pump(app);
    assert(Get().phase=="CHECKPOINT_FAILED"); // No successful core proof exists.
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    std::cout << "original early Close rejects required startup directory; no authorization\n";
    return 0;
  }
  std::unique_ptr<ApplicationStartupScope> startup;
  if (mode.rfind("startup-", 0) == 0) {
    startup = std::make_unique<ApplicationStartupScope>();
    Test::initialized = false;
    assert(Get().startupInProgress);
    if (mode == "startup-without-close") {
      startup->Complete(); startup.reset();
      assert(!Get().startupInProgress);
      assert(!IsActive() && !IsWriteAdmissionActive());
      assert(Get().generation == 0 && Test::scriptShutdowns == 0);
      return 0;
    }
  }
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
  if (mode == "unobserved-writer") {
    // The same required proof now waits before closing mutation admission,
    // so installing the observer cannot reject its own native imports.
    assert(Get().phase == "CHECKPOINT_REQUESTED" && !Get().requestReady);
    assert(!InfinityScriptPersistence::WriteProtectionActive());
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    Get().expires=Clock::now(); Status(SESSION,OWNER,getpid());
    assert(Get().phase=="CHECKPOINT_FAILED" && !AuthorizeTermination(SESSION,OWNER,getpid()));
    return 0;
  }
  if (startup) {
    const auto started = Get().started, expires = Get().expires;
    const auto generation = Get().generation;
    assert(PublishStartupOwner()); // A pending Close cannot break profile startup ownership.
    if (mode == "startup-late-scope") {
      ApplicationStartupScope late; late.Complete();
      assert(Get().startupInProgress && !IsWriteAdmissionActive());
    }
    assert(IsActive() && !IsWriteAdmissionActive());
    assert(IsStartupParticipantAdmissionOpen());
    assert(Test::scriptStartupCutoffs == 1);
    assert(Get().phase == "CHECKPOINT_REQUESTED" && !Get().requestReady);
    assert(!InfinityScriptPersistence::WriteProtectionActive());
    assert(Test::scriptShutdowns == 0);
    { CheckpointWriteGuard directory("directory-work"); assert(directory); }
    { CheckpointWriteGuard jobs("jobs"); assert(jobs); }
    { CheckpointWriteGuard command("playback-command"); assert(!command); }
    { CheckpointWriteGuard optional("optional-cache-work"); assert(!optional); }
    Pump(app); // Startup is not initialized: do not run or fake the save sequence.
    assert(Get().phase == "CHECKPOINT_REQUESTED");
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    if (mode == "startup-failed") {
      startup.reset();
      assert(Get().phase == "CHECKPOINT_FAILED");
      assert(!IsStartupParticipantAdmissionOpen());
      assert(Get().error.find("application_startup_initialization_failed") != std::string::npos);
      assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
      return 0;
    }
    if (mode == "startup-deadline") {
      Get().expires = Clock::now();
      Status(SESSION, OWNER, getpid());
      assert(Get().phase == "CHECKPOINT_FAILED");
      assert(!IsStartupParticipantAdmissionOpen());
      startup->Complete();
      assert(!IsWriteAdmissionActive() && !AuthorizeTermination(SESSION, OWNER, getpid()));
      return 0;
    }
    if (mode == "startup-write-failed") {
      const auto errors = ErrorGeneration();
      RecordPersistenceFailure("native_databases", "genuine_startup_save_failed");
      startup->Complete();
      assert(HasFailureSince(errors));
      assert(Get().owners["native_databases"].error == "genuine_startup_save_failed");
      assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
      return 0;
    }
    if (mode == "startup-write-pending") {
      const auto path = Test::root+"/favourites.xml";
      pendingWrite = InfinityScriptPersistence::BeginProtectedOperation(42, {path}, "real_startup_write");
      assert(pendingWrite);
      std::ofstream(path) << "retained startup state";
    }
    if (mode == "startup-observer-pending" || mode == "startup-observer-failed")
      InfinityScriptPersistence::Admit(43,"startup.pending:service.py");
    startup->Complete();
    assert(Get().startupCoreComplete && !Get().startupInProgress);
    assert(!IsStartupParticipantAdmissionOpen());
    // Kodi's public IsInitialized also waits for the optional GUI_UI_READY
    // startup-animation message. Successful Create/CreateGUI/Initialize is
    // genuine core readiness; all original essential saves are still required.
    assert(!Test::initialized);
    startup.reset();
    Pump(app);
    if (mode == "startup-observer-pending" || mode == "startup-observer-failed") {
      assert(!Get().startupInProgress && !IsWriteAdmissionActive() && !Get().requestReady);
      assert(Get().pendingDetail=="python_persistence_observer_initialization");
      assert(!InfinityScriptPersistence::WriteProtectionActive());
      if (mode == "startup-observer-failed") {
        InfinityScriptPersistence::Fail(43,"checked_python_observer_initialization_failed","original python exception");
        Pump(app);
        assert(Get().phase=="CHECKPOINT_FAILED" && !AuthorizeTermination(SESSION,OWNER,getpid()));
        return 0;
      }
      InfinityScriptPersistence::Observed(43);
      Pump(app);
    }
    assert(Get().started == started && Get().expires == expires && Get().generation == generation);
    assert(IsWriteAdmissionActive() && Get().requestReady && Test::scriptShutdowns >= 1);
    { CheckpointWriteGuard lateDirectory("directory-work"); assert(!lateDirectory); }
    { CheckpointWriteGuard lateJobs("jobs"); assert(!lateJobs); }
  }
  if (localRepository) {
    Pump(app); active(); Pump(app);
    assert(Get().phase == "QUIESCE" && Test::freezes == 0);
    assert(!AuthorizeTermination(SESSION, OWNER, getpid()));
    if (mode == "repository-local-failure")
      RecordFailure("native_databases", "genuine_admitted_repository_write_failed");
    localRepository.reset();
  }
  if (mode == "first-party-missing" || mode == "startup-first-party-missing") {
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
  if (mode == "protected-writer" || mode == "startup-write-pending") {
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
  assert(InfinityScriptPersistence::Snapshot().active == (mode=="startup-observer-pending"?2u:1u));
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
    p.add_argument("--case", action="append", help="Select existing or targeted coordinator controls")
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
        stubs = stubs.replace('namespace Test {', 'namespace Test {\ninline unsigned scriptShutdowns=0,scriptStartupCutoffs=0;')
        stubs = stubs.replace('void BeginShutdown(){};', 'void BeginShutdown(){++Test::scriptShutdowns;};void BeginCheckpointStartupAdmission(){++Test::scriptStartupCutoffs;};')
        stubs = stubs.replace('bool IsInitialized()const', 'bool Create();bool CreateGUI();bool Initialize();int Run();bool Stop(int);void Cleanup();void Process();bool IsInitialized()const')
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
        entry = (args.variant_source/'platform/xbmc.cpp').read_text()
        # Compile the actual staged production entry; its Kodi application and
        # platform peers are controlled above, not a rewritten entry function.
        entry = entry[entry.index('extern "C" int XBMC_Run'):]
        assert entry.index('ApplicationStartupScope infinityStartup') < entry.index('g_application.Create()')
        assert entry.index('g_application.Initialize()') < entry.index('infinityStartup.Complete()') < entry.index('g_application.Run()')
        app_source = (args.variant_source/'application/Application.cpp').read_text()
        process_start = app_source.index('void CApplication::Process()')
        process_end = app_source.index('  // dispatch the messages generated', process_start)
        process = app_source[process_start:process_end]+'}\n'
        assert 'InfinityAndroidCheckpoint::Pump' in process
        harness = old.HARNESS.split("int main(int argc,char**argv)", 1)[0] + ENTRY_PEERS + entry + process + MAIN
        (src / "test.cpp").write_text(harness)
        binary = work / "test"
        subprocess.run(["g++", "-std=c++17", "-DTARGET_ANDROID", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", "-pthread",
                        "-I", str(src), str(src / "test.cpp"), str(src / "utils/Variant.cpp"), "-o", str(binary)], check=True)
        cases = args.case or CASES
        assert set(cases) <= set(CASES)
        for case in cases:
            result = subprocess.run([str(binary), case, str(work / case)], capture_output=True, text=True, timeout=5)
            if case == "optional-blocked" and result.returncode == 0:
                fixture = json.loads(result.stdout)
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.with_name("runtime-native-safe-fixture.json").write_text(json.dumps(fixture, indent=2)+"\n")
            results.append({"case": case, "exit_code": result.returncode, "error": result.stderr,
                            "observation":result.stdout if case.startswith('startup-') else ''})
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
