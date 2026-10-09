# Infinity join-target diagnostics — SOURCE ONLY

## What this is

An isolated, local diagnostic source delta for the two verified files from the
retained 2103334 native lineage. **It is not a shutdown repair, an APK, a new
baseline, a GitHub change, or physical Fold acceptance.** It does not establish
which APK produced historical PID 32099. No GitHub push or workflow was started.

The original investigation resolved an upper wait chain but did not identify the
script worker being joined. This delta makes that specific missing relationship
observable in a *new* close attempt. It cannot recover overwritten historical
records or prove that Kodi Favourites Sync caused PID 32099's ANR.

## Files changed in the prepared delta

- `xbmc/interfaces/generic/LanguageInvokerThread.cpp`: sample the worker's OS TID
  at startup; mark broad worker stages; emit target identity before language stop
  and immediately before the existing thread-stop/join scope.
- `xbmc/interfaces/generic/LanguageInvokerThread.h`: hold the diagnostic-only
  atomic snapshot and declare the trace method, under `TARGET_ANDROID`.
- `xbmc/interfaces/generic/InfinityInvokerTarget.h`: a small, lock-free atomic
  `(OS TID, stage)` observation. Only the worker writes it; the closer reads it.

No production CThread, ApplicationMessenger, Python abort helper, finalizer,
shutdown timeout, save/checkpoint code, service coordinator, provider, Android UI,
skin, signer, or baseline metadata is modified by this source delta. Removing the
new Android-only blocks leaves every original nonblank source line in its original
order. Instrumentation still adds overhead and can change race timing; preservation
of statements does not guarantee identical runtime timing.

## What a new trace would contain

New phases use the existing `scripts.*` critical-stream selector:

- `scripts.target_before_stop`
- `scripts.target_before_join` for `Stop(true)`
- `scripts.target_before_nonblocking_stop` for `Stop(false)`

The existing row fields identify `pid`, native trace `session_start_ns`, caller
`tid`, `invoker_id`, and `addon_id`. Its existing `target_thread` text field carries
`os_tid.<number>.stage.<stage>`. For example, **synthetic host-test data only**:

```json
{
  "phase": "scripts.target_before_join",
  "invoker_id": 42,
  "addon_id": "service.test.fixture",
  "target_thread": "os_tid.1234.stage.finalizer",
  "outcome": "snapshot_not_liveness"
}
```

The phases distinguish execution, reusable-worker wait, wrapper mutex acquisition,
language finalizer, and manager completion callback, including exception paths.
They are broad source-boundary observations, **not a Python/native stack trace or
an identification of the underlying lock/request**.

The OS TID comes from the worker itself, not the closing thread. `tid=0` means no
worker startup observation is available. An empty `addon_id` stays unknown. A
sampled TID/stage is not a guarantee that a thread is still alive. `exit_reported`
means the wrapper's manager callback returned, not thread termination or clean
process exit. Do not equate CPython's `thread_id`/pthread identity to an OS TID.

Startup state stays in memory even when the existing trace has not started. This
delta does not call the trace's Begin(), create another log file, add persistence,
acquire the GIL, or capture URLs, arguments, locals, source text, or credentials.
The existing writer's file access, event limits, truncation and retention rules
still apply. Missing/dropped rows remain unknown. The target label is checked to
fit the existing 65-byte buffer, including the longest stage and a 32-bit TID.

## Evidence for the selected source inputs

The two source SHA-256 values match the retained engine's `source-manifest.json`
`after` map exactly. Upstream source blob identities were verified independently
before reproducing the inherited diagnostic transform. See
`evidence/PARENT-IDENTITY.json` for the artifact hash, source hashes and provenance.

This is a **two-file match**, not a reconstruction/verification of the complete
engine, a claim that 2103334 is the current locked base, or proof of PID 32099's
exact APK. `parent/` is deliberately only a test fixture containing these two files.
The known current/accepted lineage must be independently resolved before integrating
this into a real build. Changed target hashes cause preparation to refuse the input;
never force those guards to pass against another revision.

## Run the included host checks

