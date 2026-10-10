/*
 *  Copyright (C) 2013-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "ScriptInvocationManager.h"
#include "platform/android/activity/InfinityShutdownTrace.h"
#if defined(TARGET_ANDROID) && defined(HAS_PYTHON)
#include "ServiceBroker.h"
#include "interfaces/python/XBPython.h"
#endif
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "platform/android/activity/InfinityCheckpointFile.h"
#include "platform/android/activity/InfinityScriptPersistence.h"
#endif

#include "interfaces/generic/ILanguageInvocationHandler.h"
#include "interfaces/generic/ILanguageInvoker.h"
#include "interfaces/generic/LanguageInvokerThread.h"
#include "filesystem/SpecialProtocol.h"
#include "utils/FileUtils.h"
#include "utils/StringUtils.h"
#include "utils/URIUtils.h"
#include "utils/XTimeUtils.h"
#include "utils/log.h"

#include <algorithm>
#include <cerrno>
#include <climits>
#include <chrono>
#include <fcntl.h>
#include <map>
#include <memory>
#include <mutex>
#include <sstream>
#include <set>
#include <string>
#include <sys/stat.h>
#include <thread>
#include <unistd.h>
#include <utility>
#include <vector>

#if defined(TARGET_ANDROID)
namespace InfinityAddonQuarantine
{
struct Record
{
  unsigned failures{0};
  bool quarantined{false};
  std::string reason;
  std::string signature;
};
struct Registry
{
  std::mutex mutex;
  bool loaded{false};
  std::map<std::string, Record> records;
  std::set<std::string> probation;
};
Registry& Get()
{
  static auto* registry = new Registry;
  return *registry;
}
bool ValidAddonId(const std::string& addon)
{
  return !addon.empty() && addon.size() <= 128 &&
         std::all_of(addon.begin(), addon.end(), [](unsigned char c) {
           return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                  (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-';
         });
}
bool Protected(const std::string& addon)
{
  return addon == "script.infinity.commandcenter" ||
         addon == "service.infinity.compat" ||
         addon == "script.kodihealthcenter" ||
         addon == "service.infinity.continuity";
}
bool ServiceScript(const std::string& script)
{
  return URIUtils::GetFileName(script) == "service.py";
}
std::string Path()
{
  return CSpecialProtocol::TranslatePath(
      "special://profile/addon_data/script.infinity.commandcenter/.android-checkpoint/addon-quarantine.tsv");
}

std::string ProbeRequestPath()
{
  return CSpecialProtocol::TranslatePath(
      "special://profile/addon_data/script.infinity.commandcenter/.android-checkpoint/addon-probation.request");
}
std::string ServiceSignature(const std::string& script)
{
  const std::string path = CSpecialProtocol::TranslatePath(script);
  struct stat info{};
  if (path.empty() || ::lstat(path.c_str(), &info) != 0 || !S_ISREG(info.st_mode) || S_ISLNK(info.st_mode))
    return {};
  return std::to_string(static_cast<long long>(info.st_size)) + ":" +
         std::to_string(static_cast<long long>(info.st_mtime));
}
bool ConsumeProbeRequest(const std::string& addon)
{
  const std::string path = ProbeRequestPath();
  const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0)
    return false;
  struct stat info{};
  bool ok = ::fstat(fd, &info) == 0 && S_ISREG(info.st_mode) && info.st_size > 0 && info.st_size <= 256;
  std::string value;
  if (ok)
  {
    value.resize(static_cast<size_t>(info.st_size));
    size_t offset = 0;
    while (offset < value.size())
    {
      ssize_t count = ::read(fd, &value[offset], value.size() - offset);
      if (count < 0 && errno == EINTR) continue;
      if (count <= 0) { ok = false; break; }
      offset += static_cast<size_t>(count);
    }
  }
  ::close(fd);
  while (!value.empty() && (value.back() == '\n' || value.back() == '\r'))
    value.pop_back();
  if (!ok || value != addon)
    return false;
  if (::unlink(path.c_str()) != 0)
    return false;
  const auto slash = path.rfind('/');
  const std::string parent = slash == std::string::npos ? "." : path.substr(0, slash);
  const int dir = ::open(parent.c_str(), O_RDONLY | O_CLOEXEC | O_DIRECTORY);
  if (dir >= 0) { ::fsync(dir); ::close(dir); }
  return true;
}
void PersistLocked(const Registry& registry)
{
  std::string bytes = "infinity-addon-quarantine-v1\n";
  for (const auto& entry : registry.records)
  {
    if (!ValidAddonId(entry.first))
      continue;
    bytes += entry.first + "\t" + std::to_string(entry.second.failures) + "\t" +
             (entry.second.quarantined ? "1" : "0") + "\t" +
             entry.second.reason.substr(0, 96) + "\t" +
             entry.second.signature.substr(0, 96) + "\n";
  }
  const auto result = infinity::checkpoint::files::SaveDirty(Path(), bytes);
  if (!result.ok)
    CLog::Log(LOGWARNING, "Infinity add-on quarantine ledger save failed at {}",
              infinity::checkpoint::files::StageName(result.stage));
}
void LoadLocked(Registry& registry)
{
  if (registry.loaded)
    return;
  registry.loaded = true;
  const std::string path = Path();
  const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd >= 0)
  {
    struct stat info{};
    if (::fstat(fd, &info) == 0 && S_ISREG(info.st_mode) && info.st_size >= 0 && info.st_size <= 65536)
    {
      std::string bytes(static_cast<size_t>(info.st_size), '\0');
      size_t offset = 0;
      while (offset < bytes.size())
      {
        ssize_t count = ::read(fd, &bytes[offset], bytes.size() - offset);
        if (count < 0 && errno == EINTR)
          continue;
        if (count <= 0)
        {
          bytes.clear();
          break;
        }
        offset += static_cast<size_t>(count);
      }
      if (!bytes.empty())
      {
        std::istringstream input(bytes);
        std::string line;
        if (std::getline(input, line) && line == "infinity-addon-quarantine-v1")
        {
          while (std::getline(input, line))
          {
            const auto first = line.find('\t');
            const auto second = first == std::string::npos ? first : line.find('\t', first + 1);
            const auto third = second == std::string::npos ? second : line.find('\t', second + 1);
            if (first == std::string::npos || second == std::string::npos || third == std::string::npos)
              continue;
            const std::string addon = line.substr(0, first);
            if (!ValidAddonId(addon) || Protected(addon))
              continue;
            unsigned failures = 0;
            try
            {
              const auto parsed = std::stoul(line.substr(first + 1, second - first - 1));
              failures = parsed > UINT_MAX ? UINT_MAX : static_cast<unsigned>(parsed);
            }
            catch (...)
            {
              continue;
            }
            const std::string quarantine = line.substr(second + 1, third - second - 1);
            if (quarantine != "0" && quarantine != "1")
              continue;
            Record record;
            record.failures = failures;
            record.quarantined = quarantine == "1";
            const auto fourth = line.find('\t', third + 1);
            record.reason = line.substr(third + 1, fourth == std::string::npos ? 96 :
                                        std::min<std::size_t>(96, fourth - third - 1));
            if (fourth != std::string::npos)
              record.signature = line.substr(fourth + 1, 96);
            registry.records[addon] = std::move(record);
          }
        }
      }
    }
    ::close(fd);
  }

  // Physical Fold evidence 2026-10-09: this service is already throwing a
  // startup error and the user does not use it. Quarantine ONLY its resident
  // service; keep the shared module installed for dependencies that import it.
  if (registry.records.find("script.module.slyguy") == registry.records.end())
  {
    registry.records["script.module.slyguy"] = {2u, true, "seeded_fold_startup_error", {}};
    PersistLocked(registry);
  }
}
bool ShouldSuppress(const std::string& addon, const std::string& script)
{
  if (!ValidAddonId(addon) || Protected(addon) || !ServiceScript(script))
    return false;
  auto& registry = Get();
  std::lock_guard<std::mutex> lock(registry.mutex);
  LoadLocked(registry);
  auto found = registry.records.find(addon);
  if (found == registry.records.end() || !found->second.quarantined)
    return false;
  if (registry.probation.count(addon))
    return false;

  const std::string signature = ServiceSignature(script);
  bool changed = false;
  if (found->second.signature.empty() && !signature.empty())
  {
    found->second.signature = signature;
    changed = true;
  }
  const bool codeChanged = !signature.empty() && !found->second.signature.empty() &&
                           signature != found->second.signature;
  const bool requested = ConsumeProbeRequest(addon);
  if (requested || codeChanged)
  {
    registry.probation.insert(addon);
    if (codeChanged)
    {
      // Consume this code revision as the automatic retry candidate now. If the
      // probation later hits hard persistence uncertainty, the unchanged code
      // will be quarantined on the next launch instead of auto-retried forever.
      found->second.signature = signature;
      found->second.reason = "probation_code_change";
      PersistLocked(registry);
      changed = false;
    }
    CLog::Log(LOGINFO, "Infinity quarantine: probation granted for {} ({})", addon,
              requested ? "Health Center request" : "service code changed");
    return false;
  }
  if (changed)
    PersistLocked(registry);
  return true;
}
bool SuppressErrorToast(const std::string& addon, const std::string& script)
{
  if (!ServiceScript(script))
    return false;
  auto& registry = Get();
  std::lock_guard<std::mutex> lock(registry.mutex);
  return registry.probation.count(addon) != 0;
}
void RecordCleanFailure(const std::string& addon, const std::string& script)
{
  if (!ValidAddonId(addon) || Protected(addon) || !ServiceScript(script))
    return;
  auto& registry = Get();
  std::lock_guard<std::mutex> lock(registry.mutex);
  LoadLocked(registry);
  auto& record = registry.records[addon];
  if (record.quarantined)
  {
    if (registry.probation.erase(addon) != 0)
    {
      if (record.failures < UINT_MAX) ++record.failures;
      record.reason = "probation_runtime_failure";
      record.signature = ServiceSignature(script);
      PersistLocked(registry);
    }
    return;
  }
  if (record.failures < UINT_MAX)
    ++record.failures;
  record.reason = record.failures >= 2 ? "repeated_clean_uncaught_service_failure" :
                                        "clean_uncaught_service_failure_candidate";
  if (record.failures >= 2)
  {
    record.quarantined = true;
    record.signature = ServiceSignature(script);
  }
  PersistLocked(registry);
}
void RecordCleanSuccess(const std::string& addon, const std::string& script)
{
  if (!ValidAddonId(addon) || Protected(addon) || !ServiceScript(script))
    return;
  auto& registry = Get();
  std::lock_guard<std::mutex> lock(registry.mutex);
  LoadLocked(registry);
  const auto found = registry.records.find(addon);
  if (found == registry.records.end())
    return;
  if (found->second.quarantined)
  {
    if (registry.probation.erase(addon) != 0)
    {
      found->second.failures = 0;
      found->second.quarantined = false;
      found->second.reason = "restored_after_probation";
      found->second.signature = ServiceSignature(script);
      PersistLocked(registry);
      CLog::Log(LOGINFO, "Infinity quarantine: {} restored after clean probation", addon);
    }
    return;
  }
  if (found->second.reason == "restored_after_probation")
    return; // Keep a durable Health Center recovery receipt.
  registry.records.erase(found); // first-strike candidate recovered normally
  PersistLocked(registry);
}
} // namespace InfinityAddonQuarantine
#endif

CScriptInvocationManager::~CScriptInvocationManager()
{
  Uninitialize();
}

CScriptInvocationManager& CScriptInvocationManager::GetInstance()
{
  static CScriptInvocationManager s_instance;
  return s_instance;
}

void CScriptInvocationManager::Process()
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  // go through all active threads and find and remove all which are done
  std::vector<LanguageInvokerThread> tempList;
  for (LanguageInvokerThreadMap::iterator it = m_scripts.begin(); it != m_scripts.end(); )
  {
    if (it->second.done)
    {
      tempList.push_back(it->second);
      m_scripts.erase(it++);
    }
    else
      ++it;
  }

  // remove the finished scripts from the script path map as well
  for (const auto& it : tempList)
    m_scriptPaths.erase(it.script);

  // we can leave the lock now
  lock.unlock();

  // finally remove the finished threads but we do it outside of any locks in
  // case of any callbacks from the destruction of the CLanguageInvokerThread
  tempList.clear();

  // let the invocation handlers do their processing
  for (auto& it : m_invocationHandlers)
    it.second->Process();
}

bool CScriptInvocationManager::IsShutdownRequested() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  return m_shutdownRequested;
}

void CScriptInvocationManager::BeginShutdown()
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  m_shutdownRequested = true;
}

namespace
{
std::string VerifiedCheckpointContract(const std::string& script,
                                       const CLanguageInvokerThreadPtr& thread,
                                       const std::string& admittedContract)
{
#if defined(TARGET_ANDROID)
  const auto& addon = thread->GetAddon();
  if (!admittedContract.empty() &&
      InfinityAndroidCheckpoint::ClassifyScript(script, addon ? addon->ID() : "") == admittedContract)
    return admittedContract;
#else
  (void)script;
  (void)thread;
  (void)admittedContract;
#endif
  return {};
}
}

void CScriptInvocationManager::BeginAndroidCheckpoint()
{
  std::vector<CLanguageInvokerThreadPtr> pending;
  {
    std::unique_lock<CCriticalSection> lock(m_critSection);
    m_shutdownRequested = true;
    m_androidCheckpointRetirementStarted = std::chrono::steady_clock::now();
    m_androidCheckpointRetirementArmed = true;
    m_androidCheckpointEscalatedIds.clear();
    m_androidCheckpointEscalationsActive = 0;
    for (const auto& entry : m_scripts)
      if (!entry.second.done)
      {
        const auto contract = VerifiedCheckpointContract(entry.second.script, entry.second.thread,
                                                         entry.second.checkpointContract);
        if (contract.empty() || contract.rfind("nonpersistent:", 0) == 0 ||
            contract.rfind("reconstructible-cache:", 0) == 0)
          pending.push_back(entry.second.thread);
      }
  }
#if defined(TARGET_ANDROID) && defined(HAS_PYTHON)
  for (const auto& thread : pending)
  {
    // First pass is deliberately cooperative. Give add-ons a chance to observe
    // Monitor/legacy abort and flush their own state before any escalation.
    CServiceBroker::GetXBPython().NotifyScriptAborting(thread.get());
    const auto invoker = thread->GetInvoker();
    if (invoker)
      invoker->Stop(false);
    thread->Release();
  }
#endif
}

void CScriptInvocationManager::PumpAndroidCheckpointRetirement(bool force)
{
#if defined(TARGET_ANDROID) && defined(HAS_PYTHON)
  struct Candidate
  {
    int id;
    CLanguageInvokerThreadPtr thread;
    std::string addon;
    std::string script;
  };
  constexpr std::size_t MAX_PARALLEL_ESCALATIONS = 8;
  const auto grace = std::chrono::seconds(3);
  std::vector<Candidate> launch;
  {
    std::unique_lock<CCriticalSection> lock(m_critSection);
    if (!m_androidCheckpointRetirementArmed)
      return;
    if (!force && std::chrono::steady_clock::now() - m_androidCheckpointRetirementStarted < grace)
      return;
    if (m_androidCheckpointEscalationsActive >= MAX_PARALLEL_ESCALATIONS)
      return;
    std::size_t available = MAX_PARALLEL_ESCALATIONS - m_androidCheckpointEscalationsActive;
    for (const auto& entry : m_scripts)
    {
      if (available == 0)
        break;
      if (entry.second.done ||
          !VerifiedCheckpointContract(entry.second.script, entry.second.thread,
                                      entry.second.checkpointContract).empty() ||
          m_androidCheckpointEscalatedIds.count(entry.first) != 0)
        continue;
      const auto& addon = entry.second.thread->GetAddon();
      m_androidCheckpointEscalatedIds.insert(entry.first);
      ++m_androidCheckpointEscalationsActive;
      launch.push_back({entry.first, entry.second.thread,
                        addon ? addon->ID() : "unidentified",
                        URIUtils::GetFileName(entry.second.script)});
      --available;
    }
  }

  for (const auto& item : launch)
  {
    InfinityShutdownTrace::Event("milestone", "scripts.checkpoint_escalation_start", item.id,
                                 0, 0, 0, item.addon.c_str(), "started", item.script.c_str());
    try
    {
      std::thread([this, item]() {
        const bool stopped = item.thread->Stop(true);
        InfinityShutdownTrace::Event("milestone", "scripts.checkpoint_escalation_end", item.id,
                                     0, 0, 0, item.addon.c_str(),
                                     stopped ? "stop_returned" : "stop_rejected",
                                     item.script.c_str());
        std::unique_lock<CCriticalSection> lock(m_critSection);
        if (m_androidCheckpointEscalationsActive > 0)
          --m_androidCheckpointEscalationsActive;
        if (!stopped)
        {
          const auto found = m_scripts.find(item.id);
          if (found != m_scripts.end() && !found->second.done)
            m_androidCheckpointEscalatedIds.erase(item.id);
        }
      }).detach();
    }
    catch (...)
    {
      {
        std::unique_lock<CCriticalSection> lock(m_critSection);
        if (m_androidCheckpointEscalationsActive > 0)
          --m_androidCheckpointEscalationsActive;
        m_androidCheckpointEscalatedIds.erase(item.id);
      }
      InfinityAndroidCheckpoint::RecordFailure(
          "python_services", "checkpoint_retirement_escalation_worker_start_failed");
    }
  }
#else
  (void)force;
#endif
}

std::size_t CScriptInvocationManager::AndroidCheckpointEscalationsActive() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  return m_androidCheckpointEscalationsActive;
}

std::size_t CScriptInvocationManager::AndroidCheckpointForeignScripts() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  std::size_t active = 0;
  for (const auto& entry : m_scripts)
    if (!entry.second.done && VerifiedCheckpointContract(entry.second.script, entry.second.thread, entry.second.checkpointContract).empty())
      ++active;
  return active;
}

std::size_t CScriptInvocationManager::AndroidCheckpointResidentCount() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  std::size_t active = 0;
  for (const auto& entry : m_scripts)
    if (!entry.second.done && VerifiedCheckpointContract(entry.second.script, entry.second.thread, entry.second.checkpointContract) == "command_center")
      ++active;
  return active;
}

std::size_t CScriptInvocationManager::AndroidCheckpointCompatCount() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  std::size_t active = 0;
  for (const auto& entry : m_scripts)
    if (!entry.second.done && VerifiedCheckpointContract(entry.second.script, entry.second.thread, entry.second.checkpointContract) == "compat")
      ++active;
  return active;
}

std::vector<std::string> CScriptInvocationManager::AndroidCheckpointUnresolvedWriters() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  std::vector<std::string> result;
  for (const auto& name : m_checkpointUnresolvedWriterLedger)
    if (!InfinityScriptPersistence::DurableRetirement(name) &&
        !InfinityScriptPersistence::BlockedRetirement(name))
      result.push_back(name);
  if (result.size() >= 8)
    return result;
  for (const auto& entry : m_scripts)
  {
    if (entry.second.done || !VerifiedCheckpointContract(entry.second.script, entry.second.thread, entry.second.checkpointContract).empty())
      continue;
    const auto& addon = entry.second.thread->GetAddon();
    result.push_back((addon ? addon->ID() : "unidentified") + ":" + URIUtils::GetFileName(entry.second.script));
    if (result.size() >= 8)
      break;
  }
  return result;
}
bool CScriptInvocationManager::AndroidQuarantineSuppressErrorToast(
    const std::string& addonId, const std::string& script)
{
#if defined(TARGET_ANDROID)
  return InfinityAddonQuarantine::SuppressErrorToast(addonId, script);
#else
  (void)addonId; (void)script;
  return false;
#endif
}

void CScriptInvocationManager::Uninitialize()
{
  InfinityShutdownTrace::Scope methodEvidence("scripts.uninitialize", -1, nullptr, nullptr);
  std::unique_lock<CCriticalSection> lock(m_critSection);

  // execute Process() once more to handle the remaining scripts
  {
    InfinityShutdownTrace::Scope evidence("scripts.final_process", -1, nullptr, nullptr);
    Process();
  }

  // it is safe to release early, thread must be in m_scripts too
  m_lastInvokerThread = nullptr;

  // make sure all scripts are done
  std::vector<LanguageInvokerThread> tempList;
  for (const auto& script : m_scripts)
    tempList.push_back(script.second);

  m_scripts.clear();
  m_scriptPaths.clear();

  // we can leave the lock now
  lock.unlock();

  // finally stop and remove the finished threads but we do it outside of any
  // locks in case of any callbacks from the stop or destruction logic of
  // CLanguageInvokerThread or the ILanguageInvoker implementation
  for (auto& it : tempList)
  {
    if (!it.done)
      {
        const auto& addon = it.thread->GetAddon();
        // Match this script basename and add-on to scripts.target_before_join
        // by invoker_id in the same PID/session. target_thread is a label here.
        const std::string scriptName = URIUtils::GetFileName(it.script);
        InfinityShutdownTrace::Scope evidence("scripts.join_remaining", it.thread->GetId(),
                                               addon ? addon->ID().c_str() : nullptr,
                                               scriptName.c_str());
        it.thread->Stop(true);
      }
  }

  lock.lock();

  {
    InfinityShutdownTrace::Scope evidence("scripts.destroy_invokers", -1, nullptr, nullptr);
    tempList.clear();
  }

  // uninitialize all invocation handlers and then remove them
  for (auto& it : m_invocationHandlers)
    {
      InfinityShutdownTrace::Scope evidence("scripts.handler_uninitialize", -1, nullptr, nullptr);
      it.second->Uninitialize();
    }

  m_invocationHandlers.clear();
}

void CScriptInvocationManager::RegisterLanguageInvocationHandler(ILanguageInvocationHandler *invocationHandler, const std::string &extension)
{
  if (invocationHandler == NULL || extension.empty())
    return;

  std::string ext = extension;
  StringUtils::ToLower(ext);
  if (!StringUtils::StartsWithNoCase(ext, "."))
    ext = "." + ext;

  std::unique_lock<CCriticalSection> lock(m_critSection);
  if (m_invocationHandlers.find(ext) != m_invocationHandlers.end())
    return;

  m_invocationHandlers.insert(std::make_pair(extension, invocationHandler));

  bool known = false;
  for (const auto& it : m_invocationHandlers)
  {
    if (it.second == invocationHandler)
    {
      known = true;
      break;
    }
  }

  // automatically initialize the invocation handler if it's a new one
  if (!known)
    invocationHandler->Initialize();
}

void CScriptInvocationManager::RegisterLanguageInvocationHandler(ILanguageInvocationHandler *invocationHandler, const std::set<std::string> &extensions)
{
  if (invocationHandler == NULL || extensions.empty())
    return;

  for (const auto& extension : extensions)
    RegisterLanguageInvocationHandler(invocationHandler, extension);
}

void CScriptInvocationManager::UnregisterLanguageInvocationHandler(ILanguageInvocationHandler *invocationHandler)
{
  if (invocationHandler == NULL)
    return;

  std::unique_lock<CCriticalSection> lock(m_critSection);
  //  get all extensions of the given language invoker
  for (std::map<std::string, ILanguageInvocationHandler*>::iterator it = m_invocationHandlers.begin(); it != m_invocationHandlers.end(); )
  {
    if (it->second == invocationHandler)
      m_invocationHandlers.erase(it++);
    else
      ++it;
  }

  // automatically uninitialize the invocation handler
  invocationHandler->Uninitialize();
}

bool CScriptInvocationManager::HasLanguageInvoker(const std::string &script) const
{
  std::string extension = URIUtils::GetExtension(script);
  StringUtils::ToLower(extension);

  std::unique_lock<CCriticalSection> lock(m_critSection);
  std::map<std::string, ILanguageInvocationHandler*>::const_iterator it = m_invocationHandlers.find(extension);
  return it != m_invocationHandlers.end() && it->second != NULL;
}

int CScriptInvocationManager::GetReusablePluginHandle(const std::string& script)
{
  std::unique_lock<CCriticalSection> lock(m_critSection);

  if (m_lastInvokerThread)
  {
    if (m_lastInvokerThread->Reuseable(script))
      return m_lastPluginHandle;
    m_lastInvokerThread->Release();
    m_lastInvokerThread = nullptr;
  }
  return -1;
}

LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvoker(const std::string& script)
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  if (m_shutdownRequested)
    return LanguageInvokerPtr();

  if (m_lastInvokerThread)
  {
    if (m_lastInvokerThread->Reuseable(script))
    {
      CLog::Log(LOGDEBUG, "{} - Reusing LanguageInvokerThread {} for script {}", __FUNCTION__,
                m_lastInvokerThread->GetId(), script);
      m_lastInvokerThread->GetInvoker()->Reset();
      return m_lastInvokerThread->GetInvoker();
    }
    m_lastInvokerThread->Release();
    m_lastInvokerThread = nullptr;
  }

  std::string extension = URIUtils::GetExtension(script);
  StringUtils::ToLower(extension);

  std::map<std::string, ILanguageInvocationHandler*>::const_iterator it = m_invocationHandlers.find(extension);
  if (it != m_invocationHandlers.end() && it->second != NULL)
    return LanguageInvokerPtr(it->second->CreateInvoker());

  return LanguageInvokerPtr();
}

int CScriptInvocationManager::ExecuteAsync(
    const std::string& script,
    const ADDON::AddonPtr& addon /* = ADDON::AddonPtr() */,
    const std::vector<std::string>& arguments /* = std::vector<std::string>() */,
    bool reuseable /* = false */,
    int pluginHandle /* = -1 */)
{
  if (script.empty())
    return -1;

  if (!CFileUtils::Exists(script, false))
  {
    CLog::Log(LOGERROR, "{} - Not executing non-existing script {}", __FUNCTION__, script);
    return -1;
  }

  LanguageInvokerPtr invoker = GetLanguageInvoker(script);
  return ExecuteAsync(script, invoker, addon, arguments, reuseable, pluginHandle);
}

