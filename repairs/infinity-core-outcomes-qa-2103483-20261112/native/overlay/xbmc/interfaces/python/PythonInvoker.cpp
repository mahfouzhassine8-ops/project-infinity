/*
 *  Copyright (C) 2013-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

// clang-format off
// python.h should always be included first before any other includes
#include <mutex>
#include <Python.h>
// clang-format on

#include "PythonInvoker.h"
#include "interfaces/generic/InfinityStartupTrace.h"
#if defined(TARGET_ANDROID)
#include "threads/InfinityPythonWaitProbe.h"
#include "threads/InfinityProbeExport.h"
#include "utils/URIUtils.h"
#include <dlfcn.h>
#endif
#if defined(TARGET_ANDROID)
#include "filesystem/InfinityCloseNetworkGate.h"
#endif
#if defined(TARGET_ANDROID)
#include "InfinityServiceStartupWait.h"
#endif
#if defined(TARGET_ANDROID)
#include "InfinityPythonExitEvidence.h"
#include "InfinityPythonPersistence.h"
#include "interfaces/generic/ScriptInvocationManager.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "platform/android/activity/InfinityVfsOpenTrace.h"
#endif
#include "platform/android/activity/InfinityShutdownTrace.h"

#include "ServiceBroker.h"
#include "addons/AddonManager.h"
#include "addons/addoninfo/AddonInfo.h"
#include "addons/addoninfo/AddonType.h"
#include "dialogs/GUIDialogKaiToast.h"
#include "filesystem/SpecialProtocol.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIWindowManager.h"
#include "guilib/LocalizeStrings.h"
#include "interfaces/python/PyContext.h"
#include "interfaces/python/pythreadstate.h"
#include "interfaces/python/swig.h"
#include "messaging/ApplicationMessenger.h"
#include "threads/SingleLock.h"
#include "threads/SystemClock.h"
#include "utils/CharsetConverter.h"
#include "utils/FileUtils.h"
#include "utils/StringUtils.h"
#include "utils/URIUtils.h"
#include "utils/XTimeUtils.h"
#include "utils/log.h"
#include "windowing/GraphicContext.h"

// clang-format off
// This breaks fmt because of SEP define, don't include
// before anything that includes logging
#include <osdefs.h>
// clang-format on

#include "XBPython.h"

#include <cassert>
#include <iterator>

#ifdef TARGET_WINDOWS
extern "C" FILE* fopen_utf8(const char* _Filename, const char* _Mode);
#else
#define fopen_utf8 fopen
#endif

#define GC_SCRIPT \
  "import gc\n" \
  "gc.collect(2)\n"

#define PY_PATH_SEP DELIM

// Time before ill-behaved scripts are terminated
#define PYTHON_SCRIPT_TIMEOUT 5000ms // ms

using namespace XFILE;
using namespace std::chrono_literals;

static const std::string getListOfAddonClassesAsString(
    XBMCAddon::AddonClass::Ref<XBMCAddon::Python::PythonLanguageHook>& languageHook)
{
  std::string message;
  std::unique_lock<CCriticalSection> l(*(languageHook.get()));
  const std::set<XBMCAddon::AddonClass*>& acs = languageHook->GetRegisteredAddonClasses();
  bool firstTime = true;
  for (const auto& iter : acs)
  {
    if (!firstTime)
      message += ",";
    else
      firstTime = false;
    message += iter->GetClassname();
  }

  return message;
}


#if defined(TARGET_ANDROID)
// Invoked ONLY on a native checkpoint's final interpreter retirement path.
// The GIL is already owned by this invoker thread. Never acquire it again.
// threading._shutdown() is CPython's real ordered callback protocol; unlike
// manually clearing private callback lists, it retains callback error semantics.
// A callback blocked in C can still block: fail the native checkpoint honestly,
// rather than hiding the interpreter or forcing thread-state destruction.
static bool InfinityRunRegisteredThreadShutdown(int id, const char* addon)
{
  PyObject *previousType = nullptr, *previousValue = nullptr, *previousTrace = nullptr;
  PyErr_Fetch(&previousType, &previousValue, &previousTrace);
  InfinityShutdownTrace::Event("milestone", "python.runtime.threading_shutdown.begin",
                              id, 0, 0, 0, addon);
  bool success = true;
  PyObject* modules = PyImport_GetModuleDict(); // borrowed, interpreter alive
  if (!modules)
    success = false;
  else
  {
    PyObject* threading = PyDict_GetItemString(modules, "threading"); // borrowed
    if (threading)
    {
      // Hold the imported module while executing callbacks. Never touch it
      // after Py_EndInterpreter(), when the sub-interpreter is destroyed.
      Py_INCREF(threading);
      PyObject* shutdown = PyObject_GetAttrString(threading, "_shutdown");
      if (!shutdown || !PyCallable_Check(shutdown))
        success = false;
      else
      {
        PyObject* result = PyObject_CallNoArgs(shutdown);
        if (!result)
          success = false;
        Py_XDECREF(result);
      }
      Py_XDECREF(shutdown);
      Py_DECREF(threading);
    }
    else if (PyErr_Occurred())
      success = false;
  }
  if (PyErr_Occurred())
    success = false;
  if (!success)
  {
    // Never call PyErr_Clear without first recording an enduring native
    // failure receipt. This explicitly prevents SAFE_TO_TERMINATE.
    InfinityScriptPersistence::Fail(id, "registered_python_thread_shutdown_failed");
    PyErr_Clear(); // prior script exception is restored below
  }
  InfinityShutdownTrace::Event("milestone",
      success ? "python.runtime.threading_shutdown.complete"
              : "python.runtime.threading_shutdown.failed",
      id, 0, 0, 0, addon, success ? "completed" : "failed");
  PyErr_Restore(previousType, previousValue, previousTrace);
  return success;
}
#endif

CPythonInvoker::CPythonInvoker(ILanguageInvocationHandler* invocationHandler)
  : ILanguageInvoker(invocationHandler), m_threadState(NULL)
{
}

CPythonInvoker::~CPythonInvoker()
{
  InfinityShutdownTrace::Scope methodEvidence("python.invoker_destructor", GetId(), nullptr, nullptr);
  // nothing to do for the default invoker used for registration with the
  // CScriptInvocationManager
  if (GetId() < 0)
    return;

  if (GetState() < InvokerStateExecutionDone)
    CLog::Log(LOGDEBUG, "CPythonInvoker({}): waiting for python thread \"{}\" to stop", GetId(),
              (!m_sourceFile.empty() ? m_sourceFile : "unknown script"));
  Stop(true);
  pulseGlobalEvent();

  onExecutionFinalized();
}

bool CPythonInvoker::Execute(
    const std::string& script,
    const std::vector<std::string>& arguments /* = std::vector<std::string>() */)
{
#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::InitializationProgress(GetId(), "native.execute.enter", 0);
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::ExecuteEnter, GetId());
#endif
  if (script.empty())
    return false;

