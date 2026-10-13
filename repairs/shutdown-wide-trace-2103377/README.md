# Additive shutdown-wide diagnostics for Infinity 2103377

This is the next phase of the existing implementation, on branch
`work/infinity-2103377-shutdown-wide-diagnostics`. The original branch,
targeted Playlist Browser diagnostic, and signed APK remain unchanged at
`837b9824c2114aceb3f533a2c7ead1c264db76b2`. Its full engine compilation,
preservation checks and permanent signing passed in run **38378882508**.
`TARGETED-ROLLBACK.json` pins that APK, artifacts and every original tracer file.

The expansion calls the preserved targeted transform first, then adds coverage.
It uses one tracer instance and the existing native trace/export channel.
It retains the accepted 274-test candidate byte for byte, the matched native
entry wrapper, all termination and persistence authority, and the 25-second
deadline. No add-on, provider, player, layout, skin, timeout or baseline is changed.

## Four capabilities

1. **Concrete backend identity:** RTTI checks identify the 29 known factory/cache
   classes under their existing platform guards, including redirected and reused
   objects. Factory selection and concrete identity are distinct observations.
   Nested special/resource/cache file calls retain parent operation IDs.
2. **Operation timing:** 19 CFile entry points report process-unique IDs, owner
   invoker/execution IDs, native thread IDs, current stages, stage start,
   operation start and observed return timestamps. Active records exist before
   Close. Existing native scopes also retain their original start and nesting
   before Close, including SQLite and database operations.
3. **Cancellation:** coordinator requests, existing abort flags and Python
   escalation are distinct from backend cancellation. The existing Curl Cancel
   and FileCache StopThread callbacks report entry, flag assignment, callback
   return or unwind and operation return. Curl's loop reports observing its
   cancellation flag, and transfer completion reports the numeric Curl result.
   Callback correlation survives the operation returning first.
4. **Shutdown correlation:** all native Python invokers are registered, with
   native language-hook ownership propagated through DelayedCallGuard to child
   calls. Service activity, child-state waiting, bytecode return, interpreter
   finalization, Py_EndInterpreter return, stopped-event notification, the
   authoritative retirement receipt and native exit/stop callbacks remain
   separate observations. Checkpoint generation, authoritative failed/safe
   results and the 17 required durability owners join that timeline. Coordinator
   result/owner snapshots use atomics under its existing mutex; append output
   happens after the mutex is released.

No callback is called by the tracer. No successful cancellation, durability,
engine death or device repair is inferred from a callback or compile.

## Explicit coverage limits

- Unknown concrete subclasses, absent backend objects and operations blocked
  before backend construction are labeled unclassified or unselected.
- IFile has no generic cancellation API. Ordinary backends are labeled
  `no_generic_IFile_cancel_API`; this does not establish what private code
  supports. Add-on VFS private cancellation is explicitly unknown.
- FileCache worker stopping does not prove cancellation of its underlying source.
  Curl callback return does not prove the operation returned or saved data.
- Backend-private OS calls, DNS/TLS internals and uninstrumented native/directory
  operations cannot be assigned an invented backend or internal stage.
  Existing job, directory, lease and checkpoint evidence remains available.
- Child-state exhaustion bounds Python retirement. It is not an exact timestamp
  for every Python child OS thread's death. Exit callbacks and nonblocking stop
  returns are explicitly not thread-death proof.
- Curl poll/check loops update stage atoms without per-iteration append output.
  They expose the latest stage/start at snapshots and return, not every poll.
  Native scope snapshots taken at capture begin use generation zero and join
  the subsequent checkpoint request through the process/session and operation ID.
- Registries are bounded at 128 entries. Concurrent snapshots/history gaps,
  capacity exhaustion, event limits and missing/partial output mean incomplete
  evidence. Separate diagnostic retention does not consume the original
  critical timeline's 1024-event allowance.

Only fixed categories, installed add-on IDs, numeric IDs/counters and clocks
enter the additional trace. No resource paths, URLs, query strings, credentials,
playlist content, error text or pointer values are exported. There is no native
append logging before Close, new thread, new mutex, cancellation call, fsync,
sleep, retry loop or increase in the shutdown deadline.

## Independent verification and integration gate

Real-thread host regressions cover pre-Close work, simultaneous services and
child ownership, nested calls, return/cancellation races, native work, cache
workers, failed durability, unknown support, stale IDs, gaps and capacity limits.
The actual type-classifier body is compiled and executed against fixture types
for POSIX, Windows and tvOS configurations. These are host proofs, not physical
Galaxy Fold acceptance or real-backend I/O tests.

The separate workflow recompiles the complete matched Kodi engine, checks
native exports and dependencies, and saves receipts. It neither cancels the
original workflow nor signs/installs a replacement APK. Integration into the
existing 2103377 branch follows successful preservation, native compatibility
and regression checks. The final repair remains dependent on physical evidence.
No promotion or lock is performed.

## 075108 Fold evidence and overflow repair

The main stream reached 8192 rows after 2.910618801 seconds. The existing
Health Center exporter copied only the first 2 MiB of the critical file, ending
at 2.153600624 seconds. The checkpoint remained failed at 25.087 seconds.
Eight pending services remain UNKNOWN; no specific optional abandonment has
been approved. Actual installed dependency/write behavior is still required.

The additional retention fix uses six separate byte reservations for checkpoint,
cancellation, interpreter retirement, initial ownership, native returns and
legacy evidence. Their sum is 1.75 MiB, below the unchanged 2 MiB export cap;
small bounded loss markers fit in the remaining space. Fast SQLite/database
telemetry is aggregated; actual database operations and save barriers are
unchanged. Operations sampled during shutdown retain their return in the
retirement lane. Limits remain explicitly incomplete evidence.

All original 18 host scenarios remain unchanged and passing. Three added flood
scenarios verify late callbacks, failed checkpoint/owner receipts, interpreter
retirement, active native SQL scopes and independent lane exhaustion. Four
recovery-collector tests verify late-file recovery, privacy and link refusal.
Full Kodi compilation is a separate gate. This is an evidence repair, not
a verified shutdown correction or approval to abandon unknown data.

The one-shot recovery add-on reads the two existing allowlisted native critical
files and installed source hashes/filtered ASTs of the eight pending services.
It does not require another Close test. If admission/access is blocked, preserve
the current session and report the failure; do not force shutdown to run it.

During an active checkpoint, the automatic escalation launcher returns before
launching Stop(true) for unverified writers. Cooperative Monitor/legacy
notifications and durable retirement remain required. No writer is declared
disposable. The legacy stop implementation and every save/termination gate
remain available; no successful save is synthesized. This implements the
explicit protection policy and does not establish that the Fold closes promptly.
