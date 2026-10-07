# 2103324 — Kodi instance ownership and chooser recovery

## Exact locked base

- User requested this correction on newly locked **Cobra Pro 2103323**.
- Lock commit: `65e58a8fc21c3c62c7fc9db2014585e71e0b6a2b`.
- Exact APK/source build commit: `5de1ce637d136ab6ae737303e758ad96b092cc57`.
- Successful build run: `37574574345`; APK SHA-256: `1ab9354722f5f36c0441f0a604ff38ee8ee5beec11eceaeb415aeef247ae8055`.
- Exact 254-file source map SHA-256: `1d5e56fd0cb8af866cec522d093c41017161e1557555ee77104b41c733e6906d`.

## Report and evidence

The user reports using Cobra only, then seeing “Infinity is still closing” on
the chooser. At 2026-10-07 01:25:05.170 America/Detroit, about five seconds
before the screenshot, diagnostics record `handoff.waitClosingOwner` and
`handoff_ms=-1`. No new Kodi handoff is captured in those current sessions.
The clipboard summary is truncated and omits the current ownership JSON; it
does not prove that the current false warning was caused by PID reuse.

The source has two confirmed defects: it infers the recorded Kodi instance is
alive from any extant PID (including every non-ESRCH signal-check error), and
startXBMC can show a stalled-close recovery dialog on ordinary chooser entry.
Historical close rows are evidence of earlier sessions. In particular the
previously recorded PID 24758 cleanup completed after 60.371 seconds; an
observer timeout alone is not evidence of failed cleanup.

## Correction

The Kodi process acquires a private OS file lock named for its random instance
token before publishing schema 2 status. A static descriptor retains that lock
for the entire process lifetime, including native destruction. The chooser
probes only that exact instance lock without loading or starting Kodi. A free
or missing lock cannot make a record pending. PID reuse and device restart
cannot retain a terminated process's lock. No process signals are used to infer
ownership. The chooser never opens a second descriptor for its own lease,
avoiding platforms where closing another descriptor releases process locks.

Schema 1 rows remain readable as historical evidence; they cannot be promoted
to a current owner because they have no verifiable instance lease. Matching
native cleanup receipts still confirm completion only after the instance lease
is gone. Force requests remain guarded by the actual receiving process's PID
and owner token and can never be represented as successful cleanup. Missing
or corrupt status rechecks cached ownership instead of retaining stale pending
state forever. Neither polling age nor a timeout triggers an automatic kill.

Ordinary chooser entry with a real pending Kodi close displays the existing
chooser and progress indicator without opening the recovery dialog. Explicit
Infinity selection, Infinity deep links and an Infinity launch default retain
their recovery behavior. Explicit and remembered Cobra entry remain independent.

## Preservation gates

Only `InfinityKodiShutdown.java.in` and `Splash.java.in` change. Every Splash
Java token outside `startXBMC` must remain identical. The other **252 source
files** must have the exact locked hashes. Cobra Sports feed/ticker fixes,
More position, alert placement, playback, providers, native cleanup, close
timing, user preferences, assets, resources and skin remain preserved.

The package recipe compares every protected compiled class after resolving
observed D8 helper relocations to their exact instruction bodies. Only the two
declared class families and version metadata may differ. All protected APK
entries, native/JNI contract, manifest contract, resources, permanent signer,
package identity and skin are checked against the exact 2103323 APK.

## Verification

The workflow runs the ten locked suites (**167 tests**), four existing shutdown
suites (**28 original tests**) with schema/liveness fixtures updated for the
instance-aware reader, **five additional chooser routing tests**, and
**14 new ownership tests**: **214 tests expected**, zero skipped/failed/error.
The new ownership suite executes production lock probes against real locks held
by separate OS processes. It covers stale records with an unrelated live PID,
released locks, different owners, historical receipts, pending genuine cleanup,
live acknowledgement, missing/corrupt records, invalid tokens and force status.

CI verifies controlled Android behavior and actual host OS file locks. Physical
acceptance on the user's Android 17 Samsung device remains to be confirmed.
2103324 is a forward test candidate; 2103323 remains the locked base and the
2103322 rollback remains preserved.