#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::InitializationProgress(GetId(), "native.execute.file_exists", 0);
#endif
  if (!CFileUtils::Exists(script))
  {
    InfinityStartupTrace::Record(InfinityStartupTrace::Stage::ExecuteMissing, GetId());
    CLog::Log(LOGERROR, "CPythonInvoker({}): python script \"{}\" does not exist", GetId(),
              CSpecialProtocol::TranslatePath(script));
    return false;
  }

#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::InitializationProgress(GetId(), "native.handler.initialize", 0);
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::HandlerBegin, GetId());
#endif
  if (!onExecutionInitialized())
  { InfinityStartupTrace::Record(InfinityStartupTrace::Stage::HandlerRejected, GetId()); return false; }

#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::InitializationProgress(GetId(), "native.handler.initialized", 0);
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::HandlerReady, GetId());
#endif
  return ILanguageInvoker::Execute(script, arguments);
}

bool CPythonInvoker::execute(const std::string& script, const std::vector<std::string>& arguments)
{
  std::vector<std::wstring> w_arguments;
  for (const auto& argument : arguments)
  {
    std::wstring w_argument;
    g_charsetConverter.utf8ToW(argument, w_argument, false);
    w_arguments.push_back(w_argument);
  }
  return execute(script, w_arguments);
}

bool CPythonInvoker::execute(const std::string& script, std::vector<std::wstring>& arguments)
{
  // copy the code/script into a local string buffer
  m_sourceFile = script;
#if defined(TARGET_ANDROID)
  // Bind the executing Python service's addon to synchronous Curl reads.
  // No AST inspection, diagnostic-tracer dependence or global network ban.
  InfinityCloseNetworkGate::ScopedOwner infinityNetworkOwner(
      m_addon ? m_addon->ID() : std::string{});
#endif
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Invoker infinityVfsSubject(GetId(),
    true,m_addon?m_addon->ID().c_str():nullptr);
#endif
  std::set<std::string> pythonPath;

  CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): start processing", GetId(), m_sourceFile);

  std::string realFilename(CSpecialProtocol::TranslatePath(m_sourceFile));
  std::string scriptDir = URIUtils::GetDirectory(realFilename);
  URIUtils::RemoveSlashAtEnd(scriptDir);

  // set m_threadState if it's not set.
  PyThreadState* l_threadState = nullptr;
  bool newInterp = false;
  {
    if (!m_threadState)
    {
#if defined(TARGET_ANDROID)
      InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.main_state", 0);
#endif
      PyThreadState* owner = CServiceBroker::GetXBPython().GetMainThreadState();
      if (owner == nullptr)
      {
        InfinityStartupTrace::Record(InfinityStartupTrace::Stage::MainStateMissing, GetId());
        CLog::LogF(LOGERROR, "({}, {}) Python main thread state unavailable", GetId(), m_sourceFile);
        return false;
      }

#if defined(TARGET_ANDROID)
      InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.thread_state", 0);
#endif
      m_mainThreadState = PyThreadState_New(owner->interp);
      if (m_mainThreadState == nullptr)
      {
        InfinityStartupTrace::Record(InfinityStartupTrace::Stage::ThreadStateFailed, GetId());
        CLog::LogF(LOGERROR, "({}, {}) PyThreadState_New failed", GetId(), m_sourceFile);
        return false;
      }

#if defined(TARGET_ANDROID)
      InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.acquire_gil", 0);
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::GilWait, GetId());
#endif
      PyEval_RestoreThread(m_mainThreadState);
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::GilAcquired, GetId());
      m_invokerOwnsGil = true;
#if defined(TARGET_ANDROID)
      InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.create", 0);
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::InterpreterCreate, GetId());
#endif
      l_threadState = Py_NewInterpreter();
      if (l_threadState != nullptr)
      {
#if defined(TARGET_ANDROID)
        InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.created", reinterpret_cast<uintptr_t>(l_threadState->interp));
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::InterpreterCreated, GetId());
#endif
        PyEval_ReleaseThread(l_threadState);
        m_invokerOwnsGil = false;
      }
      if (l_threadState == nullptr)
      {
        InfinityStartupTrace::Record(InfinityStartupTrace::Stage::InterpreterFailed, GetId());
        CLog::Log(LOGERROR, "CPythonInvoker({}, {}): FAILED to get thread m_threadState!", GetId(),
                  m_sourceFile);
        PyThreadState_Clear(m_mainThreadState);
        PyThreadState_DeleteCurrent();
        m_mainThreadState = nullptr;
        m_invokerOwnsGil = false;
        return false;
      }
      newInterp = true;
    }
    else
      l_threadState = m_threadState;
  }

  // get the GIL
