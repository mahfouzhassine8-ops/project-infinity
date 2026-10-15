#!/usr/bin/env python3
"""2103254: harden PythonInvoker teardown/failure ownership after captured RC4 SIGSEGV.

This layers two narrowly-scoped fixes on top of the already accepted 2103209
Python 3.11 thread-state/GIL repair:

1. Backport Kodi upstream 92315ab07a59938180ed0ddaede73556ee43c57c
   Python sub-interpreter teardown ordering: clear Python error state, run GC,
   clear the sub-interpreter module dict while the interpreter is still valid,
   run GC again, clear errors, then call Py_EndInterpreter().
2. Track whether the invoker thread currently owns Python's GIL. This prevents
   CPythonInvoker::onExecutionFailed() from unconditionally calling
   PyEval_SaveThread() after an exception that happened while the GIL was
   already released, the device-observed fatal class that can recurse into
   CPython fatal-error reporting.

No Android UI/player/provider/timeshift/Cobra behavior is changed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INVOKER = Path("xbmc/interfaces/python/PythonInvoker.cpp")
INVOKER_H = Path("xbmc/interfaces/python/PythonInvoker.h")
UPSTREAM_TEARDOWN = "92315ab07a59938180ed0ddaede73556ee43c57c"
CAPTURED_ENGINE_SHA = "db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected one exact anchor, found {count}")
    return text.replace(old, new, 1)


def patch_header(text: str) -> str:
    return once(
        text,
        "  PyThreadState* m_mainThreadState{nullptr};\n  bool m_stop = false;\n",
        "  PyThreadState* m_mainThreadState{nullptr};\n"
        "  // True only while the invoker thread itself owns Python's GIL.\n"
        "  // Stop/abort helper threads use temporary thread states and do not touch this flag.\n"
        "  bool m_invokerOwnsGil{false};\n"
        "  bool m_stop = false;\n",
        "invoker GIL ownership field",
    )


def patch_cpp(text: str) -> str:
    # New interpreter creation: v2 already changed Swap -> RestoreThread.
    text = once(
        text,
        """      PyEval_RestoreThread(m_mainThreadState);
      l_threadState = Py_NewInterpreter();
      if (l_threadState != nullptr)
        PyEval_ReleaseThread(l_threadState);
""",
        """      PyEval_RestoreThread(m_mainThreadState);
      m_invokerOwnsGil = true;
      l_threadState = Py_NewInterpreter();
      if (l_threadState != nullptr)
      {
        PyEval_ReleaseThread(l_threadState);
        m_invokerOwnsGil = false;
      }
""",
        "track GIL around Py_NewInterpreter",
    )
    text = once(
        text,
        """        PyEval_RestoreThread(m_mainThreadState);
        PyThreadState_Clear(m_mainThreadState);
        PyThreadState_DeleteCurrent();
        m_mainThreadState = nullptr;
        return false;
""",
        """        PyEval_RestoreThread(m_mainThreadState);
        m_invokerOwnsGil = true;
        PyThreadState_Clear(m_mainThreadState);
        PyThreadState_DeleteCurrent();
        m_mainThreadState = nullptr;
        m_invokerOwnsGil = false;
        return false;
""",
        "track GIL on failed interpreter cleanup",
    )
    text = once(
        text,
        """  // get the GIL
  PyEval_RestoreThread(l_threadState);
  if (newInterp)
""",
        """  // get the GIL
  PyEval_RestoreThread(l_threadState);
  m_invokerOwnsGil = true;
  if (newInterp)
""",
        "track normal invoker GIL acquire",
    )
    text = once(
        text,
        """  XBMCAddon::RetardedAsyncCallbackHandler::clearPendingCalls(m_threadState);
  PyEval_ReleaseThread(m_threadState);

  setState(stateToSet);
""",
        """  XBMCAddon::RetardedAsyncCallbackHandler::clearPendingCalls(m_threadState);
  PyEval_ReleaseThread(m_threadState);
  m_invokerOwnsGil = false;

  setState(stateToSet);
""",
        "track normal invoker GIL release",
    )

    old_teardown = """    PyEval_RestoreThread(m_threadState);

    onDeinitialization();

    // run the gc before finishing
    //
    // if the script exited by throwing a SystemExit exception then going back
    // into the interpreter causes this python bug to get hit:
    //    http://bugs.python.org/issue10582
    // and that causes major failures. So we are not going to go back in
    // to run the GC if that's the case.
    if (!m_stop && m_languageHook->HasRegisteredAddonClasses() && !m_systemExitThrown &&
        PyRun_SimpleString(GC_SCRIPT) == -1)
      CLog::Log(LOGERROR,
                "CPythonInvoker({}, {}): failed to run the gc to clean up after running prior to "
                "shutting down the Interpreter",
                GetId(), m_sourceFile);

    // PyErr_Clear() is required to prevent the debug python library to trigger an assert() at the Py_EndInterpreter() level
    PyErr_Clear();

    Py_EndInterpreter(m_threadState);
