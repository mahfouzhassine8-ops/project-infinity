# Infinity 2103514 targeted diagnostics

The branch starts at the signed 2103514 source commit. The patch is a diagnostic
overlay kept separately from the production tree. The source hashes in
`SCOPE.json` come from the retained ARM64 build that produced the engine in
2103514. No application or engine build was run for this step.

The patch adds the canonical add-on ID to the existing `interpreter.create`
event and records `interpreter.returned` immediately after
`Py_NewInterpreter()`. `interpreter.returned value=1` means Python returned
a thread state. The existing `interpreter.created` marks completion of the
subsequent persistence ledger call. A return marker without a created marker
narrows the investigation to that bookkeeping interval. A create marker
without a return marker narrows it to the call and requires a thread stack to
identify what it is waiting on. Interpret gaps only in a capture that covers
the relevant period and has capacity for both events.

The trace uses the existing process check, time limit, and ring capacity. The
new ID field contains only a bounded add-on identifier obtained from Kodi's
add-on object. The patch carries no profile paths, script arguments, playback
URLs, or tokens. GIL ownership, interpreter cleanup, and persistence
bookkeeping are preserved in the patch.

The host check applied the patch to the exact three source preimages and
compiled the instrumented call site and trace ring. It simulated the two waits
independently, verified a NULL return, checked that a disabled trace emits
nothing, and checked identifier filtering, errno preservation, and the
existing ring limit. This establishes marker behavior, with Android and the
intermittent Fold fault still unverified.

```sh
python -B repairs/infinity-2103514-targeted-20261118/verify_startup_boundary.py /path/to/authenticated/native/source
```

## Evidence needed for a repair

- Continue Playing requires the selected `items` entry from an existing
  `continue-watching.json` snapshot and its matching `sources` and
  `navigation_recovery` data. Match by the logged key and verified identity.
  Retain the original destination privately and compare its SHA-256 against
  the stored route and `failed_routes`. On that exact path, verify the
  installed provider files and contract used by the APK. The existing logs
  show recovery before playback but cannot distinguish the route rejection
  reasons. The prior positive and negative route and offset replays remain
  the fixture evidence.
- Empty Shell requires a stack for an incomplete worker, bound to the same
  process and TID. A retained `script_persistence.initialization_progress`
  snapshot from that process can supply the add-on mapping for the original
  capture. The new markers can distinguish the two intervals if the symptom
  recurs in an instrumented environment. The host result is not a
  reproduction of the Fold stall.

No fix, installer, or signing operation is authorized by the diagnostic
results themselves.
