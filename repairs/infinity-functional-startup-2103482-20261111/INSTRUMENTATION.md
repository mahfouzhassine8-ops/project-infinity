# Internal native startup diagnostic

Authorized continuation: owner instruction after 93d025b6. This includes bounded
diagnostics and the proven CPython NULL-cleanup repair below. It is not yet a
causally established repair of the Fold failure.

Four source-bound call-site files change: `ScriptInvocationManager.cpp`,
`AddonBuiltins.cpp`, `PythonInvoker.cpp`, and `XBPython.cpp`. One header supplies
the bounded recorder. `prepare_instrumentation.py` derives overlays from the
retained hashes; the existing native checkout is never edited. The 2103482
checkpoint receipt correction remains in the build input.

The header defaults to disabled. The isolated internal QA builder explicitly
prepends `INFINITY_STARTUP_TRACE_QA=1` to its copied header and records that exact
header hash in the build map. Android capture additionally requires the exact
`com.projectinfinity.kodi:kodi` process identity, independently of skin,
foreground or checkpoint state. No Java, DEX, Cobra or provider hook changes.

## Observation contract

- `RunScript`: request begin/end, resolution boundary and actual invocation
  result. The public built-in still returns zero as before.
- Manager: lookup/dispatch lock waits and acquisition, refusal reason, current
  shutdown/startup flags, tracked-invoker count, fresh/reused dispatch and ID.
  The count is the existing map size, not a claim of runnable worker count.
- Python: runtime initialization-lock wait, ready/new-runtime state, GIL waits
  and acquisition, interpreter creation/result, Kodi module initialization,
  observer return and bytecode entry/return/exception. New Python queries occur
  only inside the enabled branch while the normal execution path owns the GIL;
  the NULL-interpreter branch performs no Python-state query.
- Existing persistence-stage and failure receipts remain intact. These provide
  per-import detail when observer initialization fails before bytecode.

Records contain fixed stage codes, native thread/invoker/request IDs, monotonic
time, numeric results and flags. No paths, arguments, source text, URL, account,
token or exception-message fields exist. New recording does not acquire a
manager/Python/GUI mutex or write a file. Native `Process()` drains through the
existing logger before taking its manager lock, at most 32 records plus one
overflow notice per pass. Logging exceptions cannot affect invocation decisions.

Capture is limited to 8,192 records and twenty minutes from first enabled use;
overflow is explicit. Absence after either limit is not failure evidence.
Worker records normally have request zero because request tickets are local to
the calling thread. Link them through the dispatch event's invoker ID/native
thread and time. Reused invoker attribution may be ambiguous; this trace does
not invent a per-request worker-generation identity or change scheduling.

## Selected execution and preservation checks

`test_trace.py` compiles the actual modified manager, built-in and runtime-init
methods with explicit host peers. Fifteen selected cases passed: dispatch,
startup/shutdown refusal, missing file/handler, quarantine, controlled lock
delay and recovery, foreign-process disablement, capacity/batch bounds and six
trace-compiled-out equivalence cases. These do not execute CPython or Android.

`test_cpython_initialization.py` separately executes pinned CPython 3.11.7 on
Actions. A host-only audit hook makes the real interpreter API fail early. The
test verifies the real NULL result, original current thread state and expected
exception before cleanup. Run 43036170257's focused-host job passed: unchanged
cleanup self-deadlocked at the second GIL acquisition; the two-line comparison
returned, then created/ran/retired three interpreters and an independent Python
thread. The parent deadline kills only the disposable host child.

Both reviewers confirmed pinned CPython's recoverable NULL paths return before
switching away from this caller's temporary thread state; the GIL remains held.
Later initialization errors are fatal-status paths, not a contrary recoverable
NULL contract. The candidate therefore removes only the redundant
`PyEval_RestoreThread(m_mainThreadState)` and duplicate `m_invokerOwnsGil = true`
in the first NULL branch. Existing Clear/DeleteCurrent, pointer/ownership reset,
error reporting, failure return and persistence accounting remain unchanged.
The current test compares the exact candidate block with be06e127 and requires
precisely that two-line delta. No failure injection enters the Android payload.

This repairs a reproduced initialization failure path. It does not establish
that the owner's Fold entered it, suffered allocation failure, or stopped
because of Core. Continued Core Python execution is inconsistent with a GIL
self-deadlock lasting that entire observed interval. Native admission traces
remain necessary for actual failed-start attribution.

The first ARM job was cancelled during source preparation, after its host job
passed, to incorporate this proven repair before dependency/full compilation.
It is not recorded as an ARM build failure or PASS. Only the affected host
proof must rerun for the exact corrective source before its ARM build.

Independent reviewers requested removal of an unsafe/eager NULL-path Python
query and bounded log draining. Both were corrected before Android compilation;
the affected host tests were rerun. There is no change to return contracts,
admission policy, lock ordering, retry policy, protected saves or user data.

## Authenticated artifact access

Actions 43033786343 downloaded the existing APKs but failed Android SDK setup.
After pinning JDK17, 43034295742 verified original 2103482 signatures v1/v2/v3,
certificate and package/version. SHA-256:
`78b2a5dd878ea847f425f8bbf5b9c71e810d19e134fe4480588db55a7ea52a32`.
Exactly three expected members differ from signed80; 7,758 payload members are
unchanged. The earlier workspace artifact-access blocker is resolved through
authenticated Actions. No signed artifact was overwritten or re-signed.
