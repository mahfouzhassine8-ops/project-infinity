#!/usr/bin/env python3
"""Backport Kodi's Android/webOS Python thread-state fix to Infinity's exact Kodi 21.3 tree.

Upstream provenance:
  xbmc/xbmc PR #27320
  merge 0186f895271d4ce7d240b4e9f40da03b4833539d
  implementation 1ea5ca953ed91ca6dabe1c925547658c0f99949b

Infinity adds one narrow race guard at the exact 21.3 crash site observed in device diagnostics:
CPythonInvoker::execute() temporarily drops m_critical while waiting for child threads. If another
cleanup path clears m_threadState during that window, the stock 21.3 code calls clearPendingCalls()
and then aborts on assert(m_threadState != nullptr). Recheck under m_critical before touching it.

This patch changes only Kodi's Python invoker/runtime ownership. It does not change the Android
presentation layer, Cobra playback, renderer, skin, provider data, or Candidate 14.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

FILES = {
    "invoker_cpp": Path("xbmc/interfaces/python/PythonInvoker.cpp"),
    "invoker_h": Path("xbmc/interfaces/python/PythonInvoker.h"),
    "python_cpp": Path("xbmc/interfaces/python/XBPython.cpp"),
    "python_h": Path("xbmc/interfaces/python/XBPython.h"),
}
UPSTREAM_BASE = "a3a448d26b8d560a65655dab2cd122994dc4e146"
UPSTREAM_FIX = "0186f895271d4ce7d240b4e9f40da03b4833539d"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def once(text: str, old: str, new: str, label: str) -> str:
    count=text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact anchor, found {count}")
    return text.replace(old,new,1)

def patch_invoker_h(text: str) -> str:
    return once(
        text,
        "  PyThreadState* m_threadState;\n  bool m_stop = false;\n",
        "  PyThreadState* m_threadState;\n  // Thread state in the main interpreter owned by this invoker thread only.\n"
        "  PyThreadState* m_mainThreadState{nullptr};\n  bool m_stop = false;\n",
        "per-invoker main-thread state field",
    )

def patch_python_h(text: str) -> str:
    text=once(text,
        "class CPythonInvoker;\nclass CVariant;\n\ntypedef struct\n",
        "class CPythonInvoker;\nclass CVariant;\n\ntypedef struct _ts PyThreadState;\n\ntypedef struct\n",
        "PyThreadState forward declaration")
    text=once(text,
        "  ILanguageInvoker* CreateInvoker() override;\n\n  bool WaitForEvent",
        "  ILanguageInvoker* CreateInvoker() override;\n\n"
        "  PyThreadState* GetMainThreadState() const { return m_mainThreadState; }\n\n"
        "  bool WaitForEvent",
        "main-thread state getter")
    return once(text,
        "  CCriticalSection m_critSection;\n  void* m_mainThreadState{nullptr};\n",
        "  CCriticalSection m_critSection;\n  PyThreadState* m_mainThreadState{nullptr};\n",
        "typed main-thread state")

def patch_python_cpp(text: str) -> str:
    text=once(text,
        "\n// Only required for Py3 < 3.7\nPyThreadState* savestate;\n",
        "\n",
        "obsolete global savestate")
    text=once(text,
'''#if PY_VERSION_HEX >= 0x03070000
  if (Py_IsInitialized())
  {
    // Switch to the main interpreter thread before finalizing
    PyThreadState_Swap(PyInterpreterState_ThreadHead(PyInterpreterState_Main()));

    // Clear all loaded modules to prevent circular references
    PyObject* modules = PyImport_GetModuleDict();
    PyDict_Clear(modules);

    Py_Finalize();
  }
#endif''',
'''  if (Py_IsInitialized())
  {
    // Use the exact state captured by OnScriptInitialized. Borrowing an arbitrary
    // thread from the main interpreter is unsafe on Android during finalization.
    PyThreadState_Swap(m_mainThreadState);

    // Clear all loaded modules to prevent circular references
    PyObject* modules = PyImport_GetModuleDict();
    PyDict_Clear(modules);

    Py_Finalize();
  }''',
        "XBPython finalization ownership")
    return once(text,
'''    Py_Initialize();

#if PY_VERSION_HEX < 0x03070000
    // Python >= 3.7 Py_Initialize implicitly calls PyEval_InitThreads
    // Python < 3.7 we have to manually call initthreads.
    // PyEval_InitThreads is a no-op on subsequent calls, No need to wrap in
    // PyEval_ThreadsInitialized() check
    PyEval_InitThreads();
#endif

    // Acquire GIL if thread doesn't currently hold.
    if (!PyGILState_Check())
      PyEval_RestoreThread((PyThreadState*)m_mainThreadState);

    if (!(m_mainThreadState = PyThreadState_Get()))
      CLog::Log(LOGERROR, "Python threadstate is NULL.");
    savestate = PyEval_SaveThread();''',
'''    Py_Initialize();
    // Capture the main interpreter state on the thread that initialized Python.
    // Every invoker creates its own temporary state from this interpreter.
    m_mainThreadState = PyEval_SaveThread();''',
        "XBPython main-state initialization")

def patch_invoker_cpp(text: str) -> str:
    text=once(text,
        "#include <osdefs.h>\n// clang-format on\n\n#include <cassert>\n",
        "#include <osdefs.h>\n// clang-format on\n\n#include \"XBPython.h\"\n\n#include <cassert>\n",
        "XBPython include")
    text=once(text,
'''    if (!m_threadState)
    {
#if PY_VERSION_HEX < 0x03070000
      // this is a TOTAL hack. We need the GIL but we need to borrow a PyThreadState in order to get it
      // as of Python 3.2 since PyEval_AcquireLock is deprecated
      extern PyThreadState* savestate;
      PyEval_RestoreThread(savestate);
#else
      PyThreadState* ts = PyInterpreterState_ThreadHead(PyInterpreterState_Main());
      PyEval_RestoreThread(ts);
#endif
      l_threadState = Py_NewInterpreter();
      PyEval_ReleaseThread(l_threadState);
      if (l_threadState == NULL)
      {
        CLog::Log(LOGERROR, "CPythonInvoker({}, {}): FAILED to get thread m_threadState!", GetId(),
                  m_sourceFile);
        return false;
      }
      newInterp = true;
    }''',
'''    if (!m_threadState)
    {
      PyThreadState* owner = CServiceBroker::GetXBPython().GetMainThreadState();
      if (owner == nullptr)
      {
        CLog::LogF(LOGERROR, "({}, {}) Python main thread state unavailable", GetId(), m_sourceFile);
        return false;
      }

      m_mainThreadState = PyThreadState_New(owner->interp);
      if (m_mainThreadState == nullptr)
      {
        CLog::LogF(LOGERROR, "({}, {}) PyThreadState_New failed", GetId(), m_sourceFile);
        return false;
      }

      PyThreadState_Swap(m_mainThreadState);
      l_threadState = Py_NewInterpreter();
      if (l_threadState != nullptr)
        PyEval_ReleaseThread(l_threadState);
      if (l_threadState == nullptr)
      {
        CLog::Log(LOGERROR, "CPythonInvoker({}, {}): FAILED to get thread m_threadState!", GetId(),
                  m_sourceFile);
        PyThreadState_Swap(m_mainThreadState);
        PyThreadState_Clear(m_mainThreadState);
        PyThreadState_DeleteCurrent();
        m_mainThreadState = nullptr;
        return false;
      }
      newInterp = true;
    }''',
        "new interpreter thread-state ownership")

    text=once(text,
'''      PyEval_RestoreThread((PyThreadState*)m_threadState);

      //tell xbmc.Monitor to call onAbortRequested()
      if (m_addon)
      {
        CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): trigger Monitor abort request", GetId(),
                  m_sourceFile);
        AbortNotification();
      }

      PyEval_ReleaseThread(m_threadState);''',
'''      PyThreadState* ts = PyThreadState_New(m_threadState->interp);
      if (ts == nullptr)
      {
        CLog::LogF(LOGERROR, "({}, {}) PyThreadState_New failed", GetId(), m_sourceFile);
        return false;
      }

      PyEval_RestoreThread(ts);

      //tell xbmc.Monitor to call onAbortRequested()
      if (m_addon)
      {
        CLog::Log(LOGDEBUG, "CPythonInvoker({}, {}): trigger Monitor abort request", GetId(),
                  m_sourceFile);
        AbortNotification();
      }

      PyThreadState_Clear(ts);
      PyThreadState_DeleteCurrent();''',
        "stop running temporary thread state")

    text=once(text,
'''    if (m_threadState != NULL)
    {
      {
        // grabbing the PyLock while holding the m_critical is asking for a deadlock
        CSingleExit ex2(m_critical);
        PyEval_RestoreThread((PyThreadState*)m_threadState);
      }


      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);''',
'''    if (m_threadState != NULL)
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
        PyEval_RestoreThread(ts);
      }

      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);''',
        "stop cleanup temporary thread state")
    text=once(text,
'''      // If a dialog entered its doModal(), we need to wake it to see the exception
      pulseGlobalEvent();

      PyEval_ReleaseThread(m_threadState);''',
'''      // If a dialog entered its doModal(), we need to wake it to see the exception
      pulseGlobalEvent();

      PyThreadState_Clear(ts);
      PyThreadState_DeleteCurrent();''',
        "stop cleanup temporary thread release")

    # Device crash guard: execute() released m_critical while waiting for child threads.
    text=once(text,
'''  // pending calls must be cleared out
  XBMCAddon::RetardedAsyncCallbackHandler::clearPendingCalls(m_threadState);

  assert(m_threadState != nullptr);
  PyEval_ReleaseThread(m_threadState);''',
'''  // The child-thread wait above temporarily releases m_critical. A concurrent abort/finalization
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
  PyEval_ReleaseThread(m_threadState);''',
        "device-observed line-412 abort guard")

    text=once(text,
'''#if PY_VERSION_HEX < 0x03070000
    PyEval_ReleaseLock();
#else
    PyThreadState_Swap(PyInterpreterState_ThreadHead(PyInterpreterState_Main()));
    PyEval_SaveThread();
#endif''',
'''    PyThreadState_Swap(m_mainThreadState);
    PyThreadState_Clear(m_mainThreadState);
    PyThreadState_DeleteCurrent();
    m_mainThreadState = nullptr;''',
        "invoker finalization owner release")
    return text

def verify(source: Path) -> dict:
    source=source.resolve()
    text={key:(source/path).read_text() for key,path in FILES.items()}
    cpp=text["invoker_cpp"]; ih=text["invoker_h"]; xcpp=text["python_cpp"]; xh=text["python_h"]
    checks={
        "upstream_main_state_getter":"GetMainThreadState() const" in xh,
        "upstream_typed_main_state":"PyThreadState* m_mainThreadState{nullptr};" in xh,
        "invoker_owns_main_state":"PyThreadState* m_mainThreadState{nullptr};" in ih,
        "new_interpreter_uses_owned_state":"PyThreadState_New(owner->interp)" in cpp,
        "stop_uses_temporary_state":cpp.count("PyThreadState_New(m_threadState->interp)") >= 2,
        "temporary_states_deleted":cpp.count("PyThreadState_DeleteCurrent();") >= 4,
        "finalization_uses_owned_state":"PyThreadState_Swap(m_mainThreadState);" in cpp,
        "xbpython_finalization_uses_saved_state":"PyThreadState_Swap(m_mainThreadState);" in xcpp,
        "xbpython_init_saves_state":"m_mainThreadState = PyEval_SaveThread();" in xcpp,
        "no_arbitrary_main_thread_borrow":"PyInterpreterState_ThreadHead(PyInterpreterState_Main())" not in cpp,
        "no_global_savestate":"savestate" not in xcpp and "savestate" not in cpp,
        "device_abort_guard":"thread state cleaned while waiting for child threads" in cpp,
        "line412_assert_removed":"assert(m_threadState != nullptr)" not in cpp,
        "guard_precedes_pending_clear":cpp.index("thread state cleaned while waiting for child threads") < cpp.index("RetardedAsyncCallbackHandler::clearPendingCalls(m_threadState)"),
        # Existing Infinity refcount hardening must coexist with this backport.
        "module_refcount_hardening_preserved":"setModuleItem" in cpp,
        "pyobject_deleter_assert_absent":"assert(Py_REFCNT(p) == 2)" not in cpp,
    }
    failed=[k for k,v in checks.items() if not v]
    if failed: raise RuntimeError("Python invoker hardening verification failed: "+", ".join(failed))
    return {
      "schema":1,"kodi_base":UPSTREAM_BASE,"upstream_fix":UPSTREAM_FIX,
      "failure_class":"pythoninvoker_threadstate_native_abort",
      "device_assertion":"m_threadState != nullptr",
      "native_rebuild_required":True,"candidate14_modified":False,
      "checks":checks,"files":{str(path):sha(source/path) for path in FILES.values()}
    }

def apply(source: Path, receipt: Path) -> None:
    source=source.resolve()
    paths={k:source/v for k,v in FILES.items()}
    for p in paths.values():
        if not p.is_file(): raise FileNotFoundError(p)
    before={str(FILES[k]):sha(p) for k,p in paths.items()}
    paths["invoker_cpp"].write_text(patch_invoker_cpp(paths["invoker_cpp"].read_text()))
    paths["invoker_h"].write_text(patch_invoker_h(paths["invoker_h"].read_text()))
    paths["python_cpp"].write_text(patch_python_cpp(paths["python_cpp"].read_text()))
    paths["python_h"].write_text(patch_python_h(paths["python_h"].read_text()))
    result=verify(source);result["before"]=before
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PASS: Kodi 21.3 PythonInvoker thread-state ownership backport + device abort guard applied")

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("apply");a.add_argument("--source",type=Path,required=True);a.add_argument("--receipt",type=Path,required=True)
    a=sub.add_parser("verify");a.add_argument("--source",type=Path,required=True)
    args=p.parse_args()
    if args.cmd=="apply":apply(args.source,args.receipt)
    else:
        print(json.dumps(verify(args.source),indent=2,sort_keys=True))
        print("PASS: PythonInvoker thread-state hardening verified")
if __name__=="__main__":main()
