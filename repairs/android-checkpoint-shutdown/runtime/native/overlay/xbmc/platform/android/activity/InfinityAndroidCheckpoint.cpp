#include "InfinityAndroidCheckpoint.h"

#include "InfinityCheckpointXml.h"
#include "InfinityPlaybackCheckpoint.h"
#include "ServiceBroker.h"
#include "addons/Skin.h"
#include "application/Application.h"
#include "application/ApplicationPlayer.h"
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include "favourites/FavouritesService.h"
#include "filesystem/Directory.h"
#include "filesystem/SpecialProtocol.h"
#include "interfaces/AnnouncementManager.h"
#include "interfaces/generic/ScriptInvocationManager.h"
#include "peripherals/Peripherals.h"
#include "profiles/ProfileManager.h"
#include "pvr/PVRManager.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include "utils/JSONVariantParser.h"
#include "utils/JSONVariantWriter.h"
#include "utils/JobManager.h"
#include "utils/Variant.h"

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <ctime>
#include <fcntl.h>
#include <map>
#include <mutex>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace InfinityAndroidCheckpoint
{
namespace
{
using Clock = std::chrono::steady_clock;
constexpr auto DEADLINE = std::chrono::seconds(25);
constexpr const char* REQUIRED[] = {"native_admission", "python_services", "background_jobs",
  "playback", "command_center", "kodi_settings", "profiles", "skin_settings", "addon_settings",
  "favourites", "peripherals", "xml_files", "native_databases", "pvr"};

struct Owner
{
  uint64_t generation{0};
  uint64_t durableGeneration{0};
  bool dirty{true};
  bool complete{false};
  bool committed{false};
  std::string error;
  int64_t elapsed{0};
  int64_t started{0};
};
struct State
{
  std::mutex mutex;
  std::atomic<bool> active{false};
  bool sealed{false};
  bool authorized{false};
  bool requestReady{false};
  bool lifecycleTeardown{false};
  std::string session;
  std::string owner;
  int pid{0};
  uint64_t generation{0};
  uint64_t errors{0};
  size_t activeWrites{0};
  std::string phase{"IDLE"};
  std::string error;
  std::string blocking{"native_admission"};
  std::string pendingDetail;
  int64_t safeUtcMs{0};
  std::map<std::string, Owner> owners;
  Clock::time_point started;
  Clock::time_point expires;
  unsigned int stage{0}; // Written only by the application-thread pump.
  std::string directory;
  std::vector<std::string> unresolvedForeignOwners;
  std::string safeStatus; // Immutable full receipt while SAFE remains valid.
};
State& Get()
{
  static State* state = new State;
  return *state;
}
thread_local unsigned int permissionDepth = 0;
thread_local unsigned int acceptedPlaybackDepth = 0;

bool Token(const std::string& token)
{
  return token.size() >= 16 && token.size() <= 128 &&
    std::all_of(token.begin(), token.end(), [](unsigned char c) {
      return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
             (c >= '0' && c <= '9') || c == '_' || c == '-';
    });
}
bool Matches(const State& s, const std::string& session, const std::string& owner, int pid)
{
  return s.active.load() && s.session == session && s.owner == owner && s.pid == pid &&
         pid == static_cast<int>(::getpid());
}
int64_t Elapsed(const State& s)
{
  return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - s.started).count();
}
void FailLocked(State& s, const std::string& owner, const std::string& detail)
{
  ++s.errors;
  s.phase = "CHECKPOINT_FAILED";
  s.sealed = true;
  s.error = (owner + ": " + detail).substr(0, 512);
  s.owners[owner].error = detail.substr(0, 384);
  s.owners[owner].complete = false;
  s.safeStatus.clear();
}
void CheckDeadlineLocked(State& s)
{
  if (s.active.load() && s.phase != "CHECKPOINT_FAILED" && s.phase != "ENGINE_TERMINATING" &&
      Clock::now() >= s.expires)
    FailLocked(s, s.blocking.empty() ? "native_admission" : s.blocking,
               "checkpoint_deadline_exceeded; owner proof incomplete");
}
void Operation(const char* owner)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  s.blocking = owner;
  auto& tracked = s.owners[owner];
  if (tracked.started == 0)
    tracked.started = Elapsed(s);
}
void Complete(const char* name, bool committed)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (s.phase == "CHECKPOINT_FAILED")
    return;
  auto& owner = s.owners[name];
  owner.complete = true;
  owner.dirty = false;
  owner.committed = committed;
  owner.durableGeneration = owner.generation;
  owner.elapsed = Elapsed(s);
}
std::string EncodeStatusLocked(const State& s)
{
  CVariant result(CVariant::VariantTypeObject);
  result["schema"] = 1;
  result["session"] = s.session;
  result["owner"] = s.owner;
  result["pid"] = s.pid;
  result["generation"] = s.generation;
  result["phase"] = s.phase;
  result["admission_sealed"] = s.sealed;
  result["error"] = s.error;
  result["blocking_operation"] = s.blocking;
  result["pending_detail"] = s.pendingDetail;
  result["safe_to_terminate_utc_ms"] = s.safeUtcMs;
  result["elapsed_ms"] = Elapsed(s);
  result["active_native_writers"] = static_cast<uint64_t>(s.activeWrites);
  result["required_owners"] = CVariant(CVariant::VariantTypeArray);
  result["owners"] = CVariant(CVariant::VariantTypeArray);
  for (const char* name : REQUIRED)
  {
    result["required_owners"].push_back(name);
    const auto found = s.owners.find(name);
    const Owner owner = found == s.owners.end() ? Owner{} : found->second;
    CVariant item(CVariant::VariantTypeObject);
    item["owner"] = name;
    item["checkpoint_generation"] = s.generation;
    item["generation"] = owner.generation;
    item["durable_generation"] = owner.durableGeneration;
    item["dirty"] = owner.dirty;
    item["dirty_remaining"] = owner.dirty;
    item["dirty_before"] = owner.committed;
    item["required_writes_finished"] = owner.complete;
    item["result"] = !owner.error.empty() ? "FAILED" : !owner.complete ? "PENDING" :
                      owner.committed ? "COMMITTED" : "ALREADY_DURABLE";
    item["elapsed_ms"] = owner.elapsed;
    item["start_elapsed_ms"] = owner.started;
    item["end_elapsed_ms"] = owner.complete ? owner.elapsed : 0;
    item["duration_ms"] = owner.complete ? owner.elapsed - owner.started : Elapsed(s) - owner.started;
    item["error"] = owner.error;
    result["owners"].push_back(item);
  }
  std::string encoded;
  if (!CJSONVariantWriter::Write(result, encoded, true))
    return "{\"schema\":1,\"phase\":\"CHECKPOINT_FAILED\",\"error\":\"status_encoding_failed\"}";
  return encoded;
}

