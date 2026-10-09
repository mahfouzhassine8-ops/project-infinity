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

#include <cerrno>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

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
    // Cooperative checkpoint shutdown has two safe parts:
    // 1) notify xbmc.Monitor so running scripts can finish normally;
    // 2) release reusable invoker waits so scripts that already returned can
    //    reach onExecutionDone immediately. This never injects SystemExit,
    //    never joins the GUI thread and never bypasses persistence finalization.
    CServiceBroker::GetXBPython().NotifyScriptAborting(thread.get());
    thread->Release();
  }
#endif
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

  std::unique_lock<CCriticalSection> lock(m_critSection);
  LanguageInvokerThreadMap::iterator script = m_scripts.find(scriptId);
  if (script != m_scripts.end())
  {
#if defined(TARGET_ANDROID)
    const bool retired = InfinityScriptPersistence::TakeInterpreterRetirement(scriptId);
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
#endif
    script->second.done = true;
  }
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
