# API37 Version Check / Essential-First Close investigation

Run [39126569633](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39126569633)
used exact signed APK2103386 SHA256
`342587d9079f7e51b61ef525c04ae9b62adb6d128791164acbd99ec691fbac87`,
skin1.0.5.227 and UI helper0.1.0. Its 89 actual UI observations passed,
including both Stop paths and both-column popup dismissal across the theme/size
matrix. The overall run FAILED at real Essential-First Close. Physical Fold
acceptance, durable Close/reopen on API37 and the separate status139 diagnosis
remain unproved.

## Observed failure and actual operation

The same-owner Close receipt entered CHECKPOINT_FAILED after1724ms:

```
native_admission: unverified_protected_writer:service.xbmc.versioncheck:runner.py:external_or_opaque_writer_requires_explicit_participant
```

The native script ledger identifies `executable=lsb_release;argc=2` and
`unobserved_native_child_process`, detail `readonly_child_scope_absent`.
There was no termination authorization, no durable/sealed essential proof,
and no confirmed process death. Preserve this rejection and all its assertions.

The packaged call chain is `runner.py -> version_check.service` import ->
`distro.linux_distribution()` -> `distro._lsb_release_info` ->
`open(os.devnull, 'w')` and `subprocess.check_output(('lsb_release', '-a'),
stderr=devnull)`. This runs before `run()` consults the enabled setting.
Android's Python platform string takes the desktop Linux branch. The actual
local output descriptor is `/dev/null`; this receipt is not proof of a
protected user-data write or proof that the executable successfully launched.

The observer requires verified child command, environment, descriptors and
lifetime. A missing-command exception requires every PATH candidate to be
absent on an approved immutable system mount, as visible to the app. Unknown
or inaccessible candidates must remain blocked. The current receipt does not
identify which predicate rejected this attempt; the targeted probe captures
app-interpreter PATH, loader-variable names only, per-candidate errno and
ancestor read-only mount evidence without running a child inside Infinity.

The writer retired at about12:21:19UTC; Close was requested about12:33:50UTC.
Its unresolved capability blocker remained in the ownership ledger. Waiting
longer, clearing that ledger, or exempting the service would not prove durability.

## Source comparison and correction candidate

Locked2103384 and signed2103386 have all103 Version Check assets byte-identical.
Original `service.py` SHA256:
`166a1f5974fd2f7c297f801dd36040b4e7d6ccf6655e2edfa335803f3bbc58d5`.
Original `addon.xml` SHA256:
`f1a3d4cc5e4339f385752038b1f655fdb03834d2ef2077ad9c62818ee9c13c4d`.
The existing9404-file locked native source comparison and three-file UI delta
also show unchanged persistence/shutdown sources. Runtime comparison on API37
is still required; source identity alone does not pass that gate.

The additive candidate `service.xbmc.versioncheck` version0.5.28+infinity.1
changes only its manifest version and Android platform detection in service.py.
On actual `System.Platform.Android`, set `DISTRIBUTION='android'`; desktop
Linux probing remains under `elif`. This avoids the incorrect Linux probe and
the fallback `platform.uname()` while retaining the service, enabled setting,
normal non-APT version check, notifications, translations and desktop behavior.
No native allowlist, write admission, persistence receipt, timeout, user setting,
APK, signing identity, or shutdown policy changes are made.

`versioncheck_android.py` builds deterministically from the hash-pinned signed
APK. The ZIP SHA256 is
`58d8869b16f2c6f409887de1e6c05b86908d3d314c439d780a294e8ccb88fb88`;
the candidate service.py SHA256 is
`6eb8ed9dd5d4712aacb44d55c3e006b1da5198c6bee076315579927c437bcfc1`.
This package is a targeted experimental candidate, not an accepted installation.

