#!/usr/bin/env python3
"""Shutdown-only delta on the SHA-verified Rails Handoff RC1 source.

Uses the existing script ledger, database barrier and coordinator. Compilation
is not delivery authorization; packaging requires independent runtime evidence.
"""
import hashlib
import json
from pathlib import Path
import stage_experiment

HERE = Path(__file__).resolve().parent
CHECKPOINT = stage_experiment.CHECKPOINT
MANAGER = 'xbmc/interfaces/generic/ScriptInvocationManager.cpp'
SQLITE = 'xbmc/dbwrappers/sqlitedataset.cpp'
POSIX = 'xbmc/platform/posix/filesystem/PosixFile.cpp'
DIRECTORY = 'xbmc/platform/posix/filesystem/PosixDirectory.cpp'
JOBS = 'xbmc/utils/JobManager.cpp'
INSTALLER = 'xbmc/addons/AddonInstaller.cpp'
ADDON = 'xbmc/addons/Addon.cpp'
REPOSITORY = 'xbmc/addons/RepositoryUpdater.cpp'
ENGINE_ENTRY = 'xbmc/platform/xbmc.cpp'
APPLICATION = 'xbmc/application/Application.cpp'
PYTHON_INVOKER = 'xbmc/interfaces/python/PythonInvoker.cpp'
PINS = {
    CHECKPOINT: stage_experiment.PIN,
    MANAGER: 'b3ff61b946ed767e3c586caa74fab0ae1c35b404ecef4b46839270d84f57f16e',
    SQLITE: '18206a86843f11bea447ebbe1ecca474bf3ae62aef9bd204e37c671515111920',
    POSIX: '0a880f1de9c1cb9d7c1cd0c99fc1ae0334c87ddb77faa50b81af8d80d7ef3baa',
    DIRECTORY: '68e638f060868bca397dd5a8e1f85232a70df31f92692460b0e741a63205094a',
    JOBS: '8315f6ad8c794d5a96bcb544b0e53eee585faec121e15806edd163f97f4b8d3c',
    INSTALLER: 'a9e21a3b0c9da59b33376d15b53ac7ba8886613c15b59878496cb31833502b9b',
    ADDON: 'bb6339e695d36f72639668acfafdd8422fb5f2c15dcb864749c9521203655fbc',
    REPOSITORY: '92e44c82995060552f71b675bdc03c9bb08b63430d2d83b59fcdb78ea7d5c0f2',
    ENGINE_ENTRY: '2ca7a10d3c2bb19d79a35f2faecd8b2f01a428fc31aae9fe63f568cd878ac362',
    APPLICATION: '3f064f1a6dd941d78c1a58383b29fce8c0c553ed5cb030e319c9955c4ae4be06',
    PYTHON_INVOKER: '1ad5a73740a622c42ad1ed5a9ed40bf1d903513a7540e7a745c266f5b62b5a7e',
}
once = stage_experiment.once