int CScriptInvocationManager::ExecuteAsync(
    const std::string& script,
    const LanguageInvokerPtr& languageInvoker,
    const ADDON::AddonPtr& addon /* = ADDON::AddonPtr() */,
    const std::vector<std::string>& arguments /* = std::vector<std::string>() */,
    bool reuseable /* = false */,
    int pluginHandle /* = -1 */)
{
  if (script.empty() || languageInvoker == NULL)
    return -1;

#if defined(TARGET_ANDROID)
  if (addon && InfinityAddonQuarantine::ShouldSuppress(addon->ID(), script))
  {
    CLog::Log(LOGINFO, "Infinity quarantine: suppressing failing background service {}", addon->ID());
    return -1;
  }
#endif

  if (!CFileUtils::Exists(script, false))
  {
    CLog::Log(LOGERROR, "{} - Not executing non-existing script {}", __FUNCTION__, script);
    return -1;
  }

  std::string checkpointContract;
#if defined(TARGET_ANDROID)
  if (!reuseable)
    checkpointContract = InfinityAndroidCheckpoint::ClassifyScript(script, addon ? addon->ID() : "");
#endif
  std::unique_lock<CCriticalSection> lock(m_critSection);
  if (m_shutdownRequested)
    return -1;

#if defined(TARGET_ANDROID)
  // Capture before Execute can finish (or fail) and before Process may erase
  // the invoker. A completed unknown interpreter is still an unproved writer.
  if (checkpointContract.empty() && m_checkpointUnresolvedWriterLedger.size() < 8)
    m_checkpointUnresolvedWriterLedger.push_back(
        (addon ? addon->ID() : "unidentified") + ":" + URIUtils::GetFileName(script));
#endif

  if (m_lastInvokerThread && m_lastInvokerThread->GetInvoker() == languageInvoker)
  {
    if (addon != NULL)
      m_lastInvokerThread->SetAddon(addon);

    // Keep dispatch serialized with BeginShutdown; no script join occurs here.
    CLanguageInvokerThreadPtr invokerThread = m_lastInvokerThread;
    const auto existing = m_scripts.find(invokerThread->GetId());
    if (existing != m_scripts.end())
      existing->second.checkpointContract = checkpointContract;
#if defined(TARGET_ANDROID)
    if (checkpointContract.empty())
      InfinityScriptPersistence::Admit(invokerThread->GetId(),
        (addon ? addon->ID() : "unidentified") + ":" + URIUtils::GetFileName(script));
#endif
    invokerThread->Execute(script, arguments);

    return invokerThread->GetId();
  }

  m_lastInvokerThread = std::make_shared<CLanguageInvokerThread>(languageInvoker, this, reuseable);
  if (m_lastInvokerThread == NULL)
    return -1;

  if (addon != NULL)
    m_lastInvokerThread->SetAddon(addon);

  m_lastInvokerThread->SetId(m_nextId++);
  m_lastPluginHandle = pluginHandle;

  LanguageInvokerThread thread = {m_lastInvokerThread, script, false, checkpointContract};
  m_scripts.insert(std::make_pair(m_lastInvokerThread->GetId(), thread));
  m_scriptPaths.insert(std::make_pair(script, m_lastInvokerThread->GetId()));
  // Create signals its start event before running the script. Do not let
  // BeginShutdown pass this registration before the thread is actually started.
  CLanguageInvokerThreadPtr invokerThread = m_lastInvokerThread;
#if defined(TARGET_ANDROID)
  if (checkpointContract.empty())
    InfinityScriptPersistence::Admit(invokerThread->GetId(),
      (addon ? addon->ID() : "unidentified") + ":" + URIUtils::GetFileName(script));
#endif
  invokerThread->Execute(script, arguments);

  return invokerThread->GetId();
}

