/*
 *  Copyright (C) 2013-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "LanguageInvokerThread.h"
#include "platform/android/activity/InfinityShutdownTrace.h"

#include "ScriptInvocationManager.h"

#include <utility>
#if defined(TARGET_ANDROID)
#include <cstdio>
#include <sys/syscall.h>
#include <unistd.h>
#endif

CLanguageInvokerThread::CLanguageInvokerThread(LanguageInvokerPtr invoker,
                                               CScriptInvocationManager* invocationManager,
                                               bool reuseable)
  : ILanguageInvoker(NULL),
    CThread("LanguageInvoker"),
    m_invoker(std::move(invoker)),
    m_invocationManager(invocationManager),
    m_reusable(reuseable)
{ }

CLanguageInvokerThread::~CLanguageInvokerThread()
{
  InfinityShutdownTrace::Scope methodEvidence("invoker_thread.destructor", GetId(), nullptr, nullptr);
  Stop(true);
}

InvokerState CLanguageInvokerThread::GetState() const
{
  if (m_invoker == NULL)
    return InvokerStateFailed;

  return m_invoker->GetState();
}

void CLanguageInvokerThread::Release()
{
  m_bStop = true;
  m_condition.notify_one();
}

bool CLanguageInvokerThread::execute(const std::string &script, const std::vector<std::string> &arguments)
{
  if (m_invoker == NULL || script.empty())
    return false;

  m_script = script;
  m_args = arguments;

  if (CThread::IsRunning())
  {
    std::unique_lock<std::mutex> lck(m_mutex);
    m_restart = true;
    m_condition.notify_one();
  }
  else
    Create();

  //Todo wait until running

  return true;
}

bool CLanguageInvokerThread::stop(bool wait)
{
  InfinityShutdownTrace::Scope methodEvidence("invoker_thread.stop", GetId(), nullptr, nullptr);
  if (m_invoker == NULL)
    return false;

  if (!CThread::IsRunning())
    return false;

#if defined(TARGET_ANDROID)
  InfinityTraceTarget("scripts.target_before_stop");
#endif
  Release();

  bool result = true;
  if (m_invoker->GetState() < InvokerStateExecutionDone)
  {
    // stop the language-specific invoker
    {
      InfinityShutdownTrace::Scope evidence("invoker_thread.python_stop", GetId(), nullptr, nullptr);
      result = m_invoker->Stop(wait);
    }
  }
  // stop the thread
#if defined(TARGET_ANDROID)
  InfinityTraceTarget(wait ? "scripts.target_before_join"
                           : "scripts.target_before_nonblocking_stop");
#endif
  {
    InfinityShutdownTrace::Scope evidence("invoker_thread.join", GetId(), nullptr, nullptr);
    CThread::StopThread(wait);
  }

  return result;
}

void CLanguageInvokerThread::OnStartup()
{
#if defined(TARGET_ANDROID)
  {
    InfinityShutdownTrace::PreserveErrno keepErrno;
    m_infinityDiagnosticTarget.Start(static_cast<std::uint32_t>(::syscall(SYS_gettid)));
  }
#endif
  if (m_invoker == NULL)
    return;

  m_invoker->SetId(GetId());
  if (m_addon != NULL)
    m_invoker->SetAddon(m_addon);
}

void CLanguageInvokerThread::Process()
{
  if (m_invoker == NULL)
    return;

#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ProcessMutex);
#endif
  std::unique_lock<std::mutex> lckdl(m_mutex);
  do
  {
    m_restart = false;
#if defined(TARGET_ANDROID)
    m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::Execute);
#endif
    m_invoker->Execute(m_script, m_args);

    if (m_invoker->GetState() != InvokerStateScriptDone)
      m_reusable = false;

#if defined(TARGET_ANDROID)
    m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ReuseWait);
#endif
    m_condition.wait(lckdl, [this] { return m_bStop || m_restart || !m_reusable; });

  } while (m_reusable && !m_bStop);
}

void CLanguageInvokerThread::OnExit()
{
  if (m_invoker == NULL)
    return;

#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::Finalizer);
#endif
  m_invoker->onExecutionDone();
#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ManagerCallback);
#endif
  m_invocationManager->OnExecutionDone(GetId());
#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExitReported);
#endif
}

void CLanguageInvokerThread::OnException()
{
  if (m_invoker == NULL)
    return;

#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExceptionFinalizer);
#endif
  m_invoker->onExecutionFailed();
#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExceptionManagerCallback);
#endif
  m_invocationManager->OnExecutionDone(GetId());
#if defined(TARGET_ANDROID)
  m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExceptionReported);
#endif
}

#if defined(TARGET_ANDROID)
void CLanguageInvokerThread::InfinityTraceTarget(const char* phase) const
{
  InfinityShutdownTrace::PreserveErrno keepErrno;
  const auto snapshot = m_infinityDiagnosticTarget.Read();
  char target[65]{};
  std::snprintf(target, sizeof(target), "os_tid.%u.stage.%s",
                static_cast<unsigned>(snapshot.tid), InfinityInvokerTarget::Name(snapshot.stage));
  // Uses the existing selected scripts.* trace stream and its existing budgets.
  // This does not start capture, create a new file, acquire the GIL, or prove
  // that the sampled thread is still alive. TID and stage are one observation.
  InfinityShutdownTrace::Event("milestone", phase, GetId(), 0, 0, 0,
                              m_addon ? m_addon->ID().c_str() : nullptr,
                              snapshot.tid ? "snapshot_not_liveness" : "target_not_started", target);
}
#endif