bool ReadJson(const std::string& path, CVariant& value)
{
  std::string local;
  if (!LocalCheckpointPath(path, local))
    return false;
  const int fd = ::open(local.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0)
    return false;
  struct stat info{};
  bool ok = ::fstat(fd, &info) == 0 && S_ISREG(info.st_mode) &&
            info.st_size > 0 && info.st_size <= 262144;
  std::string bytes;
  if (ok)
  {
    bytes.resize(static_cast<size_t>(info.st_size));
    size_t offset = 0;
    while (offset < bytes.size())
    {
      const ssize_t got = ::read(fd, &bytes[offset], bytes.size() - offset);
      if (got < 0 && errno == EINTR)
        continue;
      if (got <= 0) { ok = false; break; }
      offset += static_cast<size_t>(got);
    }
  }
  if (::close(fd) != 0)
    ok = false;
  return ok && CJSONVariantParser::Parse(bytes, value) && value.isObject();
}
bool WriteJson(const std::string& path, const CVariant& value)
{
  std::string bytes;
  return CJSONVariantWriter::Write(value, bytes, true) && SaveCheckpointXml(path, bytes);
}
CVariant Identity(const State& s)
{
  CVariant result(CVariant::VariantTypeObject);
  result["schema"] = 1;
  result["pid"] = s.pid;
  result["owner"] = s.owner;
  result["session"] = s.session;
  return result;
}
bool SameIdentity(const CVariant& value, const State& s, bool session)
{
  return value["schema"].isInteger() && value["schema"].asInteger() == 1 &&
    value["pid"].isInteger() && value["pid"].asInteger() == s.pid &&
    value["owner"].isString() && value["owner"].asString() == s.owner &&
    (!session || (value["session"].isString() && value["session"].asString() == s.session));
}
bool ParticipantResponse(State& s, const char* expected)
{
  CVariant response;
  if (!ReadJson(s.directory + "/response.json", response) || !SameIdentity(response, s, true))
    return false;
  if (response["status"].asString() == "CHECKPOINT_FAILED")
  {
    std::string detail = "participant_reported_failure";
    if (response["error"].isString())
      detail += ":" + response["error"].asString().substr(0, 160);
    const auto& operations = response["operations"];
    for (auto it = operations.begin_array(); it != operations.end_array(); ++it)
      if ((*it)["ok"].isBoolean() && !(*it)["ok"].asBoolean())
        detail += ";" + (*it)["name"].asString().substr(0, 80);
    RecordFailure("command_center", detail.substr(0, 384).c_str());
    return false;
  }
  return response["participant"].isString() && response["participant"].asString() == "command-center-json" &&
    response["status"].isString() && response["status"].asString() == expected &&
    response["global_safe_to_terminate"].isBoolean() &&
    !response["global_safe_to_terminate"].asBoolean();
}
bool BeginEngineHandshake(State& s)
{
  s.directory = CSpecialProtocol::TranslatePath(
      "special://profile/addon_data/script.infinity.commandcenter/.android-checkpoint");
  if (!XFILE::CDirectory::Create(s.directory) || !CheckpointCreatedDirectory(s.directory))
    return false;
  CVariant previous;
  const bool hadPrevious = ReadJson(s.directory + "/engine.json", previous);
  CVariant engine = Identity(s);
  engine["native_api"] = 1;
  if (hadPrevious && previous["owner"].asString() != s.owner)
  {
    const auto oldPid = previous["pid"].asInteger();
    const std::string oldOwner = previous["owner"].asString();
    if (oldPid <= 0 || oldPid == s.pid || oldPid > 2147483647 || !Token(oldOwner) ||
        ::kill(static_cast<pid_t>(oldPid), 0) == 0 || errno != ESRCH)
      return false; // Never infer previous owner death from a missing receipt alone.
    engine["previous_owner"]["pid"] = oldPid;
    engine["previous_owner"]["token"] = oldOwner;
  }
  return WriteJson(s.directory + "/engine.json", engine);
}
} // namespace

