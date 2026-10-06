# Infinity 2103314 — shutdown evidence candidate

User-authorized baseline: APK **2103312**, `1.0.9-Cobra-Pro-Teams-RC1`, permanent signer, Infinity skin **1.0.5.201**, Diggz Arctic Mirage 421 and Cobra retained. 2103313 was not accepted and is not this engine's parent. This candidate observes the original 3312 shutdown behavior, allowing the next physical run to identify the six-minute wait. It is not a claimed six-minute repair.

## Grounded findings

The supplied logcat records close request 21:28:12.405, quit acceptance 21:28:14.300, pre-destroy cleanup 21:28:14.307 and seven separate five-second add-on timeout messages between 21:28:19.327 and 21:28:54.649. Add-on startup and network work continues during that interval. The capture ends 21:28:55.803, approximately 43.4 seconds after close request. It neither contains the full six-minute wait nor pins an APK version to that exact process. The separate 17:01 Health export identifies 2103307 only for its own capture.

3312's normal Close route waits for Android stop before JSON-RPC Quit, performs a pre-destroy script/service cleanup, then later performs final native shutdown and joins the Kodi thread. The chooser refuses Kodi handoff while the old PID is alive and in a closing phase. The 15-second observer records only. These facts prove the state gate and native waits, not the cause or necessity of the entire six minutes. Two service-stop passes alone do not prove duplicate wait: the first clears the service registry.

3313's simulated stop test used immediate fake Python GIL APIs. It did not validate end-to-end native cleanup. A first GIL acquisition can also occur before the five-second cooperative timer; another can occur afterward. The current device has not been proven blocked at either call.

## Diagnostic delta

Eight original native source files receive call boundary scopes; one header supplies process-owned evidence. The original shutdown statements and their ordering remain. Trace starts only on real shutdown, with APK code, PID, native TID, monotonic boot clock, session, unique span, invoker ID and completed duration. It covers both GIL acquisitions, cooperative waits, invoker joins/destructors, interpreter teardown, settings saves, player/network/audio shutdown, script manager finalization, service deinitialization, Kodi thread join, native destroy, and the request to exit the process. No new process kill, shutdown deadline, Python abort policy or premature completion is introduced.

The writer uses direct bounded append writes independently of Kodi's log/registry/Python locks. No sampling thread or retained file descriptor. It preserves errno. The current and previous 2 MiB traces live in the app's internal files directory and are readable by the isolated chooser while Kodi is closing. Best-effort evidence failures never imply successful cleanup.

Only three Android source owners change: Health export attaches both traces; Splash's existing worker-built report includes entered/unended stages and completed durations; the runtime engine identity now uses the actual packaged engine SHA instead of the stale inherited hard-coded hash. No new UI or native JNI method.

## Verification

Host CPython 3.12 tests hold a real GIL while another real PyEval_RestoreThread waits. They verify the begin record is readable during the wait and an end/duration appears only after release. Concurrent stage records, absence of startup writes, errno preservation and idempotent trace start are checked. This verifies evidence behavior, not the phone's Kodi runtime or total shutdown. CI builds the entire ARM64 engine and Android diagnostics, runs Health Center report/export tests, verifies the complete locked source preimages, and rejects changes to protected APK assets/resources/other native libraries. Disassembled compiled classes outside the declared diagnostics owners must remain identical, including Cobra. The permanent signer is required.

## One physical reproduction

Install 2103314 over the current APK. Open Infinity, let Home load, choose **Close Kodi**, and immediately reopen the app. If it remains closing, export **Health Center → Export diagnostics ZIP while the wait is happening**, ideally after 30 seconds and again at the reported six minutes; do not force-close before the first export. One later export after it exits is useful because the native trace is retained. Send the ZIP, which identifies the build/PID/session and stage durations. There is no reason to wait beyond the already-observed six minutes for diagnosis. This file can establish the measured native call; a thread stack may still be required to distinguish the resource it is waiting on. A computer is not required for this capture.

Physical-device-verified=false; six-minute-root-cause-proven=false; locked=false. Keep 2103312 as the accepted lock until a fix is physically accepted.