int CScriptInvocationManager::ExecuteSync(
    const std::string& script,
    const ADDON::AddonPtr& addon /* = ADDON::AddonPtr() */,
    const std::vector<std::string>& arguments /* = std::vector<std::string>() */,
    uint32_t timeoutMs /* = 0 */,
    bool waitShutdown /* = false */)
{
  if (script.empty())
    return -1;

  if (!CFileUtils::Exists(script, false))
  {
    CLog::Log(LOGERROR, "{} - Not executing non-existing script {}", __FUNCTION__, script);
    return -1;
  }

  LanguageInvokerPtr invoker = GetLanguageInvoker(script);
  return ExecuteSync(script, invoker, addon, arguments, timeoutMs, waitShutdown);
}

int CScriptInvocationManager::ExecuteSync(
    const std::string& script,
    const LanguageInvokerPtr& languageInvoker,
    const ADDON::AddonPtr& addon /* = ADDON::AddonPtr() */,
    const std::vector<std::string>& arguments /* = std::vector<std::string>() */,
    uint32_t timeoutMs /* = 0 */,
    bool waitShutdown /* = false */)
{
  int scriptId = ExecuteAsync(script, languageInvoker, addon, arguments);
  if (scriptId < 0)
    return -1;

  bool timeout = timeoutMs > 0;
  while ((!timeout || timeoutMs > 0) && IsRunning(scriptId))
  {
    unsigned int sleepMs = 100U;
    if (timeout && timeoutMs < sleepMs)
      sleepMs = timeoutMs;

    KODI::TIME::Sleep(std::chrono::milliseconds(sleepMs));

    if (timeout)
      timeoutMs -= sleepMs;
  }

  if (IsRunning(scriptId))
  {
    Stop(scriptId, waitShutdown);
    return ETIMEDOUT;
  }

  return 0;
}