bool IsActive() { return Get().active.load(); }
bool IsAcceptedPlaybackWorkOnThisThread() { return acceptedPlaybackDepth != 0; }
bool IsPersistingOnThisThread()
{
  if (permissionDepth == 0)
    return false;
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  return s.active.load() && s.phase != "SAFE_TO_TERMINATE" &&
         s.phase != "ENGINE_TERMINATING" && s.phase != "CHECKPOINT_FAILED";
}
bool AllowNativeWrite(const char*)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  return !s.active.load() || (!s.sealed && s.phase != "CHECKPOINT_FAILED") ||
    (permissionDepth != 0 && s.phase == "PERSISTING");
}
CheckpointWriteGuard::CheckpointWriteGuard(const char* name)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  const std::string owner = name ? name : "unknown";
  const bool newJob = owner == "jobs" || owner == "playback-command";
  m_admitted = !s.active.load() ||
    (!newJob && !s.sealed && s.phase != "CHECKPOINT_FAILED") ||
    (owner == "jobs" && acceptedPlaybackDepth != 0 && !s.sealed && s.phase == "QUIESCE") ||
    (permissionDepth != 0 && s.phase == "PERSISTING");
  if (m_admitted)
  {
    ++s.activeWrites;
    auto& tracked = s.owners[owner];
    ++tracked.generation;
    tracked.dirty = true;
    tracked.complete = false;
  }
}
CheckpointWriteGuard::~CheckpointWriteGuard()
{
  if (m_admitted)
  {
    auto& s = Get();
    std::lock_guard<std::mutex> lock(s.mutex);
    --s.activeWrites;
  }
}
CoordinatorWriteScope::CoordinatorWriteScope() { ++permissionDepth; }
CoordinatorWriteScope::~CoordinatorWriteScope() { --permissionDepth; }
AcceptedPlaybackWorkScope::AcceptedPlaybackWorkScope()
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (!s.sealed && (!s.active.load() || s.phase == "QUIESCE"))
  {
    ++acceptedPlaybackDepth;
    ++s.activeWrites;
    m_counted = true;
  }
  else if (s.active.load())
    FailLocked(s, "playback", "playback_callback_after_persistence_seal");
}
AcceptedPlaybackWorkScope::~AcceptedPlaybackWorkScope()
{
  if (m_counted)
  {
    --acceptedPlaybackDepth;
    auto& s = Get();
    std::lock_guard<std::mutex> lock(s.mutex);
    --s.activeWrites;
  }
}
void RecordPersistenceFailure(const char* owner, const char* detail)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (s.active.load())
    FailLocked(s, owner ? owner : "unknown", detail ? detail : "unspecified_failure");
}
uint64_t ErrorGeneration()
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  return s.errors;
}
bool HasFailureSince(uint64_t generation) { return ErrorGeneration() != generation; }
void NotifyLegacyTeardown(const char* operation)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  s.lifecycleTeardown = true;
  if (s.active.load())
    FailLocked(s, "native_admission", operation ? operation : "independent_legacy_teardown_started");
}