Requirements: a **Linux host**, Python 3.9 or newer, `g++` with C++17 support, and `git`.
The native host fixture uses Linux `SYS_gettid`; it is not a macOS executable or
a phone installer. The Python source preparer itself is platform-independent.
Run from the unpacked folder:

```sh
python3 run_tests.py --out HOST-TEST-RESULTS.json
```

These tests compile the actual transformed .cpp/.h, but use **explicit test doubles
for Kodi's runtime, the trace writer, and all language/runtime boundaries**. They
use real host std::threads and joins. The tests simulate blocked finalization and
manager callbacks; they do not embed CPython or Android.

Completed validation: nine check groups, including eight C++ scenarios repeated
three times (24 scenario passes), wrong-parent and overwrite rejection, original
source-line preservation, git-apply round trip, Android-guard host compilation,
and non-Android-guard host compilation. The atomic snapshot was also exercised
under a concurrent reader. See the machine-readable results in `evidence/`.
No NDK cross-compile, ARM device test, full Kodi regression run, historic five-minute
hang reproduction, sanitizer run, or physical Fold test was performed.

## Prepare files from a full, already-verified source tree

This command reads the specified source but writes only to a **new sibling or
otherwise separate directory**. It does not apply changes to the source tree:

```sh
python3 prepare_delta.py --source /path/to/verified-kodi-source --output /path/to/new-diagnostic-delta
```

The output contains complete replacement files, `diagnostic-only.patch`, and
`DELTA-RECEIPT.json`. Both original file hashes must match. The helper must not
already exist, and the output directory must not already exist or overlap the
input. Whole-engine provenance validation is an additional gate, not supplied by
this two-file preparer. The command does not build/sign/install an APK.

## Integration gates that remain open

1. Select and verify the actual source/rollback lineage. Review this delta against
   it; do not overwrite concurrent work or designate 2103334 a new baseline.
2. Review diagnostics at production boundaries. The helper requires lock-free
   64-bit atomics; unsupported toolchains/architectures fail the static assertion
   instead of silently adding locks. No compatibility with the separate 32-bit TV
   branch has been tested.
3. A separate native diagnostic build is required. The class layout changes, so
   rebuild affected translation units and link a new engine; packaging the old
   libkodi.so cannot activate this diagnostic. Use distinct diagnostic identity,
   exact engine hash, and source/packaging receipts. No engine tag/version was
   allocated or bumped in this source-only package.
4. Keep any diagnostic candidate distinct from a device-ready fix or accepted
   release. Preserve signing/update-over behavior and run appropriate regressions.
5. Capture the existing Health Center native/critical traces during the stuck
   session before further Kodi sessions rotate them. The inspected Android exporter
   reads them from app-private `getFilesDir()`; this package does not assume an
   unprivileged ADB shell can read those files. Capture access is not device-verified.
6. Pair the new target observation with a contemporaneous full dump for the same
   PID/session. Match target OS TID to the dump's `sysTid`, then inspect that worker's
   Python/native stack and lock/request owner. When those frames remain unavailable,
   report the narrower stage and missing inner evidence; do not infer an add-on
   root cause from its name or a record from another process.
7. Only then propose a minimal behavior repair. Physical Fold evidence remains
   necessary before claiming acceptance. A clean close under instrumentation does
   not by itself disprove the historical intermittent hang.

## Primary source references inspected

- Retained engine run 37730777127, source commit 927e7a8be98a440a53759ef976463fe824e2fb28,
  and its native source-manifest and reviewed patch (archive hash in evidence).
- https://github.com/mahfouzhassine8-ops/project-infinity/blob/927e7a8be98a440a53759ef976463fe824e2fb28/repairs/shutdown-diagnostics-2103325/native_patch.py
- https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/interfaces/generic/LanguageInvokerThread.cpp
- https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/interfaces/generic/LanguageInvokerThread.h
- https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/interfaces/generic/ILanguageInvoker.h

All numeric TIDs in host-test output are test-process identities, not phone evidence.
This archive contains no APK, native binary, font, raw user diagnostic log, credential,
or signing material. The source retains SPDX GPL-2.0-or-later licensing notices.
