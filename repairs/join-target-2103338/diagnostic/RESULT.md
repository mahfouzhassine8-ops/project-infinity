# Infinity shutdown investigation — diagnostic source prepared

## Result

A local, diagnostic-only native source delta has been prepared and host-tested.
It records the missing invoker/add-on → target OS thread → broad worker-stage link
at the existing stop and join boundaries. **No root-cause repair or APK has been
produced. No GitHub push, workflow, application install, or baseline change occurred.**

The historical PID 32099 worker and exact APK remain unproven. This work enables a
new capture; it does not recover missing historical evidence or establish Kodi
Favourites Sync as the cause.

## Concrete source work

The two input files, LanguageInvokerThread.cpp and LanguageInvokerThread.h, were
reconstructed and matched exactly to the retained 2103334 native source receipt.
This is a verified two-file investigation target, not a whole-engine reconstruction
or a declaration that 2103334 is the current locked base.

The prepared delta changes those two files and adds InfinityInvokerTarget.h. It
records the worker's actual Linux OS TID on startup, stores `(TID, stage)` in one
lock-free atomic word, and emits that observation before existing stop/join calls.
The invoker and add-on IDs travel in the existing trace fields. Unknown identifiers
remain unknown. Nonblocking stop is explicitly distinguished from a requested join.

The worker stages cover execution, reusable-worker wait, wrapper mutex acquisition,
language finalization, manager callback, and exception equivalents. They identify
a broad phase, not the particular statement, native lock, request or child thread.
Matching a contemporaneous stack remains necessary.

No original cancellation, wait, join, finalizer or completion statement is removed,
reordered or replaced. The new records use the existing scripts.* diagnostic stream;
no new log file, trace-start policy, save/checkpoint layer or shutdown coordinator is
added. The existing trace budgets and retention limitations remain. Instrumentation
adds overhead and can alter race timing, so its presence is not proof of identical
runtime timing or a successful repair.

## Checks actually executed

Nine host check groups passed. Eight C++ scenarios ran successfully three times,
for 24 scenario passes. These cover coherent atomic snapshots and label bounds,
null invokers, active-execution cancellation, blocked finalizer joins, blocked
manager callbacks, exception finalization, nonblocking stop labeling, and unknown
add-on identity. A blocked host worker continued to hold a real std::thread::join
until the test released it; logging did not bypass that join.

Additional gates verified exact preimages, preservation of all original nonblank
source lines in order, refusal of changed parents/overwrites/overlapping output
paths, patch application matching the complete prepared files, and host compilation
of both Android-guard and non-Android-guard paths with warnings treated as errors.

**Test limitations:** Kodi CThread/runtime behavior, trace writing, and language
boundaries were mocked. There was no CPython embedding, Android NDK cross-compile,
full Kodi regression run, sanitizer run, historical five-minute-hang reproduction,
live phone connection, or physical Fold test. Host TIDs are not phone evidence.

## Deliverables

`Infinity-Join-Target-Diagnostic-Source-Only.zip` contains complete prepared files,
a hash-gated preparer that never edits its input source, the unified patch, the
two-file parent fixture, host test sources, input provenance and executed results.
The README gives reproduction commands and all open integration/device gates.
No binary, APK, font, raw personal diagnostic archive, credential or signing material
is included.

## Next engineering gate

Review and integrate against the verified intended lineage in a separate diagnostic
build with a distinct engine identity and matched source/native/APK receipts. The
native class layout changed, so the old engine cannot merely be repackaged. This
build was not started. The package is source for engineering review, not an update
to install or a device-ready fix.

During a stuck close, collect the existing native/critical trace before another Kodi
session rotates it, plus a contemporaneous complete thread dump. Pair the new
`os_tid` to `sysTid` in that same PID/session. Do not equate CPython thread identities
to OS TIDs, borrow a different process's completion, treat a stage as a full stack,
or treat `exit_reported`/snapshot rows as proof of thread or process death.

Only evidence identifying the inner blocked worker operation can justify a minimal
behavior repair. The historical root-cause diagnosis and physical Fold acceptance
remain open.
