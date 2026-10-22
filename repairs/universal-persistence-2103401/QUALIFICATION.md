# Universal persistence repair — RC8 qualification, not accepted for release

Physical Fold acceptance and real installed-provider validation remain mandatory.
`physical_fold_verified` and `final_lock` are false. The existing user installation,
profile, provider code, databases and service configuration have not been changed.
No merge, accepted APK delivery or permanent-resolution claim is authorized by
these host and emulator results alone.

## Exact identity and gates

| Item | Identity or result |
|---|---|
| Protected 2103400 APK | `e1334ce46bc96edce76a8b7af2d3ebb9871ac7c351526ac2cc6cc58820da009a` |
| Input 2103401 APK | `17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6` |
| RC7 build source | `d9edecbe843eb92457e26cbeab712f0264c55192` |
| RC7 Android test source | `cca956c99e04615885499232a8fe52be9bee607b` |
| RC8 build source | `2ec8cb7e0323c1e2c4ba0c57594eb678541eb222` |
| RC8 original Android test source | `b6785590354556ad841f8a63e94fa0e9700f6d1e` |
| RC8 explicit-check fixture source | `e7adb8a24a7855399d08be90a858c9586e726912` |
| RC8 signed APK | `4c3e465eb78ebbba14df02b810b1851188dc8fbcb20fe17b4cc41f84dc824879` |
| RC8 primary DEX | `8b3f0cf83cf05e99f0b6d7e141d543af0d5f096e2406e73751ea4cfbff774d7c` |
| RC8 receipt ART, signing and downloaded-artifact audit | Passed: 100/100 writes during 1,769 concurrent reads; six failure controls; 7,879 protected classes and 25,931 original fields checked |
| RC7 signed APK | `5b4519fa570ef80c0fbb9287c8cb09bd635f1e7babcbb82370e860de0c69643d` |
| RC7 native engine | `a538ef1cca66a8841ba116e3af028fc76dcebecfcb94ac5db9a0405d023e3fc8` |
| Permanent signer | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Host production-source cases | 263 passed locally and in CI: 51 cases × five identities, five original-baseline controls, three process cycles |
| Retained native and SQLite regressions | 47 passed locally and in CI |
| ARM64 build, signing and downloaded-artifact audit | Passed; 9,404 source files and every APK member independently rehashed |
| RC7 Android 17 matrix | Four negative controls passed; native safe gate passed; completion receipt failed. Rejected. |
| RC8 final explicit-check Android 17 matrix | Passed all five modes; three complete safe Close/reopen cycles and a fourth startup. Independent downloaded receipt/data audit passed. |
| RC8 first installed Android 17 matrix | Four negative controls passed. Initial safe profile crashed before the first Close. Two fresh repeats achieved COMPLETE and engine death, then failed a readback assertion before reopen. Readback investigation found the VFS fixture file empty. The final matrix confirms optimization level 1 and actual per-write readbacks after replacing the removable assertions. Earlier failures remain archived. |
| Real installed providers and physical Fold | Not performed; release blocked |

[Build 39862996414](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39862996414)
and [Android matrix 39863205054](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39863205054)
are pinned to the source identities above. All internal candidates retain version
code 2103401; the complete APK hash distinguishes them.

## Confirmed Fold failure and error semantics

The October 22 physical Fold receipt names `plugin.video.thecrew:service.py`,
`vfs_write_exception`, `TypeError` and `value_type=NoneType`. The exact Kodi buffer
converter accepts Unicode, bytes and bytearray; None is rejected before the
native `File::write` backend. The argument is invalid. Infinity's observer also
has an error: it treats that verified conversion rejection as an uncertain
mutation. The evidence does not establish why the provider supplied None.

The original signed APK reproduces this behavior through its actual Android 17
VFS binding. The host harness executes the matching production converter, write
loop, observer, native hooks and ledger; its native type and POSIX backend are
host adapters. The candidate invokes the same captured original native callable.
Exact original type/method identity, invalid buffer type, original TypeError and
a live matching writer/thread/checkpoint lease establish only
`argument_rejected_before_native_write`.

