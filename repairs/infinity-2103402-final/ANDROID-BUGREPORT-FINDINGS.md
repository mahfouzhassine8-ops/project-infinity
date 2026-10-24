# Original Android bugreport — 2103402 continuation

The original archive has been read without modifying it. Its SHA-256 is
`938f1859648fcbf1c7118646e3896de0c721c5a4c2d9f0b037446e0d186af0c9`.
Raw dumpstate, memory dumps and protobufs remain outside the repository.
The accompanying JSON contains only allowlisted evidence. All times below are
America/Detroit, as recorded by the device.

## What the new evidence establishes

| Incident | Verified evidence | Remaining attribution gap |
|---|---|---|
| Oct24 15:22:18.390 Search exit, PID9097 | Android reason2, signal7, RSS719MB, importance100, trace=null. All32 text and32 protobuf tombstones checked; no matching record. | Original instruction, bus-error subtype, address and caller are absent. No Search fix claimed. |
| Oct23 21:44:50, PID3071 | Pure-virtual abort, SIGABRT, main thread, uptime3s. Tombstone27 has two post-handler frames. | No original C++ caller, object or ownership sequence. |
| Oct23 22:00:06, PID3485/TID18800 | Scudo internal map failure, SIGABRT, uptime915s; OS RSS2.0GB. Tombstone28 has65685 mappings and150 threads, including29749 Scudo secondary mappings (28713 occupy4096 virtual bytes each). | Strong mapping-pressure lead, but no allocating stack, growth sequence or captured device map limit. Virtual sizes must not be reported as physical memory usage. |
| Oct24 excessive CPU | Four distinct exits at01:35,04:39,05:41,05:51, all importance400. OS retains CPU-window numbers. | No per-thread samples proving which operation consumed the CPU. No services disabled or settings altered. |
| Oct24 08:11 signal9 | RSS3.6GB recorded. | Signal9 alone does not identify who killed the process or prove an OOM kill. |

The October23 recorder executable's build ID matches the signed2103401 recorder.
Reversing only the already-existing engine SHA field restores the exact original
recorder hash. This confirms the recorder code path, **not** the October23 Kodi
engine identity: its producer must not be inferred from a recorder build ID.
The current signed libkodi has no GNU build ID; its exact APK/native SHA and
runtime mapping are required for future symbol matching.

## Original context partly recovered

The text tombstones contain the recorder's on-stack ASCII buffer near its frame
pointer. Decoding the displayed little-endian words recovers complete original
PID/TID, signal, si_code, PC, SP, FP and LR fields for both October23 incidents.
Both original PCs are `0x716c9129f0`, with LR `0x716c9129cc`, in the mapped libc.
These are original abort-time registers, not an identified C++ caller.

The corresponding protobufs each contain only two crashing-thread frames and
256-byte memory fragments; none covers the recovered original stack pointer.
They contain no allocation-cause or stack-history fields. A full original caller
cannot be reconstructed from these fragments. The recorder's `fault_address`
field is intentionally excluded from recovered SIGABRT evidence: this union
contains sender information for that signal and is not a verified fault address.

## Confirmed diagnostic defect and isolated correction

The original recorder saves the original registers, restores the prior signal
handler, then calls `tgkill`. Android consequently receives a new signal and
context inside `restore_and_reraise`, matching both tombstones. This is a
confirmed loss of downstream diagnostic context, not the cause of the crashes.

An isolated source transform now forwards the original `siginfo_t` and
`ucontext` to an existing SA_SIGINFO handler after restoring its disposition.
If it returns, the fatal signal is still delivered with the default disposition;
the previous handler is not called twice. Legacy/default/ignore fallbacks retain
their existing behavior. A constructor guard permits installation only for the
exact `com.projectinfinity.kodi:kodi` process. No Kodi engine or Cobra changes.

Five focused host checks pass. A real mmap-beyond-EOF SIGBUS reproduces the old
loss of code/address/PC; the candidate preserves them in the previous handler.
Queued SIGABRT metadata, handler mask, fatal termination, unwritable record path,
legacy fallback, exact process guard and source/binary bounds are checked.
These are Linux host results: ARM64 compilation, ART/debuggerd integration and
Android17/Fold execution remain **NOT RUN**. The candidate is isolated source,
not a modified baseline APK or an accepted repair.

Android Health export also now retains OS PSS/RSS (KB) and importance for each
retained exit. Zero memory samples are represented as unavailable. A resource
getter failure cannot discard the existing signal/process identity. The existing
Java host harness passes with the new cases and all its previous checks intact.
No new polling, background job, shutdown change or database write was introduced.

## Why the Search context is still missing

Three findings must remain separate:

1. The recorder demonstrably loses original context when passing a fatal signal
   to its downstream handler. The older tombstones show that mechanism.
2. The previous Android exporter omitted non-native-reason exit metadata and
   labelled an empty source as available; earlier staged fixes retain honest
   signal/empty-source status.
3. Neither finding proves why the Search incident has no OS tombstone or why its
   app-private crash file is empty. Handler ownership, failed record I/O, and
   Android collection failure for PID9097 are not established by these files.

The original bugreport has now been used; do not ask for it again. A fresh
non-APK capture during reproduction on the installed baseline remains viable,
but this workspace has no ADB/device or Android17 emulator. No interim diagnostic
APK is requested. The50 Search,30 playback-return and20 rotation cycles remain
NOT RUN. Prior UI/Home corrections and the protected baseline remain intact.
No signed2103402 package exists and final release gates remain open.

## Primary technical references

- [AOSP debuggerd handler](https://android.googlesource.com/platform/system/core/+/refs/heads/main/debuggerd/handler/debuggerd_handler.cpp): passes the supplied original signal and context into crash_dump; checks SA_SIGINFO before consuming siginfo; queues the fatal signal after collecting evidence. Reviewed blob `88278ca667e84f432125c791298bd70ad1e4deca`; OEM behavior still needs runtime verification.
- [AOSP tombstone protobuf](https://android.googlesource.com/platform/system/core/+/refs/heads/main/debuggerd/proto/tombstone.proto): header, crashing-thread, memory-fragment and mapping field definitions. Reviewed blob `9deeeec9e185f79747acf5fb6a7e71586eb7da16`.
- [Scudo report implementation](https://android.googlesource.com/platform/external/scudo/+/refs/heads/main/standalone/report_linux.cpp): map-error text reports a failed mapping operation; it does not identify an allocating application caller.