#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.restore_gil", reinterpret_cast<uintptr_t>(l_threadState->interp));
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::RestoreGilWait, GetId());
#endif
  PyEval_RestoreThread(l_threadState);
  InfinityStartupTrace::Record(InfinityStartupTrace::Stage::RestoreGilAcquired, GetId());
  m_invokerOwnsGil = true;
  if (newInterp)
  {
    m_languageHook = new XBMCAddon::Python::PythonLanguageHook(l_threadState->interp);
    m_languageHook->RegisterMe();

#if defined(TARGET_ANDROID)
    InfinityScriptPersistence::InitializationProgress(GetId(), "native.kodi_module.initialize", reinterpret_cast<uintptr_t>(l_threadState->interp));
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::KodiInitialize, GetId());
#endif
    onInitialization();
#if defined(TARGET_ANDROID)
    InfinityScriptPersistence::InitializationProgress(GetId(), "native.kodi_module.initialized", reinterpret_cast<uintptr_t>(l_threadState->interp));
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::KodiInitialized, GetId());
#endif
    setState(InvokerStateInitialized);

    if (realFilename == m_sourceFile)
      CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): the source file to load is \"{}\"", GetId(),
                m_sourceFile, m_sourceFile);
    else
      CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): the source file to load is \"{}\" (\"{}\")",
                GetId(), m_sourceFile, m_sourceFile, realFilename);

    // get path from script file name and add python path's
    // this is used for python so it will search modules from script path first
    pythonPath.emplace(scriptDir);

    // add all addon module dependencies to path
    if (m_addon)
    {
      std::set<std::string> paths;
      getAddonModuleDeps(m_addon, paths);
      for (const auto& it : paths)
        pythonPath.emplace(it);
    }
    else
    { // for backwards compatibility.
      // we don't have any addon so just add all addon modules installed
      CLog::Log(
          LOGWARNING,
          "CPythonInvoker({}): Script invoked without an addon. Adding all addon "
          "modules installed to python path as fallback. This behaviour will be removed in future "
          "version.",
          GetId());
      ADDON::VECADDONS addons;
      CServiceBroker::GetAddonMgr().GetAddons(addons, ADDON::AddonType::SCRIPT_MODULE);
      for (unsigned int i = 0; i < addons.size(); ++i)
        pythonPath.emplace(CSpecialProtocol::TranslatePath(addons[i]->LibPath()));
    }

    PyObject* sysPath = PySys_GetObject("path");

    std::for_each(pythonPath.crbegin(), pythonPath.crend(),
                  [&sysPath](const auto& path)
                  {
                    PyObject* pyPath = PyUnicode_FromString(path.c_str());
                    PyList_Insert(sysPath, 0, pyPath);

                    Py_DECREF(pyPath);
                  });

    CLog::Log(LOGDEBUG, "CPythonInvoker({}): full python path:", GetId());

    Py_ssize_t pathListSize = PyList_Size(sysPath);

    for (Py_ssize_t index = 0; index < pathListSize; index++)
    {
      if (index == 0 && !pythonPath.empty())
        CLog::Log(LOGDEBUG, "CPythonInvoker({}):   custom python path:", GetId());

      if (index == static_cast<ssize_t>(pythonPath.size()))
        CLog::Log(LOGDEBUG, "CPythonInvoker({}):   default python path:", GetId());

      PyObject* pyPath = PyList_GetItem(sysPath, index);
      CLog::Log(LOGDEBUG, "CPythonInvoker({}):     {}", GetId(), PyUnicode_AsUTF8(pyPath));
    }

    { // set the m_threadState to this new interp
      std::unique_lock<CCriticalSection> lockMe(m_critical);
      m_threadState = l_threadState;
    }
  }
  else
    // swap in my thread m_threadState
    PyThreadState_Swap(m_threadState);

#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::AttachLanguageHook(GetId(),m_languageHook.get());
#endif
  PyObject* sysArgv = PyList_New(0);

  if (arguments.empty())
    arguments.emplace_back(L"");

  CLog::Log(LOGDEBUG, "CPythonInvoker({}): adding args:", GetId());

  for (const auto& arg : arguments)
  {
    PyObject* pyArg = PyUnicode_FromWideChar(arg.c_str(), arg.length());
    PyList_Append(sysArgv, pyArg);
    CLog::Log(LOGDEBUG, "CPythonInvoker({}):  {}", GetId(), PyUnicode_AsUTF8(pyArg));

    Py_DECREF(pyArg);
  }

  PySys_SetObject("argv", sysArgv);
  Py_DECREF(sysArgv);

  CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): entering source directory {}", GetId(), m_sourceFile,
            scriptDir);
  PyObject* module = PyImport_AddModule("__main__");
  PyObject* moduleDict = PyModule_GetDict(module);

#if defined(TARGET_ANDROID)
  // Attach before the cancellation/file-open gate. Admission already created a
  // persistence obligation; abort-before-bytecode must still run the checked
  // observer and interpreter-retirement path. No cancellation-only waiver.
  // BEGIN INFINITY_PREBYTECODE_OBSERVER
#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::InitializationProgress(GetId(), "native.observer.before_start", reinterpret_cast<uintptr_t>(m_threadState->interp));
      InfinityStartupTrace::Record(InfinityStartupTrace::Stage::ObserverBegin, GetId());
#endif
  m_infinityPersistenceObserver = InfinityPythonPersistence::Start(GetId(), m_threadState->interp);
  if (InfinityStartupTrace::Enabled()) InfinityStartupTrace::Record(InfinityStartupTrace::Stage::ObserverReturned, GetId(), PyErr_Occurred() ? 1 : 0);
  // QA observer has no effect on admission, persistence or the Core path.
  if (m_infinityPersistenceObserver && !PyErr_Occurred() && m_addon)
  {
    std::string coreSource = realFilename;
    if (m_addon->ID() == "plugin.video.adulthideout")
    {
      ADDON::AddonPtr coreAddon;
      if (CServiceBroker::GetAddonMgr().GetAddon("service.adulthideout.core", coreAddon, ADDON::OnlyEnabled::CHOICE_NO))
        coreSource = CSpecialProtocol::TranslatePath(coreAddon->LibPath());
      else
        coreSource.clear();
    }
    InfinityCoreQA::Install(GetId(), m_addon->ID(), coreSource,
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver)->globals);
  }
  // END INFINITY_PREBYTECODE_OBSERVER