bool Request(const std::string& session, const std::string& owner, int pid)
{
  if (!Token(session) || !Token(owner) || pid != static_cast<int>(::getpid()))
    return false;
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.lifecycleTeardown)
      return false;
    if (s.active.load())
      return Matches(s, session, owner, pid) && s.phase != "CHECKPOINT_FAILED";
    s.session = session;
    s.owner = owner;
    s.pid = pid;
    ++s.generation;
    s.started = Clock::now();
    s.expires = s.started + DEADLINE;
    s.phase = "QUIESCE";
    s.stage = 0;
    for (const char* name : REQUIRED)
    {
      auto& participant = s.owners[name];
      participant.complete = false;
      participant.dirty = true;
      participant.error.clear();
    }
    s.active.store(true);
  }
  // Close script admission under its own lock, then retain unresolved owners.
  // Script completion is not a durable-state acknowledgment (an exception can
  // mark an invoker done while interpreter-owned file buffers still exist).
  CScriptInvocationManager::GetInstance().BeginShutdown();
  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    s.unresolvedForeignOwners = unresolved;
    s.requestReady = true;
  }
  return true;
}
std::string Status(const std::string& session, const std::string& owner, int pid)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (!Matches(s, session, owner, pid))
    return "{\"schema\":1,\"phase\":\"CHECKPOINT_FAILED\",\"error\":\"stale_or_foreign_identity\"}";
  CheckDeadlineLocked(s);
  return s.phase == "SAFE_TO_TERMINATE" ? s.safeStatus : EncodeStatusLocked(s);
}
bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)
{
  auto& s = Get();
  const auto database = InfinityDatabaseBarrier::GetSnapshot();
  std::lock_guard<std::mutex> lock(s.mutex);
  CheckDeadlineLocked(s);
  if (!Matches(s, session, owner, pid) || s.lifecycleTeardown ||
      s.phase != "SAFE_TO_TERMINATE" || !s.sealed ||
      s.authorized || s.activeWrites != 0 || !database.sealed || !database.Ready() ||
      database.session != s.generation)
    return false;
  for (const char* name : REQUIRED)
  {
    const auto found = s.owners.find(name);
    if (found == s.owners.end() || !found->second.complete || found->second.dirty ||
        found->second.generation != found->second.durableGeneration || !found->second.error.empty())
      return false;
  }
  s.authorized = true;
  s.phase = "ENGINE_TERMINATING";
  return true;
}

