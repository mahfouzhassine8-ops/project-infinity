# Universal persistence repair — REJECTED internal RC1

This is an isolated internal QA candidate, not an accepted release. Physical
Fold acceptance and real installed-provider integration remain required.
`physical_fold_verified` and `final_lock` are false.

## Exact identities

| Item | Identity |
|---|---|
| Protected 2103400 APK | `e1334ce46bc96edce76a8b7af2d3ebb9871ac7c351526ac2cc6cc58820da009a` |
| Input 2103401 APK | `17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6` |
| Internal RC1 APK | `033e48211b646bfbcf34894ae69ef934d433a38213aed8e368dc7bb2b2bd3317` |
| RC1 native engine | `40c5d327abbda0f8967d66f502c6ce2af74a31f86ba4f819ac30b84974ad377f` |
| Build source | `d31f9919c43641afb76bf154b2cedb458c512719` |
| Android test source | `bb26371447a674e9e2ff0a7a5a9d3e6972ea8e65` |
| Permanent signer | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |

Build: [39834562848](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39834562848).
Android matrix: [39834620646](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39834620646).
The version code remains 2103401; use the full APK hash to identify this candidate.

## Root cause and correction

The October 22 Fold receipt identifies `plugin.video.thecrew:service.py`,
`vfs_write_exception`, `TypeError`, and `value_type=NoneType`. Kodi's exact buffer
converter accepts Unicode, bytes and bytearray and rejects null before entering
the native `File::write` backend. The invalid argument remains a caller/API error;
the observer's blanket classification incorrectly treats that rejection as an
uncertain persistent mutation. The receipt does not establish why the provider
supplied None, and the repair does not change provider code or invent that cause.

The original signed 2103401 APK reproduces this failure with a previously unknown
service on Android 17, using its actual installed Python/VFS implementation. The
host controls additionally execute the exact production converter and write loop,
observer, native hooks and persistence ledger with a small POSIX backend adapter.

The native checked dispatch calls the same captured original method with the same
argument. Only the exact original native type/method, invalid buffer type,
TypeError, interpreter owner and live thread/operation/checkpoint lease establish
the diagnostic `argument_rejected_before_native_write`. It retains the original
exception, result and errno. This diagnostic is not a saved-write receipt and does
not settle any other operation. False/partial writes, overrides, subclasses and
unverified effects retain their blocking behavior; the generic failure allowlist
is not expanded.

The repair also registers writable VFS opens as drain obligations through checked
close. Successful namespace operations can establish bounded absence evidence
when removed parents must be synced. Every missing component needs native removal
evidence; overlapping later operations revoke it; aliases, unknown disappearance
and failed directory identity/fsync checks remain blocked.

An add-on name or private profile directory no longer makes its data optional.
Only explicit trusted cache roots and verified nonpersistent targets retain that
classification. Native SQLite transactions capture their actual current writer.
Unresolved operation, buffer and transaction diagnostics include writer, thread,
interpreter/admission and checkpoint generation. Existing invocation admission,
worker/subprocess observation, cooperative shutdown, interpreter retirement,
quarantine/probation and mandatory-owner barriers are retained. No new GUI-thread
wait, provider exemption, service-disable mechanism or forced retirement is added.

## Preservation boundary

All 9,404 native source inputs were independently verified. Exactly five change;
the other 9,399 remain byte-identical to 2103401. See `NATIVE-SOURCE.patch` and
`SOURCE-DELTA.json` for the complete change and before/after hashes.

| Native file | Change |
|---|---|
| `InfinityPythonPersistence.h` | Captured native VFS dispatch and verified rejection outcome |
| `InfinityPythonPersistenceSource.h` | Observer dispatch and writable VFS drain obligation |
| `InfinityPythonWriteHooks.h` | Successful native namespace-removal evidence |
| `InfinityProtectedWrites.h` | Required profile data, operation ownership, bounded namespace durability |
| `InfinityScriptPersistence.h` | Native namespace evidence storage |

