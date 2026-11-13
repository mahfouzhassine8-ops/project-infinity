# Signed Cast-only QA built directly on 2103490

**Engineering QA, not physical acceptance. No accepted baseline is promoted.**

Both APKs were prepared from the exact original-signed 2103490 APK, SHA-256
`63b1e380d9ff079e47793b0a182725561a9265cd63a0de288fc8357dfb1d7733`.
The signed 2103490 artifact and matching source are pinned in [BASELINE.json](BASELINE.json).

| Download artifact ZIP | Extract this APK | Signed source |
|---|---|---|
| [Cast correction QA 2103492](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43337938186/artifacts/13997164302) | `Infinity-2103492-Combined-Original-Signer.apk` | `c5c82e47ed776b10326f6837c121f77e26628bb2` |
| [Matching forward recovery 2103493](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43338973202/artifacts/13998143809) | `Infinity-2103493-Combined-Original-Signer.apk` | `68b62b96ebebadea2b922fe2ce72dab5854d11ea` |

GitHub may require sign-in. The checksums apply to the extracted APKs, not the
artifact ZIPs:

```text
3a3c08d5d168d040a34562d6a033f75b8680a242202afef965ac42fdd7383827  Infinity-2103492-Combined-Original-Signer.apk
2cf9343ea2fe17cadb73360963aaf557c07abffd2161052d09d749773702177c  Infinity-2103493-Combined-Original-Signer.apk
```

Package: `com.projectinfinity.kodi`. Both passed actual v1/v2/v3 signature
verification with the original certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
The unchanged original assembler in the existing sole signing workflow
**397702717** signed them. Registry generations 77/78 reserve versions
2103492/2103493; neither earlier version is overwritten or reused.

## Actual corrections and physical evidence limit

The current production controller had a reproducible premature-abort defect:
its connection-only 20-second timer remained active after connection, during
source preparation and media loading. The corrected controller has bounded,
separately owned phases and cleans up missing SDK load/seek outcomes. It retains
source-bound phone/native ownership and requires actual receiver PLAYING.

The original format sniffer also labeled genuine Matroska as WebM because both
share the EBML magic. The corrected bounded DocType parser distinguishes them,
preserves real WebM support and refuses unsupported Matroska with a reason.

The candidate handles the existing SDK's detailed media-error callback, reports
receiver state/load/seek/play errors without private data, and retains the
failure explanation after return to the phone. Explicit cancellation is logged
separately from receiver failures. This is a functional correction plus failure
reporting in one candidate, not a diagnostics-only release.

**The uploaded recording does not establish the actual stream container,
receiver error code or media-request failure.** It confirms the receiver loading
presentation and subsequent return to phone/home. The exact cause of that
physical attempt remains unproven. No same-attempt Kodi/logcat log was supplied
or assumed, and no repeated owner playback test was requested. Detailed
attribution, code changes and synthetic reproductions are in
[CORRECTION-REPORT.md](CORRECTION-REPORT.md) and
[EVIDENCE-BASELINE.json](EVIDENCE-BASELINE.json). The raw video remains private.

## Preservation

Only three production files changed: `InfinityCastSession.java`,
`InfinityCastSource.java` and `InfinityCastRelay.java`.

The complete signed candidate comparison against exact 2103490 passed:

- Changed APK members: `classes6.dex`, typed `AndroidManifest.xml` versionCode,
  and `assets/experience-component-updates.properties` Infinity label.
- **7,772 payload members are byte-identical; zero additions or removals.**
- The ARM64 native engine remains byte-identical to 2103490, SHA-256
  `3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75`.
  Its existing compile/link/ABI evidence is reused; no unnecessary native rebuild.
- Original five DEX, private resource package, dependency versions, Command
  Center, skin, Cobra, Movies/Infinity Movies, Continue Watching, TV, providers,
  Search, tracking/resume/Watchlists, Python startup and all shutdown/persistence
  safeguards remain unchanged. No user account, profile, database or setting was
  read or modified by packaging.

The forward recovery restores **2103490 functionality**, retaining every
improvement already in that development foundation. It differs from signed
2103490 only in its two APK/Infinity version metadata members: **7,773 members
remain identical**. It does not roll back to 2103488 or 2103486. Historical
2103486/2103488/2103490/2103491 signed artifacts and protected locks remain intact.

Signed full-member receipts: [candidate](SIGNED-CANDIDATE-PASS.json),
[recovery](SIGNED-RECOVERY-PASS.json), [preparation](PREPARATION-PASS.json).

## Verification

| Gate | Result |
|---|---|
| Actual controller with deterministic SDK/native test backends | PASS: 15 focused assertions; no real receiver claim |
| Actual progressive HTTP range/auth/privacy/retirement | PASS: 38 assertions |
| Actual adaptive HTTP plus FFmpeg decoding and seeking | PASS: 57 assertions; HLS TS/fMP4/separate audio/AES-128 and DASH templates/timelines/ranges retained |
| Real generated Matroska/WebM parser boundary | PASS: Matroska no longer mislabeled; valid WebM retained |
| Narrow original release metadata guard | PASS: seven cases, including rejection of an older baseline |
| Android API 36 component | PASS: [43335737427](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43335737427), exact signed90 APIs/resources; private progressive/HLS/DASH/cookies and five cleanup cycles |
| Complete unsigned pair and member equality | PASS: [43336490642](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43336490642) |
| Registry review | PASS: [43337566137](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43337566137), [43338652765](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43338652765) |
| Original signing and full signed-payload equality | PASS: [43337938186](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43337938186), [43338973202](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43338973202) |
| Android normal install90 → QA92 → forward93, signature/package/data ownership | PASS: [43339660861](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43339660861) |
| Physical Fold/Onn provider-movie transfer, controls, return, tracking continuity, post-Cast shutdown | NOT TESTED; one owner acceptance session |

The superseded no-key registry attempt `43337249109` was canceled to bind the
selected 90→92→93 installer verification before signing. Compiled and prepared
payloads were reused unchanged; no additional owner-facing APK was issued.

The actual installation sequence retained UID, package data directory and
first-install timestamp. It used no uninstall, reset or forced downgrade and
did not launch the app. See [INSTALL-RECOVERY-PASS.json](INSTALL-RECOVERY-PASS.json).
This verifies update ownership on Android, not physical user-data acceptance.

## Installation and one acceptance session

Extract the **2103492** APK and install it as a normal update over 2103490.
Do not uninstall, clear data, reset add-ons or force a downgrade. Keep the
**2103493** forward recovery in reserve; install it normally only if deliberately
restoring the 2103490 functionality. It is not a second Cast candidate.

Use one consolidated session: existing provider-movie playback → existing Cast
entry point → compatible video receiver → actual TV playback and position →
Pause/Resume/seek → distinguish Close Controls from Return to Phone/Disconnect →
local playback and Continue Watching → normal Exit and relaunch. If a transfer
fails, the retained failure status is meaningful evidence; success is not
inferred from connecting or a loading screen. Only the owner can accept the result.

Supported delivery remains progressive MP4/M4V/WebM and compatible HLS/DASH,
with legitimate sender-side authentication. Receiver codecs, manifest features
and the supported local IPv4 route still matter. Matroska is not transcoded or
remuxed by this candidate; DRM and unsupported source/receiver combinations
fail explicitly while preserving phone playback. There is no provider rewrite,
new tracking infrastructure, system-wide network change or shutdown bypass.
