# Cobra 2103444 quality-refresh testing candidate

**Acceptance update, 2026-11-01:** The user subsequently instructed “Lock it”.
[2103444 is now the user-approved baseline](../locks/INFINITY-COBRA-2103444-USER-APPROVED-BASELINE-20261101.md),
with an exact-source lock reference and 2103442 retained for recovery. The report
below preserves the original delivery-time status and verification limitations;
no APK was rebuilt and no historical test result was changed. GitHub-enforced
branch protection still requires repository-administrator permission.

Original-key signed **2103444** contains three measured Cobra presentation fixes:
reuse programme-time formatting machinery, reuse bounded and content-validated
next-programme projections, and skip identical preview layout assignments. Existing
layout calculations, player callbacks and data-publication behavior are retained.
Source, host, package, signature and actual Android install-over checks pass.
**Full candidate Android interaction verification remains blocked by the QA
observer deadline below. This is a testing candidate, not a full end-to-end PASS.**

**2103442 remains the accepted recovery baseline.** Candidate 2103444 is not locked
or promoted. Internally signed 2103443 is withheld; 2103444 is the single final
testing delivery for this assignment.
The original [signed 2103442 recovery artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41270516686/artifacts/13069261267)
remains available and unchanged.

## Downloads and source

- [Signed APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114/artifacts/13074830138): extract `Infinity-2103444-Combined-Original-Signer.apk`.
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114/artifacts/13074134837): `COBRA.zip`, `INFINITY.zip`, `CHOOSER_SHELL.zip`, `MINIMAL_ANDROID_CONTRACT.zip`.
- [Successful original-key signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114).
- [Official component preparation run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41283814406).
- Signed source: [`1b7a4ef16524854fab77a1c974538aee8a1132bb`](https://github.com/mahfouzhassine8-ops/project-infinity/commit/1b7a4ef16524854fab77a1c974538aee8a1132bb).
- Component producer source: `3544e741871d1a9f79a21c193cc75fbc5973e839`.
- [Signing and preservation evidence artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114/artifacts/13074652626).

GitHub artifact downloads require repository access. Download the artifact ZIP and
install its APK over the existing `com.projectinfinity.kodi` application. No
uninstall, data clearing or settings reset is required. The versionCode is
**2103444**; the retained versionName is `1.0.9-Final-Corrections-TEST0011`.

## SHA-256 and original signing identity

| File | SHA-256 |
|---|---|
| `Infinity-2103444-Combined-Original-Signer.apk` | `38dff935ffc0967e2c16e8d61e6e4bfd693fcb73bbaa130e8fa354e468b85a76` |
| `COBRA.zip` | `f00c5e887cd221b12ee37a1e2a801dd61e60ecf555e0cfc1bb38974fd41ba690` |
| `INFINITY.zip` | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| `CHOOSER_SHELL.zip` | `cfc83c9caf57bc4978d8a12625537e90515be400a48d0f6359695c962d20f1da` |
| `MINIMAL_ANDROID_CONTRACT.zip` | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |

The downloaded APK verifies with v1, v2 and v3 signatures, RSA 4096, and the original
certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
`zipalign -c -P 16 4` passes. Package identity is unchanged and versionCode increases
over accepted 2103442 and withheld 2103443. Checksums are also in
[`delivery444/SHA256SUMS`](delivery444/SHA256SUMS).

## Exact preservation against signed 2103442

Independent downloaded-byte comparison passes: **7,611 unchanged payload members,
no members added or removed, all 47 native libraries unchanged**. Infinity's full
owner ZIP, all 7,516 payload members and its compiled DEX are exact. Shared DEX,
chooser DEX, resources, launcher icons and the second Cobra DEX are exact.

The only changed payload members are:

1. `classes4.dex`: three reviewed Cobra presentation paths and Cobra version metadata.
2. `AndroidManifest.xml`: typed versionCode only, from 2103442 to 2103444.
3. `assets/experience-component-updates.properties`: truthful Cobra version metadata.

Three ZIP signature records and the v2/v3 signing block are regenerated using the
same original key. Every before/after member hash is recorded in
[`ALL-APK-MEMBERS.json`](delivery444/ALL-APK-MEMBERS.json) and
[`SIGNATURE-MEMBERS.json`](delivery444/SIGNATURE-MEMBERS.json).

At canonical class/method level, 7,171 of 7,174 original Cobra class definitions, all 1,801 unrelated
activity methods, all 46 unrelated CobraSix methods, and all original fields and
annotations are identical. Seven helper/nested classes implement the fixes.
Cards, Pro, Pro Sports, themes, Multi-View and player-binding classes remain exact.
See [`OWNER-PRESERVATION.json`](final-evidence444/OWNER-PRESERVATION.json) and
[`METHOD-ALLOWLIST.json`](METHOD-ALLOWLIST.json).

The official component archive matches the verified prepared component ZIPs, and
every component DEX/payload matches the signed APK. The shared bundle's historical
manifest receives only the required typed versionCode during assembly; this
exception is checked explicitly in
[`COMPONENT-TO-APK.json`](delivery444/COMPONENT-TO-APK.json).

No physical-device user data was accessed. Android QA uses a disposable emulator
with synthetic channel data. Shutdown remains unchanged and was not tested.
The existing 2103442 lock still resolves to
`2e88f85250ef2e46952192cf0fdb42ac5af7c9c8`; no acceptance pointer was changed.
Repository ruleset enforcement was not changed; the earlier integration-permission
limitation is not presented as enforced branch protection.

## Measured improvements and verification

Actual Cobra owner DEX, API 35 native-graphics host fixtures, synthetic EPG, 21
warmups and 42 measured batches; these are **host results, not Fold speed claims**.

| Operation | Accepted 442 p50 / p95 | Candidate 444 p50 / p95 | Allocation before → after |
|---|---:|---:|---:|
| 500 programme-time labels | 1.253 / 3.158 ms | 0.265 / 0.336 ms | 1,580,000 → 780,000 bytes |
| 100 next-programme queries | 4.667 / 12.731 ms | 0.620 / 1.050 ms | 9,136,800 → 36,000 bytes |
| 32 identical preview placements | 32 layout requests | 0 layout requests | Same final rectangle |

**39 current host checks pass**, covering 75 mode/screen/theme cases and 90
font/screen/theme cases, mutable EPG/cache invalidation and bounds, Cards LIVE
state/Preview/actual decor presses, approved Pro geometry/touch, all 11 Multi-View
arrangements, all 14 actual display-size modes/custom controls, profile/filter
freshness, resize, selection/focus and scroll reuse. Four release-protocol checks
and signer-policy checks also pass. Six full Pro comparison renders have zero
changed pixels against accepted 442.

Historical fixture/setup failures and their exact corrections remain recorded in
[`IMPLEMENTATION.md`](IMPLEMENTATION.md). They are not relabeled as passes or used
as evidence of production crashes. Current results are in
[`TEST-RESULTS.json`](final-evidence444/TEST-RESULTS.json).

## Android result and exact remaining blocker

[Run 41285455894](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41285455894)
completed the selected **accepted 442** front/inner mode, scrolling, drawer,
window-resize and cover-return journey. That sub-result passes; the overall run
failed later on a legacy warm-return XML observation. Its completed matrix was
retained and reused with exact source/outcome hashes.

[Run 41286787645](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41286787645)
then confirmed baseline warm return through the existing live-root observer and
**installed 444 over 442 successfully**. The installed APK SHA-256 is exactly the
delivered hash; the application UID remained `u0a229` / `10229`. No uninstall or
data clear occurred. The normal update itself stops the old process through
PackageManager; this is not a shutdown test.

After the candidate launch, the known Android native-library compatibility notice
was verified against the unchanged native members and its informational OK was
pressed once. The following root query completed at **2,084 ms**, beyond the
observer's unchanged **2,000 ms** readiness limit. The late result was discarded.
Android's captured activity dump shows the candidate resumed and visible, but
that does not prove its controls or destination readiness passed. The candidate's
full interaction matrix and warm-return check were **not reached**.

The run remains **FAILED**, with the exact receipt and evidence in
[`RUNTIME-SUMMARY.json`](delivery444/android-41286787645/RUNTIME-SUMMARY.json) and
[the original Android artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41286787645/artifacts/13076160142).
No observer deadline, native library or compatibility setting was changed to
force a PASS. No additional runtime attempt or APK rebuild was started after
this boundary. Physical Fold testing of the delivered candidate is the next
acceptance step; a future automated closure requires a reliable fresh-root
observation, without using a late result as a valid current interaction target.

The emulator used API 37.1, x86_64/ARM translation, software graphics, synthetic
20,226-channel EPG and decoded loopback video. Baseline Android resource snapshots
are retained; there is no completed matched candidate trace from which to claim
Android frame-rate, CPU, memory or cold/warm speed improvement.

## Completion boundaries

The A–F workstream ledger, unchanged feature controls, tested environments and
physical acceptance procedure are in
[`COVERAGE-AND-ACCEPTANCE.md`](COVERAGE-AND-ACCEPTANCE.md).

Physical Samsung hinge/inset behavior, real provider-account latency, hardware
decoder/audio/PiP continuity under calls and process pressure, long-duration
memory/thermal behavior and physical cold/warm/channel-switch timing require the
user's Galaxy Fold. No native-crash repair, battery gain or universal real-provider
speedup is claimed. Existing VOD/recording/live-sports network behavior is preserved
by owner/method equality; it is not represented as freshly exercised account testing.

Install the candidate for physical acceptance. No new baseline lock is created.