def checkpoint(text):
    # Reuse the completed sequencing change; replace the historical fake-hook
    # experiment with the existing persistence ledger's real runtime leases.
    text = stage_experiment.checkpoint(text)
    text = text.replace('InfinityEssentialScriptFence.h', 'InfinityProtectedWrites.h')
    text = text.replace('InfinityEssentialScriptFence::Snapshot()', 'InfinityScriptPersistence::EssentialWrites()')
    text = text.replace('InfinityEssentialScriptFence::Authorized(', 'InfinityScriptPersistence::EssentialWritesAuthorized(')
    text = text.replace('essential.sealed', '(essential.phase == 3)')
    text = text.replace('static_cast<uint64_t>(essential.optionalUnfinished)',
                        'static_cast<uint64_t>(InfinityScriptPersistence::OptionalUnfinishedWriters())')
    start = text.index('bool AuthorizeTermination(')
    authorization = text[start:]
    authorization = once(authorization, '    if (!Matches(s, session, owner, pid))',
                         '    if (!Matches(s, session, owner, pid) || s.phase != "SAFE_TO_TERMINATE")')
    text = text[:start] + authorization
    text = once(text, '  InfinityShutdownTrace::Begin();', '''  if (!InfinityScriptPersistence::BeginWriteProtection(infinityDiagnosticGeneration,
        {CSpecialProtocol::TranslatePath("special://profile"),
         CSpecialProtocol::TranslatePath("special://masterprofile")},
        {CSpecialProtocol::TranslatePath("special://temp")}))
  { RecordFatalFailure("native_admission", "protected_write_request_failed"); return false; }
  InfinityShutdownTrace::Begin();''')
    start = text.index('      // First-party callbacks have finished.')
    end = text.index('      Operation("background_jobs");', start)
    text = text[:start] + '''      // Keep optional retirement receipts diagnostic. First-party callbacks
      // above and the required background jobs below are still mandatory.
      const auto scripts = InfinityScriptPersistence::Snapshot();
      if (scripts.durable && scripts.active == 0 && scripts.blockingCount == 0)
        Complete("python_services", true);

''' + text[end:]
    text = once(text, '''      if (!InfinityDatabaseBarrier::Begin(s.generation))''', '''      if (!InfinityScriptPersistence::CloseParticipantWrites(s.generation))
      { RecordFatalFailure("native_admission", "protected_participant_admission_close_failed"); return; }
      if (!InfinityDatabaseBarrier::Begin(s.generation))''')
    text = once(text, '''      if (!InfinityEssentialScriptFence::Seal(s.generation))
      { RecordFatalFailure("native_admission", "essential_script_file_seal_failed"); return; }
      Complete("native_admission", false);
''', '')
    # Seal only AFTER final essential callbacks and native database durability.
    text = once(text, '''      bool databaseBlocked=false;''', '''      if (!InfinityScriptPersistence::SealEssentialWrites(s.generation))
      {
        const auto proof = InfinityScriptPersistence::EssentialWrites();
        RecordFatalFailure("native_admission", proof.blockers.empty() ?
            "protected_write_seal_not_durable" : proof.blockers.front().c_str());
        return;
      }
      Complete("native_admission", false);

      bool databaseBlocked=false;''')
    start = text.index('  result["blocking_jobs"] = CVariant(CVariant::VariantTypeArray);')
    end = text.index('  result["resolved_job_obligations"]', start)
    optional = text[start:end].replace('blocking_jobs', 'optional_unfinished_jobs').replace(
        's.jobs.blockers', 's.jobs.optionalUnfinished')
    text = text[:end] + optional + text[end:]
    assert 'InfinityEssentialScriptFence' not in text
    return startup_checkpoint(text)


def initialization_diagnostics(text):
    anchor = '  std::string encoded;\n  if (!CJSONVariantWriter::Write(result, encoded, true))\n    return "{\\\"schema\\\":1,\\\"phase\\\":\\\"CHECKPOINT_FAILED\\\",\\\"error\\\":\\\"status_encoding_failed\\\"}";'
    return once(text, anchor, '''  // Bound only new diagnostic bytes, after measuring the complete original
  // status. The unchanged Java parser accepts 64 KiB; preserve every existing
  // safety field and leave 1 KiB for diagnostic metadata/array separators.
  std::string beforeInitializationProgress;
  const bool originalStatusEncoded = CJSONVariantWriter::Write(result, beforeInitializationProgress, true);
  // If auxiliary metadata has no margin, return the exact original bytes.
  // A full safety inventory must never become an oversized status because
  // optional progress counters were appended to a zero-byte budget.
  if (originalStatusEncoded && beforeInitializationProgress.size() >= 64512)
    return beforeInitializationProgress;
  const std::size_t initializationProgressBudget = originalStatusEncoded && beforeInitializationProgress.size() < 64512
      ? std::min<std::size_t>(24576, 64512 - beforeInitializationProgress.size()) : 0;
  std::size_t initializationProgressBytes = 0;
  bool initializationProgressTruncated = false;
  std::vector<CVariant> initializationRows;
  std::vector<const InfinityScriptPersistence::Evidence::Initialization*> initializationSources;
  std::vector<std::size_t> initializationSizes;
  // First include current identity/stage for every diagnostic row that fits.
  // Optional history cannot displace a later writer's current-stage evidence.
  for (const auto& progress : scripts.initialization)
  {
    CVariant row(CVariant::VariantTypeObject);
    row["writer_id"] = progress.writerId;
    row["writer"] = progress.writer;
    row["pid"] = progress.pid;
    row["native_tid"] = progress.current.nativeTid;
    row["interpreter_identity"] = progress.current.interpreterIdentity;
    row["observed"] = progress.observed;
    row["stage"] = progress.current.stage;
    row["elapsed_ms"] = progress.elapsedMs;
    row["stage_elapsed_ms"] = progress.stageElapsedMs;
    row["steps_total"] = static_cast<uint64_t>(progress.steps.size());
    row["steps_overflow"] = progress.stepsOverflow;
    row["steps"] = CVariant(CVariant::VariantTypeArray);
    std::string progressJson;
    if (initializationRows.size() >= 64 || !CJSONVariantWriter::Write(row, progressJson, true) ||
        progressJson.size() + initializationProgressBytes > initializationProgressBudget)
    { initializationProgressTruncated = true; continue; }
    initializationProgressBytes += progressJson.size();
    initializationRows.push_back(row);
    initializationSources.push_back(&progress);
    initializationSizes.push_back(progressJson.size());
  }
  for (std::size_t rowIndex = 0; rowIndex < initializationRows.size(); ++rowIndex)
  {
    CVariant enriched = initializationRows[rowIndex];
    const auto& progress = *initializationSources[rowIndex];
    const auto firstStep = progress.steps.size() > 4 ? progress.steps.size() - 4 : 0;
    for (auto stepIndex = firstStep; stepIndex < progress.steps.size(); ++stepIndex)
    {
      const auto& step = progress.steps[stepIndex];
      CVariant entry(CVariant::VariantTypeObject);
      entry["stage"] = step.stage;
      entry["elapsed_ms"] = step.elapsedMs;
      enriched["steps"].push_back(entry);
    }
    std::string progressJson;
    if (CJSONVariantWriter::Write(enriched, progressJson, true) &&
        progressJson.size() + initializationProgressBytes - initializationSizes[rowIndex] <= initializationProgressBudget)
    {
      initializationProgressBytes += progressJson.size() - initializationSizes[rowIndex];
      initializationRows[rowIndex] = enriched;
    }
  }
  scriptEvidence["initialization_progress_contract"] = "native_python_initialization_progress_v1";
  scriptEvidence["initialization_progress"] = CVariant(CVariant::VariantTypeArray);
  for (const auto& row : initializationRows)scriptEvidence["initialization_progress"].push_back(row);
  scriptEvidence["initialization_progress_total_writers"] = static_cast<uint64_t>(scripts.initialization.size());
  scriptEvidence["initialization_progress_reported_writers"] = static_cast<uint64_t>(initializationRows.size());
  scriptEvidence["initialization_progress_truncated"] = initializationProgressTruncated;
  result["script_persistence"] = scriptEvidence;
''' + anchor)


