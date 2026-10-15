# Infinity 2103326 — Cooperative close repair candidate

Working parent: passed diagnostic 2103325 at `235da39bec78577a7aea511225bbacacf6564f62`. Locked rollback: 2103324. Skin remains `skin.infinity.diggz 1.0.5.201`. No automatic lock, data reset, add-on changes or claim of physical acceptance.

## Evidence and its limits

The supplied device exports show repeated approximately five-second Python service/invoker shutdown waits. A later live Android bugreport records the still-existing Kodi process being frozen as cached, then unfrozen during diagnostic collection. The native diagnostic stream filled before that freezer event. This identifies both serial cooperative waits and freezer exposure, but does not identify the exact unrecorded native wait before freezing. Low CPU alone is not a deadlock diagnosis or proof that all I/O was finished. Private bugreports, credentials, device identifiers and provider data are not committed here.

## Native repair

Reconstruct and verify the entire passed 2103325 native source map before changing eight files. Close script admission before OnQuit; preserve settings/skin snapshots before broadcasting native monitor abort; broadcast to all existing monitors and deliver the same signal to late registrations. Share one existing five-second cooperative grace period rather than accumulating one per invoker. Release script/service registry locks around stop callbacks while retaining snapshot ownership. Individual script stops outside application shutdown retain their prior timeout behavior. Existing Python escalation, GIL handling, joins, database close, settings persistence and final native cleanup remain.

The earlier cooperative implementation is recovered from immutable 2103313 source for review/reuse, not substituted as the APK or native parent. Its Android shell and old native binary are never shipped.

Both normal pre-destruction shutdown and externally triggered final shutdown close admission and signal monitors. Actual host tests run the production changed methods with real locks, threads and elapsed time; Python C API and Android dependencies in that harness are fakes. A separate test uses real embedded CPython for trace/GIL recording. None is a physical Fold test.

## Android shutdown ownership

Normal Close no longer begins with finishAndRemoveTask. While the current Kodi Activity is still alive, it starts an unexported, nonsticky service in that existing Kodi process. A separate default-process short foreground service binds to it using BIND_IMPORTANT without BIND_AUTO_CREATE, verifies the exact held PID/owner lease, and acknowledges readiness through an in-app Messenger ticket. Only then does the original Application.Quit request run. Duplicate or stale messages cannot queue another quit.

The existing native stage-one code stops scripts before finishing the Activity. NativeActivity destruction still triggers stage two and final native cleanup. Moving all final cleanup before Activity destruction would create a circular lifecycle dependency in this engine, so this candidate does not make that change. The temporary foreground client's binding is intended to keep the existing Kodi process out of cached/freezable state during that required handoff; verify the real process state on the Fold.

The guard has a fixed 150-second maximum, below shortService's platform limit. Its timeout callbacks run outside Kodi's potentially blocked UI thread. It unbinds/stops only its own services and notification, never kills Kodi or marks cleanup complete. This is a safety ceiling, not a target shutdown duration or a promise that a still-blocked process can run indefinitely. No wake lock, global freezer switch, battery-optimization bypass, hidden API or new permission is introduced. Two private service declarations are the only manifest additions. All old manifest attributes and permissions remain protected.

The two temporary services are START_NOT_STICKY, and the binding lacks AUTO_CREATE so it cannot restart a dead Kodi engine. They contain no native loader. Initial guard failure leaves normal close un-dispatched instead of silently force-closing. Force Close remains the independent explicit user command. Existing chooser owner-lease/native-receipt completion rules remain unchanged.

## Diagnostic continuity

Retain all 2103325 recording. Increase bounded detail capacity and add separately budgeted high-level current/previous native timelines so low-level thread traffic cannot hide final cleanup. Health Center includes those files and a small independent Android guard report. A guard release, timeout, returned scope or exit-request marker never counts as successful cleanup. Missing/truncated data remains unknown. High-level mirror sequence gaps are expected because it selects events from the detail stream.

## Build and preservation gates

Native source commit: `6aed7f82ae4810233af9dcbfca6b6ed28725b2ad`, run `37620440517`. APK packaging is pinned to that exact run/commit and fails closed on a mismatch. Verify the complete native and 254-file Android parent maps, exact declared deltas, all untouched source/payload bytes, JNI declarations, stable resource IDs, compiled manifest additions and permanent signing. No successful native build is substituted for the required repaired engine. The inherited DEX bridge guard remains active outside the reviewed close/guard/export/version families; unrelated differences must be reviewed, not broadly exempted.

Required Java suites: the 15 inherited regression suites plus 16 cooperative state/identity/lifecycle tests and 9 exporter/clock tests. Physical-device acceptance is separate from host/compiler checks.

## Fold acceptance

Install only the fully verified signed APK over the existing app; do not uninstall, clear data, reset providers or use Start Fresh. Test settled idle and after playback, then immediate chooser relaunch and Cobra isolation. Normal Close should show a temporary Closing Infinity notification while legitimate cleanup proceeds. Export Health Center's diagnostics ZIP after each initial test, before further close cycles replace prior captures. Verify guard readiness precedes quit, pre-script saves precede abort broadcast, repeated per-script grace does not accumulate, final native completion matches the correct owner, the guard ends without restarting Kodi, and watched/resume/settings data survive.

If close still stalls, export before using explicit Force Close and report that recovery action. The critical timeline should now retain the later native stage. No automatic lock, and no claim that an unmeasured late native stall is already repaired.
