# Infinity 2103250 — Native Crash Forensics instrumentation

## Scope
This is diagnostic instrumentation only, branched from the exact locked mobile/Cobra runtime 2103229. It does **not** claim the user's SIGSEGV is fixed.

## Why
A fresh Health Center incident after Start Fresh captured Android `REASON_SIGNALED` / signal 11 (`SIGSEGV`) for the new process, but Android did not expose a matching tombstone. The existing collector only requested traces for ANR / `REASON_CRASH_NATIVE`, leaving the fatal-signal case without an exact native frame.

## Delta
- Exact `libkodi.so` stays byte-identical to the locked Python 3.11 GIL-stability engine.
- Add one isolated `libinfinitycrash.so` diagnostic companion loaded before libkodi.
- On SIGSEGV/SIGABRT/SIGBUS/SIGILL/SIGFPE, write a bounded async-signal-safe register record and then restore/re-raise to Android so platform crash handling remains owner.
- Preserve PID/TID, signal, `si_code`, fault address, PC, SP, FP, LR, PSTATE, timestamp and exact native-engine SHA.
- Preserve `/proc/self/maps` for module-offset resolution.
- Record privacy-safe Activity lifecycle breadcrumbs and `ApplicationExitInfo` process-state summary.
- Attempt `getTraceInputStream()` for fatal `REASON_SIGNALED` exits as well as documented native crashes, while explicitly recording null platform results.
- Correlate app-owned native crash record to Android exit history by PID/timestamp.

## Explicitly unchanged
Playback/native engine, providers, timeshift, Multi-View behavior, skin, Command Center, user data and provider data.

## Acceptance
Automated checks can prove preservation and instrumentation integrity. A physical crash reproduction + Health Center 2.5.8 export is required before the actual native root cause can be identified.