def startup_checkpoint(text):
    text = initialization_diagnostics(text)
    text = once(text, '  bool requestReady{false};', '''  bool requestReady{false};
  bool startupInProgress{false};
  bool startupCoreComplete{false};
  bool writeAdmissionStarted{false};
  bool preparingWriteAdmission{false};''')
    text = once(text, '    if (!s.ownerRegistered || s.active.load() || s.lifecycleTeardown || s.ownerPublishing)',
                '    if (!s.ownerRegistered || (s.active.load() && (!s.startupInProgress || s.writeAdmissionStarted)) || s.lifecycleTeardown || s.ownerPublishing)')
    text = once(text, '  result["schema"] = 1;\n  result["exit_policy"]', '''  result["schema"] = 1;
  result["application_startup_in_progress"] = s.startupInProgress;
  result["application_core_initialized"] = s.startupCoreComplete;
  result["write_admission_started"] = s.writeAdmissionStarted;
  result["exit_policy"]''')
    text = once(text, 'bool IsActive() { return Get().active.load(); }', '''bool IsActive() { return Get().active.load(); }
bool IsWriteAdmissionActive()
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  return s.active.load() && s.writeAdmissionStarted;
}''')
    text = once(text, '  m_admitted = !s.active.load() ||', '''  const bool acceptedStartup = s.startupInProgress && !s.writeAdmissionStarted &&
      !s.sealed && s.phase == "CHECKPOINT_REQUESTED" &&
      (owner == "jobs" || owner == "directory-work");
  m_admitted = acceptedStartup || !s.active.load() ||''')
    start = text.index('bool Request(')
    end = text.index('std::string Status(', start)
    request = text[start:end]
    admission_start = request.index('  if (!InfinityScriptPersistence::BeginWriteProtection(')
    admission = request[admission_start:request.rindex('  return true;')]
    # Identity/deadline/trace begin at the user's request, not at activation.
    for line in ('  InfinityShutdownTrace::Begin();\n',
                 '  InfinityVfsOpenTrace::CheckpointBegin(infinityDiagnosticGeneration);\n',
                 '  InfinityShutdownTrace::Event("milestone", "checkpoint.request");\n'):
        admission = once(admission, line, '')
    admission = once(admission, '  CScriptInvocationManager::GetInstance().BeginShutdown();\n', '')
    request = request[:admission_start] + '''  InfinityShutdownTrace::Begin();
  InfinityVfsOpenTrace::CheckpointBegin(infinityDiagnosticGeneration);
  InfinityShutdownTrace::Event("milestone", "checkpoint.request");
  return ActivateWriteAdmission(infinityDiagnosticGeneration);
}

'''
    request = once(request, '    s.phase = "QUIESCE";', '''    s.phase = s.startupInProgress ? "CHECKPOINT_REQUESTED" : "QUIESCE";
    s.writeAdmissionStarted = false;
    s.requestReady = false;''')
    request = once(request, '    s.safeStatus.clear();s.blocking="native_admission";s.pendingDetail.clear();', '''    s.safeStatus.clear();s.blocking="native_admission";
    s.pendingDetail = s.startupInProgress ? "application_startup_initialization" : "";''')
    request = once(request, '    if (s.lifecycleTeardown || !s.ownerRegistered || !s.ownerPublished || s.ownerPublishing ||',
                   '    if (s.lifecycleTeardown || !s.startupError.empty() || !s.ownerRegistered || !s.ownerPublished || s.ownerPublishing ||')
    text = once(text, '      if (!application.IsInitialized())',
                '      if (!application.IsInitialized() && !s.startupCoreComplete)')
    activation = '''bool ActivateWriteAdmission(uint64_t infinityDiagnosticGeneration)
{
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    CheckDeadlineLocked(s);
    if (!s.active.load()) return true;
    if (s.generation != infinityDiagnosticGeneration || s.phase == "CHECKPOINT_FAILED") return false;
    if (s.startupInProgress) return true; // Accepted request; original deadline keeps running.
    if (s.writeAdmissionStarted || s.preparingWriteAdmission) return true;
    s.preparingWriteAdmission = true;
  }
  // Freeze only new invoker admission first. Already admitted observers must
  // install before mutation rejection, or a normal zlib/ctypes import can be
  // rejected by the very write hooks it is trying to install. Observed() is
  // recorded before add-on bytecode; this never waits for optional service work.
  CScriptInvocationManager::GetInstance().BeginShutdown();
  const auto observers = InfinityScriptPersistence::Snapshot();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    s.preparingWriteAdmission = false;
    CheckDeadlineLocked(s); // Initialization never resets or extends expiry.
    if (s.phase == "CHECKPOINT_FAILED") return false;
    if (observers.observed != observers.active)
    {
      s.phase = "CHECKPOINT_REQUESTED";
      s.pendingDetail = "python_persistence_observer_initialization";
      if (observers.blockingCount != 0 || observers.blockingOverflow)
      {
        FailLocked(s, "native_admission", "python_persistence_observer_initialization_failed");
        return false;
      }
      return true;
    }
    s.writeAdmissionStarted = true;
    s.phase = "QUIESCE";
    s.pendingDetail.clear();
  }
''' + admission + '''  return true;
}

ApplicationStartupScope::ApplicationStartupScope()
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  // Only the one engine entry before Create/Initialize establishes this scope.
  if (!s.active.load() && !s.startupInProgress)
  { s.startupInProgress = true; m_started = true; }
}
ApplicationStartupScope::~ApplicationStartupScope()
{
  if (!m_started || m_completed) return;
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  s.startupInProgress = false;
  s.startupError = "application_startup_initialization_failed";
  if (s.active.load()) FailLocked(s, "native_admission", s.startupError);
}
void ApplicationStartupScope::Complete()
{
  if (!m_started || m_completed) return;
  m_completed = true;
  uint64_t generation = 0;
  {
    auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
    s.startupCoreComplete = true;
    s.startupInProgress = false;
    generation = s.generation;
  }
  ActivateWriteAdmission(generation);
}

'''
    text = text[:start] + activation + request + text[end:]
    return once(text, '''void Pump(CApplication& application)
{''', '''void Pump(CApplication& application)
{
  uint64_t pendingGeneration = 0;
  {
    auto& s = Get();
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.active.load() && !s.requestReady) pendingGeneration = s.generation;
  }
  if (pendingGeneration) ActivateWriteAdmission(pendingGeneration);''')


