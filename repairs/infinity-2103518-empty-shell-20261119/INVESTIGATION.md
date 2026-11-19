# Infinity 2103518 Empty Shell investigation

## Fold incident

The supplied capture summary identifies living Kodi PID 3093 and
`interpreter.create` for TMDb Helper TID 4389 and UI Repair TID 4475.
It reports no corresponding `interpreter.returned` and no confirmed crash
or Android kill. Full same-process event sequences and native stacks for
those workers were unavailable.

The call site is `xbmc/interfaces/python/PythonInvoker.cpp` lines 270–322
in the authenticated 2103518 engine source. The worker obtains a fresh
state for the main interpreter and acquires the shared CPython 3.11.7 GIL.
It emits `interpreter.create`, calls `Py_NewInterpreter()`, records the
result, and then updates the persistence ledger. Add-on module paths
and bytecode come later. Commit `679807f7`'s NULL-return cleanup remains in
this engine. Its old double-GIL-acquire mechanism happens after a NULL
return, which would be observable before cleanup in a complete capture.

A missing return narrows the interval only when the capture continued
after the symptom, the ring kept draining, and its finite time and
capacity limits left room for the event. The brief alone does not show
what either thread was waiting for or name the owning thread.

## Reproduced native lock path

The return marker rules out the subsequent ledger update as a point
inside CPython's call. Earlier native write hooks can still reach the
same ledger from within the call. CPython initializes standard streams
in `Python/pylifecycle.c` at `init_sys_streams()` and `create_stdio()`.
The shared FileIO initializer previously installed by an earlier observer
can proceed through `InfinityPythonWriteHooks::RawInitialize()` at
`xbmc/interfaces/python/InfinityPythonWriteHooks.h:729` and acquire the
persistence mutex in `BeginProtectedOperation()` at
`xbmc/platform/android/activity/InfinityProtectedWrites.h:196`.

The host fixture executed the exact signed-QA call boundary with CPython
3.11.7 and the pinned stdio hooks. All 256 stock creations and all 256
hooked creations completed while fresh starts and earlier retirements
overlapped. The hooked run observed 512 completed operation tokens. A
separate, deliberate 350 ms hold by a host-only native thread reproduced
a create-before-return wait. The symbolized waiter ran through
`Py_NewInterpreter → init_sys_streams → create_stdio → RawInitialize →
BeginProtectedOperation`. All eight invocations completed after the
fixture released the mutex. This identifies a real wait path without
establishing that it was the path or holder in PID 3093.
[Source hashes and results](RECEIPT.json)

The host driver accepts the authenticated source directory, the local
pinned CPython 3.11.7 source/core build, the pinned SQLite header directory,
and a fresh output directory. It checks each source hash and saves the
symbolized stack from the selected contention control.
[Reproducer](reproduce_host_startup.py)

## Signed Android 17 baseline probe

Run 44546288895 authenticated the original-signed 2103518 APK and used its
exact ARM64 engine and signed module payload. All 48 independent scripts
reached interpreter return, bookkeeping completion, bytecode entry, and
bytecode return. The five adjacent bursts overlapped. The ring reported
zero overflows. The longest create-to-return time was 6.651 seconds on
the ARM64-translated emulator. The physical Fold failure did not reproduce
in this test. [Android 17 evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44546288895/artifacts/14539869383)

## Resume Hub warning

`repairs/resume-hub-2103292/InfinityResumeHubInstaller.java.in:34` pins a
legacy overlay from Command Center 0.3.5.17 to 0.3.5.19. The branch at
line 75 warns and returns for 0.3.5.87 before opening the overlay archive.
The signed 2103514 and 2103518 authorities agree on the installer class,
its archive, and the current signed `resume_hub.py` member. The Android 17
probe reproduced the exact 0.3.5.87 warning while the signed .87 payload
activated and all 48 workers completed. The guard is functioning and
does not account for the observed missing interpreter returns.

## Older saves on 2103518

The owner confirmed that the older saved playback still enters the same
failure flow on the Fold. The fixture proved the missing-flat-TMDb-ID
movie pattern. An earlier positive result for a fixture cannot establish
the field record's branch.

