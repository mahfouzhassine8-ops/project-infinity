# Infinity APK 2103311 — Kodi process isolation

Exact working parent: APK 2103310, commit 3f102ac4776f0562d018802084e765f9fe109a7d.
User reported the filling ring followed by the whole interface closing. Source
confirms native android_main completes cleanup then exit(0), ending its process.

Kodi Main and its native callers, providers, power/background bridge and jobs
now live together in :kodi. Splash/Choose Your Experience and all Cobra components
keep their original default process. No native replacement or shutdown-policy
change; Kodi's final exit(0) and data saving remain intact.

Weather freshness reads the cross-process live status. Responsive/Fold tracing
uses its existing shared enable file so Kodi sees chooser start/stop immediately.
Health Center exports the bounded process state and native cleanup receipt,
alongside existing exit records and Android traces, for PID/time correlation.

A bounded atomic status file replaces chooser reads of Main's process-local
static objects. Reads/writes run on workers. Immutable snapshots carry the owner
PID, process token, launch token and completed lifecycle stage. A separate entry
activity performs process-local property/cache preparation and rechecks the real
local Main before native entry. The chooser remains until a matching, live Main
acknowledges its launch. Closing owners cannot be re-entered. Explicit force
recovery validates PID/token and the original stalled Plan again in Kodi.

The ring still grows only at completed milestones. Full blue requires BOTH the
native CXBMCApp.Destroy.complete receipt for this PID/session AND that process's
actual end. Java onDestroy, elapsed time, an old receipt or process disappearance
without a receipt cannot fill it. Unconfirmed cleanup holds an amber partial
ring and exposes an error; it never pretends to be ready.

Cobra source/DEX, skin 1.0.5.201, all assets/resources/native libraries, installed
Diggz Arctic Mirage 421 and permanent signing are preserved. The declared APK
manifest delta is limited to Kodi process attributes and one private entry
activity. No profile reset or automatic timed force-stop.

Validation: 20 production Robolectric tests for rendered gears, ownership,
receipts, failures, lifecycle and bounded diagnostic export; an Android 35 emulator probe uses the production
status reader/writer, an actual second process and System.exit(0), and verifies
the chooser stays alive and receives completion. The probe SIMULATES the native
cleanup receipt; it does not run the ARM64 Kodi engine. Packaging compares all
other DEX classes, JNI declarations, resources, native/assets bytes and manifest.
The emulator probe runs through adb am instrument with Android JUnit, retaining
its raw completion status and logcat. Packaging requires the one test to pass.
Phone startup, native cleanup, providers, PiP, keyboard/media/background routing
and rapid close/reopen still require physical validation.

Device check: open Infinity; Power → Close Kodi; immediately reopen. The chooser
must stay visible, the ring must finish when Kodi exits, and entering Infinity
again must prepare a fresh Kodi process. Check Cobra, cover/inner resize and a
normal playback session as well. Candidate is not locked before device acceptance.