The original code is bundled under the APK's `assets/addons/` tree. The ZIP is
a separately installed same-ID add-on under `special://home/addons/`; its
persistent `special://profile/addon_data/service.xbmc.versioncheck` directory
is not included or altered. Normal service notification settings can still be
saved through the existing code. Installing corrected code cannot clear an
already-recorded ownership failure in a running process. No ledger reset or
forced-stop workaround is included; the experiment starts isolated fresh
processes and any later physical installation requires a successful normal Close.

Eight host tests pass: original Android negative control attempts lsb even with
notifications disabled; corrected enabled version check still runs without
distribution children; disabled setting retained; desktop Linux results
unchanged; unknown source rejected; all103 files preserved except the two
declared edits with deterministic archive/staging checks; tampered ZIP/proof
and existing symlink rejection. These tests execute
the actual bundled service/distro with controlled external inputs and do not
stand in for Android proof.

## Targeted runtime gate

Compare locked384, original386 and386 with the Android add-on candidate on
separate disposable API37 emulators using identical full227 skin, helper and
dependency inputs. Observe the service's actual startup and app-side command
environment. Run the unchanged actual Infinity Power Close validator, verify
all16 essential/17 owner proofs, same owner/PID, durable seals, whole-UID death,
reopen and seeded state preservation. Retain failed controls as failures.
Capture live thread evidence on failure without forcing process death.

Do not repeat the full interface suite until this targeted gate is understood
and the corrected case passes. No API35 automatic run is authorized. Samsung
One UI9.0/Fold physical testing remains separate. No final lock.

The October18 physical abnormal exit139 remains a separate open investigation.
This controlled Close rejection is not a native crash backtrace and does not
establish the cause of that exit. Private physical diagnostics remain private.

## Targeted run result: blocked before Android

Correction/source commit: `05788ec42bde21f93287a23ea97e5232d198f78c`.
Targeted run [39128510997](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39128510997)
failed in all three cases before emulator installation/start:

| Case | Job | Result |
| --- | --- | --- |
| locked384 |117678634767|draft input retrieval HTTP403|
| original386 |117678634886|draft input retrieval HTTP403|
| android-guard386 |117678634872|draft input retrieval HTTP403|

All three logs show effective `GITHUB_TOKEN` **Contents:read**. Rechecking the
exact committed workflow in05788ec4 confirms that its job also requested
Contents:read. The earlier report incorrectly said it requested write; this
was a workflow configuration mistake, not evidence of GitHub overriding a
write request. Reading existing unpublished release416125865
returned `Resource not accessible by integration (HTTP403)` before its exact
asset651868759 could be downloaded. The earlier full API37 run had effective
Contents:write and could read this same asset. No permission policy was changed,
draft release published, credential substituted, or test input replaced.

The APK identity/source comparison, eight service/package host tests, five
collector tests and six existing evidence tests passed before that boundary.
The unchanged seven Close-validator tests also pass locally (26 focused host
and guard tests total). Locked-source protection run39128510888 passed. None
of these results is an API37 shutdown pass.

The correction sets only the targeted job to the same Contents:write access
already used by the existing API37 workflow. The workflow-level default stays
read-only. No repository-wide policy, credential, release visibility or input
changes are needed. Preserve the original input SHA256
`852dce3899b1976556b3b46f696a805b668eca4a513df6194c642d108da58834`.
Do not blindly rerun unchanged jobs. No equivalent API37 Close receipt or
app-UID path evidence was produced by these three jobs; the precise native
read-only predicate remains unobserved. The correction remains experimental
and is not qualified for physical installation or final lock.

Before relaunching the comparison, the observation gate was also corrected:
all three disposable arms now enable debug file logging before startup. The
probe requires the exact native runner path/invocation; the corrected arm must
also reach the service's existing exact-version `started` or configured
`Disabled` message. A healthy service need not produce a cleanup warning or
exception. The two new host tests reject inventory-only, wrong-path,
wrong-version and missing run evidence. No addon package or Close assertion
changes accompany this collection correction.