#endif

  // we need to check if we was asked to abort before we had inited
  bool stopping = false;
  {
    GilSafeSingleLock lock(m_critical);
    stopping = m_stop;
  }

  bool failed = false;
  std::string exceptionType, exceptionValue, exceptionTraceback;
  if (stopping) { InfinityStartupTrace::Record(InfinityStartupTrace::Stage::StoppingBeforeBytecode, GetId()); }
  if (!stopping)
  {
    try
    {
      // run script from file
      // We need to have python open the file because on Windows the DLL that python
      //  is linked against may not be the DLL that xbmc is linked against so
      //  passing a FILE* to python from an fopen has the potential to crash.

      PyObject* pyRealFilename = Py_BuildValue("s", realFilename.c_str());
      FILE* fp = _Py_fopen_obj(pyRealFilename, "rb");
      Py_DECREF(pyRealFilename);

      if (fp != NULL)
      {
        PyObject* f = PyUnicode_FromString(realFilename.c_str());
        PyDict_SetItemString(moduleDict, "__file__", f);


        onPythonModuleInitialization(moduleDict);

        Py_DECREF(f);
        setState(InvokerStateRunning);
        XBMCAddon::Python::PyContext
            pycontext; // this is a guard class that marks this callstack as being in a python context
#if defined(TARGET_ANDROID)
        InfinityPythonWaitProbe::Context* waitProbe=nullptr;
        Dl_info identity{};dladdr(reinterpret_cast<void*>(&InfinityStabilityProbe::Configure),&identity);
        try {
          InfinityStabilityProbe::Configure(CSpecialProtocol::TranslatePath("special://temp/infinity-stability-probe.jsonl"),reinterpret_cast<uintptr_t>(identity.dli_fbase));
          InfinityProbeExport::Install();
        }catch(...){/* Evidence must not prevent an add-on from running. */}
        if(m_addon && m_addon->ID()=="plugin.video.umbrella" && URIUtils::GetFileName(realFilename)=="service.py") {
          waitProbe=InfinityPythonWaitProbe::Start(GetId());
        }
        try {
#endif
          InfinityStartupTrace::Record(InfinityStartupTrace::Stage::BytecodeEnter, GetId());
          executeScript(fp, realFilename, moduleDict);
          if (InfinityStartupTrace::Enabled()) InfinityStartupTrace::Record(InfinityStartupTrace::Stage::BytecodeReturned, GetId(), PyErr_Occurred() ? 1 : 0);
#if defined(TARGET_ANDROID)
        }catch(...){InfinityStartupTrace::Record(InfinityStartupTrace::Stage::BytecodeException, GetId());if(waitProbe)InfinityPythonWaitProbe::BodyReturned();throw;}
        if(waitProbe)InfinityPythonWaitProbe::BodyReturned();
#endif
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.bytecode_return","observed");
#endif
        InfinityShutdownTrace::Event("milestone", "python.bytecode_returned", GetId(), 0, 0, 0,
                                    m_addon ? m_addon->ID().c_str() : nullptr);
      }
      else
        CLog::Log(LOGERROR, "CPythonInvoker({}, {}): {} not found!", GetId(), m_sourceFile,
                  m_sourceFile);
    }
    catch (const XbmcCommons::Exception& e)
    {
      setState(InvokerStateFailed);
      e.LogThrowMessage();
      failed = true;
    }
    catch (...)
    {
      setState(InvokerStateFailed);
      CLog::Log(LOGERROR, "CPythonInvoker({}, {}): failure in script", GetId(), m_sourceFile);
      failed = true;
    }
  }

  if (InfinityStartupTrace::Enabled()) InfinityStartupTrace::Record(InfinityStartupTrace::Stage::ExecutionFinished, GetId(), (failed ? 1 : 0) | (PyErr_Occurred() ? 2 : 0));
  m_systemExitThrown = false;
  InvokerState stateToSet;
  if (!failed && !PyErr_Occurred())
  {
    CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): script successfully run", GetId(), m_sourceFile);
    stateToSet = InvokerStateScriptDone;
    onSuccess();
  }
  else if (PyErr_ExceptionMatches(PyExc_SystemExit))
  {
    m_systemExitThrown = true;
    CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): script aborted", GetId(), m_sourceFile);
    stateToSet = InvokerStateFailed;
#if defined(TARGET_ANDROID)
    // This SystemExit has already been classified as an aborted script. Consume
    // it before onAbort so it cannot masquerade as a later cleanup failure.
    // New callback errors and the persistence ledger remain authoritative.
    PyErr_Clear();
