# Infinity 2103252 — Native Crash Forensics RC3

## Scope
Diagnostic instrumentation only, still anchored to exact locked mobile/Cobra runtime 2103229. It does **not** claim the user's SIGSEGV is fixed.

## Evidence from RC2 device test
Health Center 2.5.8 confirmed a new post-baseline SIGSEGV for PID 23598 on versionCode 2103251. Lifecycle breadcrumbs prove RC2 loaded the crash recorder after Kodi/NativeActivity onCreate, but the exported native-crash-last.txt was zero bytes.

Binary/source audit found the persistence defect: the recorder constructor opened native-crash-last.txt with O_TRUNC on every normal app start. Reopening Infinity after the crash therefore erased the previous-process record before the asynchronous Java collector could preserve it.

## RC3 correction
- Keep the corrected RC2 signal-handler install order (after Kodi/NativeActivity onCreate).
- Open native-crash-last.txt without O_TRUNC so a normal restart cannot destroy crash evidence.
- Only after a *new fatal signal has entered the signal handler*, atomically clear the old slot with async-signal-safe ftruncate/lseek and write the new bounded register record.
- Continue to restore/re-raise the fatal signal to Android after recording.
- Keep exact locked libkodi.so byte-identical.
- No playback, provider, timeshift, Multi-View, skin, Command Center, or Health Center behavior changes.

## Acceptance
CI must prove the startup open path cannot truncate the crash slot and that ftruncate/lseek/write/fsync occur only in the fatal handler. Physical device verification is still required before promoting anything.
