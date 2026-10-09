#include "InfinityAndroidCheckpoint.h"
#include "InfinityScriptPersistence.h"

#include "InfinityCheckpointXml.h"
#include "InfinityPlaybackCheckpoint.h"
#include "JNIMainActivity.h"
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
#include "pvr/addons/PVRClients.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include "utils/JSONVariantParser.h"
#include "utils/JSONVariantWriter.h"
#include "utils/JobManager.h"
#include "utils/Variant.h"

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <climits>
#include <chrono>
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
  "playback", "command_center", "compat", "kodi_settings", "profiles", "skin_settings", "addon_settings",
  "favourites", "peripherals", "audio_policy", "deferred_dialog_state", "xml_files", "native_databases", "pvr"};

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
struct Blocker
{
  std::string owner;
  std::string detail;
  unsigned count{1};
  bool fatal{false};
};
struct State
{
  std::mutex mutex;
  std::atomic<bool> active{false};
  bool sealed{false};
  bool authorized{false};
  bool requestReady{false};
  bool lifecycleTeardown{false};
  bool ownerRegistered{false};
  bool ownerPublished{false};
  bool ownerPublishing{false};
  std::string filesDirectory;
  std::string startupError;
  std::string session;
  std::string owner;
  int pid{0};
  uint64_t generation{0};
  uint64_t errors{0};
  size_t activeWrites{0};
  std::string phase{"IDLE"};
  std::string error;
  std::vector<Blocker> blockers;
  bool blockerOverflow{false};
  bool inventoryComplete{false};
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
  JobCheckpoint::Snapshot jobs;
};
State& Get()
{
  static State* state = new State;
  return *state;
}
thread_local unsigned int permissionDepth = 0;
thread_local unsigned int acceptedPlaybackDepth = 0;
thread_local unsigned int startupWriteDepth = 0;

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
void BlockLocked(State& s, const std::string& ownerName, const std::string& detail, bool fatal=false)
{
  ++s.errors;
  const auto safeOwner=ownerName.substr(0,128),safeDetail=detail.substr(0,384);
  bool found=false;
  for(auto& blocker:s.blockers)
    if(blocker.owner==safeOwner && blocker.detail==safeDetail && blocker.fatal==fatal) {
      if(blocker.count<UINT_MAX)++blocker.count;
      found=true;break;
    }
  if(!found) {
    if(s.blockers.size()<128)s.blockers.push_back({safeOwner,safeDetail,1,fatal});
    else s.blockerOverflow=true;
  }
  if(s.error.empty())s.error=(safeOwner+": "+safeDetail).substr(0,512);
  auto& owner=s.owners[safeOwner];
  if(owner.error.empty())owner.error=safeDetail;
  owner.complete=false;owner.dirty=true;
  s.safeStatus.clear();
  if(fatal) {
    s.phase="CHECKPOINT_FAILED";
    s.sealed=true;
    s.inventoryComplete=true;
  }
}
void FailLocked(State& s, const std::string& owner, const std::string& detail)
{
  BlockLocked(s,owner,detail,true);
}
void FinalizeInventoryFailureLocked(State& s)
{
  s.phase="CHECKPOINT_FAILED";
  s.sealed=true;
  s.inventoryComplete=true;
  s.safeStatus.clear();
}
void CheckDeadlineLocked(State& s)
{
  if (!s.active.load() || s.phase=="CHECKPOINT_FAILED" || s.phase=="ENGINE_TERMINATING" ||
      Clock::now()<s.expires)
    return;

  // SAFE is still a time-bounded authorization capability. Expiry must revoke
  // it even when every save owner was durable, exactly as the pre-inventory
  // checkpoint did.
  if (s.phase=="SAFE_TO_TERMINATE")
  {
    FailLocked(s,"native_admission","checkpoint_deadline_exceeded; authorization_window_expired");
    return;
  }

  for(const char* name:REQUIRED) {
    auto& owner=s.owners[name];
    if(!owner.complete && owner.error.empty())
      BlockLocked(s,name,"checkpoint_deadline_exceeded; owner proof incomplete");
  }
  const auto scripts=InfinityScriptPersistence::Snapshot();
  for(const auto& name:scripts.pending)
    BlockLocked(s,"python_services","pending_writer:"+name);
  if(s.blockers.empty())
    BlockLocked(s,s.blocking.empty()?"native_admission":s.blocking,
                "checkpoint_deadline_exceeded; owner proof incomplete");
  FinalizeInventoryFailureLocked(s);
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
  if(!owner.error.empty())return;
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
  result["blocker_inventory_contract"] = "full_blocker_inventory_v1";
  result["session"] = s.session;
  result["owner"] = s.owner;
  result["pid"] = s.pid;
  result["generation"] = s.generation;
  result["phase"] = s.phase;
  result["admission_sealed"] = s.sealed;
  result["inventory_complete"] = s.inventoryComplete;
  result["error"] = s.error;
  result["blocker_count"] = static_cast<uint64_t>(s.blockers.size());
  result["blocker_overflow"] = s.blockerOverflow;
  result["blockers"] = CVariant(CVariant::VariantTypeArray);
  for(const auto& blocker:s.blockers) {
    CVariant item(CVariant::VariantTypeObject);
    item["owner"]=blocker.owner;item["detail"]=blocker.detail;
    item["count"]=static_cast<uint64_t>(blocker.count);item["fatal"]=blocker.fatal;
    result["blockers"].push_back(item);
  }
  result["blocking_operation"] = s.blocking;
  result["pending_detail"] = s.pendingDetail;
  result["safe_to_terminate_utc_ms"] = s.safeUtcMs;
  result["elapsed_ms"] = Elapsed(s);
  result["active_native_writers"] = static_cast<uint64_t>(s.activeWrites);
  const auto scripts = InfinityScriptPersistence::Snapshot();
  CVariant scriptEvidence(CVariant::VariantTypeObject);
  scriptEvidence["active_writers"] = static_cast<uint64_t>(scripts.active);
  scriptEvidence["observed_writers"] = static_cast<uint64_t>(scripts.observed);
  scriptEvidence["retired_writers"] = static_cast<uint64_t>(scripts.retired);
  scriptEvidence["failed_settled_writers"] = static_cast<uint64_t>(scripts.failedSettled);
  scriptEvidence["advisory_retired_writers"] = static_cast<uint64_t>(scripts.advisoryRetired);
  scriptEvidence["blocking_count"] = static_cast<uint64_t>(scripts.blockingCount);
  scriptEvidence["advisory_count"] = static_cast<uint64_t>(scripts.advisoryCount);
  scriptEvidence["tracked_paths"] = static_cast<uint64_t>(scripts.paths);
  scriptEvidence["sync_started"] = scripts.syncStarted;
  scriptEvidence["sync_finished"] = scripts.syncFinished;
  scriptEvidence["durable"] = scripts.durable;
  scriptEvidence["error"] = scripts.failure;
  scriptEvidence["failure_writer_id"] = scripts.failureWriterId;
  scriptEvidence["failure_writer"] = scripts.failureWriter;
  scriptEvidence["failure_detail"] = scripts.failureDetail;
  scriptEvidence["blocker_overflow"] = scripts.blockerOverflow;
  scriptEvidence["blocking_overflow"] = scripts.blockingOverflow;
  scriptEvidence["blockers"] = CVariant(CVariant::VariantTypeArray);
  for(const auto& blocker:scripts.blockers) {
    CVariant value(CVariant::VariantTypeObject);
    value["writer_id"]=blocker.writerId;value["writer"]=blocker.writer;
    value["reason"]=blocker.reason;value["detail"]=blocker.detail;
    value["count"]=static_cast<uint64_t>(blocker.count);
    value["blocking"]=blocker.blocking;
    scriptEvidence["blockers"].push_back(value);
  }
  scriptEvidence["pending_writers"] = CVariant(CVariant::VariantTypeArray);
  for (const auto& name : scripts.pending)
    scriptEvidence["pending_writers"].push_back(name);
  result["script_persistence"] = scriptEvidence;
  result["required_jobs"] = static_cast<uint64_t>(s.jobs.required);
  result["unknown_job_owners"] = static_cast<uint64_t>(s.jobs.unknown);
  result["nonpersistent_jobs"] = static_cast<uint64_t>(s.jobs.nonPersistent);
  result["blocking_jobs"] = CVariant(CVariant::VariantTypeArray);
  for (const auto& job : s.jobs.blockers)
  {
    CVariant value(CVariant::VariantTypeObject);
    value["token"] = job.token;
    value["job_id"] = job.jobId;
    value["owner"] = job.owner;
    value["operation"] = job.operation;
    value["actual_type"] = job.type;
    value["phase"] = job.phase;
    value["unknown"] = job.unknown;
    value["elapsed_ms"] = job.elapsedMs;
    result["blocking_jobs"].push_back(value);
  }
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
  return CJSONVariantWriter::Write(value, bytes, true) && SaveCheckpointProtocol(path, bytes);
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
    {std::lock_guard<std::mutex> lock(s.mutex);FailLocked(s,"command_center",detail.substr(0,384));}
    return false;
  }
  return response["participant"].isString() && response["participant"].asString() == "command-center-json" &&
    response["status"].isString() && response["status"].asString() == expected &&
    response["global_safe_to_terminate"].isBoolean() &&
    !response["global_safe_to_terminate"].asBoolean();
}
bool CompatIdentity(const CVariant& value, const State& s, bool session)
{
  return SameIdentity(value, s, session) &&
    value["participant"].isString() && value["participant"].asString() == "infinity-compat" &&
    value["participant_api"].isInteger() && value["participant_api"].asInteger() == 1 &&
    value["addon_version"].isString() && (value["addon_version"].asString() == "0.7.2" || value["addon_version"].asString() == "0.8.2") &&
    value["global_safe_to_terminate"].isBoolean() && !value["global_safe_to_terminate"].asBoolean();
}
bool CompatResponse(State& s)
{
  CVariant response;
  if (!ReadJson(s.directory + "/compat-response.json", response) || !CompatIdentity(response, s, true))
    return false;
  if (response["status"].isString() && response["status"].asString() == "CHECKPOINT_FAILED")
  {
    const auto detail = std::string("compat_participant_failed:") + response["error"].asString();
    {std::lock_guard<std::mutex> lock(s.mutex);FailLocked(s,"compat",detail.substr(0,384));}
    return false;
  }
  if (!response["status"].isString() || response["status"].asString() != "PARTICIPANT_COMPLETE" ||
      !response["guard_frozen"].isBoolean() || !response["guard_frozen"].asBoolean() ||
      !response["operations"].isArray() || response["operations"].size() != 2)
    return false;
  bool files = false;
  bool marker = false;
  for (auto it = response["operations"].begin_array(); it != response["operations"].end_array(); ++it)
  {
    if (!(*it)["name"].isString() || !(*it)["ok"].isBoolean() || !(*it)["ok"].asBoolean())
      return false;
    if ((*it)["name"].asString() == "critical_files")
    {
      if (files) return false;
      files = true;
    }
    else if ((*it)["name"].asString() == "clean_marker")
    {
      if (marker) return false;
      marker = true;
    }
    else return false;
  }
  return files && marker;
}
bool ReadOptionalJson(const std::string& path, CVariant& value, bool& present)
{
  struct stat info{};
  if (::lstat(path.c_str(), &info) != 0)
  {
    present = false;
    return errno == ENOENT;
  }
  present = true;
  return S_ISREG(info.st_mode) && ReadJson(path, value);
}
bool OwnerIdentity(const CVariant& value, const char* tokenField)
{
  return value.isObject() && value["pid"].isInteger() && value["pid"].asInteger() > 0 &&
    value["pid"].asInteger() <= 2147483647 && value[tokenField].isString() &&
    Token(value[tokenField].asString());
}
bool RequiredJobsDrained()
{
  const auto snapshot = CJobManager::AndroidCheckpointSnapshot();
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  s.jobs = snapshot;
  if (snapshot.unknown != 0)
  {
    std::string detail = "unknown_native_job_persistence_contract";
    for (const auto& job : snapshot.blockers)
      if (job.unknown) detail += ";" + job.type;
    FailLocked(s, "background_jobs", detail.substr(0, 384));
    return false;
  }
  for (const auto& job : snapshot.blockers)
    if (std::none_of(std::begin(REQUIRED), std::end(REQUIRED),
                     [&](const char* owner) { return job.owner == owner; }))
    {
      FailLocked(s, "background_jobs", "job_mapped_to_unregistered_persistence_owner");
      return false;
    }
  return snapshot.required == 0;
}
bool PvrOwnersAbsent()
{
  const auto& manager = CServiceBroker::GetPVRManager();
  const auto clients = manager.Clients();
  return manager.IsStoppedForAndroidCheckpoint() && clients && !clients->HasAndroidCheckpointOwners();
}
bool BeginEngineHandshake(State& s)
{
  const auto reject = [&](const char* detail) {
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.startupError.empty())
      s.startupError = detail;
    return false;
  };
  const auto* activity = jni::CJNIMainActivity::GetAppInstance();
  if (!activity || !activity->infinityCheckpointOwnsOwner(s.pid, s.owner))
    return reject("startup_engine_owner_lease_not_held");
  if (!XFILE::CDirectory::Create(s.directory) || !CheckpointCreatedDirectory(s.directory))
    return reject("startup_checkpoint_control_directory_unconfirmed");
  // First launch can create this whole private add-on hierarchy. Persist each
  // new directory entry, not only the final control-directory inode contents.
  const auto addonDirectory = s.directory.substr(0, s.directory.rfind('/'));
  const auto addonDataDirectory = addonDirectory.substr(0, addonDirectory.rfind('/'));
  if (!CheckpointCreatedDirectory(addonDirectory) || !CheckpointCreatedDirectory(addonDataDirectory))
    return reject("startup_checkpoint_parent_directories_unconfirmed");
  CVariant previous;
  bool hadPrevious = false;
  if (!ReadOptionalJson(s.directory + "/engine.json", previous, hadPrevious))
    return reject("startup_previous_engine_identity_unreadable");
  CVariant engine(CVariant::VariantTypeObject);
  engine["schema"] = 1;
  engine["pid"] = s.pid;
  engine["owner"] = s.owner;
  engine["native_api"] = 1;
  const auto retired = [&](const CVariant& value, const char* tokenField) {
    return OwnerIdentity(value, tokenField) &&
      activity->infinityCheckpointOwnerRetired(static_cast<int>(value["pid"].asInteger()),
                                               value[tokenField].asString());
  };
  const auto current = [&](const CVariant& value, const char* tokenField) {
    return OwnerIdentity(value, tokenField) && value["pid"].asInteger() == s.pid &&
      value[tokenField].asString() == s.owner;
  };
  if (hadPrevious)
  {
    if (!previous["schema"].isInteger() || previous["schema"].asInteger() != 1 ||
        !previous["native_api"].isInteger() || previous["native_api"].asInteger() != 1 ||
        (!current(previous, "owner") && !retired(previous, "owner")))
      return false;
    // Re-entry before all interpreters bind must retain the previous CAS proof.
    if (current(previous, "owner") && previous.isMember("previous_owner"))
    {
      if (!retired(previous["previous_owner"], "token"))
        return false;
      engine["previous_owner"] = previous["previous_owner"];
    }
  }
  CVariant journal;
  bool hadJournal = false;
  if (!ReadOptionalJson(s.directory + "/participant.json", journal, hadJournal))
    return false;
  if (hadJournal)
  {
    // A process can die after publishing engine.json but before rebinding its
    // journal. CAS targets the real journal owner, not the most recent engine.
    const auto& journalOwner = journal["owner"];
    if (!current(journalOwner, "token"))
    {
      if (!retired(journalOwner, "token"))
        return false;
      engine["previous_owner"] = journalOwner;
    }
  }
  else if (hadPrevious && !current(previous, "owner"))
  {
    engine["previous_owner"]["pid"] = previous["pid"];
    engine["previous_owner"]["token"] = previous["owner"];
  }
  if (!activity->infinityCheckpointOwnsOwner(s.pid, s.owner))
    return false;
  return WriteJson(s.directory + "/engine.json", engine);
}
} // namespace