#endif
    onAbort();
  }
  else
  {
#if defined(TARGET_ANDROID)
    if (m_infinityPersistenceObserver)
      InfinityScriptPersistence::Fail(GetId(), "uncaught_script_failure_before_persistence_receipt");
#endif
    stateToSet = InvokerStateFailed;

    // if it failed with an exception we already logged the details
    if (!failed)
    {
      PythonBindings::PythonToCppException* e = NULL;
      if (PythonBindings::PythonToCppException::ParsePythonException(exceptionType, exceptionValue,
                                                                     exceptionTraceback))
        e = new PythonBindings::PythonToCppException(exceptionType, exceptionValue,
                                                     exceptionTraceback);
      else
        e = new PythonBindings::PythonToCppException();

      e->LogThrowMessage();
      delete e;
    }

    onError(exceptionType, exceptionValue, exceptionTraceback);
  }

  std::unique_lock<CCriticalSection> lock(m_critical);
  // no need to do anything else because the script has already stopped
  if (failed)
  {
    setState(stateToSet);
    return true;
  }

  if (m_threadState)
  {
    // The main Python script may have returned before the native close
    // reached BeginAndroidCheckpoint(). Check the cooperative stop flag on
    // *every* wait iteration, not just at python.bytecode_returned.
    // This fixes the ordering deadlock where executor workers need
    // threading._shutdown() to receive their queue exit sentinels.
    for (PyThreadState* old = nullptr; m_threadState != nullptr;)
    {
#if defined(TARGET_ANDROID)
      if (m_infinityPersistenceObserver && InfinityAndroidCheckpoint::IsActive() && m_stop &&
          !m_infinityThreadingShutdownStarted)
      {
        m_infinityThreadingShutdownStarted = true;
        // CPython may join Python child threads and release the GIL; never hold
        // m_critical while executing user registered threading callbacks.
        lock.unlock();
        const bool shutdownCompleted = InfinityRunRegisteredThreadShutdown(
            GetId(), m_addon ? m_addon->ID().c_str() : nullptr);
        lock.lock();
        // In case a callback failed, the durable native owner ledger has
        // already recorded failure. The checkpoint must not authorize exit.
        (void)shutdownCompleted;
        continue;
      }
#endif
      PyThreadState* s = PyInterpreterState_ThreadHead(m_threadState->interp);
      for (; s && s == m_threadState;)
        s = PyThreadState_Next(s);

      if (!s)
      {
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.children_retired",
          "no_other_interpreter_thread_states_observed");
#endif
        break;
      }

      if (old != s)
      {
        CLog::Log(LOGINFO, "CPythonInvoker({}, {}): waiting on thread {}", GetId(), m_sourceFile,
                  (uint64_t)s->thread_id);
        old = s;
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.children_wait","other_interpreter_thread_state_observed");
#endif
        char target[32]{};
        std::snprintf(target, sizeof(target), "%lu", s->thread_id);
        InfinityShutdownTrace::Event("milestone", "python.child_thread_wait", GetId(), 0, 0, 0,
                                    m_addon ? m_addon->ID().c_str() : nullptr,
                                    "waiting", target);
      }

      lock.unlock();
      CPyThreadState pyState;
      KODI::TIME::Sleep(100ms);
      pyState.Restore();
      lock.lock();
    }
  }

  // The child-thread wait above temporarily releases m_critical. A concurrent abort/finalization
  // may legitimately clear m_threadState while that lock is dropped. Stock Kodi 21.3 asserts here
  // and SIGABRTs; recheck now that m_critical is held again before touching the state.
  if (m_threadState == nullptr)
  {
    CLog::Log(LOGWARNING,
              "CPythonInvoker({}, {}): thread state cleaned while waiting for child threads; "
              "skipping duplicate pending-call/release cleanup",
              GetId(), m_sourceFile);
    return true;
  }

  // pending calls must be cleared out
  XBMCAddon::RetardedAsyncCallbackHandler::clearPendingCalls(m_threadState);
  PyEval_ReleaseThread(m_threadState);
  m_invokerOwnsGil = false;

  setState(stateToSet);

  return true;
}

void CPythonInvoker::executeScript(FILE* fp, const std::string& script, PyObject* moduleDict)
{
  if (fp == NULL || script.empty() || moduleDict == NULL)
    return;

  #if defined(TARGET_ANDROID)
  if (InfinityServiceStartupWait::TryExecute(fp, script,
      m_addon ? m_addon->ID() : std::string{}, moduleDict))
    return;
  #endif

  int m_Py_file_input = Py_file_input;
  PyRun_FileExFlags(fp, script.c_str(), m_Py_file_input, moduleDict, moduleDict, 1, NULL);
}

FILE* CPythonInvoker::PyFile_AsFileWithMode(PyObject* py_file, const char* mode)
{
  PyObject* ret = PyObject_CallMethod(py_file, "flush", "");
  if (ret == NULL)
    return NULL;
  Py_DECREF(ret);

  int fd = PyObject_AsFileDescriptor(py_file);
  if (fd == -1)
    return NULL;

  FILE* f = fdopen(fd, mode);
  if (f == NULL)
  {
    PyErr_SetFromErrno(PyExc_OSError);
    return NULL;
  }

  return f;
}