The original exception type, text, return values and errno are retained. This is
a failed call with verified no mutation, never a successful write or a durability
receipt. Partial/false writes, valid-buffer errors, replaced methods, subclasses
and uncertain effects remain protected. No failure allowlist is expanded.
Android RC3 independently confirmed identical original TypeError messages for
None, int and memoryview; its unrelated safe-close failure is retained below.

## Generic ownership, effects and shutdown

| Area | Implementation and boundary |
|---|---|
| Add-on ownership | Existing native invocation, interpreter, worker and supported-child ownership retained; no provider-name participation exception |
| Diagnostics | Pending operations, buffers and SQLite transactions identify native writer, thread, interpreter/admission, checkpoint generation, phase and target |
| Profile durability | Removed the inherited optional-by-add-on-path heuristic; ordinary provider settings, history and databases are mandatory |
| VFS handles | Writable opens retain drain obligations until successful checked close, including opens that may already create or truncate data |
| Buffered I/O | Interpreter-owned weak receipts permit clean flush/close only with unchanged native/observer method contracts, live descriptor identity/flags and no dirty buffer in the actual native I/O chain |
| Android descriptor names | A procfs ` (deleted)` annotation is resolved only against a canonical no-follow path-only descriptor matching the live file descriptor; literal suffixed filenames, replacements and symlinks are distinguished |
| Lost dirty files | A previously named dirty buffer can become anonymous only after a verified observed removal; unknown namespace loss remains a named blocker |
| Namespace operations | Successful native removal/rename evidence is scoped to the active writer/thread lease; every missing component needs proof and the surviving directory must pass identity and fsync checks |
| Coordination barriers | Import and child-preparation barriers retain admission/pending protection; their effects come from nested native leases and unchanged audit contracts. Unknown or overlapping actual operations revoke absence evidence |
| SQLite | Native invocation scopes cover execution, cursor stepping/finalization, context exit, rollback, close and supported connection transfers; WAL, ATTACH, transaction and durability barriers remain active |
| Shutdown lifecycle | Existing admission closure, cooperative abort, required drains, mandatory owners, protected interpreter retirement, quarantine/probation and termination authorization retained |

Clean-close evidence grants no permission for a callback to write new payload.
Unknown native extensions, opaque children, symlinks, descriptor retargeting,
transaction uncertainty and failed durability checks remain blocked. No new
native-library or subprocess allowlist entry, GUI-thread wait, interpreter kill,
service disable or unfamiliar-add-on quarantine rule is introduced.

Descriptor identity inspection uses O_PATH: closing an ordinary second file
descriptor releases process-wide POSIX record locks on the inode. The production
helper is tested with an external-process lock attempt, which fails as required
after identity inspection. All metadata, no-symlink and live-descriptor checks
remain in place. This is identity evidence only, never durability.

A failed context-manager COMMIT is also distinguished from outstanding data.
The actual SQLite implementation rolls back after this COMMIT failure, while
preserving its exception. The original observer recorded a permanent context
blocker even after that verified recovery; the same source-backed sequence fails
all five identities on RC5. RC6 uses the existing generic SQLite operation
failure diagnostic, with native pending transactions/buffers and retirement
still decisive. It adds no new failure allowlist entry. A reusable scope keeps
the invocation owner through inherited native SQLite calls; real trace/function
callbacks test context exit, rollback and cursor stepping ownership. Return
values, automatic rollback and caller exceptions retain their original semantics.

A later ordinary PathLike open also reproduced the removed-directory failure
in all five host identities. RC7 preserves the unresolved native call as a
coordination lease until the native audit publishes its actual converted target.
Pending/admission protections stay active; actual overlapping effects invalidate
old absence evidence and unresolved completion identity remains blocking. Removal
receipts use the syscall's converted argument, and absence inspection/insertion
share the admission mutex. Bounded native provenance records refusals/revocations
with the responsible operation and owner, alongside the original durability error.
This host replay does not establish the exact Android invalidator; the current
device receipts must establish acceptance.

Directory effects are also distinguished: mkdir creates an empty directory or
fails without creating descendants; rmdir removes an empty directory. Neither
can recreate a removed child. Exact/ancestor identities still invalidate prior
proof, and unknown loss after a removed parent is recreated remains blocked.

