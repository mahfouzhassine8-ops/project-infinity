# Infinity 2103377 — targeted cooperative shutdown implementation

Parent: 603ef906e33927103b806a19dcf355586a468b75, preserving the green native engine, overflow corrections and exact 274-test Java/lifecycle candidate. Locked APK 2103376 and Skin 1.0.5.211 remain unchanged. No promotion or lock is authorized.

## Corrections

1. XBPython latches checkpoint abort per selected invocation under the existing native monitor-list lock. Monitors registered/recreated after the cooperative notification inherit it. Canonical Command Center/compatibility save participants continue their own existing protocol. No global early abort, asynchronous exception, thread kill or extra join is introduced.
2. Four exact loaded entry-source contracts make Account Manager readiness waits cooperative. The old functions read readiness settings and may sleep for 120 seconds without observing abort. The correction checks abort and uses Monitor.waitForAbort(1). For POV, The Crew and TMDB Helper, shutdown also prevents post-wait service initialization. Red Light's startup child returns through its existing path. Only exact SHA-256-matched loaded bytes are transformed in memory. No installed source, database, settings or add-on is overwritten. Changed source, unknown scripts and Playlist Browser retain original execution and persistence obligations.

The existing native admission, playback freeze, Command Center/compatibility finalization, Python observer, interpreter/child retirement, required jobs, file sync, native save owners, database barriers, termination authorization and Android owner/task protections remain intact. Unknown writes are never declared disposable or durable. Normal running behavior is unchanged in the tested functions. No shutdown deadline is increased. No diagnostic coverage is added.

## Actual evidence and limits

Latest capture: Infinity-Diagnostics-20261013-094401.zip, SHA-256 9336786dbf65e6d20a9fbd3c92a78083387e8b7ab4dc4a88ba71384f2dcc1781. Checkpoint failed after 25,087 ms; playback, Command Center and compatibility were committed, PVR was already durable, and eight Python services remained pending: Artist Slideshow, JetProxy, POV, Red Light, Seren, The Crew, TMDB Helper and TMDB Bingie Helper. Playlist Browser was not among the named pending writers.

Settings/database owners downstream of the Python retirement gate had not completed. These are not proven independent save defects. Three deterministic late-monitor notification failures were reproduced against the exact green XBPython method bodies and corrected. The earlier user-supplied Infinity-Installed-Addon-Code-20261008-071505.zip provides the actual four readiness-wait functions. Today’s Seren service/manifest and POV manifest hashes match the export, but complete current dependency identity is not assumed. Runtime loaded-byte guards avoid relying on stale file identity for the correction. They do not turn unknown operations into disposable work.

The capture does not establish that every pending invocation was in a corrected wait. If another operation still cannot retire safely, the original required-writer barriers continue to reject termination. Do not claim successful physical shutdown or discard that obligation to make a test green.

## Verification and build

- test_cooperative_abort.py: actual original/corrected Register and Notify method bodies compiled with controlled native peers; three deterministic failures before repair; nine corrected cases, including 1,000 concurrent registration/notification interleavings, pass.
- test_startup_waits.py: compiled source transformer, 20 scenarios using the actual archived functions, three actual caller guards, and 12 mismatched/unknown/Playlist Browser rejections pass. Ordinary ready, ready-later and 120-second timeout behavior matches the original. Shutdown exits the wait immediately or at its next cooperative boundary.
- native_ci.py: reconstructs the exact green 9,393-file native map, stages only XBPython.cpp/.h, PythonInvoker.cpp and the new guarded-wait header, preserves all other inputs, and compiles the complete matched engine. Compilation is pending until the workflow finishes.
- Workflow infinity-2103377-final-shutdown.yml independently reruns all 274 unchanged Android tests, preserves their case names and sources, builds the matching Java donor, compiles the full native engine, then packages/signs only after both gates pass.
- package.py verifies exact locked parent, fresh 274-test results, corrected native exports, original JNI/resource/asset/library contracts, the saved Main native-entry metadata delta, and the existing permanent signing identity. Physical-device acceptance remains pending; signing does not imply successful physical shutdown.

Final target is Infinity-2103377-Final-Shutdown-RC1.apk. It must use com.projectinfinity.kodi and certificate d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7. No diagnostic APK is the deliverable. No locked branch is moved and no approved add-on is removed.