bool CScriptInvocationManager::Stop(int scriptId, bool wait /* = false */)
{
  if (scriptId < 0)
    return false;

  std::unique_lock<CCriticalSection> lock(m_critSection);
  CLanguageInvokerThreadPtr invokerThread = getInvokerThread(scriptId).thread;
  if (invokerThread == NULL)
    return false;

  // Stop pumps messages and may join a thread whose OnExit needs this registry.
  // The shared pointer retains ownership while callbacks remove map entries.
  lock.unlock();
  return invokerThread->Stop(wait);
}

void CScriptInvocationManager::StopRunningScripts(bool wait /* = false */)
{
  InfinityShutdownTrace::Scope methodEvidence("scripts.stop_pass", -1, nullptr, nullptr);
  std::vector<CLanguageInvokerThreadPtr> pending;
  {
    std::unique_lock<CCriticalSection> lock(m_critSection);
    for (const auto& it : m_scripts)
    {
      if (!it.second.done)
        pending.push_back(it.second.thread);
    }
  }
  // A stop can pump Process() and erase the registry. Iterate retained owners.
  for (const auto& thread : pending)
    thread->Stop(wait);
}

bool CScriptInvocationManager::Stop(const std::string &scriptPath, bool wait /* = false */)
{
  if (scriptPath.empty())
    return false;

  std::unique_lock<CCriticalSection> lock(m_critSection);
  std::map<std::string, int>::const_iterator script = m_scriptPaths.find(scriptPath);
  if (script == m_scriptPaths.end())
    return false;

  const int scriptId = script->second;
  lock.unlock();
  return Stop(scriptId, wait);
}

