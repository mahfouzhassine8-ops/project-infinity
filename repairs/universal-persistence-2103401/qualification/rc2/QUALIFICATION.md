# Universal persistence repair — REJECTED internal RC2

This work is not an accepted release and is not permanently resolved. Physical
Fold acceptance and real installed-provider validation remain mandatory.
`physical_fold_verified` and `final_lock` remain false. No existing installation,
profile, provider code, database or service configuration was changed.

## Reproducible identity

| Item | SHA-256 or source identity |
|---|---|
| Protected 2103400 APK | `e1334ce46bc96edce76a8b7af2d3ebb9871ac7c351526ac2cc6cc58820da009a` |
| Input 2103401 APK | `17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6` |
| Internal RC2 APK | `41fcc6568bf977c8095bfec0052f9556e4cf33ac103c6e45796f48d2bf18d7fa` |
| RC2 native engine | `0fbae502828c23072078b828bb4110a31a91beb6347e1ddc835139110dec2243` |
| Build source | `b7476c548179f2615714dd5578eaf83912a46f8c` |
| Android test source | `1354467417f3581543413d54a7bb01c7958521b3` |
| Permanent signer | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |

[Build 39841286004](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39841286004)
passed. [Android matrix 39842743705](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39842743705)
failed its safe control. The version code remains 2103401; it does
not distinguish this internal candidate from its parent. Use the complete hash.

## Confirmed cause and generic correction

The October 22 Fold receipt identifies `plugin.video.thecrew:service.py`,
`vfs_write_exception`, `TypeError`, and `value_type=NoneType`. The exact Kodi
buffer converter accepts Unicode, bytes and bytearray. It rejects None before
the native `File::write` backend is called. The caller argument is invalid; the
observer incorrectly classified the verified conversion failure as a potentially
mutating write. The diagnostic does not establish why the provider supplied None.

The original signed APK reproduces the problem on Android 17 through the actual
installed VFS binding with a previously unknown service. The host harness also
executes the production buffer converter, File write loop, observer, native hooks
and persistence ledger; only its native type and POSIX backend are host adapters.

Checked dispatch invokes the same captured original native method. Only the exact
original type/method, invalid argument type, original TypeError and matching live
writer/thread/checkpoint lease establish `argument_rejected_before_native_write`.
The exception, return value and errno are preserved. This is a failed operation
with verified no mutation, never a successful save or a durability receipt.
Partial/false writes, valid-buffer errors, subclasses, replaced methods and
unverified effects remain blocked. No generic failure allowlist is expanded.

Writable VFS opens now retain drain obligations through successful checked close.
Native successful namespace operations can establish narrowly scoped absence
evidence for a removed parent. Every missing component needs evidence, overlapping
later operations revoke it, and the surviving directory must pass identity,
no-symlink and fsync checks. Unknown disappearance and failed sync remain blocked.

Android testing rejected RC1 because ordinary buffer retirement was denied.
Expanded host tests reproduced an explicit successful flush followed by denied
close. RC2 records interpreter-owned weak native-handle evidence after successful
opens and flushes. A clean flush/close is nonpersistent only when its native or
captured observer method contract, actual descriptor identity/flags and complete
native I/O chain remain valid, with no outstanding buffer obligation. It grants
no permission for callbacks to write new payload. Overrides, retargeted
descriptors, dirty buffers and unknown handles remain protected.

Add-on names and private profile paths no longer make ordinary profile data
optional. Only explicit trusted cache roots and verified nonpersistent targets
retain optional classification. SQLite transactions capture their actual native
writer. Pending operation, transaction and buffer diagnostics identify writer,
interpreter/admission, thread, checkpoint generation, phase and target path.

Existing generic invocation ownership, child-thread and supported-subprocess
tracking, native/SQLite WAL and ATTACH barriers, cooperative service shutdown,
interpreter retirement, quarantine/probation, mandatory owners and coordinator
ordering are retained. No provider-name exception, new GUI-thread wait, forced
interpreter retirement or service-disable mechanism is added. Unknown native and
opaque external writers still require an established persistence contract.

## Exact preservation boundary

The independently downloaded source archive contains 9,404 verified native inputs.
Exactly five change; all other 9,399 remain byte-identical to input 2103401.
[NATIVE-SOURCE.patch](NATIVE-SOURCE.patch) is the full 665-line patch, SHA-256
`b6f36d03cbe23d808fc28c3805cab6cc77d5becb4b597d135c93f8ff37649506`.
[SOURCE-DELTA.json](SOURCE-DELTA.json) records every pre/post hash.

| Native file | Change |
|---|---|
| `InfinityPythonPersistence.h` | Checked native VFS outcome and interpreter-owned clean-handle state |
| `InfinityPythonPersistenceSource.h` | Observer dispatch and writable VFS drain obligations |
| `InfinityPythonWriteHooks.h` | Native namespace proof and verified clean flush/close classification |
| `InfinityProtectedWrites.h` | Required profile data, actual ownership/targets and bounded directory durability |
| `InfinityScriptPersistence.h` | Native namespace evidence storage |