"""
    new_teardown = """    // execute() normally releases the GIL before this callback, but a caught
    // C++ exception can reach the terminal state while the invoker still owns it.
    // Never acquire the same GIL twice on the invoker thread.
    if (!m_invokerOwnsGil)
    {
      PyEval_RestoreThread(m_threadState);
      m_invokerOwnsGil = true;
    }

    onDeinitialization();

    // Backport Kodi upstream 92315ab: make SWIG/module destruction happen while
    // the sub-interpreter is still fully alive instead of during Py_EndInterpreter.
    PyErr_Clear();
    PyGC_Collect();

    PyObject* modules = PyImport_GetModuleDict();
    if (modules)
      PyDict_Clear(modules);

    PyGC_Collect();
    PyErr_Clear();

    Py_EndInterpreter(m_threadState);
"""
    text = once(text, old_teardown, new_teardown, "upstream sub-interpreter teardown hardening")

    text = once(
        text,
        """    PyThreadState_Swap(m_mainThreadState);
    PyThreadState_Clear(m_mainThreadState);
    PyThreadState_DeleteCurrent();
    m_mainThreadState = nullptr;

    // set stopped event - this allows ::stop to run and kill remaining threads
""",
        """    PyThreadState_Swap(m_mainThreadState);
    PyThreadState_Clear(m_mainThreadState);
    PyThreadState_DeleteCurrent();
    m_mainThreadState = nullptr;
    m_invokerOwnsGil = false;

    // set stopped event - this allows ::stop to run and kill remaining threads
""",
        "track final invoker GIL release",
    )

    text = once(
        text,
        """void CPythonInvoker::onExecutionFailed()
{
  PyEval_SaveThread();

  setState(InvokerStateFailed);
""",
        """void CPythonInvoker::onExecutionFailed()
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
""",
        "guard failed-execution SaveThread",
    )
    return text


def verify(source: Path) -> dict:
    source = source.resolve()
    cpp = (source / INVOKER).read_text()
    hdr = (source / INVOKER_H).read_text()
    checks = {
        "v2_gil_fix_preserved":
            "PyEval_RestoreThread(m_mainThreadState);\n      m_invokerOwnsGil = true;\n      l_threadState = Py_NewInterpreter();" in cpp,
        "v2_threadstate_abort_guard_preserved":
            "thread state cleaned while waiting for child threads" in cpp,
        "old_line412_assert_absent":
            "assert(m_threadState != nullptr)" not in cpp,
        "old_refcount_assert_absent":
            "assert(Py_REFCNT(p) == 2)" not in cpp,
        "gil_owner_field_present":
            "bool m_invokerOwnsGil{false};" in hdr,
        "failed_callback_guarded":
            "if (m_invokerOwnsGil)\n  {\n    PyEval_SaveThread();" in cpp,
        "failed_callback_logs_skip":
            "failure callback reached without invoker GIL ownership" in cpp,
        "teardown_error_clear_before_gc":
            "PyErr_Clear();\n    PyGC_Collect();" in cpp,
        "teardown_module_dict_preclear":
            "PyObject* modules = PyImport_GetModuleDict();\n    if (modules)\n      PyDict_Clear(modules);" in cpp,
        "teardown_second_gc":
            cpp.count("PyGC_Collect();") >= 2,
        "module_clear_precedes_end_interpreter":
            cpp.index("PyDict_Clear(modules);") < cpp.index("Py_EndInterpreter(m_threadState);"),
        "terminal_restore_guarded":
            "if (!m_invokerOwnsGil)\n    {\n      PyEval_RestoreThread(m_threadState);" in cpp,
        "normal_release_clears_owner":
            "PyEval_ReleaseThread(m_threadState);\n  m_invokerOwnsGil = false;" in cpp,
        "final_delete_clears_owner":
            "m_mainThreadState = nullptr;\n    m_invokerOwnsGil = false;" in cpp,
    }
    failed = [name for name, ok in checks.items() if not ok]
    require(not failed, "2103254 Python runtime verification failed: " + ", ".join(failed))
    return {
        "schema": 3,
        "repair": "pythoninvoker_failure_and_subinterpreter_teardown",
        "captured_parent_engine_sha256": CAPTURED_ENGINE_SHA,
        "upstream_teardown_commit": UPSTREAM_TEARDOWN,
        "checks": checks,
        "files": {
            str(INVOKER): sha(source / INVOKER),
            str(INVOKER_H): sha(source / INVOKER_H),
        },
    }


def apply(source: Path, receipt: Path) -> None:
    source = source.resolve()
    cpp = source / INVOKER
    hdr = source / INVOKER_H
    require(cpp.is_file() and hdr.is_file(), "PythonInvoker source missing")
    before = {str(INVOKER): sha(cpp), str(INVOKER_H): sha(hdr)}
    hdr.write_text(patch_header(hdr.read_text()))
    cpp.write_text(patch_cpp(cpp.read_text()))
    result = verify(source)
    result["before"] = before
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS: 2103254 PythonInvoker failure/teardown repair applied")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("--source", type=Path, required=True)
    a.add_argument("--receipt", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--source", type=Path, required=True)
    args = p.parse_args()
    if args.cmd == "apply":
        apply(args.source, args.receipt)
    else:
        print(json.dumps(verify(args.source), indent=2, sort_keys=True))
        print("PASS: 2103254 Python runtime repair verified")


if __name__ == "__main__":
    main()
