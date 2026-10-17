# Infinity TEST4 vs TEST3 — verified signed-APK and shutdown source comparison

**Read-only audit; no APK rebuilt, no user data modified, and no lock changed.**

## Exact source binaries
- Locked TEST4 2103377: `bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286`
- Current TEST3 2103382: `6e28bfea7cdb5e497ee21601a714e738db7a57edc3c5c0d29a9c19d461031854`
- Both actual APKs extracted from Actions artifacts. Each contained 4,178 entries. Every entry was independently SHA-256 checked against its counterpart: 4,173 identical; 5 changed.
- Changed: `AndroidManifest.xml`, `lib/arm64-v8a/libkodi.so`, and three regenerated signature entries: `META-INF/MANIFEST.MF`, `META-INF/INFINITY.SF`, `META-INF/INFINITY.RSA`.
- **No DEX, packaged provider, resource, asset, or other library entry changed.** Both builds are from the same permanent signing certificate.
- TEST4 engine: `2f1597ecc4f8a0ee09f24e399aa738b96a876c7760eaec0ee0ad1a18bafd6929`
- TEST3 engine: `9c2259ac06dde7a6b6788e9971dc1c9a6f67ad316ce16d379dc9d7b3861d7f3d`

## Exact native source differences
Read the two full-tree SHA-256 maps `LOCKED-TEST4-SOURCE-PRESERVATION.json` and `FINAL-SHUTDOWN-SOURCE-PRESERVATION.json` from native run [39004549623](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39004549623). Baseline contains 9,402 paths, candidate 9,404: **7 modified, 2 added, 0 deleted, 9,395 same-hash source files.**

Modified:
- `xbmc/guilib/listproviders/DirectoryProvider.cpp`: Fold deadlock lock-retirement correction
- `xbmc/GUIInfoManager.cpp`, `xbmc/interfaces/builtins/GUIBuiltins.cpp`, `xbmc/profiles/ProfileManager.cpp`: watched presentation and cache lifecycle
- `xbmc/input/InputManager.cpp`, `xbmc/guilib/GUIBaseContainer.cpp`, `xbmc/guilib/GUIBaseContainer.h`: bounded touch/hold selection

Added: `xbmc/guilib/InfinityWatchedIndex.h`, `xbmc/guilib/InfinityWatchedPresentation.h`.

Crucially, these full-tree hashes **match** between locked TEST4 source and TEST3 build source:
- `xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp`
- `xbmc/platform/android/activity/InfinityAndroidCheckpoint.h`
- `xbmc/platform/android/activity/InfinityProtectedWrites.h`
- `xbmc/dbwrappers/InfinityDatabaseBarrier.h`
- `xbmc/interfaces/python/PythonInvoker.cpp`
- `xbmc/interfaces/python/XBPython.cpp`
- `xbmc/utils/JobManager.cpp`

Build deltas `FOLD-DEADLOCK-SOURCE-DELTA.json` and `WATCHED-TOUCH-SOURCE-DELTA.json` corroborate: **TEST3 did not directly change the Essential-First shutdown code or protected-write policy relative to TEST4.** This does not prove compiled runtime timing identical.

## Implication for the real Fold

TEST4 had three physical essential-first Close successes, while TEST3 recorded an installer temp-stage `protected_durability_failed` and separately a 25-second pending owner/deadline failure. TEST4 physical configuration included skin .223, whereas current TEST3 has skin .225 and other active add-on work; the installed environments are not exact twins. The later removed-installer-stage fix is host-tested source **not included in either signed APK**. The most recent two-build GitHub emulator run failed during JSON-RPC startup, **before** Power Close, so it is not evidence of shutdown regression.

**Decision:** Do not revert or overwrite TEST3, and do not transplant identical shutdown code from TEST4. Preserve the newer deadlock/watched/touch work. Investigate the physical Fold runtime, installer staging operation, owner status and external add-on/skin activity. Build a narrow signed corrective candidate only with evidence and physically validate it. No stock-Kodi test or emulator result overrides an accepted physical Fold outcome, but do not ignore independent data-loss concerns.