def engine_entry(text):
    text = once(text, '#include "platform/android/activity/XBMCApp.h"',
                '#include "platform/android/activity/XBMCApp.h"\n#include "platform/android/activity/InfinityAndroidCheckpoint.h"')
    text = once(text, '  int status = -1;', '''  int status = -1;
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::ApplicationStartupScope infinityStartup;
#endif''')
    return once(text, '  status = g_application.Run();', '''#if defined(TARGET_ANDROID)
  // Core creation and initialization have succeeded; keep the original Close
  // deadline and activate its existing admission/save sequence now.
  infinityStartup.Complete();
#endif
  status = g_application.Run();''')


def application(text):
    anchor = 'void CApplication::FrameMove(bool processEvents, bool processGUI)'
    start = text.index(anchor)
    return text[:start] + once(text[start:], '''  if (InfinityAndroidCheckpoint::IsActive())
  {
    // Existing Python owners can finish''', '''  if (InfinityAndroidCheckpoint::IsWriteAdmissionActive())
  {
    // Existing Python owners can finish''')


def python_invoker(text):
    # Record native progress before acquiring the GIL or entering a Python
    # observer. No caller is delayed, cancelled, newly admitted or marked saved.
    def mark(stage, identity='0', indent='  '):
        return ('#if defined(TARGET_ANDROID)\n'+indent+
                'InfinityScriptPersistence::InitializationProgress(GetId(), "'+stage+'", '+identity+');\n'
                '#endif\n')
    start = text.index('bool CPythonInvoker::Execute(')
    end = text.index('bool CPythonInvoker::execute(', start)
    method = text[start:end]
    method = once(method, '  if (script.empty())', mark('native.execute.enter')+'  if (script.empty())')
    method = once(method, '  if (!CFileUtils::Exists(script))', mark('native.execute.file_exists')+'  if (!CFileUtils::Exists(script))')
    method = once(method, '  if (!onExecutionInitialized())', mark('native.handler.initialize')+'  if (!onExecutionInitialized())')
    method = once(method, '  return ILanguageInvoker::Execute(script, arguments);', mark('native.handler.initialized')+'  return ILanguageInvoker::Execute(script, arguments);')
    text = text[:start]+method+text[end:]
    text = once(text, '      PyThreadState* owner = CServiceBroker::GetXBPython().GetMainThreadState();',
                mark('native.interpreter.main_state', indent='      ')+'      PyThreadState* owner = CServiceBroker::GetXBPython().GetMainThreadState();')
    text = once(text, '      m_mainThreadState = PyThreadState_New(owner->interp);',
                mark('native.interpreter.thread_state', indent='      ')+'      m_mainThreadState = PyThreadState_New(owner->interp);')
    text = once(text, '      PyEval_RestoreThread(m_mainThreadState);\n      m_invokerOwnsGil = true;\n      l_threadState = Py_NewInterpreter();',
                mark('native.interpreter.acquire_gil', indent='      ')+'''      PyEval_RestoreThread(m_mainThreadState);
      m_invokerOwnsGil = true;
'''+mark('native.interpreter.create', indent='      ')+'      l_threadState = Py_NewInterpreter();')
    text = once(text, '      if (l_threadState != nullptr)\n      {\n        PyEval_ReleaseThread(l_threadState);',
                '      if (l_threadState != nullptr)\n      {\n'+mark('native.interpreter.created', 'reinterpret_cast<uintptr_t>(l_threadState->interp)', '        ')+'        PyEval_ReleaseThread(l_threadState);')
    text = once(text, '  // get the GIL\n  PyEval_RestoreThread(l_threadState);',
                '  // get the GIL\n'+mark('native.interpreter.restore_gil', 'reinterpret_cast<uintptr_t>(l_threadState->interp)')+'  PyEval_RestoreThread(l_threadState);')
    text = once(text, '    onInitialization();\n    setState(InvokerStateInitialized);',
                mark('native.kodi_module.initialize', 'reinterpret_cast<uintptr_t>(l_threadState->interp)', '    ')+'''    onInitialization();
'''+mark('native.kodi_module.initialized', 'reinterpret_cast<uintptr_t>(l_threadState->interp)', '    ')+'    setState(InvokerStateInitialized);')
    text = once(text, '  m_infinityPersistenceObserver = InfinityPythonPersistence::Start(GetId(), m_threadState->interp);',
                mark('native.observer.before_start', 'reinterpret_cast<uintptr_t>(m_threadState->interp)')+'  m_infinityPersistenceObserver = InfinityPythonPersistence::Start(GetId(), m_threadState->interp);')
    return text