## Exact preservation boundary

[NATIVE-SOURCE.patch](NATIVE-SOURCE.patch) is the complete 978-line native patch,
SHA-256 `551ea8a2593e4e307eb91ec9500e26d341ef1420beab65f7a88c98d218d2352a`.
The patcher verifies all 9,404 original native inputs before applying changes.
Exactly these five files change; the other 9,399 must remain byte-identical:

- `xbmc/interfaces/python/InfinityPythonPersistence.h`
- `xbmc/interfaces/python/InfinityPythonPersistenceSource.h`
- `xbmc/interfaces/python/InfinityPythonWriteHooks.h`
- `xbmc/platform/android/activity/InfinityProtectedWrites.h`
- `xbmc/platform/android/activity/InfinityScriptPersistence.h`

RC7 changes `lib/arm64-v8a/libkodi.so`, the existing 64-character engine hash
field in `lib/arm64-v8a/libinfinitycrash.so`, and three signature members. RC8
reuses those native bytes and adds a single `classes.dex` member change. Its exact
scope is six call targets in InfinityCloseGuardService and two new receipt helper
classes. The protected original class definitions and fields are retained directly
from the signed DEX; every other original method, register, branch and exception
path remains checked. `classes2.dex`, shared protocol/installer, manifest, assets,
provider files and other libraries remain unchanged. The recorder's executable
code is unchanged.

[JAVA-SOURCE.patch](JAVA-SOURCE.patch) gives the high-level equivalent of the exact
DEX callsite change; the reference Java file is not edited or recompiled. The new
helper's full source is [InfinityCheckpointReceipt.java](InfinityCheckpointReceipt.java).
The separate exact DEX patch and preservation receipts are produced by the RC8
gate. No existing shared build script or shared runtime helper is modified.

Cobra's original classes/assets and shared lifecycle paths remain untouched.
Playback, PiP, UI, Search, Option B and approved visual assets retain their 2103401
behavior and protected definitions. Static preservation does not establish
physical playback or user-data acceptance.

2103401 already differed from protected 2103400: two native files and 45 APK
members changed before this repair. Those differences are archived separately in
`qualification/rc1/PREEXISTING-*`. The cumulative native scope is seven files;
never attribute the pre-existing UI/DEX/assets differences to this repair.

## Regression evidence and rejected candidates

The five host identities are The Crew, Umbrella, Seren, POV and an invented future
provider. They run the same generic cases. They do not execute the four installed
providers' code or prove navigation, account access or playback. Separate pinned
Seren query/component tests use doubles.

The matrix covers ordinary and buffered writes; invalid, partial and overridden
VFS calls; child threads; multiple interpreters; late payload rejection; supported
and opaque children; pending native work; SQLite WAL/ATTACH, failed statements,
real SQLITE_BUSY and deferred-constraint COMMIT failures with rollback or a retained transaction; namespace
removal/recreation; unknown concurrent effects; symlinks; fsync failure; stale
Android descriptor names; actual unobserved unlink; and repeated process reopen.
Independent readback checks file contents, database integrity and synthetic
resume/history/settings sentinels after process exit.

Current component preservation checks passed 20 cases against 3,262 files verified
identical to the signed input APK; checkpoint participant checks passed 15 cases.
One legacy Resume test reports 13 passes and one pre-existing assertion failure:
it expects `Mark Watched` where unchanged 2103401 uses `Infinity Trakt`. Neither
the UI nor that assertion was changed to conceal it.