bool CScriptInvocationManager::IsRunning(int scriptId) const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  LanguageInvokerThread invokerThread = getInvokerThread(scriptId);
  if (invokerThread.thread == NULL)
    return false;

  return !invokerThread.done;
}

bool CScriptInvocationManager::IsRunning(const std::string& scriptPath) const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  auto it = m_scriptPaths.find(scriptPath);
  if (it == m_scriptPaths.end())
    return false;

  return IsRunning(it->second);
}

void CScriptInvocationManager::OnExecutionDone(int scriptId)
{
  if (scriptId < 0)
    return;

  std::string quarantineAddon;
  std::string quarantineScript;
  std::string checkpointAddon;
  std::string checkpointScript;
  bool quarantineFailure = false;
  bool quarantineSuccess = false;
  bool checkpointEscalated = false;
  bool checkpointRetired = false;
  std::unique_lock<CCriticalSection> lock(m_critSection);
  LanguageInvokerThreadMap::iterator script = m_scripts.find(scriptId);
  if (script != m_scripts.end())
  {
#if defined(TARGET_ANDROID)
    const bool cleanUncaughtFailure = InfinityScriptPersistence::AdvisoryInterpreterRetirement(
        scriptId, "uncaught_script_failure_before_persistence_receipt");
    const bool retired = InfinityScriptPersistence::TakeInterpreterRetirement(scriptId);
    checkpointEscalated = m_androidCheckpointEscalatedIds.erase(scriptId) != 0;
    if (checkpointEscalated)
    {
      const auto& addon = script->second.thread->GetAddon();
      checkpointAddon = addon ? addon->ID() : "unidentified";
      checkpointScript = URIUtils::GetFileName(script->second.script);
      checkpointRetired = retired;
    }
    if (InfinityAndroidCheckpoint::IsActive() &&
        VerifiedCheckpointContract(script->second.script, script->second.thread, script->second.checkpointContract).empty())
    {
      // Preserve the originating failure instead of blaming whichever healthy
      // Command Center/client invocation happens to finish next.
      const auto failure = InfinityScriptPersistence::Failure();
      if (!failure.empty())
        InfinityAndroidCheckpoint::RecordFailure("python_services", failure.c_str());
      else if (!retired)
      {
        const std::string addon = script->second.thread->GetAddon() ?
            script->second.thread->GetAddon()->ID() : "unidentified";
        const std::string detail = "foreign_invoker_finished_without_persistence_receipt;id=" +
            std::to_string(scriptId) + ";addon=" + addon +
            ";script=" + URIUtils::GetFileName(script->second.script);
        InfinityAndroidCheckpoint::RecordFailure("python_services", detail.c_str());
      }
    }
    if (retired && script->second.thread->GetAddon() &&
        URIUtils::GetFileName(script->second.script) == "service.py")
    {
      quarantineAddon = script->second.thread->GetAddon()->ID();
      quarantineScript = script->second.script;
      quarantineFailure = cleanUncaughtFailure;
      // A service that required checkpoint escalation did not demonstrate a
      // normal clean lifetime. Do not use shutdown force as evidence that a
      // previously quarantined add-on is healthy again.
      quarantineSuccess = !cleanUncaughtFailure && !checkpointEscalated;
    }
#endif
    script->second.done = true;
  }
  lock.unlock();
#if defined(TARGET_ANDROID)
  if (checkpointEscalated)
    InfinityShutdownTrace::Event("milestone", "scripts.checkpoint_escalated_retired", scriptId,
                                 0, 0, 0, checkpointAddon.c_str(),
                                 checkpointRetired ? "durable_retirement" : "retirement_without_receipt",
                                 checkpointScript.c_str());
  if (quarantineFailure)
    InfinityAddonQuarantine::RecordCleanFailure(quarantineAddon, quarantineScript);
  else if (quarantineSuccess)
    InfinityAddonQuarantine::RecordCleanSuccess(quarantineAddon, quarantineScript);
#endif
}

CScriptInvocationManager::LanguageInvokerThread CScriptInvocationManager::getInvokerThread(int scriptId) const
{
  if (scriptId < 0)
    return LanguageInvokerThread();

  LanguageInvokerThreadMap::const_iterator script = m_scripts.find(scriptId);
  if (script == m_scripts.end())
    return LanguageInvokerThread();

  return script->second;
}
