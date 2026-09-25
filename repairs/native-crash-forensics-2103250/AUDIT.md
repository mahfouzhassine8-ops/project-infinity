# Infinity 2103253 — Native Crash Forensics RC4

## Scope
Diagnostic instrumentation only, still anchored to the exact locked mobile/Cobra runtime 2103229. It does **not** claim the user's SIGSEGV is fixed.

## Evidence from the RC3 device test
Health Center 2.5.8 confirmed a new post-baseline SIGSEGV on RC3:
- versionCode 2103252
- PID 6253
- signal 11 / SIGSEGV
- Android trace request returned null
- native-crash-last.txt was still zero bytes

RC3 also proves the companion library itself was loaded after Kodi/NativeActivity onCreate, and the PID 6253 native maps contain libinfinitycrash.so. Because RC3 no longer truncates the file at normal startup, the zero-byte record can no longer be explained by the RC2 restart-erasure defect.

The same failing process repeatedly unloaded/reloaded the active skin after DialogSelect, including a custom_1128_WindowCustomizer session. The final reload completed at 19:43:54.898 local and Android recorded the SIGSEGV at 19:44:02.278 local. This narrows the reproduction path but does not identify the exact native instruction.

## RC4 diagnostic hardening
- Keep the corrected post-Kodi handler install order.
- Do not rely on a file descriptor opened during app startup.
- Precompute only the app-private crash-record path.
- When a fatal signal actually reaches the handler, open the record with direct openat syscall, write PID/TID/signal/fault/PC/SP/FP/LR, fsync, close, then restore/re-raise to Android.
- Add a bounded three-minute SIGSEGV ownership monitor. Every five seconds it queries the current process-wide SIGSEGV disposition.
- If another user-level handler replaced the Infinity recorder, preserve that handler as the chain target and put the recorder back on top.
- Append privacy-safe native.sigsegv ownership/rearm breadcrumbs into the existing lifecycle breadcrumb file so Health Center 2.5.8 exports the evidence without another add-on change.

## Explicitly unchanged
- exact locked libkodi.so
- playback/native engine
- providers
- timeshift
- Multi-View behavior
- Infinity skin
- Command Center
- Health Center 2.5.8 package
- user data/provider data

## Acceptance
CI must prove the crash handler contains no heap/JNI/unwinding calls, opens evidence only after the fatal signal is already in the handler, preserves/re-raises to Android, and retains exact locked 2103229 protected bytes. Physical device verification remains required before any promotion.
