/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <Python.h>
#include <algorithm>
#include <cassert>
#include <vector>

namespace InfinityPythonAbort
{
// The caller already owns the GIL through a temporary state in the TARGET
// sub-interpreter. Never use PyGILState_Ensure here: it selects the main one.
// Keep the existing SystemExit escalation policy, but use CPython's API so
// its evaluation-breaker is signalled; writing async_exc alone does not do so.
// Snapshots contain native thread IDs, not PyThreadState pointers: the API's
// DECREF may execute code and mutate the interpreter's thread-state list.
// Observer receives matched=0 for a target that left, 1 for a REQUEST (not
// proof of termination), and >1 for an ambiguous request that was reverted.
template<class Observer>
inline void RequestSystemExit(PyThreadState* caller, Observer observe)
{
  assert(caller && PyThreadState_Get() == caller);
  const unsigned long callerId = caller->thread_id;
  std::vector<unsigned long> targets;
  for (PyThreadState* state = PyInterpreterState_ThreadHead(PyThreadState_GetInterpreter(caller));
       state != nullptr; state = PyThreadState_Next(state))
  {
    const unsigned long id = state->thread_id;
    if (state != caller && id != callerId &&
        std::find(targets.begin(), targets.end(), id) == targets.end())
      targets.push_back(id);
  }
  for (const unsigned long id : targets)
  {
    const int matched = PyThreadState_SetAsyncExc(id, PyExc_SystemExit);
    if (matched > 1)
      PyThreadState_SetAsyncExc(id, nullptr);
    observe(id, matched);
  }
}
} // namespace InfinityPythonAbort
