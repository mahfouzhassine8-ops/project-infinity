#!/usr/bin/env python3
"""Apply Kodi's complete PythonInvoker thread-state fix set to Infinity Kodi 21.3.

This layers Kodi's Python 3.11 GIL follow-up (ddb60bd932b929724a9b0d2226043dc54d0d1912)
on top of Infinity's existing backport of PR #27320. The follow-up is critical: PyThreadState_Swap()
does not acquire the GIL, while Py_NewInterpreter() and its Python 3.11 initialization path require it.
Kodi upstream replaced the two new-interpreter-path swaps with PyEval_RestoreThread().

Only xbmc/interfaces/python Python runtime ownership is changed. Android UI, Cobra playback,
providers, timeshift, PiP/background behavior, themes, resources and presentation are out of scope.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

UPSTREAM_PRIMARY = "0186f895271d4ce7d240b4e9f40da03b4833539d"
UPSTREAM_FOLLOWUP = "ddb60bd932b929724a9b0d2226043dc54d0d1912"
FOLLOWUP_TITLE = "[python] Fix python 3.11 segfaults due to python API usage without holding GIL"
INVOKER = Path("xbmc/interfaces/python/PythonInvoker.cpp")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def load_v1():
    path = Path(__file__).with_name("infinity_python_invoker_hardening.py")
    require(path.is_file(), "Missing first-stage PythonInvoker hardening script")
    spec = importlib.util.spec_from_file_location("infinity_python_invoker_hardening_v1", path)
    require(spec is not None and spec.loader is not None, "Cannot load first-stage hardening module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected one exact anchor, found {count}")
    return text.replace(old, new, 1)


def apply_followup(source: Path) -> None:
    path = source / INVOKER
    text = path.read_text()
    text = once(
        text,
        """      PyThreadState_Swap(m_mainThreadState);
      l_threadState = Py_NewInterpreter();
""",
        """      PyEval_RestoreThread(m_mainThreadState);
      l_threadState = Py_NewInterpreter();
""",
        "Python 3.11 GIL acquire before Py_NewInterpreter",
    )
    text = once(
        text,
        """        PyThreadState_Swap(m_mainThreadState);
        PyThreadState_Clear(m_mainThreadState);
        PyThreadState_DeleteCurrent();
""",
        """        PyEval_RestoreThread(m_mainThreadState);
        PyThreadState_Clear(m_mainThreadState);
        PyThreadState_DeleteCurrent();
""",
        "Python 3.11 GIL acquire on Py_NewInterpreter failure cleanup",
    )
    path.write_text(text)


def verify(source: Path) -> dict:
    source = source.resolve()
    v1 = load_v1()
    first_stage = v1.verify(source)
    cpp = (source / INVOKER).read_text()
    checks = {
        "primary_threadstate_backport_present": first_stage.get("upstream_fix") == UPSTREAM_PRIMARY,
        "gil_acquired_before_new_interpreter":
            "PyEval_RestoreThread(m_mainThreadState);\n      l_threadState = Py_NewInterpreter();" in cpp,
        "gil_acquired_before_failed_interpreter_cleanup":
            "PyEval_RestoreThread(m_mainThreadState);\n        PyThreadState_Clear(m_mainThreadState);" in cpp,
        "bad_swap_before_new_interpreter_absent":
            "PyThreadState_Swap(m_mainThreadState);\n      l_threadState = Py_NewInterpreter();" not in cpp,
        "bad_swap_before_failed_cleanup_absent":
            "PyThreadState_Swap(m_mainThreadState);\n        PyThreadState_Clear(m_mainThreadState);" not in cpp,
        "device_abort_guard_preserved": "thread state cleaned while waiting for child threads" in cpp,
        "old_threadstate_assert_absent": "assert(m_threadState != nullptr)" not in cpp,
        "refcount_hardening_preserved": "assert(Py_REFCNT(p) == 2)" not in cpp,
    }
    failed = [name for name, ok in checks.items() if not ok]
    require(not failed, "Python 3.11 GIL follow-up verification failed: " + ", ".join(failed))
    return {
        "schema": 2,
        "failure_class": "python311_python_api_without_gil_during_subinterpreter_creation",
        "upstream_primary": UPSTREAM_PRIMARY,
        "upstream_followup": UPSTREAM_FOLLOWUP,
        "upstream_followup_title": FOLLOWUP_TITLE,
        "native_rebuild_required": True,
        "checks": checks,
        "first_stage_checks": first_stage.get("checks", {}),
        "files": {str(INVOKER): sha(source / INVOKER)},
    }


def apply(source: Path, receipt: Path) -> None:
    source = source.resolve()
    v1 = load_v1()
    first_receipt = receipt.with_suffix(".stage1.json")
    v1.apply(source, first_receipt)
    before_followup = sha(source / INVOKER)
    apply_followup(source)
    result = verify(source)
    result["before_followup_pythoninvoker_sha256"] = before_followup
    result["after_followup_pythoninvoker_sha256"] = sha(source / INVOKER)
    result["stage1_receipt"] = first_receipt.name
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS: complete PythonInvoker backport includes Kodi Python 3.11 GIL follow-up")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("--source", type=Path, required=True)
    a.add_argument("--receipt", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "apply":
        apply(args.source, args.receipt)
    else:
        print(json.dumps(verify(args.source), indent=2, sort_keys=True))
        print("PASS: Python 3.11 GIL follow-up verified")


if __name__ == "__main__":
    main()