The APK changes exactly two payload members: `lib/arm64-v8a/libkodi.so` and
`lib/arm64-v8a/libinfinitycrash.so`. The recorder changes only its existing
64-character engine-hash field inside `.rodata`. Three signature members are
regenerated; all other 7,576 members are byte-identical. Every DEX, manifest,
asset, provider file and other native library is unchanged. All 71,197 original
global native exports and the dynamic dependency list are preserved. Permanent
signing schemes v1/v2/v3 and zip alignment passed.

[Independent preservation evidence](INDEPENDENT-CANDIDATE-PRESERVATION.json)
contains the exact changed APK members and hashes. Complete per-member inventories,
all source inputs, signing receipts and SHA256SUMS are in the pinned build artifact.
Cobra files/assets and existing shared build scripts were not edited. Playback,
PiP, UI, Search, Option B and approved visual resources retain their 2103401 bytes.

2103401 already differed from protected 2103400 before this repair. The cumulative
delta is seven native files and 45 APK members; two native changes and the other
pre-existing APK differences are recorded separately. See
[cumulative comparison](CUMULATIVE-2103400-RC2-DELTA.json) and the
archived pre-existing comparisons under `../rc1/`. Do not attribute all
45 differences to this repair or claim input 2103401 equals protected 2103400.

## Verification and limits

| Gate | Result and scope |
|---|---|
| Production-source host cases | 143 passed: 27 cases across five identities, five original-observer controls, three process cycles |
| Retained native/SQLite regressions | 47 passed, including ownership/races, buffering, WAL/ATTACH, drain and reopen |
| Current component preservation | 20 passed against 3,262 files verified identical to the signed input APK |
| Persistence participants | 15 passed against the exact current checkpoint runtime |
| Full ARM64 build, ABI, signing, APK/source preservation | Passed; downloaded contents independently rechecked |
| Actual Android 17 baseline | Passed expected-failure control; original VFS TypeErrors block Close |
| Actual Android 17 RC2 safe/pending/opaque | FAILED safe control; expected transaction/opaque failures detected, with unrelated buffers still unresolved |
| Real installed providers and physical Fold | Not performed; acceptance blocked |

The five host identities are The Crew, Umbrella, Seren, POV and an invented future
provider. They all run the same generic cases, without production name-based
exceptions. They do not execute the four providers' installed code or prove live
provider navigation/playback. The separate pinned Seren component/query tests use
test doubles. Synthetic resume/history/settings readback does not establish
physical Resume Hub preservation.

Host cases cover normal writes, original invalid VFS arguments, partial writes,
subclass/override rejection, buffered and layered I/O, explicit close after flush,
phase-2 worker drain, native pending work, child threads, late payload rejection,
supported and opaque subprocess activity, committed/failed/uncommitted SQLite,
profile transactions, namespace changes, missing/stale namespace evidence,
symlinks, fsync failure, cached methods, descriptor retargeting and repeated
process reopen. Dirty or uncertain effects must prevent a durability seal.

One legacy Resume test reports 13 passes and one failure against unchanged input
files: it expects the older `Mark Watched` label where 2103401 uses `Infinity
Trakt`. Neither UI nor the legacy assertion was changed to conceal that result.
The matching current component tests pass.

RC1 remains rejected, with its source/APK hashes and Android failures preserved in
`../rc1/`. Its negative controls also contained unresolved future-service
buffers; their expected blockers were detected, but they were not isolated pure
transaction/opaque-writer controls. No safe Close/reopen pass is claimed for RC1.

## Android conditions and physical acceptance

Android tests use an actual API 37 / Android 17 emulator, ARM64 translation and
the exact signed APK, with SELinux enforcing. They use disposable profiles and
never touch the user's device. Profiles stage the existing CC29 and approved
compat 0.8.2 components plus a new simulated future service. Safe/pending profiles
also stage the unchanged archived compatible Version Check `0.5.28+infinity.1`;
baseline/opaque profiles retain bundled `0.5.27+matrix.1`. Runtime versions and
service hashes are verified. This is an explicit compatible-profile test, not
qualification of every service bundled in an untouched fresh install.

The safe test requires three Close/reopen cycles and a fourth successful service
start, original engine PID disappearance, consumed authorization, all 16 mandatory
owners complete, no essential blockers, verified durability and independent
file/SQLite/settings/favorites readback. Pending and opaque controls must retain
the engine and withhold authorization while naming the actual unresolved writer.

The physical Fold and installed provider accounts are not accessible in this
environment. Follow [FOLD-ACCEPTANCE.md](../../FOLD-ACCEPTANCE.md) with the exact candidate
identity. Real Crew/Umbrella/Seren/POV functionality, repeated physical Close/reopen,
Resume Hub, watched history, settings and user-data preservation remain required.
No accepted APK delivery or permanent-resolution claim follows from host or
emulator evidence alone.

RC2 Android detail: both main and worker first flushes were rejected in phase 2,
before either completed. Four buffer obligations remain, each naming its real
writer, interpreter, thread and target. The earlier host close-after-flush defect
was fixed but did not explain this additional device failure. No RC2 safe cycle
or preserved-data pass is claimed. Further investigation is required.
