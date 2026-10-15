#!/usr/bin/env python3
"""Ensure only queue admission changes; Python mutation/finalizers are retained."""
from pathlib import Path
import argparse,json,re
import native_repair as n
from test_messenger import function
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
root=a.source
old=(root/n.INVOKER).read_text();new=n.transform(n.INVOKER,old)
for sig in ('void CPythonInvoker::onExecutionDone()', 'void CPythonInvoker::onExecutionFailed()'):
    assert function(old,sig)==function(new,sig),sig
# Strip ONLY inserted diagnostic calls/header; original abort statement remains.
block='''      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);
      while (state)
      {
        // Raise a SystemExit exception in python threads
        Py_XDECREF(state->async_exc);
        state->async_exc = PyExc_SystemExit;
        Py_XINCREF(state->async_exc);
        state = PyThreadState_Next(state);
      }'''
assert old.count(block)==new.count(block)==1
for token in ('PYTHON_SCRIPT_TIMEOUT 5000ms','m_stoppedEvent.Wait(15ms)','pulseGlobalEvent();','PyThreadState_DeleteCurrent();'):
    assert old.count(token)==new.count(token),token
helper=(n.HERE/'InfinityPythonExitEvidence.h').read_text()
for bad in ('SetAsyncExc','async_exc','PyRun_','PyEval_RestoreThread','Py_EndInterpreter','PyGILState_Ensure','co_filename->','f_locals'):
    assert bad not in helper,bad
assert 'std::array<Snapshot,8>' in helper and 'depth<4' in helper
assert 'PyErr_Fetch' in helper and 'PyErr_Restore' in helper
assert 'InfinityPythonAbort.h' not in new
# Cleanup/dispatch remain exact; only SendMsg adds the under-lock recheck.
old=(root/n.MESSENGER).read_text();new=n.transform(n.MESSENGER,old)
for sig in ('void CApplicationMessenger::Cleanup()', 'void CApplicationMessenger::ProcessMessages()', 'void CApplicationMessenger::ProcessWindowMessages()', 'void CApplicationMessenger::ProcessMessage('):
    assert function(old,sig)==function(new,sig),sig
assert new.count('waitEvent->Wait();')==old.count('waitEvent->Wait();')==1
assert new.index('if (m_bStop)',new.index('ThreadMessage* msg ='))>new.index('std::unique_lock<CCriticalSection> lock(m_critSection)',new.index('ThreadMessage* msg ='))
print('PASS: Python abort policy/finalizers, queue cleanup, all dispatch and wait semantics retained; only late admission rejected')