bool CPythonInvoker::stop(bool abort)
{
#if defined(TARGET_ANDROID)
  {
    // This exact branch already holds the GIL for registered cleanup. Prevent
    // concurrent Stop(true) escalation from injecting SystemExit into
    // callbacks or re-entering the invoker while finalization is in progress.
    // Use m_critical, which also protects flag mutation in the C++ wait loop.
    std::unique_lock<CCriticalSection> finalizerGuard(m_critical);
    if (m_infinityThreadingShutdownStarted)
    {
      m_stop = true;
      return true; // The owning CLanguageInvokerThread still joins normally.
    }
  }
#endif
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Request(GetId(),abort?"escalation_stop_called":"cooperative_stop_called");
#endif
  InfinityShutdownTrace::Scope methodEvidence("python.stop", GetId(), nullptr, nullptr);
  InfinityShutdownTrace::Scope lockEvidence("python.stop.lock", GetId());
  std::unique_lock<CCriticalSection> lock(m_critical);
  lockEvidence.End();
#if defined(TARGET_ANDROID)
  if (!abort && InfinityAndroidCheckpoint::IsActive())
  {
    // Checkpoint retirement needs both generations of service API.
    // ScriptInvocationManager already sent the proven Monitor notification;
    // legacy xbmc.abortRequested() observes m_stop here. Do not wait and never
    // reach the SystemExit escalation below; persistence finalization remains
    // the authority after bytecode returns.
    m_stop = true;
    InfinityVfsOpenTrace::Request(GetId(),"legacy_abort_flag_set");
    if (!IsRunning() && !m_threadState)
      return false;
    if (m_threadState != NULL && IsRunning())
      setState(InvokerStateStopping);
    return true;
  }
#endif
  m_stop = true;
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Request(GetId(),"legacy_abort_flag_set");
#endif

  if (!IsRunning() && !m_threadState)
    return false;

  if (m_threadState != NULL)
  {
    if (IsRunning())
    {
      setState(InvokerStateStopping);
      lock.unlock();

      if (!CServiceBroker::GetXBPython().IsShutdownRequested())
      {
        PyThreadState* ts = PyThreadState_New(m_threadState->interp);
        if (ts == nullptr)
        {
          CLog::LogF(LOGERROR, "({}, {}) PyThreadState_New failed", GetId(), m_sourceFile);
          return false;
        }

        {
          InfinityShutdownTrace::Scope gilEvidence("python.abort.gil_acquire", GetId());
          PyEval_RestoreThread(ts);
        }

        //tell xbmc.Monitor to call onAbortRequested()
        if (m_addon)
        {
          CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): trigger Monitor abort request", GetId(),
                    m_sourceFile);
          AbortNotification();
        }

        PyThreadState_Clear(ts);
        PyThreadState_DeleteCurrent();
      }
    }
    else
      //Release the lock while waiting for threads to finish
      lock.unlock();

    InfinityShutdownTrace::Scope waitEvidence("python.stop.cooperative_wait", GetId());
    XbmcThreads::EndTime<> timeout(PYTHON_SCRIPT_TIMEOUT);
    while (!m_stoppedEvent.Wait(15ms))
    {
      if (CServiceBroker::GetXBPython().ShutdownGraceExpired())
      {
        CLog::Log(LOGWARNING,
                  "CPythonInvoker({}, {}): shared shutdown grace exhausted; requesting abort",
                  GetId(), m_sourceFile);
        break;
      }
      if (timeout.IsTimePast())
      {
        CLog::Log(LOGERROR,
                  "CPythonInvoker({}, {}): script didn't stop in {} seconds - let's kill it",
                  GetId(), m_sourceFile,
                  std::chrono::duration_cast<std::chrono::seconds>(PYTHON_SCRIPT_TIMEOUT).count());
        break;
      }

      // We can't empty-spin in the main thread and expect scripts to be able to
      // dismantle themselves. Python dialogs aren't normal XBMC dialogs, they rely
      // on TMSG_GUI_PYTHON_DIALOG messages, so pump the message loop.
      if (CServiceBroker::GetAppMessenger()->IsProcessThread())
      {
        CServiceBroker::GetAppMessenger()->ProcessMessages();
      }
    }

    waitEvidence.End();
    InfinityShutdownTrace::Scope relockEvidence("python.stop.relock", GetId());
    lock.lock();
    relockEvidence.End();

    setState(InvokerStateExecutionDone);

    // Useful for add-on performance metrics
    if (!timeout.IsTimePast() && !CServiceBroker::GetXBPython().ShutdownGraceExpired())
      CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): script termination took {}ms", GetId(),
                m_sourceFile, (PYTHON_SCRIPT_TIMEOUT - timeout.GetTimeLeft()).count());

    // Since we released the m_critical it's possible that the state is cleaned up
    // so we need to recheck for m_threadState == NULL
    if (m_threadState != NULL)
    {
      PyThreadState* ts = PyThreadState_New(m_threadState->interp);
      if (ts == nullptr)
      {
        CLog::LogF(LOGERROR, "({}, {}) PyThreadState_New failed", GetId(), m_sourceFile);
        return false;
      }

      {
        // grabbing the PyLock while holding the m_critical is asking for a deadlock
        CSingleExit ex2(m_critical);
        InfinityShutdownTrace::Scope escalationEvidence("python.escalation.gil_acquire", GetId());
        PyEval_RestoreThread(ts);
        escalationEvidence.End();
      }

#if defined(TARGET_ANDROID)
      InfinityPythonExitEvidence::Capture(ts, [this](unsigned long id, const char* file,
                                                     const char* function, int line) {
        char target[65]{};
        std::snprintf(target, sizeof(target), "%lu:%.16s:%d:%.16s", id, file, line, function);
        InfinityShutdownTrace::Event("milestone", "python.exit_frame", GetId(), 0, 0, 0,
                                    m_addon ? m_addon->ID().c_str() : nullptr,
                                    line > 0 ? "frame_observed" : "no_python_frame", target);
      });
#endif
      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);
      while (state)
      {
        // Raise a SystemExit exception in python threads
        Py_XDECREF(state->async_exc);
        state->async_exc = PyExc_SystemExit;
        Py_XINCREF(state->async_exc);
        state = PyThreadState_Next(state);
      }

#if defined(TARGET_ANDROID)
      InfinityVfsOpenTrace::Request(GetId(),"async_python_exception_set");
#endif
      // If a dialog entered its doModal(), we need to wake it to see the exception
      pulseGlobalEvent();

      PyThreadState_Clear(ts);
      PyThreadState_DeleteCurrent();
    }
    lock.unlock();

    setState(InvokerStateFailed);
  }

  return true;
}