def jobs(text):
    text = once(text, '  if (InfinityAndroidCheckpoint::IsActive() && !checkpointPreviouslyAccepted &&',
                '  if (InfinityAndroidCheckpoint::IsWriteAdmissionActive() && !checkpointPreviouslyAccepted &&')
    return once(text, '''      if (actualType.find("CRepositoryUpdateJob") != std::string::npos)
      {
        role = CJob::CheckpointResponsibility::Required;''', '''      if (actualType.find("CRepositoryUpdateJob") != std::string::npos)
      {
        // Repository metadata/network completion is optional. Actual native
        // SQLite transactions and file operations retain independent leases;
        // nested installation scopes remain required and admission-controlled.
        role = CJob::CheckpointResponsibility::NonPersistent;''')

def repository(text):
    text = once(text, '#include "RepositoryUpdater.h"', '''#include "RepositoryUpdater.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    # Keep the network fetch outside every save/admission lease. Only local
    # metadata operations can be admitted, and their real DB/VFS proof remains
    # mandatory. A rejected new continuation reports failure, never saved data.
    text = once(text, '''  CAddonDatabase database;
  database.Open();

  std::string oldChecksum;''', '''  CAddonDatabase database;
  std::string oldChecksum;
  {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::CheckpointWriteGuard metadataRead("optional-cache-work");
    if (!metadataRead) { MarkFinished(); return false; }
#endif
  database.Open();''')
    text = once(text, '''    oldChecksum = "";

  std::string newChecksum;''', '''    oldChecksum = "";
  }

  std::string newChecksum;''')
    text = once(text, '''  database.SetRepoUpdateData(''', '''#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard metadataWrite("optional-cache-work");
  if (!metadataWrite) { MarkFinished(); return false; }
#endif
  database.SetRepoUpdateData(''')
    # Always retire the job and signal waiters before refusing new discovery,
    # notifications, installs or timer scheduling. Existing installations keep
    # their independent required receipts and cannot be waived by this return.
    text = once(text, '''    m_doneEvent.Set();

    VECADDONS updates''', '''    m_doneEvent.Set();
    {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::CheckpointWriteGuard continuation("optional-cache-work");
    if (!continuation) return;
#endif

    VECADDONS updates''')
    text = once(text, '''    ScheduleUpdate(UpdateScheduleType::Regular);

    m_events.Publish(RepositoryUpdated{});''', '''    } // Local metadata work ends before optional timer waiting.
    ScheduleUpdate(UpdateScheduleType::Regular);
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::CheckpointWriteGuard publication("optional-cache-work");
    if (!publication) return;
#endif

    m_events.Publish(RepositoryUpdated{});''')
    text = once(text, '''  m_timer.Stop(true);

  if (CAddonSystemSettings''', '''  m_timer.Stop(true);
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard schedule("optional-cache-work");
  if (!schedule) return;
#endif

  if (CAddonSystemSettings''')
    return text

def addon(text):
    # A skin owns its values in CSkinInfo, not the placeholder CAddonSettings.
    # Keep the existing owner inventory and call its existing virtual serializer.
    # An expired ordinary owner can still have a retained dirty settings tree;
    # its original checked serialization remains the fallback.
    text = once(text, '#include <cstdint>', '#include <cstdint>\n#include <functional>')
    text = once(text, 'struct CheckpointAddonTree\n{', '''using CheckpointAddonSerializer = std::function<bool(
    const std::shared_ptr<ADDON::CAddonSettings>&, CXBMCTinyXML&)>;
struct CheckpointAddonTree
{''')
    text = once(text, '  std::uint64_t committedGeneration{0};', '''  std::uint64_t committedGeneration{0};
  CheckpointAddonSerializer serialize;''')
    text = once(text, '''void TrackCreatedAddonTree(const std::shared_ptr<ADDON::CAddonSettings>& settings,
                          const std::string& path)''', '''void TrackCreatedAddonTree(const std::shared_ptr<ADDON::CAddonSettings>& settings,
                          const std::string& path, CheckpointAddonSerializer serialize = {})''')
    text = once(text, '''  g_checkpointAddonTrees.push_back({settings, {}, settings->GetSettingsManager(), path, {}, false});''', '''  g_checkpointAddonTrees.push_back(
      {settings, {}, settings->GetSettingsManager(), path, {}, false, 0, std::move(serialize)});''')
    text = once(text, '''  if (!settings || !settings->IsLoaded())
    return;
  CXBMCTinyXML doc;''', '''  if (!settings || !settings->IsLoaded())
    return;
  CheckpointAddonSerializer serialize;
  {
    std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
    for (const auto& entry : g_checkpointAddonTrees)
      if (entry.settings.lock() == settings) { serialize = entry.serialize; break; }
  }
  CXBMCTinyXML doc;''')
    text = once(text, '''  if (!settings->Save(doc) || !CheckpointAddonBytes(doc, bytes))''', '''  if (!(serialize ? serialize(settings, doc) : settings->Save(doc)) ||
      !CheckpointAddonBytes(doc, bytes))''')
    text = once(text, '''      {settings, {}, settings->GetSettingsManager(), path, std::move(bytes), true});''', '''      {settings, {}, settings->GetSettingsManager(), path, std::move(bytes), true, 0, {}});''')
    text = once(text, '''    if (!settings->Save(doc) ||
        !CheckpointAddonBytes(doc, bytes))''', '''    if (!(entry.serialize ? entry.serialize(settings, doc) : settings->Save(doc)) ||
        !CheckpointAddonBytes(doc, bytes))''')
    text = once(text, '''    TrackCreatedAddonTree(data.m_addonSettings, data.m_userSettingsPath);''', '''    const std::weak_ptr<CAddon> checkpointOwner =
        std::dynamic_pointer_cast<CAddon>(enable_shared_from_this::shared_from_this());
    TrackCreatedAddonTree(data.m_addonSettings, data.m_userSettingsPath,
        [checkpointOwner, id](const std::shared_ptr<CAddonSettings>& settings, CXBMCTinyXML& doc) {
          const auto owner = checkpointOwner.lock();
          return owner && owner->FindInstanceSettings(id) == settings ?
              owner->SettingsToXML(doc, id) : settings->Save(doc);
        });''')
    return text

def installer(text):
    text = once(text, '#include "AddonInstaller.h"', '''#include "AddonInstaller.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    return once(text, '''  CAddonOperationReceipt completion("addon_install", m_addon->ID(), m_completionVerified);
#endif''', '''  CAddonOperationReceipt completion("addon_install", m_addon->ID(), m_completionVerified);
  // Also covers synchronous dependency installs from repository callbacks.
  // Empty existing file/database scopes prove unchanged state on rejection.
  // An already-admitted install keeps its original required durability receipt.
  InfinityAndroidCheckpoint::CheckpointWriteGuard admission("jobs");
  if (!admission) return false;
#endif''')

def manager(text):
    text = once(text, '#include "platform/android/activity/InfinityScriptPersistence.h"',
                '#include "platform/android/activity/InfinityScriptPersistence.h"\n#include "platform/android/activity/InfinityProtectedWrites.h"')
    import re
    pattern = r'(?m)^( +)if \(checkpointContract.empty\(\)\)\n +InfinityScriptPersistence::Admit\(invokerThread->GetId\(\),\n +\(addon \? addon->ID\(\) : "unidentified"\) \+ ":" \+ URIUtils::GetFileName\(script\)\);'
    def replace(match):
        pad = match.group(1)
        return pad + '''InfinityScriptPersistence::Admit(invokerThread->GetId(),
''' + pad + '''  (addon ? addon->ID() : "unidentified") + ":" + URIUtils::GetFileName(script));
''' + pad + '''if (checkpointContract == "command_center" || checkpointContract == "compat")
''' + pad + '''  InfinityScriptPersistence::RegisterParticipant(invokerThread->GetId());'''
    text, count = re.subn(pattern, replace, text)
    assert count == 2, count
    return text

def sqlite(text):
    text = once(text, '#include "InfinityDatabaseBarrier.h"',
                '#include "InfinityDatabaseBarrier.h"\n#include "InfinitySQLiteVFS.h"')
    text = once(text, '    int errorCode = sqlite3_open_v2(', '''    if (!InfinitySQLiteVFS::Install())
      throw DbErrors("Protected SQLite VFS installation failed");
    int errorCode = sqlite3_open_v2(''')
    text = once(text, '  rc = sqlite3_open(backup_path.c_str(), &pFile);', '''  if (!InfinitySQLiteVFS::Install()) return DB_UNEXPECTED_RESULT;
  rc = sqlite3_open(backup_path.c_str(), &pFile);''')
    return text

def posix(text):
    text = once(text, '#include "PosixFile.h"', '''#include "PosixFile.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityProtectedWrites.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    def guard(paths, operation, failure, descriptor='-1'):
        return '''#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::ProtectedOperation infinityWrite(
      InfinityScriptPersistence::CurrentWriteOwner(), {''' + paths + '''}, "''' + operation + '''",
      InfinityAndroidCheckpoint::IsPersistingOnThisThread(), false, ''' + descriptor + ''');
  if (!infinityWrite) return ''' + failure + ''';
#endif
'''
    text = once(text, '  m_fd = open(filename.c_str(), O_RDWR',
                guard('filename', 'posix.open_write', 'false') + '  m_fd = open(filename.c_str(), O_RDWR')
    for method, signature in [('Write', 'ssize_t CPosixFile::Write(const void* lpBuf, size_t uiBufSize)'),
                              ('Truncate', 'int CPosixFile::Truncate(int64_t size)')]:
        opening = signature+'\n{\n  if (m_fd < 0)\n    return -1;\n'
        text = once(text, opening, opening+'\n'+guard(
            'InfinityScriptPersistence::DescriptorPath(m_fd)', 'posix.'+method.lower(), '-1', 'm_fd'))
    text = once(text, '  if (unlink(filename.c_str()) == 0)', guard('filename', 'posix.unlink', 'false')+'  if (unlink(filename.c_str()) == 0)')
    text = once(text, '  if (rename(name.c_str(), newName.c_str()) == 0)\n    return true;', guard('name, newName', 'posix.rename', 'false')+'''  if (rename(name.c_str(), newName.c_str()) == 0)
  {
#if defined(TARGET_ANDROID)
    InfinityScriptPersistence::RememberAlias(name, newName);
#endif
    return true;
  }''')
    return text

def directory(text):
    text = once(text, '#include "PosixDirectory.h"', '''#include "PosixDirectory.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityProtectedWrites.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    def guard(path, operation):
        return '''#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::ProtectedOperation infinityDirectoryWrite(
      InfinityScriptPersistence::CurrentWriteOwner(), {''' + path + '''}, "''' + operation + '''",
      InfinityAndroidCheckpoint::IsPersistingOnThisThread());
  if (!infinityDirectoryWrite) return false;
#endif
'''
    text = once(text, '  if (mkdir(path.c_str(), 0755) != 0)', '''#if defined(TARGET_ANDROID)
  // CreateDirectoryEx visits existing ancestors while building an add-on
  // profile. Query an existing directory without attempting a mutation or
  // inventing a new durability obligation for that ancestor. Preserve this
  // overload's false/EEXIST result; Create(CURL) still confirms Exists(url).
  // Missing/unknown destinations keep the original checked mkdir below.
  // An earlier real creation remains independently recorded in the ledger.
  struct stat infinityExistingDirectory{};
  if (::stat(path.c_str(), &infinityExistingDirectory) == 0 &&
      S_ISDIR(infinityExistingDirectory.st_mode))
  {
    errno = EEXIST;
    return false;
  }
#endif
''' + guard('path', 'posix.mkdir')+'  if (mkdir(path.c_str(), 0755) != 0)')
    text = once(text, '  if (rmdir(url.Get().c_str()) == 0)', guard('url.Get()', 'posix.rmdir')+'  if (rmdir(url.Get().c_str()) == 0)')
    start = text.index('bool CPosixDirectory::RemoveRecursive(')
    text = text[:start] + once(text[start:], '  DIR *dir = opendir(root.c_str());', guard('root', 'posix.remove_recursive')+'  DIR *dir = opendir(root.c_str());')
    return text

def apply(root, locked_manifest):
    root = Path(root)
    expected = json.loads(Path(locked_manifest).read_text())['after']
    replacements = {}
    for name, transform in [(CHECKPOINT, checkpoint), (MANAGER, manager), (SQLITE, sqlite), (POSIX, posix), (DIRECTORY, directory), (JOBS, jobs), (INSTALLER, installer), (ADDON, addon), (REPOSITORY, repository), (ENGINE_ENTRY, engine_entry), (APPLICATION, application), (PYTHON_INVOKER, python_invoker)]:
        old = (root/name).read_bytes()
        actual = hashlib.sha256(old).hexdigest()
        assert actual == PINS[name] == expected[name], (name, actual)
        replacements[name] = transform(old.decode()).encode()
    for file in (HERE/'runtime/xbmc').rglob('*'):
        if not file.is_file(): continue
        name = str(file.relative_to(HERE/'runtime'))
        target = root/name
        if target.exists():
            assert hashlib.sha256(target.read_bytes()).hexdigest() == expected[name], name
        else:
            assert name not in expected, name
        replacements[name] = file.read_bytes()
    before = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
              for name in replacements if (root/name).exists()}
    # Resolve every preimage and transform before the first mutation.
    for name, data in replacements.items():
        target = root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    return {'before': before, 'after': {n: hashlib.sha256(b).hexdigest() for n,b in replacements.items()},
            'changed': sorted(replacements), 'diagnostic_owner_count': 17, 'essential_owner_count': 16,
            'locked': False, 'apk_deliverable': False}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--locked-manifest', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.write_text(json.dumps(apply(a.source, a.locked_manifest), indent=2)+'\n')
