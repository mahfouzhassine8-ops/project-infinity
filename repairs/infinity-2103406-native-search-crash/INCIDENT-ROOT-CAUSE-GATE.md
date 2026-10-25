# Infinity 2103406 — Search/native crash investigation and correction gate
Date: 2026-10-25 (America/Detroit)

## Protected base and narrow authorization
- Reference: GitHub run **40184543219**, signed Infinity **2103405**; source commit **d15d1c7745d3ffe85ba03b5cf81b9cb49d75aaca**.
- The user physically confirmed the Infinity Tracked / WatchNixtoons2 menu now works on the Galaxy Fold 8 Ultra.
- Do not modify Cobra, WatchNixtoons2/Infinity Tracked context integration, Save for Later, Otaku, Favorites, skin, user data, player or unrelated functionality.
- A newly mentioned, but undescribed, separate issue remains outside scope. Do not guess about it.
- No uninstall or data wipe. No speculative new APK or claim that a native crash is repaired without evidence.

## Verified pre-2103405 incident records
User-provided archive `Infinity-Diagnostics-20261025-052107.zip` (SHA-256: `e5c97199fed1d9a04631ac683c1a4bf6e5ad31f4aa2b8d2f806ed7de0beb7bdc`) contains TWO real Android tombstone protobuf streams and matching exit metadata. The archive's reported installed version is **2103403**, and Android reports a package update at **05:10:11 EDT**. Thus, these crashes are not evidence about post-2103405 acceptance.

1. **05:12:11 EDT**, pid **22197**, fatal tid **25931** (Thread-28), process uptime **114 s**. SIGABRT; `FORTIFY: pthread_mutex_lock called on a destroyed mutex (0xb4000070869f8920)`. 143 captured threads. RSS reported separately by Android exit history: **803332 KiB**. Tombstone SHA-256: `f81c7962cbaaf0b9d74e12fc6c251069a616e1b3941a2032d6b29461c1bc3ef3`.
2. **05:20:54 EDT**, pid **26366**, fatal tid **4967** (Thread-54), process uptime **514 s**. SIGABRT; `FORTIFY: pthread_mutex_lock called on a destroyed mutex (0xb40000708a3f6e40)`. 126 captured threads. RSS **1990188 KiB** per Android exit history. Tombstone SHA-256: `9d6a97a723d8262fa75b2844f3add7ba7ccf26bf51fbedb2ad50f5c70eb85e2b`.
3. Earlier independent **02:16:29 EDT** pid **20410**, tid **27720**, SIGSEGV fault at `0x2c`, from `Infinity-Diagnostics-20261025-021641.zip`. Android classifies its process exit as `EXIT_SELF`, status **139**, trace unavailable. Do not treat this as the same signature as the two SIGABRT incidents.

## What the tombstones actually prove and do NOT prove
- The fatal pthread call used an already destroyed mutex. This is a native synchronization/object lifetime problem, not a Python exception or Search-results mismatch.
- Both SIGABRT tombstone backtraces have ONLY two surviving frames: `libc.so:syscall` -> `libinfinitycrash.so:restore_and_reraise`. The original caller in Kodi/provider/driver code is NOT preserved. Build ID of the recorder seen in both: `030b7fecb9bfdd816047454dd76f8438dca92479`.
- These detailed records were exported from the **existing** ZIP, not from any newly requested user repro. Tombstone memory maps exist, but ASLR mapping alone cannot restore the overwritten original fatal caller.
- There are 5,700+ memory mappings and over 120 threads. At 05:20, RSS was close to 2 GiB. This warrants a *separate targeted* allocation/thread ownership review. It is not proof that Search alone caused memory growth.
- The Search result-invoker thread explicitly uses the name `InfinitySearchResult` in the signed 2103405 Python module. Fatal threads are `Thread-28` and `Thread-54`, not conclusively that named consumer. Python and native callbacks may still be indirectly related.
- The old Search host tests passed, but the resulting 2103403 application still experienced native crashes. Host tests alone are insufficient for acceptance.

## Confirmed diagnostic code deficiency
- Review `repairs/infinity-2103402-final/native-overlay/infinity_crash_recorder.c` and the production `libinfinitycrash.so`: `restore_and_reraise` and `forward_original_signal` re-signal/exit after the recorder's fatal handler, overwriting the original fatal stack. The two tombstones themselves show `restore_and_reraise`, exactly matching this failure mode. Recorder source/installed binary must be reconciled by Build ID before changing it.
- Correcting signal forwarding is distinct from curing the underlying destroyed-mutex or SIGSEGV defect. Do not misrepresent the former as the latter.
- Consider a scoped crash-recorder correction that delegates fatal signals to Android debuggerd *without* changing Kodi executable instructions, preserving on-device startup maps and diagnostic privacy. Keep rollback to signed 2103405. Any change needs native Android 17 validation.

## Recorder correction now staged (SOURCE ONLY; no APK)
- Added `sigabrt_tombstone_forwarding_fix.py` to this work branch. It enforces the exact audited recorder source Git blob `fc7be4f72c7e19606b718d4ef04487756a17a901` and makes precisely one reversible change: remove SIGABRT from the recorder's intercepted signal list.
- Existing SIGSEGV/SIGBUS/SIGILL/SIGFPE recorders, startup native-map capture and forward/chain methods remain source-identical. Android can then retain the original SIGABRT fatal stack rather than only a recorder re-raise frame, subject to physical verification.
- Static host checks pass: source pin, unique edit, reversibility, intended retained signal list, original diagnostic functions, Cobra untouched. **This has not been built or tested on Android 17.**
- It addresses documented forensics corruption, NOT the mutex lifetime root cause and NOT the earlier SIGSEGV. The two native defect classes remain open until their respective original call sites are determined.

## Code investigation targets (not proven root causes)
- Kodi's native ScriptRunner/PluginDirectory Infinity result lease and lifetime of GUI Window / graphics-context locks.
- Native CPythonInvoker per-add-on subinterpreter shutdown and live child threads during Search/return.
- Existing Search `_leased_directory` owns one request thread and waits for real completion; inspect races at `ActivateWindow`, keyboard release, cancellation and provider result processing.
- Android 17 native thread/memory behavior under repeated searches and provider changes.
- Both `SIGABRT` and `SIGSEGV` scenarios separately; no single unproven blanket fix.

## Release gates
1. Pin exact deployed binaries and diff against signed 2103405, preserving Cobra and all working WatchNixtoons2 content byte-for-byte.
2. Reproduce or otherwise prove the specific native lifetime failure through code/tests with original caller evidence. If evidence is incomplete, identify the unresolved blocker openly.
3. Execute Android 17 focused tests (native abort, Search Enter/button, Search All, cancel/return, rotation/lifecycle, rapid repeated use) with real native owner completion and no fake success.
4. Verify bounded workers, no native mutex UAF, no memory/thread runaway; preserve Essential-First shutdown.
5. Compile full matching ARM64 native library if required, permanently sign with original certificate, package exact matching ZIPs.
6. Physical Galaxy Fold Android 17 acceptance; NO final lock or resolved-crash claim before device evidence.

## Current state
Investigation checkpoint only. Native crash root function remains unproven. No 2103406 APK was built or signed.