// Always called from Invoker thread
void CPythonInvoker::onExecutionDone()
{
  InfinityShutdownTrace::Scope methodEvidence("python.execution_done", GetId(), nullptr, nullptr);
  InfinityShutdownTrace::Scope callbackLock("python.finalize.lock", GetId());
  std::unique_lock<CCriticalSection> lock(m_critical);
  callbackLock.End();
  if (m_threadState != NULL)
  {
    CLog::Log(LOGDEBUG, "{}({}, {})", __FUNCTION__, GetId(), m_sourceFile);

    // execute() normally releases the GIL before this callback, but a caught
    // C++ exception can reach the terminal state while the invoker still owns it.
    // Never acquire the same GIL twice on the invoker thread.
    {
      InfinityShutdownTrace::Scope evidence("python.finalize.gil_guard", GetId(), nullptr, nullptr);
      if (!m_invokerOwnsGil)
    {
      PyEval_RestoreThread(m_threadState);
      m_invokerOwnsGil = true;
    }
    }

    {
      InfinityShutdownTrace::Scope evidence("python.finalize.addon_callback", GetId(), nullptr, nullptr);
      onDeinitialization();
    }

#if defined(TARGET_ANDROID)
    if (m_infinityPersistenceObserver && InfinityAndroidCheckpoint::IsActive() &&
        !m_infinityThreadingShutdownStarted)
    {
      m_infinityThreadingShutdownStarted = true;
      lock.unlock();
      const bool shutdownCompleted = InfinityRunRegisteredThreadShutdown(
          GetId(), m_addon ? m_addon->ID().c_str() : nullptr);
      lock.lock();
      (void)shutdownCompleted; // Failure is kept in native persistence ledger.
    }
    if (m_infinityPersistenceObserver)
    {
      if (PyErr_Occurred())
        InfinityScriptPersistence::Fail(GetId(), "python_cleanup_failed_before_save_retirement");
      PyErr_Clear();
      const bool checkpointEscalated =
          CScriptInvocationManager::GetInstance().AndroidCheckpointWasEscalated(GetId());
      InfinityCoreQA::BeforeFinish(
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver)->globals, m_threadState);
      InfinityPythonPersistence::Finish(
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver),
        m_threadState, checkpointEscalated);
      if (PyErr_Occurred())
        InfinityScriptPersistence::Fail(GetId(), "python_observer_retirement_failed",
                                       checkpointEscalated ?
                                           "checkpoint_escalated_observer_exception" : "");
      PyErr_Clear();
      // Do not destroy an interpreter that still owns an uncommitted transaction
      // or an unflushed buffer. The coordinator fails with a specific save reason;
      // retain that state until an explicit legacy stop or process force-close.
      auto* persistence = static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver);
      while ((persistence->preservePending || persistence->waitingWorkers) &&
             (!m_stop || InfinityAndroidCheckpoint::IsActive()))
      {
        PyEval_ReleaseThread(m_threadState);
        m_invokerOwnsGil = false;
        lock.unlock();
        KODI::TIME::Sleep(100ms);
        PyEval_RestoreThread(m_threadState);
        m_invokerOwnsGil = true;
        lock.lock();
        if (persistence->waitingWorkers)
        {
          InfinityCoreQA::BeforeFinish(persistence->globals, m_threadState);
          InfinityPythonPersistence::Finish(persistence, m_threadState, checkpointEscalated);
          if (PyErr_Occurred())
          {
            InfinityScriptPersistence::Fail(GetId(), "python_worker_retirement_finalization_failed");
            persistence->preservePending = true;
            PyErr_Clear();
          }
        }
      }
    }
#endif
    // Backport Kodi upstream 92315ab: make SWIG/module destruction happen while
    // the sub-interpreter is still fully alive instead of during Py_EndInterpreter.
    {
      InfinityShutdownTrace::Scope evidence("python.finalize.gc_before_modules", GetId(), nullptr, nullptr);
      PyErr_Clear();
    PyGC_Collect();
    }

    {
      InfinityShutdownTrace::Scope evidence("python.finalize.modules_clear", GetId(), nullptr, nullptr);
      PyObject* modules = PyImport_GetModuleDict();
    if (modules)
      PyDict_Clear(modules);
    }

    {
      InfinityShutdownTrace::Scope evidence("python.finalize.gc_after_modules", GetId(), nullptr, nullptr);
      PyGC_Collect();
    PyErr_Clear();
    }

    {
      InfinityShutdownTrace::Scope evidence("python.finalize.end_interpreter", GetId(), nullptr, nullptr);
#if defined(TARGET_ANDROID)
      InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.interpreter_finalize","before_Py_EndInterpreter");
#endif
#if defined(TARGET_ANDROID)
      auto* retiredInterpreter = m_threadState->interp;
#endif
      Py_EndInterpreter(m_threadState);
#if defined(TARGET_ANDROID)
      InfinityPythonWaitProbe::Retired(GetId());
#endif
#if defined(TARGET_ANDROID)
      InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.interpreter_end_return",
        "Py_EndInterpreter_returned_not_durability_proof");
#endif
#if defined(TARGET_ANDROID)
      InfinityPythonPersistence::End(
        static_cast<InfinityPythonPersistence::Context*>(m_infinityPersistenceObserver), retiredInterpreter);
      m_infinityPersistenceObserver = nullptr;
#endif
    }

    // If we still have objects left around, produce an error message detailing what's been left behind
    if (m_languageHook->HasRegisteredAddonClasses())
      CLog::Log(LOGWARNING,
                "CPythonInvoker({}, {}): the python script \"{}\" has left several "
                "classes in memory that we couldn't clean up. The classes include: {}",
                GetId(), m_sourceFile, m_sourceFile, getListOfAddonClassesAsString(m_languageHook));

    // unregister the language hook
    m_languageHook->UnregisterMe();

    PyThreadState_Swap(m_mainThreadState);
    PyThreadState_Clear(m_mainThreadState);
    PyThreadState_DeleteCurrent();
    m_mainThreadState = nullptr;
    m_invokerOwnsGil = false;

    // set stopped event - this allows ::stop to run and kill remaining threads
    // this event has to be fired without holding m_critical
    // also the GIL (PyEval_AcquireLock) must not be held
    // if not obeyed there is still no deadlock because ::stop waits with timeout (smart one!)
    m_stoppedEvent.Set();
#if defined(TARGET_ANDROID)
    InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.stopped_event",
      "existing_event_set_not_native_thread_death");
#endif

    m_threadState = nullptr;
#if defined(TARGET_ANDROID)
    m_infinityThreadingShutdownStarted = false;