bool RegisterStartupOwner(const std::string& owner, int pid, const std::string& filesDirectory)
{
  if (!Token(owner) || pid != static_cast<int>(::getpid()) || filesDirectory.empty() ||
      filesDirectory.front() != '/' || filesDirectory.find('\0') != std::string::npos)
    return false;
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (s.lifecycleTeardown || s.active.load())
    return false;
  if (s.ownerRegistered)
    return s.owner == owner && s.pid == pid && s.filesDirectory == filesDirectory;
  s.ownerRegistered = true;
  s.owner = owner;
  s.pid = pid;
  s.filesDirectory = filesDirectory;
  return true;
}
bool PublishStartupOwner()
{
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    if (!s.ownerRegistered || s.active.load() || s.lifecycleTeardown || s.ownerPublishing)
      return false;
    s.ownerPublishing = true;
    s.ownerPublished = false;
    s.startupError.clear();
    s.directory = CSpecialProtocol::TranslatePath(
        "special://profile/addon_data/script.infinity.commandcenter/.android-checkpoint");
  }
  bool published = false;
  ++startupWriteDepth;
  try { published = BeginEngineHandshake(s); }
  catch (...) { published = false; }
  --startupWriteDepth;
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    s.ownerPublishing = false;
    s.ownerPublished = published && !s.lifecycleTeardown && s.startupError.empty();
    if (!s.ownerPublished && s.startupError.empty())
      s.startupError = "startup_owner_identity_or_durability_proof_failed";
    return s.ownerPublished;
  }
}
bool IsActive() { return Get().active.load(); }
bool IsRequiredOwner(const std::string& owner)
{
  return std::any_of(std::begin(REQUIRED), std::end(REQUIRED),
                     [&](const char* candidate) { return owner == candidate; });
}
bool IsAcceptedPlaybackWorkOnThisThread() { return acceptedPlaybackDepth != 0; }
bool IsPersistingOnThisThread()
{
  if (startupWriteDepth != 0)
    return true; // Native identity publication only, before any profile services start.
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
  const bool newCommand = owner == "playback-command" || owner == "pvr-start" || owner == "optional-cache-work";
  const bool newJob = owner == "jobs" || owner == "directory-work" || newCommand;
  m_admitted = !s.active.load() ||
    (!newJob && !s.sealed && s.phase != "CHECKPOINT_FAILED") ||
    (owner == "jobs" && acceptedPlaybackDepth != 0 && !s.sealed && s.phase == "QUIESCE") ||
    (!newCommand && permissionDepth != 0 && s.phase == "PERSISTING");
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
  const bool jobFailure = owner && std::string(owner) == "background_jobs";
  const auto jobs = jobFailure ? CJobManager::AndroidCheckpointSnapshot() : JobCheckpoint::Snapshot{};
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (s.active.load())
  {
    if (jobFailure)
      s.jobs = jobs;
    BlockLocked(s, owner ? owner : "unknown", detail ? detail : "unspecified_failure");
  }
  else if (startupWriteDepth != 0)
    s.startupError = std::string(owner ? owner : "unknown") + ":" +
                     (detail ? detail : "unspecified_startup_failure");
}
void RecordFatalFailure(const char* owner,const char* detail)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(s.active.load())FailLocked(s,owner?owner:"unknown",detail?detail:"unspecified_failure");
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
  const auto* activity = jni::CJNIMainActivity::GetAppInstance();
  if (!activity || !activity->infinityCheckpointOwnsOwner(pid, owner))
    return false;
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.lifecycleTeardown || !s.ownerRegistered || !s.ownerPublished || s.ownerPublishing ||
        s.owner != owner || s.pid != pid)
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
    s.sealed=false;s.authorized=false;s.inventoryComplete=false;
    s.error.clear();s.errors=0;s.blockers.clear();s.blockerOverflow=false;
    s.safeStatus.clear();s.blocking="native_admission";s.pendingDetail.clear();
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
  {
    // A rejected request must retain its real cause. This is diagnostic only;
    // it cannot create a checkpoint, change admission, or authorize termination.
    if (Token(session) && Token(owner) && pid == static_cast<int>(::getpid()) &&
        (!s.ownerRegistered || (s.owner == owner && s.pid == pid)))
    {
      CVariant result(CVariant::VariantTypeObject);
      result["schema"] = 1;
      result["session"] = session;
      result["owner"] = owner;
      result["pid"] = pid;
      result["phase"] = "CHECKPOINT_FAILED";
      result["error"] = s.lifecycleTeardown ? "legacy_teardown_already_started" :
          !s.ownerRegistered ? "startup_engine_owner_not_registered" :
          !s.startupError.empty() ? s.startupError :
          !s.ownerPublished || s.ownerPublishing ? "startup_owner_publication_pending" :
          "native_checkpoint_request_identity_rejected";
      result["startup_owner_registered"] = s.ownerRegistered;
      result["startup_owner_published"] = s.ownerPublished;
      result["startup_owner_publishing"] = s.ownerPublishing;
      std::string encoded;
      if (CJSONVariantWriter::Write(result, encoded, true))
        return encoded;
    }
    return "{\"schema\":1,\"phase\":\"CHECKPOINT_FAILED\",\"error\":\"stale_or_foreign_identity\"}";
  }
  CheckDeadlineLocked(s);
  return s.phase == "SAFE_TO_TERMINATE" ? s.safeStatus : EncodeStatusLocked(s);
}
bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)
{
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    if (!Matches(s, session, owner, pid))
      return false;
  }
  const auto* activity = jni::CJNIMainActivity::GetAppInstance();
  if (!activity || !activity->infinityCheckpointOwnsOwner(pid, owner))
  {
    RecordFatalFailure("native_admission","engine_owner_lease_not_held_at_termination");
    return false;
  }
  if (!PvrOwnersAbsent())
  {
    RecordFatalFailure("pvr","pvr_owner_present_at_termination");
    return false;
  }
  const auto scripts = InfinityScriptPersistence::Snapshot();
  if (!scripts.failure.empty() || scripts.blockingCount != 0 || scripts.blockingOverflow)
  {
    RecordFatalFailure("python_services",scripts.failure.empty()?"python_blocker_after_safe":scripts.failure.c_str());
    return false;
  }
  if (!scripts.durable || scripts.active != 0)
    return false;
  const auto database = InfinityDatabaseBarrier::GetSnapshot();
  std::lock_guard<std::mutex> lock(s.mutex);
  CheckDeadlineLocked(s);
  if (!Matches(s, session, owner, pid) || s.lifecycleTeardown ||
      s.phase != "SAFE_TO_TERMINATE" || !s.sealed || !s.blockers.empty() ||
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
      { RecordFatalFailure("native_admission", "application_not_initialized"); return; }
      CScriptInvocationManager::GetInstance().BeginShutdown(); // Admission only; no Stop/join.
      CServiceBroker::GetJobManager()->UnPauseJobs(); // Drain previously accepted low-priority work.
      if (!PvrOwnersAbsent())
      { RecordFatalFailure("pvr", "active_or_retained_pvr_owner_has_no_persistence_participant"); return; }
      Complete("pvr", false);
      const auto* activity = jni::CJNIMainActivity::GetAppInstance();
      if (!activity || !activity->infinityCheckpointOwnsOwner(s.pid, s.owner))
      { RecordFatalFailure("command_center", "engine_owner_lease_not_held"); return; }
      s.stage = 1;
    }
    if (s.stage == 1)
    {
      Operation("command_center");
      CVariant active;
      if (!ReadJson(s.directory + "/active.json", active) || !SameIdentity(active, s, false) ||
          !active["status"].isString() || active["status"].asString() != "ACTIVE" ||
          !active["participant_api"].isInteger() || active["participant_api"].asInteger() != 1 ||
          !active["addon_version"].isString() || (active["addon_version"].asString() != "0.3.5.19" && active["addon_version"].asString() != "0.3.5.20"))
        return;
      if (CScriptInvocationManager::GetInstance().AndroidCheckpointResidentCount() != 1)
      { RecordFatalFailure("command_center", "exactly_one_canonical_resident_required"); return; }
      Operation("compat");
      if (CScriptInvocationManager::GetInstance().AndroidCheckpointCompatCount() != 1)
      { RecordFatalFailure("compat", "exactly_one_hash_verified_compat_resident_required"); return; }
      CVariant compatActive;
      if (!ReadJson(s.directory + "/compat-active.json", compatActive) ||
          !CompatIdentity(compatActive, s, false) || !compatActive["status"].isString() ||
          compatActive["status"].asString() != "ACTIVE")
        return;
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
      { RecordFatalFailure("playback", failure.c_str()); return; }
      if (playback != InfinityPlaybackCheckpoint::PollResult::Complete)
        return;
      Complete("playback", true);
      // Let already-admitted generic add-on writers run their normal cleanup
      // with a frozen player clock. This sends cooperative abort notifications;
      // it never injects exceptions, joins on the GUI thread, or kills workers.
      CScriptInvocationManager::GetInstance().BeginAndroidCheckpoint();
      Operation("command_center");
      CVariant request = Identity(s);
      request["phase"] = "PREPARE";
      if (!WriteJson(s.directory + "/request.json", request))
      { RecordFatalFailure("command_center", "prepare_request_write_failed"); return; }
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
      { RecordFatalFailure("command_center", "finalize_request_write_failed"); return; }
      s.stage = 4;
    }
    if (s.stage == 4)
    {
      Operation("command_center");
      if (!ParticipantResponse(s, "PARTICIPANT_COMPLETE"))
        return;
      Complete("command_center", true);
      Operation("compat");
      if (!CompatResponse(s))
        return;
      Complete("compat", true);

      // Inventory every script writer before deciding the global checkpoint.
      // A failed interpreter may settle without receiving a durable retirement receipt.
      Operation("python_services");
      auto scripts = InfinityScriptPersistence::Snapshot();
      if (scripts.blockingCount != 0 || scripts.blockingOverflow)
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        if (s.owners["python_services"].error.empty())
          BlockLocked(s, "python_services", "python_writer_blockers_present");
      }
      for (const auto& name : s.unresolvedForeignOwners)
        if (!InfinityScriptPersistence::DurableRetirement(name) &&
            !InfinityScriptPersistence::BlockedRetirement(name))
          return;
      if (!CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters().empty())
        return;
      if (!InfinityScriptPersistence::PollInventory())
        return; // Durability sync may finish even when a writer-level blocker is retained.
      scripts = InfinityScriptPersistence::Snapshot();
      if (scripts.blockingCount == 0 && !scripts.blockingOverflow && scripts.durable)
        Complete("python_services", true);
      else
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        if (s.owners["python_services"].error.empty())
          BlockLocked(s, "python_services", scripts.failure.empty() ?
              "python_persistence_not_durable" : scripts.failure);
      }

      Operation("background_jobs");
      if (!RequiredJobsDrained())
        return;
      Complete("background_jobs", false);
      if (CScriptInvocationManager::GetInstance().AndroidCheckpointResidentCount() != 1 ||
          CScriptInvocationManager::GetInstance().AndroidCheckpointCompatCount() != 1 ||
          CScriptInvocationManager::GetInstance().AndroidCheckpointForeignScripts() != 0)
      { RecordFatalFailure("python_services", "source_contract_changed_or_unproven_writer_admitted"); return; }
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        if (s.activeWrites != 0 || s.phase == "CHECKPOINT_FAILED")
          return;
        s.sealed = true; // No ordinary mutation can enter between drain and save.
        s.phase = "PERSISTING";
      }
      if (!InfinityDatabaseBarrier::Begin(s.generation))
      { RecordFatalFailure("native_databases", "database_barrier_begin_failed"); return; }
      Complete("native_admission", false);
      s.stage = 5;
    }
    if (s.stage == 5)
    {
      Operation("native_databases");
      const auto pendingDatabase = InfinityDatabaseBarrier::GetSnapshot();
      if (pendingDatabase.failures || pendingDatabase.rejectedWrites || pendingDatabase.unsupportedOwners)
        RecordFailure("native_databases", "failed_or_unsupported_database_owner");
      if (!pendingDatabase.Ready())
        return;
      InfinityDatabaseBarrier::CheckpointWriteScope databasePermission(s.generation);
      if (!databasePermission.IsValid())
      { RecordFatalFailure("native_databases", "checkpoint_database_scope_rejected"); return; }

      Operation("deferred_dialog_state");
      {
        const auto before=ErrorGeneration();
        const bool ok=CheckpointDeferredDialogState();
        if(!ok)RecordFailure("deferred_dialog_state","pending_dialog_state_checkpoint_failed");
        (void)before; // Completion waits for final database seal.
      }

      Operation("skin_settings");
      {
        const auto before=ErrorGeneration();
        const bool ok=CheckpointSkinSettings();
        if(!ok)RecordFailure("skin_settings","skin_settings_save_failed");
        if(ok && !HasFailureSince(before))Complete("skin_settings",true);
      }

      Operation("addon_settings");
      {
        const auto before=ErrorGeneration();
        const bool ok=CheckpointLoadedAddonSettings();
        if(!ok)RecordFailure("addon_settings","loaded_addon_settings_save_failed");
        if(ok && !HasFailureSince(before))Complete("addon_settings",true);
      }

      Operation("favourites");
      {
        const auto before=ErrorGeneration();
        const bool ok=CServiceBroker::GetFavouritesService().CheckpointForAndroidExit();
        if(!ok)RecordFailure("favourites","favourites_save_failed");
        if(ok && !HasFailureSince(before))Complete("favourites",true);
      }

      Operation("peripherals");
      {
        const auto before=ErrorGeneration();
        const bool ok=CServiceBroker::GetPeripherals().CheckpointForAndroidExit();
        if(!ok)RecordFailure("peripherals","peripheral_settings_save_failed");
        if(ok && !HasFailureSince(before))Complete("peripherals",true);
      }

      Operation("audio_policy");
      {
        const auto before=ErrorGeneration();
        const bool ok=CheckpointAudioPolicyFile();
        if(!ok)RecordFailure("audio_policy","audio_policy_file_checkpoint_failed");
        if(ok && !HasFailureSince(before))Complete("audio_policy",true);
      }

      // Save base settings after add-on/skin callbacks, so accepted setting
      // effects are included even when another independent owner already failed.
      Operation("kodi_settings");
      {
        const auto before=ErrorGeneration();
        const bool ok=CServiceBroker::GetSettingsComponent()->GetSettings()->Save();
        if(!ok)RecordFailure("kodi_settings","settings_save_failed");
        if(ok && !HasFailureSince(before))Complete("kodi_settings",true);
      }

      Operation("profiles");
      {
        const auto before=ErrorGeneration();
        const bool ok=CServiceBroker::GetSettingsComponent()->GetProfileManager()->Save();
        if(!ok)RecordFailure("profiles","profiles_save_failed");
        if(ok && !HasFailureSince(before))Complete("profiles",true);
      }

      {
        std::lock_guard<std::mutex> lock(s.mutex);
        if(s.owners["xml_files"].error.empty()) {
          auto& owner=s.owners["xml_files"];
          owner.complete=true;owner.dirty=false;owner.committed=true;
          owner.durableGeneration=owner.generation;owner.elapsed=Elapsed(s);
        }
      }
      s.stage = 6;
    }
    if (s.stage == 6)
    {
      // Checkpoint callbacks can enqueue accepted persistence jobs. Their queue
      // and destructor lifetimes must drain before final inventory can close.
      Operation("background_jobs");
      if (!RequiredJobsDrained())
        return;
      Complete("background_jobs", false);

      Operation("native_databases");
      if (!PvrOwnersAbsent())
      { RecordFatalFailure("pvr", "pvr_owner_present_before_final_seal"); return; }
      const auto database = InfinityDatabaseBarrier::GetSnapshot();
      if (database.failures || database.rejectedWrites || database.unsupportedOwners)
        RecordFailure("native_databases", "database_owner_failed_before_final_seal");
      if (!database.Ready())
        return;
      if (!InfinityDatabaseBarrier::Seal(s.generation))
        RecordFailure("native_databases", "database_barrier_not_durable_or_drained");

      bool databaseBlocked=false;
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        databaseBlocked=!s.owners["native_databases"].error.empty();
      }
      if(!databaseBlocked)Complete("native_databases", true);

      bool deferredBlocked=false;
      {
        std::lock_guard<std::mutex> lock(s.mutex);
        deferredBlocked=!s.owners["deferred_dialog_state"].error.empty();
      }
      if(!deferredBlocked && !databaseBlocked)
        Complete("deferred_dialog_state", true); // Captured state covered by settings save + DB seal.

      std::lock_guard<std::mutex> lock(s.mutex);
      CheckDeadlineLocked(s);
      if (s.phase == "CHECKPOINT_FAILED" || s.activeWrites != 0)
        return;
      for (const char* name : REQUIRED)
      {
        const auto& owner = s.owners.at(name);
        if ((!owner.complete || owner.dirty || owner.generation != owner.durableGeneration) &&
            owner.error.empty())
          BlockLocked(s, name, "required_owner_not_durable");
      }
      if(!s.blockers.empty() || s.blockerOverflow) {
        FinalizeInventoryFailureLocked(s);
        s.blocking=s.blockers.empty()?"blocker_inventory_overflow":s.blockers.front().owner;
        return;
      }
      s.inventoryComplete=true;
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
    RecordFatalFailure("native_admission", "checkpoint_exception");
  }
  catch (...)
  {
    RecordFatalFailure("native_admission", "checkpoint_unknown_exception");
  }
}
} // namespace InfinityAndroidCheckpoint
