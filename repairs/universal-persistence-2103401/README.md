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

Local production-source host execution: 263 new/control/cycle cases and 47 retained
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

RC2 also compiled, signed and passed exact preservation checks, but Android still
rejected first flushes. Read-only device diagnostics found a live descriptor
reported with a ` (deleted)` suffix even though the original name still existed
with matching device, inode, mode and one link. Replaying that descriptor report
reproduced the failure in all five host identities.

RC3 resolves that annotation only through the live descriptor and a canonical,
no-follow opened name with matching metadata. Literal suffixed filenames keep
their identity. Replaced files, symlinks and unknown paths do not gain permission.
A genuinely unlinked dirty buffer may become anonymous only after an observed
successful removal; an unverified loss of its namespace remains a named blocker.
The added multi-interpreter, composite I/O, stale-descriptor and negative cases
pass with all retained gates: 183 source-backed cases plus 47 native regressions.

RC3 compiled and signed, with all five source inputs and exact APK-member deltas
independently verified. Actual Android 17 drained both buffers, preserving the
original TypeErrors as no-mutation failures. Pending SQLite and opaque-child
controls were isolated and correctly blocked. The safe test then exposed a
namespace durability failure. No RC3 safe Close/reopen pass is claimed.

The combined host sequence reproduces that failure: importing a supported native
module or preparing a supported child used an unknown-target coordination lease
that erased earlier removal evidence. RC4 represents namespace effects separately
from admission/pending ownership. Only the existing native import and child
preparation barriers observe effects through their nested native leases and
unchanged audit contracts. They retain all admission and pending-owner gates.
Unknown operations, unknown concurrent writers and nested mutations still revoke
or prevent absence proof. A live preparation barrier still prevents sealing.
No new native-extension or subprocess allowlist entry is added.

RC4B additionally preserves removed-child evidence across mkdir: creating an empty
directory or finding an existing one cannot recreate its children. Exact and
ancestor identities still invalidate; unknown loss after parent recreation blocks.
The combined case now includes ordinary makedirs(exist_ok=True).

RC4B runs directory removal in the combined SQLite/child/buffer sequence and adds
concurrent barrier, unknown-effect and real SQLITE_BUSY COMMIT/rollback controls.
All 218 source-backed cases (RC4B) and 47 retained regressions pass locally. ADB startup
handshake retry is limited to test infrastructure before installation; no Close
acceptance check is relaxed.

RC4B built, signed and passed exact source/APK audits, but a focused lock test
then rejected its descriptor identity probe: closing an ordinary second fd
releases POSIX record locks held by the process on that inode. RC5 uses O_PATH
for no-follow identity inspection, retaining the same metadata/namespace checks
without releasing those locks. The real production helper now passes an external
process lock probe across every host identity. The earlier probe fails all five.

A reader-lock Android fault injection did not produce SQLITE_BUSY even on the
original baseline, so it was not a valid failed-COMMIT device control. The Android
fixture now uses deferred foreign-key enforcement and requires a real failed
COMMIT, a still-active transaction, explicit rollback and independent value
readback. Host BUSY tests are retained; recovered and unresolved deferred-COMMIT
cases are added. All 233 source-backed cases and 47 retained regressions pass.

RC5's context-manager regression exposed a separate ordinary SQLite failure:
`with connection:` can fail COMMIT, complete its automatic rollback, and still
leave a permanent observer blocker. The same production-source replay fails all
five identities. RC6 records that original exception through the existing generic
SQLite operation diagnostic; native transaction/buffer checks and verified
retirement still decide safety. No failed write is reported as successful.

A reusable owner scope now covers inherited cursor stepping/finalization,
rollback, context exit, close and the supported connection transfer operations.
It holds invocation identity through the original native call, including released
GIL I/O. It grants no persistent-path permission; every VFS admission and drain
check remains active. Return values and exceptions come from the original call.
Native trace/function callbacks verify owner identity for context exit, rollback
and cursor stepping. All 253 source-backed cases and 47 retained regressions pass.

RC5 Android safe Close still failed at removed-directory durability, although
its pending-transaction and lost-file controls passed. RC6's context fix does
not establish resolution of that separate failure. A composite host replay now
reproduces the same failure across all five identities when an ordinary PathLike
open follows completed namespace removal.

RC7 keeps an unresolved, natively audited path operation as a coordination lease
until the actual converted target arrives. Its admission/pending protection is
unchanged; native audit children still classify every actual effect, and missing
completion identity still blocks. Removal receipts use those actual converted
arguments, including PathLike rename/removal. Overlapping recreation and unknown
writers still invalidate evidence. Absence inspection/insertion now share the
admission mutex, preventing an intervening admitted mutation. Bounded provenance
identifies why absence proof was refused or revoked and which native operation
and owner caused it; original durability error strings are retained.

The composite PathLike replay, PathLike removal and recreation controls, and
existing unknown-effect diagnostics pass with all retained gates: 263 production-
source cases plus 47 native/SQLite regressions. This host reproduction alone is
not proof of the exact Android invalidator; RC7 device receipts remain decisive.

Pending for RC7: full ARM64 compilation, permanent signing/member verification,
actual Android 17 whole-engine tests, real-provider integration, and physical Fold
Close/reopen/data-preservation acceptance. Final lock remains false. No permanent
resolution claim is permitted without the physical evidence.