In Command Center `plugin.py:272`, an existing verified remembered
destination is checked before the typed-ID fallback even runs. In
`saved_navigation.py:517` a prior failure, fingerprint mismatch, or
rejected provider contract can still select recovery. A previously
failed original fingerprint or unavailable original also selects
recovery at lines 530–538. These are separate from the Empty Shell lock
question. A privacy-safe `continue_navigation` outcome from the
owner's existing log, or the exact selected record with its route and
failure metadata redacted, would differentiate these routes.

## Release status

The Fold root cause is unconfirmed. Identifying the next production
change requires a native stack for an incomplete worker and its lock
owner, or a matched reproduction that yields those stacks. A complete
same-PID trace would also verify that the return marker was not lost.
There are zero production source changes and no new signed APK.
Accepted 2103514 remains protected.

## Follow-up evidence review

The available logs and release artifacts contain the 514 incident and the
controlled Android 17 examples. They contain no `continue_navigation`
sequence from the owner's failed 518 selection or native snapshot from
PID 3093. The connected Mac was offline during this review.

The 514 and 518 signing authorities bind the same binary manifest after
normalizing the typed versionCode. The digest is
`4c07e8ee95e02945bdd4057f0305f9417b366b7545e127b7aeeb07204cf21517`.
Parsing that manifest confirms the app declares neither
`android:debuggable` nor a `profileable` element. The existing root-free
startup log can identify both worker boundaries, but it has no waiter or
owner event for the persistence mutex. A native diagnostic would need a
same-process sample of the actual waiting thread, the lock it is waiting
on, and the owner of that instance. A timeout snapshot needs to be
independent of that mutex and the Python GIL so it can run while progress
is stalled. No sampling change was packaged.

For Continue Playing, use the recovery decision from
`saved_navigation.py:517–537`, followed by the chooser branch at
`saved_navigation.py:690–727`. A remembered-provider rejection may have
an accompanying URI parse or pin outcome at lines 456–505. An original
route may have a provider source rejection from
`experience.py:90–137`. If there is a verified native failure ticket,
the route was attempted before recovery. A handoff return alone cannot
establish playback. A provider name in the chooser cannot establish any
of these distinctions.

The off-device [Continue Playing log filter](../infinity-2103514-targeted-20261118/filter_continue_trace.py)
now accepts only the 60 boundary/outcome pairs emitted by the authenticated
518 Python source. The offline check retained the distinct decision and
handoff events in order and dropped 14 malformed or private rows. It can
read an existing private Kodi log directly. The device and its saved
records are not involved in the filter check.

## 2103520 physical acceptance failed

The owner reports that Empty Shell recurred and older saved movies still
failed to navigate or resume on the Fold. 2103520 is rejected for both
features. The Android 17 result remains evidence for the diagnostic's
install-over and logging. There was no naturally slow mutex sample in that
test, and the prior deliberate host hold establishes only a possible wait
path.

The Fold acceptance report contains no trace. The Mac was offline and no
matching capture was available in the workspace or repository records.
Whether a capture was collected is unknown. If the failed session is still
in Android's retained log, [read it without rerunning either test](FOLD-MUTEX-CAPTURE.md#retrieve-the-completed-test-first).

For startup, the required evidence is `interpreter.create`,
`interpreter.returned` and the subsequent bookkeeping marker where present,
alongside `InfinityPersistenceMutex` owner/waiter tickets, native thread IDs
and monotonic times for the same PID and stall window. Preserve trace loss
and observer lifecycle markers to bound conclusions from missing events.
The actual wait site and owner remain unresolved.

For the old save, the required evidence is the `continue_navigation`
sequence from that selection. `recovery_required` names a remembered
fingerprint mismatch, prior failure, or provider/route rejection when one
occurs. `remembered_provider` can give a specific validation reason.
`native_failure_ticket_verified` or `dispatch_failed` identifies a failure
after selection begins. `dispatch_returned` alone confirms that the call
returned. The owner's exact branch remains unresolved.

No production source or release authority changed. The accepted 2103514
lock remains at `3f79964746c37310e4baeb4f7ea6bae87f0a4380`.
