# Internal native startup diagnostic

Authorized continuation: owner instruction after 93d025b6. This is diagnostic
instrumentation, not a claimed repair of the Fold failure.

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

`test_cpython_initialization.py` is separately selected for pinned CPython
3.11.7 on Actions. A host-only audit hook makes the real interpreter API fail
early. It compares the unchanged cleanup against a host-only removal of the
redundant GIL acquisition. It also creates/runs/retires three real interpreters
and verifies an independent Python thread. A baseline timeout is recorded as a
reproduced defect, never successful application initialization. This injection
is not present in the Android payload, and the cleanup comparison is not applied
to production. Fold attribution remains a separate gate.

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