The APK has exactly two changed payload members: `lib/arm64-v8a/libkodi.so` and
`lib/arm64-v8a/libinfinitycrash.so`. The latter changes only its existing fixed-size
engine-hash field in `.rodata`; all recorder bytes outside that field are identical.
Three signature members are regenerated. The other 7,576 members are byte-identical,
including every DEX, the manifest, assets and other libraries. All 71,197 original
global native exports and the dynamic dependency list are preserved. APK signature
schemes v1/v2/v3 and zip alignment passed, using the existing permanent signer.

Cobra files, DEX/resources and existing shared build scripts are not changed by
this repair. No existing user installation, provider directory, settings or
database was edited. Tests write only disposable host/emulator profiles. Existing
UI, playback, PiP, Search, Option B and visual assets remain the exact 2103401 bytes.

2103401 already differed from protected 2103400 before this work. The qualification
directory retains that pre-existing delta separately. The cumulative comparison
has seven native source changes (two pre-existing, five from this repair) and 45
APK-member differences; it must not be mistaken for 45 new repair changes.

## Completed verification

| Gate | Result and scope |
|---|---|
| Production-source host cases | 98 passed: 18 cases across five identities, five original-observer controls, three process cycles |
| Retained native/SQLite regressions | 47 passed, including native races/ownership, buffering, WAL/ATTACH, drain and reopen |
| Current 2103401 component tests | 20 passed against 3,262 component files verified identical to the signed parent APK |
| Persistence-participant tests | 15 passed against the exact current checkpoint runtime |
| Complete ARM64 engine | Compiled successfully; full source map checked after compilation |
| Permanent signing/ABI/APK delta | Passed; independently downloaded and rechecked |
| Android 17 candidate matrix | FAILED safe control; pending and opaque controls passed |
| Physical Fold / actual installed providers | Not performed; required before acceptance |

The host identity matrix covers The Crew, Umbrella, Seren, POV and an invented
future provider. It does not run those four providers' installed services or prove
their playback functionality. A separate Seren query/component test uses pinned
provider code with test doubles, which is also not live provider acceptance.
Synthetic history/settings readback is not physical Resume Hub acceptance.

One legacy Resume preservation test against unchanged 2103401 files reports
13 passes and one failure because it expects the earlier `Mark Watched` label
where the existing 2103401 component uses `Infinity Trakt`. No UI or legacy test
was changed to conceal that result. The matching current component suite passes.

An earlier full ARM64 compilation passed but its post-build verifier searched for
a diagnostic that is assembled from separate strings at runtime. That gate failed
and produced no signed candidate. The verifier was corrected to check the actual
binary string components; the complete build and all host gates were then rerun.
No runtime protection was weakened to pass that check.

## Android scope and remaining acceptance

Android tests use actual API 37 / Android 17 emulator images with ARM64 translation
and the exact signed ARM64 APK, with SELinux enforcing. They are not physical Fold
tests. Each disposable profile stages the exact current Command Center component,
the existing approved compat 0.8.2 package, and a new future-provider service.
The safe and pending profiles additionally use the unchanged archived compatible
Version Check package `0.5.28+infinity.1`; baseline and opaque controls retain the
bundled `0.5.27+matrix.1`. Runtime version and service-source hashes are checked.
This is an explicit compatible-profile test, not proof that the untouched bundled
Version Check service can safely run its opaque desktop subprocess on Android.

The original Android baseline reproduces all three VFS TypeErrors and remains
CHECKPOINT_FAILED with its engine alive. RC1 failed the safe control with outstanding buffers after flush/close admission
was denied. No successful Close/reopen or data-preservation pass is claimed for
RC1. The pending-transaction and opaque-writer controls passed. The opaque operation
and genuinely uncommitted transaction must remain blocked with their actual owner.

Use `FOLD-ACCEPTANCE.md` for physical acceptance. Real Crew/Umbrella/Seren/POV
operation, repeated physical Close/reopen, Resume Hub, watched history, settings,
playback and user-data preservation remain unverified. No permanent-resolution
claim or accepted-release delivery is authorized by these host/emulator results.
