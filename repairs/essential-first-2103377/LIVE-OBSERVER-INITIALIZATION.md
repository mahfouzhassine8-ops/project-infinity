# Exact live Python initialization stage

The same signed RC05 APK failed the phase-matched Android comparison
**38963791371**, source `ccf1a103`. Input identity, native build identity, permanent
signer, all 308 saved regressions, 21 comparison controls and emulator setup passed.
No engine or APK was rebuilt for that comparison.

Core Run began at 20:48:38.070 UTC; the Close receipt began at 20:48:43.919.
At the native 25.294s deadline, all 41 writers had passed native hook installation
but remained at `python.source`, the call to `PyRun_String`. None was observed,
no Python exception was recorded, tracked paths were zero and write admission
never started. No essential save participant ran and termination was refused.
The coordinator recorded 25.811s total. Full artifact identity and findings are in
`evidence/rc05-core-initialized-38963791371.json`.

This is not the earlier cold-start outcome, which initialized both required
observers and reached Command Center PREPARE. Both failures remain recorded.

The successful RC05 loaded control initialized Command Center/compat observers
in 42.496s/43.218s before Close. Unchanged TEST3 controls also show substantial
41-service startup cost. Scratch pinned CPython 3.11.7 controls initialized 37
concurrent real subinterpreters in about 1.6s on two host CPUs, with and without
deferred Close. Compilation averaged about 8ms; imports dominated host wall time.
The host did not reproduce Android's delay. Translated Android backtraces cannot
name the waiting guest Python function. A deadlock and a specific import cause
are both unproven.

The exact gap is that existing `_INFINITY_INITIALIZATION_STAGE` assignments are
copied to the native receipt only when an exception is raised. There was no
exception at this deadline. The next diagnostic checkpoint publishes those same
stages live and distinguishes outer source compilation from execution, retaining
the existing `PyRun_String` call and all imports. It adds no observer/save success,
write waiver, timeout extension or new termination authority.

The green native build **38957212563** / `92b5be78`, 308 regressions, permanent
signer and TEST2/TEST3 baselines, fresh Close (13.319s), loaded Close (5.017s),
all essential receipts, both Java seals, external whole-UID death, database
integrity and retained-data reopening remain preserved. These are disposable
controls, not physical Fold or complete Diggz validation. The physical installation
has not been changed. No test APK has been promoted; physical approval and final lock remain pending.

Local validation passed: seven live-stage controls, eleven preserved initialization
cases, five preserved Close-race cases, eight progress cases, eleven actual native
write controls and sixteen strict source contracts. A blocked real durability
write still refuses sealing and authorization. Independent review approved only
a diagnostic build. Required compiled binary markers now include the live bridge.

Diagnostic source `e78c769d99b626b47292fb2bcac0d09661735fc6` completed full
native workflow **38967896318** successfully, including host guards and ARM64.
The isolated Android diagnostic **38968517075** passed that exact native gate
and its 21 packaging controls, then stopped before signing or Android launch.

The packager compared all host-side installed-addon artifact files. Actual
artifact comparison proves all 22 source/configuration files are byte-identical;
11 generated CPython 3.10 caches differ only at timestamp-header bytes 8–11.
Their bytecode bodies are identical. The existing Android fixture already
excludes `__pycache__` and `*.pyc`. This is a packaging inventory error, not new
Android runtime evidence. Exact artifact digests and per-cache evidence are in
`../android-checkpoint-shutdown/runtime-tests/evidence/live-stage-packaging-38968517075.json`.

The correction compares the same files that the existing fixture installs and
records the excluded cache hashes separately. Every installed source/configuration
file still must match; the APK entry names and every non-engine payload byte,
including any cache inside the APK, retain their independent exact-byte check.
All 21 original packaging controls plus nine targeted controls pass normally and
under Python 3.11.7 `-O`. Real downloaded artifacts also pass source, native proof,
compiled marker, export/JNI and dependency verification. No local signing occurred.

Retry only isolated packaging/diagnostics using the already green native engine
and exact saved RC05 Java/manifest/assets plus the 308-test proof. No native or
Java rebuild is required by this packaging-only correction. The actual Android
observer wait is still unresolved; no candidate is promoted or locked.

The failed emulator log used `skin.estuary`, with 37 controlled services. It is
a lifecycle/observer control, not a clone of the Fold's Diggz ecosystem and
`skin.infinity.diggz` 1.0.5.223 configuration.