#endif

    setState(InvokerStateExecutionDone);
  }
  ILanguageInvoker::onExecutionDone();
}

void CPythonInvoker::onExecutionFailed()
{
  // CThread invokes this for an uncaught C++ exception. Depending on where the
  // exception crossed the Python boundary, the invoker may already have released
  // the GIL. PyEval_SaveThread() without GIL ownership is a fatal CPython error.
  if (m_invokerOwnsGil)
  {
    PyEval_SaveThread();
    m_invokerOwnsGil = false;
  }
  else
  {
    CLog::Log(LOGWARNING,
              "CPythonInvoker({}, {}): failure callback reached without invoker GIL ownership; "
              "skipping PyEval_SaveThread",
              GetId(), m_sourceFile);
  }

  setState(InvokerStateFailed);
  CLog::Log(LOGERROR, "CPythonInvoker({}, {}): abnormally terminating python thread", GetId(),
            m_sourceFile);

  std::unique_lock<CCriticalSection> lock(m_critical);
  m_threadState = NULL;

  ILanguageInvoker::onExecutionFailed();
}

void CPythonInvoker::onInitialization()
{
  XBMC_TRACE;

  // get a possible initialization script
  const char* runscript = getInitializationScript();
  if (runscript != NULL && strlen(runscript) > 0)
  {
    // redirecting default output to debug console
    if (PyRun_SimpleString(runscript) == -1)
      CLog::Log(LOGFATAL, "CPythonInvoker({}, {}): initialize error", GetId(), m_sourceFile);
  }
}

void CPythonInvoker::onPythonModuleInitialization(void* moduleDict)
{
  if (m_addon.get() == NULL || moduleDict == NULL)
    return;

  PyObject* moduleDictionary = (PyObject*)moduleDict;

  // PyDict_SetItemString adds its own reference on success. Keep ownership of the
  // temporary object in PyObjectPtr and always release only that owned reference.
  // A failed insertion therefore remains safe instead of tripping an exact-refcount
  // assertion and aborting the whole Android process.
  const auto setModuleItem = [this, moduleDictionary](const char* key, PyObjectPtr value)
  {
    if (!value)
    {
      CLog::Log(LOGERROR, "CPythonInvoker({}, {}): failed creating module item {}", GetId(),
                m_sourceFile, key);
      PyErr_Clear();
      return false;
    }
    if (PyDict_SetItemString(moduleDictionary, key, value.get()) != 0)
    {
      CLog::Log(LOGERROR, "CPythonInvoker({}, {}): failed setting module item {}", GetId(),
                m_sourceFile, key);
      PyErr_Clear();
      return false;
    }
    return true;
  };

  setModuleItem("__xbmcaddonid__", PyObjectPtr(PyUnicode_FromString(m_addon->ID().c_str())));

  ADDON::CAddonVersion version = m_addon->GetDependencyVersion("xbmc.python");
  setModuleItem("__xbmcapiversion__",
                PyObjectPtr(PyUnicode_FromString(version.asString().c_str())));

  setModuleItem("__xbmcinvokerid__", PyObjectPtr(PyLong_FromLong(GetId())));

  CLog::Log(LOGDEBUG,
            "CPythonInvoker({}, {}): instantiating addon using automatically obtained id of \"{}\" "
            "dependent on version {} of the xbmc.python api",
            GetId(), m_sourceFile, m_addon->ID(), version.asString());
}

void CPythonInvoker::onDeinitialization()
{
  XBMC_TRACE;
}

void CPythonInvoker::onError(const std::string& exceptionType /* = "" */,
                             const std::string& exceptionValue /* = "" */,
                             const std::string& exceptionTraceback /* = "" */)
{
#if defined(TARGET_ANDROID)
  if (m_addon && CScriptInvocationManager::AndroidQuarantineSuppressErrorToast(
                     m_addon->ID(), m_sourceFile))
  {
    CLog::Log(LOGWARNING, "Infinity quarantine probation: suppressed service error toast for {}",
              m_addon->ID());
    return;
  }
#endif
  CPyThreadState releaseGil;
  std::unique_lock<CCriticalSection> gc(CServiceBroker::GetWinSystem()->GetGfxContext());

  CGUIDialogKaiToast* pDlgToast =
      CServiceBroker::GetGUI()->GetWindowManager().GetWindow<CGUIDialogKaiToast>(
          WINDOW_DIALOG_KAI_TOAST);
  if (pDlgToast != NULL)
  {
    std::string message;
    if (m_addon && !m_addon->Name().empty())
      message = StringUtils::Format(g_localizeStrings.Get(2102), m_addon->Name());
    else
      message = g_localizeStrings.Get(2103);
    pDlgToast->QueueNotification(CGUIDialogKaiToast::Error, message, g_localizeStrings.Get(2104));
  }
}

void CPythonInvoker::getAddonModuleDeps(const ADDON::AddonPtr& addon, std::set<std::string>& paths)
{
  for (const auto& it : addon->GetDependencies())
  {
    //Check if dependency is a module addon
    ADDON::AddonPtr dependency;
    if (CServiceBroker::GetAddonMgr().GetAddon(it.id, dependency, ADDON::AddonType::SCRIPT_MODULE,
                                               ADDON::OnlyEnabled::CHOICE_YES))
    {
      std::string path = CSpecialProtocol::TranslatePath(dependency->LibPath());
      if (paths.find(path) == paths.end())
      {
        // add it and its dependencies
        paths.insert(path);
        getAddonModuleDeps(dependency, paths);
      }
    }
  }
}

void CPythonInvoker::PyObjectDeleter::operator()(PyObject* p) const
{
  // PyObjectPtr owns one new reference. The object may have any additional
  // references (for example from a module dictionary), so exact total refcount
  // is not an ownership invariant. Release only the reference we own.
  Py_DECREF(p);
}