| Candidate | Why rejected; retained evidence |
|---|---|
| RC7 | Native mandatory owners, durability and engine retirement passed on Android17; Java completion receipt commit failed. Exact signed DEX reproduced the concurrent AtomicFile reader deleting a live stage. `qualification/rc7/`. |
| RC5 | Context-manager COMMIT recovery left an observer blocker in all five host reproductions. Android pending/lost-file controls passed; safe Close still failed removed-directory durability. Opaque control failed SDK ZIP setup before installation. `qualification/rc5/`. |
| RC6 | SQLite context recovery correction passes 300 host cases. PathLike open after removal reproduces namespace evidence loss. Android negative controls pass, but safe Close still fails removed-directory durability. `qualification/rc6/`. |
| RC1 | Android buffer retirement failed. Host reproduction also found explicit flush followed by denied close. `qualification/rc1/` |
| RC2 | Host clean-close correction passed, but Android first flush still failed. Device fd/name metadata and a host replay isolated stale procfs annotations. `qualification/rc2/` |
| RC4 (superseded before APK acceptance) | Existing-parent makedirs reproduced another false invalidation. The added parent-recreation negative control remains blocking in RC4B. `qualification/rc4/` |
| RC4B | Source/APK/signature audit passed, but the ordinary identity probe released POSIX record locks in a direct production-helper regression. Its reader-lock Android COMMIT fault did not fail even on the original baseline; no ready/Close acceptance was obtained. `qualification/rc4b/` |
| RC3 | Actual Android buffers drained and transaction/opaque controls were isolated, but safe Close failed on removed-directory durability. Combined host operations reproduced removal-proof invalidation by coordination barriers. Lost-file test failed before installation due to ADB transport startup. `qualification/rc3/` |

RC1/RC2 negative controls contained unrelated buffer blockers; only detection of
the intended failures is claimed for them. No safe Close/reopen pass is claimed
for any rejected candidate. Their build/source/APK/signature identities, failures
and causal reproductions remain archived.

## Completion receipt race and targeted RC8 scope

RC7's exact installed Android17 engine PID disappeared only after mandatory native
owners passed and authorization was consumed. The coordinator then reported
`completion_receipt_commit_failed`; logcat records failure to rename the receipt's
`.new` file while Splash resumed. This is a full Close failure, despite native
persistence success.

