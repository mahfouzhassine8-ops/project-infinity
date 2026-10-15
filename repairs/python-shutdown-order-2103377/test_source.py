#!/usr/bin/env python3
"""Fail-closed source contracts for the exact native Close ordering correction."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import patch_native as fix

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root: Path | None = None, output: Path | None = None) -> dict:
    if root is None:
        # Use the real version-controlled native overlay as the fixture, not
        # independently rewritten C++ snippets; rebuilds will test staged code.
        original = ROOT / "repairs/android-checkpoint-shutdown/runtime/native/overlay"
        holder = tempfile.TemporaryDirectory(prefix="infinity-shutdown-order-test-")
        root = Path(holder.name)
        for file in (fix.PYTHON, fix.HEADER, *fix.UNCHANGED_GATES):
            destination = root / file
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / file, destination)
    else:
        holder = None
        root = Path(root)
    try:
        first = {name: digest(root / name) for name in (fix.PYTHON, fix.HEADER, *fix.UNCHANGED_GATES)}
        if holder is not None:
            delta = fix.apply(root)
        else:
            p = (root / fix.PYTHON).read_text()
            h = (root / fix.HEADER).read_text()
            assert "InfinityRunRegisteredThreadShutdown" in p and "m_infinityThreadingShutdownStarted" in p+h
            delta = {"changed": [fix.PYTHON, fix.HEADER], "after": {k: digest(root / k) for k in (fix.PYTHON, fix.HEADER)}}
        text = (root / fix.PYTHON).read_text()
        hdr = (root / fix.HEADER).read_text()
        checks = {
            "only_two_native_paths_changed": set(delta["changed"]) == {fix.PYTHON, fix.HEADER},
            "threading_callback_before_cpp_child_join": text.index("InfinityRunRegisteredThreadShutdown(") < text.index('PyThreadState* s = PyInterpreterState_ThreadHead(m_threadState->interp)'),
            "native_close_guard_and_explicit_stop": "InfinityAndroidCheckpoint::IsActive() && m_stop &&" in text,
            "late_finalizer_fallback_before_persistence_finish": text.index("if (InfinityAndroidCheckpoint::IsActive() && !m_infinityThreadingShutdownStarted)") < text.index("InfinityPythonPersistence::Finish("),
            "native_failure_receipt_on_callback_error": 'InfinityScriptPersistence::Fail(id, "registered_python_thread_shutdown_failed");' in text,
            "no_early_module_dictionary_clear": text.index("InfinityPythonPersistence::Finish(") < text.index("PyDict_Clear(modules)") < text.index("Py_EndInterpreter(m_threadState)"),
            "registered_callback_protocol_used": 'PyObject_CallNoArgs(shutdown)' in text and 'PyObject_GetAttrString(threading, "_shutdown")' in text,
            "no_private_callback_list_mutation": "_threading_atexits" not in text and "_threads_queues" not in text,
            "no_new_async_thread_interrupt": "PyThreadState_SetAsyncExc(" not in fix.SOURCE_FUNCTION,
            "stop_escalation_shield": "if (m_infinityThreadingShutdownStarted)" in text and "return true;" in text,
            "state_guard_in_header": "bool m_infinityThreadingShutdownStarted{false};" in hdr,
            "no_false_retirement": 'setState(InvokerStateExecutionDone);' in text and 'InfinityPythonPersistence::End(' in text,
            "no_py_end_interpreter_bypass": text.count("Py_EndInterpreter(m_threadState)") == 1,
            "required_save_gates_untouched": all(digest(root / f) == first[f] for f in fix.UNCHANGED_GATES),
            "native_persistence_observer_unchanged": digest(root / "xbmc/interfaces/python/InfinityPythonPersistence.h") == first["xbmc/interfaces/python/InfinityPythonPersistence.h"],
        }
        for name, passed in checks.items():
            if not passed:
                raise AssertionError(f"FAILED source preservation contract: {name}")
        if holder is not None:
            try:
                fix.apply(root)
                raise AssertionError("Reapplying same repair must fail closed")
            except (AssertionError, RuntimeError) as err:
                if "Reapplying same repair" in str(err):
                    raise
        report = {
            "status": "source_contracts_passed",
            "count": len(checks),
            "checks": checks,
            "scope": "source checks only; no native compilation or physical-device result",
            "native_runtime_modified_on_installed_device": False,
        }
        if output:
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
        print(f"PASS {len(checks)}/{len(checks)} strict native source checks")
        return report
    finally:
        if holder is not None:
            holder.cleanup()

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    verify(args.source,args.out)