void Pump(CApplication& application)
{
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    CheckDeadlineLocked(s);
    if (!s.active.load() || !s.requestReady || s.phase == "CHECKPOINT_FAILED" ||
        s.phase == "SAFE_TO_TERMINATE" || s.phase == "ENGINE_TERMINATING")
      return;
  }
  CoordinatorWriteScope permission;
  try
  {
    if (s.stage == 0)
    {
      Operation("native_admission");
      if (!application.IsInitialized())
      { RecordFailure("native_admission", "application_not_initialized"); return; }
      CScriptInvocationManager::GetInstance().BeginShutdown(); // Admission only; no Stop/join.
      CServiceBroker::GetJobManager()->UnPauseJobs(); // Drain previously accepted low-priority work.
      if (!CServiceBroker::GetPVRManager().IsStopped())
      { RecordFailure("pvr", "active_pvr_owner_has_no_persistence_participant"); return; }
      Complete("pvr", false);
      if (!BeginEngineHandshake(s))
      { RecordFailure("command_center", "engine_owner_handshake_write_or_previous_owner_failed"); return; }
      s.stage = 1;
    }
    if (s.stage == 1)
    {
      Operation("command_center");
      CVariant active;
      if (!ReadJson(s.directory + "/active.json", active) || !SameIdentity(active, s, false) ||
          !active["status"].isString() || active["status"].asString() != "ACTIVE" ||
          !active["participant_api"].isInteger() || active["participant_api"].asInteger() != 1 ||
          !active["addon_version"].isString() || active["addon_version"].asString() != "0.3.5.19")
        return;
      if (CScriptInvocationManager::GetInstance().AndroidCheckpointResidentCount() != 1)
      { RecordFailure("command_center", "exactly_one_canonical_resident_required"); return; }
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        if (s.activeWrites != 0)
          return; // An admitted pre-close seek/command must enqueue before freeze.
      }
      Operation("playback");
      std::string failure;
      const auto playback = InfinityPlaybackCheckpoint::Poll(
          *application.GetComponent<CApplicationPlayer>(), application, s.session, failure);
      if (playback == InfinityPlaybackCheckpoint::PollResult::Failed)
      { RecordFailure("playback", failure.c_str()); return; }
      if (playback != InfinityPlaybackCheckpoint::PollResult::Complete)
        return;
      Complete("playback", true);
      Operation("command_center");
      CVariant request = Identity(s);
      request["phase"] = "PREPARE";
      if (!WriteJson(s.directory + "/request.json", request))
      { RecordFailure("command_center", "prepare_request_write_failed"); return; }
      s.stage = 2;
    }
    if (s.stage == 2)
    {
      if (!ParticipantResponse(s, "PLAYBACK_CHECKPOINTED"))
        return;
      s.stage = 3;
    }
    if (s.stage == 3)
    {
      const CVariant marker = Identity(s);
      CServiceBroker::GetAnnouncementManager()->Announce(
          ANNOUNCEMENT::Other, "Infinity", "InfinityCheckpointDrain", marker);
      CVariant request = Identity(s);
      request["phase"] = "FINALIZE";
      request["player_freeze_complete"] = true;
      if (!WriteJson(s.directory + "/request.json", request))
      { RecordFailure("command_center", "finalize_request_write_failed"); return; }
      s.stage = 4;
    }
    if (s.stage == 4)
    {
      Operation("command_center");
      if (!ParticipantResponse(s, "PARTICIPANT_COMPLETE"))
        return;
      Complete("command_center", true);
      Operation("python_services");
      if (!s.unresolvedForeignOwners.empty())
      {
        std::string detail = "unproven_raw_file_or_sqlite_writer_contracts";
        for (const auto& writer : s.unresolvedForeignOwners)
          detail += ";" + writer;
        RecordFailure("python_services", detail.substr(0, 384).c_str());
        return;
      }
      Complete("python_services", false);
      Operation("background_jobs");
      if (CServiceBroker::GetJobManager()->AndroidCheckpointOutstandingJobs() != 0 ||
          CJobQueue::AndroidCheckpointOutstandingQueues() != 0)
        return;
      Complete("background_jobs", false);
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        if (s.activeWrites != 0 || s.phase == "CHECKPOINT_FAILED")
          return;
        s.sealed = true; // No ordinary mutation can enter between drain and save.
        s.phase = "PERSISTING";
      }
      if (!InfinityDatabaseBarrier::Begin(s.generation))
      { RecordFailure("native_databases", "database_barrier_begin_failed"); return; }
      Complete("native_admission", false);
      s.stage = 5;
    }
    if (s.stage == 5)
    {
      Operation("native_databases");
      const auto pendingDatabase = InfinityDatabaseBarrier::GetSnapshot();
      if (pendingDatabase.failures || pendingDatabase.rejectedWrites || pendingDatabase.unsupportedOwners)
      { RecordFailure("native_databases", "failed_or_unsupported_database_owner"); return; }
      if (!pendingDatabase.Ready())
        return;
      InfinityDatabaseBarrier::CheckpointWriteScope databasePermission(s.generation);
      if (!databasePermission.IsValid())
      { RecordFailure("native_databases", "checkpoint_database_scope_rejected"); return; }
      const uint64_t errors = ErrorGeneration();
      Operation("skin_settings");
      if (!CheckpointSkinSettings())
      { RecordFailure("skin_settings", "skin_settings_save_failed"); return; }
      if (HasFailureSince(errors))
        return;
      Complete("skin_settings", true);
      Operation("addon_settings");
      if (!CheckpointLoadedAddonSettings())
      { RecordFailure("addon_settings", "loaded_addon_settings_save_failed"); return; }
      Complete("addon_settings", true);
      Operation("favourites");
      if (!CServiceBroker::GetFavouritesService().CheckpointForAndroidExit())
      { RecordFailure("favourites", "favourites_save_failed"); return; }
      Complete("favourites", true);
      Operation("peripherals");
      if (!CServiceBroker::GetPeripherals().CheckpointForAndroidExit())
      { RecordFailure("peripherals", "peripheral_settings_save_failed"); return; }
      Complete("peripherals", true);
      // Save base settings after add-on/skin callbacks, so any accepted setting
      // effects from their serialization are included in the final snapshot.
      Operation("kodi_settings");
      if (!CServiceBroker::GetSettingsComponent()->GetSettings()->Save())
      { RecordFailure("kodi_settings", "settings_save_failed"); return; }
      Complete("kodi_settings", true);
      Operation("profiles");
      if (!CServiceBroker::GetSettingsComponent()->GetProfileManager()->Save())
      { RecordFailure("profiles", "profiles_save_failed"); return; }
      Complete("profiles", true);
      if (HasFailureSince(errors))
        return;
      Complete("xml_files", true);
      s.stage = 6;
    }
    if (s.stage == 6)
    {
      Operation("native_databases");
      if (!InfinityDatabaseBarrier::Seal(s.generation))
      { RecordFailure("native_databases", "database_barrier_not_durable_or_drained"); return; }
      Complete("native_databases", true);
      std::lock_guard<std::mutex> lock(s.mutex);
      CheckDeadlineLocked(s);
      if (s.phase == "CHECKPOINT_FAILED" || s.activeWrites != 0)
        return;
      for (const char* name : REQUIRED)
      {
        const auto& owner = s.owners.at(name);
        if (!owner.complete || owner.dirty || owner.generation != owner.durableGeneration || !owner.error.empty())
        { FailLocked(s, name, "required_owner_not_durable"); return; }
      }
      s.phase = "SAFE_TO_TERMINATE";
      s.pendingDetail.clear();
      s.blocking.clear();
      s.safeUtcMs = std::chrono::duration_cast<std::chrono::milliseconds>(
          std::chrono::system_clock::now().time_since_epoch()).count();
      s.safeStatus = EncodeStatusLocked(s);
    }
  }
  catch (const std::exception&)
  {
    RecordFailure("native_admission", "checkpoint_exception");
  }
  catch (...)
  {
    RecordFailure("native_admission", "checkpoint_unknown_exception");
  }
}
} // namespace InfinityAndroidCheckpoint