[Investigation 39867073954](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39867073954)
executed the unchanged signed APK's actual reader/writer methods on Android17 ART.
The reader deterministically removed a staged `.new` file. With concurrent reads,
75 of 100 calls to the original writer failed exact receipt readback. Android's
[AtomicFile implementation](https://android.googlesource.com/platform/frameworks/base/+/HEAD/core/java/android/util/AtomicFile.java)
requires callers to protect this interaction. The replay establishes the race;
the original failed application run does not contain syscall-level attribution
of which reader performed its deletion.

The original atomic writer also serves the installer, so it remains unchanged.
RC8 redirects only the six Infinity Close coordinator calls. Its private exclusive
stage has no reserved `.new` name. Checked write, file fsync and close precede
rename; directory fsync, inode/owner checks and exact readback precede success.
GUI-thread calls and concurrent coordinator writers fail without waiting.
Unexpected names, symlinks, unverified identities, pending legacy recovery,
oversized receipts and actual I/O failures remain errors. Post-rename failure
is explicitly uncertain mutation, never a false no-mutation or success receipt.
The existing native proof validation, failure UI and completion ordering remain.

RC8 compiles only the new helper. Its native engine and 310 host cases are bound
to RC7's exact passed source/build hashes. A separate Android17 production-DEX
race/negative matrix is required before permanent signing, followed by the full
five-mode installed-APK matrix. The receipt gate passed: 100/100 corrected writes during 1,769 reads, all six
failure controls rejected, and the original writer failed 71/100 calls in the
same run. Permanent v1/v2/v3 signing and independent downloaded source/member/DEX
audits passed. The first installed-APK matrix passed its four negative controls. Its safe
profile crashed in talloc_lib_init during library loading, before the first Close
and before the new receipt writer ran. The failure is retained; that first run established no full Close pass. Two fresh-profile runs retained every acceptance assertion and added
startup/tombstone diagnostics. Both reached COMPLETE, with all 16 mandatory
owners satisfied, durability verified and the old engine PID absent. Both then
failed a readback assertion before reopening. Independent downloaded copies
confirm four ordinary/buffered files, preserved settings, and three SQLite
databases with integrity and expected-value checks. The readback investigation found the essential VFS file empty before and after
Close. Its three valid VFS writes were embedded inside Python assertions, which
optimization can remove entirely. Therefore the earlier fixture is not evidence
that those writes returned True, nor that its other assertion checks ran. Twelve
fixture controls now reproduce the original omission at optimization 1/2 and
verify the corrected fixture performs all writes and rejects both False returns
and true-without-data peers at optimization 0/1/2. Those peers only test fixture
integrity. A new full installed-APK matrix captures the actual optimization flag,
per-write native size/position, filesystem size and independent byte readback,
with all twelve original assertions replaced by explicit checks. Every original
Close and data-preservation gate is retained; the signed APK is unchanged. No automatic application assertion retry is added.

The final [five-mode Android17 run 39872761320](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39872761320)
passed with the same exact RC8 APK. All modes report Python optimization level 1,
confirming the earlier assertion-elision diagnosis. Native VFS calls return True
for text/bytes/bytearray, with independent readbacks of 4, 9 and 14 bytes. No
runtime VFS change was needed for the empty-file investigation. The original
None/int/memoryview TypeErrors still match the signed input exactly.

The safe profile completed three Closes, each with all 16 mandatory owners,
verified sealed/durable writes, consumed authorization and independent engine PID
disappearance. File/VFS bytes, three fixture databases, settings, favorites and
Kodi database integrity survived every Close. A fourth startup used a new engine
owner and retained all four history/watched rows. The pending transaction, opaque
writer and externally lost dirty-file controls withheld authorization and named
their actual unresolved work. The original-input control remained blocked on its
misclassified invalid VFS arguments. Independent inspection of the downloaded
receipts and read-only database/file copies passed; see
`qualification/rc8/INDEPENDENT-ANDROID17-EXECUTED-MATRIX.json`. This is compatible
emulator-profile acceptance only. The preceding startup crash remains unwaived.

The read-only ELF analysis resolves both external call targets and the local
address operands. The input and candidate talloc constructors have the same
instructions; the crash is the four-byte read at offset 60 from the auxiliary
random pointer plus seven. Why that pointer was unmapped remains unproven.
Native translation is present, but a platform-only cause is not established.
See `qualification/rc8/STARTUP-CONSTRUCTOR-ANALYSIS.json`. The failed startup remains
a qualification limitation even if subsequent Close checks pass.

[First repeats 39870395699](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39870395699)
and [readback investigation 39871348002](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39871348002)
use the identical signed RC8 APK. Their test-source commits and immutable artifact
digests are in `qualification/rc8/PROVENANCE.json`.

[RC8 build 39868217775](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39868217775)
and [RC8 Android matrix 39868780521](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39868780521)
are bound to the RC8 identities above.

## Android test conditions and final physical gate

The Android matrix uses actual API 37 / Android 17, ARM64 translation, enforcing
SELinux, the exact permanently signed APK and disposable fresh emulator profiles.
It stages the exact existing CC29 and approved compat 0.8.2 components plus a new
unknown service. Safe/pending/lost-file profiles also use the unchanged archived
compatible Version Check `0.5.28+infinity.1`; baseline/opaque profiles retain bundled
`0.5.27+matrix.1`. Runtime service versions and hashes are checked. This is an
explicit compatible-profile test, not acceptance of every bundled stock service.
No real provider or installed user profile is edited or disabled.

The safe gate requires three Close/reopen cycles, a fourth service start, old
engine PID disappearance, consumed authorization, all 16 mandatory owners complete,
no essential blockers, verified durability and independent file/SQLite/settings/
favorites readback, including a real deferred-constraint COMMIT failure followed by
explicit rollback and preserved database values. Negative controls must retain the engine and withhold
termination authorization while naming the actual unresolved operation.

All preceding build/signing/preservation gates and the final compatible-profile
Android17 matrix now pass. The physical Fold and provider accounts are inaccessible here. Follow
[FOLD-ACCEPTANCE.md](FOLD-ACCEPTANCE.md) only after the candidate passes its preceding
gates. Real Crew/Umbrella/Seren/POV functionality, at least five physical Close/reopen
cycles, Resume Hub, watched history, settings and existing user-data preservation
remain required. Until that evidence exists, release and permanent-resolution
claims remain withheld.
