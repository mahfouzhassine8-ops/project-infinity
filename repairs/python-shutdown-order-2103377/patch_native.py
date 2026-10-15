#!/usr/bin/env python3
"""RC1: run CPython's authentic threading shutdown before Kodi's pre-finalization
child-thread polling loop, on the real FINAL native Close path only.

No global CPython monkeypatching, no SetAsyncExc, no bypassed Python writer gate,
no later post-Py_EndInterpreter access and no changes to the locked runtime.
The native coordinator's 17 persistence receipts remain authoritative.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

PYTHON = "xbmc/interfaces/python/PythonInvoker.cpp"
HEADER = "xbmc/interfaces/python/PythonInvoker.h"
UNCHANGED_GATES = (
    "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp",
    "xbmc/platform/android/activity/InfinityScriptPersistence.h",
    "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp",
    "xbmc/interfaces/generic/ScriptInvocationManager.cpp",
    "xbmc/interfaces/python/InfinityPythonPersistence.h",
)
SOURCE_FUNCTION = r'''
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

'''
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def replace_once(text: str, before: str, after: str, key: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"RC1 anchor {key}: expected exactly 1 occurrence; got {count}")
    return text.replace(before, after, 1)

def apply(root: Path, expected_python_sha: str | None = None) -> dict:
    root = Path(root)
    before = {f: (root / f).read_bytes() for f in (PYTHON, HEADER, *UNCHANGED_GATES)}
    if expected_python_sha and sha(before[PYTHON]) != expected_python_sha:
        raise RuntimeError("Refusing different PythonInvoker than verified stability parent")
    p = before[PYTHON].decode("utf-8")
    h = before[HEADER].decode("utf-8")
    assert "InfinityPythonPersistence::Finish(" in p
    assert "Py_EndInterpreter(m_threadState)" in p
    assert "PyDict_Clear(modules)" in p
    assert "python.child_thread_wait" in p
    assert "m_infinityThreadingShutdownStarted" not in p+h
    assert "InfinityRunRegisteredThreadShutdown" not in p
    assert "registered_python_thread_shutdown_failed" not in p

    p = replace_once(
        p,
        "CPythonInvoker::CPythonInvoker(ILanguageInvocationHandler* invocationHandler)",
        SOURCE_FUNCTION + "CPythonInvoker::CPythonInvoker(ILanguageInvocationHandler* invocationHandler)",
        "shutdown_function",
    )
    h = replace_once(
        h, "  bool m_stop = false;\n",
        """  bool m_stop = false;
#if defined(TARGET_ANDROID)
  // Protected by m_critical. Once the final interpreter callback protocol
  // begins, no Stop(true) thread may inject async SystemExit into its cleanup.
  bool m_infinityThreadingShutdownStarted{false};
#endif
""",
        "finalizer_state",
    )
    p = replace_once(
        p,
        '''  m_stop = true;

  if (!IsRunning() && !m_threadState)''',
        '''  m_stop = true;
#if defined(TARGET_ANDROID)
  if (m_infinityThreadingShutdownStarted)
  {
    // CThread::StopThread(true) will still join the real invoker; do not
    // inject SystemExit into legitimate threading callbacks or cleanup writes.
    return true;
  }
#endif

  if (!IsRunning() && !m_threadState)''',
        "no_async_during_final_cleanup",
    )
    p = replace_once(
        p,
        '''    // make sure all sub threads have finished
    for (PyThreadState* old = nullptr; m_threadState != nullptr;)''',
        '''    // The main Python script may have returned before the native close
    // reached BeginAndroidCheckpoint(). Check the cooperative stop flag on
    // *every* wait iteration, not just at python.bytecode_returned.
    // This fixes the ordering deadlock where executor workers need
    // threading._shutdown() to receive their queue exit sentinels.
    for (PyThreadState* old = nullptr; m_threadState != nullptr;)
'''.rstrip(),
        "pre_child_join_loop_comment",
    )
    # The loop's very first operation is our final-close-only protocol.
    p = replace_once(
        p,
        '''    for (PyThreadState* old = nullptr; m_threadState != nullptr;)
    {
      PyThreadState* s = PyInterpreterState_ThreadHead(m_threadState->interp);''',
        '''    for (PyThreadState* old = nullptr; m_threadState != nullptr;)
    {
#if defined(TARGET_ANDROID)
      if (InfinityAndroidCheckpoint::IsActive() && m_stop &&
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
      PyThreadState* s = PyInterpreterState_ThreadHead(m_threadState->interp);''',
        "run_before_child_wait",
    )
    # Finalizing a script with no children can bypass the loop's stop gate if
    # BeginAndroidCheckpoint() started after the last child-state poll.
    # OnExit definitively means the invoker will NOT be reused.
    p = replace_once(
        p,
        '''      onDeinitialization();
    }

#if defined(TARGET_ANDROID)
    if (m_infinityPersistenceObserver)''',
        '''      onDeinitialization();
    }

#if defined(TARGET_ANDROID)
    if (InfinityAndroidCheckpoint::IsActive() && !m_infinityThreadingShutdownStarted)
    {
      m_infinityThreadingShutdownStarted = true;
      lock.unlock();
      const bool shutdownCompleted = InfinityRunRegisteredThreadShutdown(
          GetId(), m_addon ? m_addon->ID().c_str() : nullptr);
      lock.lock();
      (void)shutdownCompleted; // Failure is kept in native persistence ledger.
    }
    if (m_infinityPersistenceObserver)''',
        "run_before_save_observer_if_not_in_loop",
    )
    # stop(true) no longer interrupts callbacks: retire only after the existing
    # Python observer and Py_EndInterpreter finish, not at thread shutdown start.
    p = replace_once(
        p,
        '''    m_threadState = nullptr;

    setState(InvokerStateExecutionDone);''',
        '''    m_threadState = nullptr;
#if defined(TARGET_ANDROID)
    m_infinityThreadingShutdownStarted = false;
#endif

    setState(InvokerStateExecutionDone);''',
        "flag_lifecycle",
    )

    changed = {PYTHON: p.encode(), HEADER: h.encode()}
    for name, new_content in changed.items():
        (root/name).write_bytes(new_content)
    for name in UNCHANGED_GATES:
        if (root/name).read_bytes() != before[name]:
            raise RuntimeError("Required persistence/ownership source modified: "+name)
    after = {f: sha(blob) for f, blob in changed.items()}
    if any(after[f] == sha(before[f]) for f in changed):
        raise RuntimeError("Expected native correction missing")
    return {
        "scope": "Real CPython threading shutdown before child wait / module teardown; native close only",
        "changed": sorted(changed),
        "before": {f: sha(before[f]) for f in changed},
        "after": after,
        "protected": {f: sha(before[f]) for f in UNCHANGED_GATES},
        "early_swig_module_clear_preserved": True,
        "genuine_python_threading_callbacks": True,
        "reusable_script_path_unchanged": True,
        "no_py_end_interpreter_bypass": True,
        "async_watchdog_added": False,
        "python_persistence_authorization_unmodified": True,
        "truly_blocking_callback_still_possible": True,
        "physical_fold_verified": False,
    }
