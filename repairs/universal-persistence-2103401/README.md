# Infinity universal persistence repair — work in progress

Protected baseline: 2103400. Input candidate: signed 2103401 from run 39779917183,
commit f3ad961ffc4e0c0121c1f60385ba2ca3add60a6f. No release or Fold qualification.

## Confirmed cause

The October 22 Fold receipt reports a blocking `vfs_write_exception` for
`plugin.video.thecrew:service.py`, with `value_type=NoneType` and `TypeError`.
The matching Kodi buffer typemap accepts only Unicode, bytes and bytearray.
A null argument is rejected before `File::write` reaches its backend. The old
observer treats that conversion error as an uncertain mutation. The invalid
argument is still an add-on/API error; it must still raise the original error.
It is not a successful save and does not discharge other write obligations.

`CheckedVfsWrite` invokes and checks the same captured native method. Only the
original static native type, original native method descriptor, invalid buffer
type, TypeError, and live matching writer/thread/generation lease establish a
no-mutation diagnostic. Subclasses, replaced methods, valid-buffer errors and
partial/false writes retain blocking behavior or the pre-existing verified
optional-target rules. No provider names appear in the implementation.

Two additional generic failures were reproduced: writable VFS handles lacked a
close-drain obligation, and successful namespace operations could leave a missing
parent that the seal could not sync. Writable VFS opens now register an obligation
until successful checked close. Missing parent traversal requires successful
native removal evidence for every missing component, rejects aliases, checks
surviving directory identity and requires fsync. Later overlapping writes revoke
old evidence. Unknown disappearance, stale proof and fsync failures stay blocked.

## Scope

Five exact native input files change; all other 9,399 inputs must match the complete
signed source map. The patch does not edit the shared Kodi buffer converter or
File implementation, providers, databases, UI, playback, PiP, Search or Option B.
Cobra code and existing shared build infrastructure are not edited. Packaging
permits only libkodi.so, the crash recorder's bounded engine-hash field, and
regenerated signature material to differ from the existing 2103401 APK.
DEX, manifest, assets and every other library must remain byte-identical.

Existing generic admission/ownership, interpreter/worker retirement, native leases,
SQLite VFS/WAL/ATTACH barriers, supported subprocess tracking, quarantine/probation,
mandatory-owner checks and coordinator ordering are retained. Unknown writers
remain blocked. A failure cannot be erased by interpreter completion.

The inherited add-on-name heuristic for optional profile data is removed. Only
the coordinator's explicit trusted cache roots and verified nonpersistent targets
are optional; ordinary third-party profile databases/history are mandatory.
SQLite transactions capture the current native writer instead of always -1.
Pending operation, buffer and transaction diagnostics include the actual writer,
thread, interpreter/admission identity and current checkpoint generation.

## Verification status

Local production-source host execution: 143 new/control/cycle cases and 47 retained
native/SQLite regressions passed. The buffer conversion and File write loop are
extracted from the exact production sources; only their host POSIX backend and
native type harness are adapters. The actual observer, native hooks and ledger
run. Baseline null-argument controls block; candidate controls preserve the same
TypeError while admitting a seal only after remaining obligations resolve.

The five provider identities are Crew, Umbrella, Seren, POV and an invented future
provider. These tests do NOT execute their real installed add-on code. Host process
reopen and synthetic resume/watched/settings sentinels are NOT device Resume Hub or
provider-functionality acceptance. Test-only process exit is not Android termination
or interpreter-retirement evidence.

RC1 compiled and passed permanent signing/member verification. Android 17 proved
native VFS rejection semantics and correct pending-transaction/opaque-writer
blocking, but the safe control failed: successful buffer flush erased permission
for the subsequent close. The expanded host cases reproduce that error.

RC2 keeps weak, interpreter-owned native handle evidence after successful opens
and flushes. Clean close/flush is classified nonpersistent only with unchanged
native/observer method contracts, descriptor identity/flags, a live weak reference
and no pending buffer in its actual I/O chain. It never grants a callback new
payload-write permission. Overrides, retargeted descriptors, dirty buffers and
unknown handles remain protected. Explicit closes, layered/cached buffers, phase-2
worker draining and negative controls pass with the 47 retained regressions.

Pending for RC2: full ARM64 compilation, permanent signing/member verification,
actual Android 17 whole-engine tests, real-provider integration, and physical Fold
Close/reopen/data-preservation acceptance. Final lock remains false. No permanent
resolution claim is permitted without the physical evidence.
