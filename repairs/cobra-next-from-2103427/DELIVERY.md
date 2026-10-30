> **User-reported physical success (2026-10-30):** “431 works perfect it fixes the issues I told you about so where’s the confusion?” The reported button issue is fixed according to the user. Exact signed 2103431 bytes remain the delivery. Replacement work and further runs have stopped; no automatic lock or promotion follows. It does not itemize modes, icon surfaces or performance measurements.

# Consolidated signed 2103431 delivery

Signed **2103431** contains both P0 corrections—Cobra Fullscreen/PiP/More dispatch and theme-aware Infinity launcher resources—plus all retained 2103429 layout, gesture, logo, reflow and performance improvements. **2103430 is superseded.** The user has physically reported that 431 works perfectly and fixes the reported issues. Engineering retains the exact signed release and stops replacement work; no lock or promotion occurred.

## Downloads, source and identity

- [One original-key signed APK](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971769136/artifacts/12940184150): `Infinity-2103431-Combined-Original-Signer.apk`.
- [Exactly matching four component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971769136/artifacts/12940139275).
- [Successful signing build 40971769136](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971769136); signed source **`9ccc4c362a65118eeba38a8e7e4b0de5723c69af`**.
- Tested owner producer `b41d51daa8b32dfee265dc9ea0abf844bff8f44e`, [successful CI 40971144336](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971144336). Production files match the signed source exactly.

Package `com.projectinfinity.kodi`, versionCode **2103431**, **778,358,062 bytes**. Original v1/v2/v3 signatures, certificate, package identity and higher versionCode establish install-over compatibility. The user reports successful physical use of 431. Engineering performed no phone installation, and populated-device data preservation was not separately measured.

Original certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

Chooser labels remain **Infinity Version 2103427**, **Cobra Version 2103431**, **App version 2103431**. Existing Version wording, design, code, selection preferences and behavior are preserved.

## Corrections

The internal `cobraProControl` dispatcher used indices into a hidden preview row whose More button had moved. It now resolves the original native action views by identity. That method name does not establish which visible mode was involved in the physical report; mode attribution remains unresolved and does not override the user’s successful test. Existing listeners, playback/PiP/menu bodies, appearance, ordering and hitboxes are preserved.

| Visible button | Signed 2103429 host Pro fixture | Corrected host Pro fixture |
|---|---|---|
| Fullscreen | PiP | Fullscreen |
| PiP | PiP | PiP |
| More | Fullscreen | Original More menu |

The earlier route comparison above runs in a Pro fixture; it is **not** verification of the reported non-Pro path. Subsequent genuine non-Pro preview host checks kept Pro inactive and passed 60 native view presses per version on signed429 and baseline27, including retained-mode, narrow/wide and remote cases. They did not reproduce the physical symptom. The user’s installed431 success is separate physical evidence; the causal attribution of the non-Pro report remains unresolved. [Scoped non-Pro evidence](results/nonpro-correction/host/COMPARISON.json).

The existing launcher icon IDs use normal Android day/night resources. Light is white with the original emblem in black; dark uses the original navy/cyan assets byte-for-byte. Modern emblem alpha and placement are preserved; legacy densities resample the original mask to the established viewport. There are no aliases, component toggles, polling or startup hooks, and the separate CobraTV icon is unchanged.

Verification exposed a density-override inflation defect in unaccepted 2103430: an inline white drawable color yielded resource ID zero. Final 2103431 uses a nested white shape. Only its two light adaptive XMLs and genuine version data change from 430; the table, IDs, five light PNGs, dark assets and button implementation remain exact. [Correction and negative-control evidence](FOLLOWUP-2103431.md).

## Focused verification

| Requirement | Host | API37 emulator | Physical Fold |
|---|---|---|---|
| Fullscreen → Fullscreen | PASS — production-view dispatch; terminal spy | PASS — native fullscreen in 40973858059 and 40975572601 | Covered by user’s collective report that the button issue is fixed; modes not itemized |
| More → original menu | PASS — production-view dispatch; terminal spy | INCOMPLETE — complete native CI journey not verified | Covered by the same user-reported physical fix |
| PiP → system PiP and return | PASS — production-view dispatch; terminal spy | INCOMPLETE — dedicated CI journey not completed | Reported button issue fixed; separate return sequence not itemized |
| Light App Info icon | PASS — API35 native rendering | PASS — reviewed white/black App Info frame | Not separately verified in the user’s general success report |
| Dark App Info icon | PASS — API35 rendering matches original dark pixels | PASS — reviewed navy/cyan App Info frame | Not separately verified |
| Automatic launcher refresh | Day/night resource selection verified; no host refresh claim | LIMITATION — Pixel Launcher retained its light bitmap after the observed dark switch | Samsung/Finder/suggestions/monochrome not separately verified |

Six actual production-view touch/key tests and three adjacent regressions pass, covering initial/retained Pro, horizontal scrolling, clipped targets, resizing, remote activation and synthetic Sports ordering. Signed 429 reproduces one genuine route assertion failure with zero fixture errors. Terminal fullscreen/menu/OS-PiP boundaries are host spies; they do not prove decoder or Android transitions.

Nine offline icon checks, aapt2 parsing and one API35 native-framework test pass. Sixteen baseline/candidate renders cover both IDs, day/night and default/420 density, including exact original dark pixels and the required signed-430 ResourceID0 negative control. Actual signed-431 App Info and Pixel Launcher observations are retained from [40973858059](results/runtime/candidate31-first-actions/REVIEW.md); correct framework resource selection does not guarantee every launcher surface refreshes.

**Latest engineering CI:** [40984628762](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40984628762) remains **FAIL**: the synthetic QA1 Pro setup was reached, but the OS runner lacked `android.test.RepetitiveTest` and aborted before `testPress`. No selected button injection or probe JSON occurred. Its trailing `OK (1 test)` was correctly rejected by the strict JSON guard. [Preserved evidence](results/runtime/candidate31-framework-classpath/). The complete native More/PiP CI journey remains incomplete. The user’s subsequent physical success is separate, decisive evidence for the reported fix; no further run or replacement build is planned.


## Preserved evidence and limitations

All preceding failures remain failures. The table identifies where each stopped; none substitutes for a complete native button PASS.

| Prior run | Actual result and stopped stage | Evidence |
|---|---|---|
| [40972601469](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40972601469) | Install client timed out before Activity launch; server installation completed | [Install evidence](results/runtime/candidate31-install-client/) |
| [40973858059](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40973858059) | Fullscreen passed; later old More coordinate produced system PiP after an intervening reveal/layout. Final touched view undetermined | [Action review](results/runtime/candidate31-first-actions/REVIEW.md) |
| [40975572601](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40975572601) | Fullscreen passed; freshness guard stopped before More. Extra reveal left More five pixels visible and PiP under the old coordinate | [Fresh-target review](results/runtime/candidate31-fresh-target/REVIEW.md) |
| [40976739449](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40976739449) | Host accessibility-query overhead exceeded 3.5s; stopped before any selected button press | [Timing review](results/runtime/candidate31-host-timing/REVIEW.md) |
| [40979186412](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40979186412) | Incremental install succeeded; full installed-file hash exceeded the old infrastructure timeout before launch | [Hash evidence](results/runtime/candidate31-incremental-hash/) |
| [40980338717](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40980338717) | Old 30s infrastructure limit truncated the full-stream install at 541,530,240/778,358,062 bytes; no launch | [Transfer evidence](results/runtime/candidate31-stream-truncation/) |
| [40981874553](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40981874553) | Full install/exact hash passed in 94.241s; launch succeeded; Android compatibility notice obscured the first-screen observer | [Notice evidence](results/runtime/candidate31-compatibility-modal/) |
| [40983247126](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40983247126) | Install/exact hash passed in 94.551s; initial notice OK and welcome passed; framework icon selection passed. Notice recurred after icon-observer return; next welcome guard failed before helper/buttons | [Recurrence review](results/runtime/candidate31-notice-recurrence/REVIEW.md) |
| [40984628762](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40984628762) | Synthetic QA1 Pro reached; QA JAR hash passed. OS runner lacked `android.test.RepetitiveTest` and aborted before `testPress`; no selected press or probe JSON | [Classpath review](results/runtime/candidate31-framework-classpath/REVIEW.md) |

Cancelled 40975410956 stopped at invalid-source checkout before emulator/install. QA transfer and notice-observer times are infrastructure observations, not clean application-startup benchmarks.

The emulator’s Android notice reports **ELF LOAD/RELRO segment alignment** failures and page-size compatibility mode. All 47 native libraries remain unchanged. The APK's 16KB ZIP-offset alignment for three stored native libraries is a different property; it does not prove ELF compatibility or repair the warning.

Samsung launcher/app drawer/Finder/suggestions, monochrome palettes, detailed fold/window behavior and populated-data preservation were not separately itemized in the user’s general physical success report. Pixel Launcher demonstrably cached the light bitmap across the observed dark switch; no unsafe cache-reset or component workaround is included.

Prior host performance counts remain valid within their fixture scope: **7,000 repeated layout requests → zero** and **100 cold duplicate-logo submissions → one**. No new Fold-speed, frame-rate, CPU, thermal, battery or long-running-memory improvement is claimed. [Performance measurements](PERFORMANCE.md) and the [completion ledger](COMPLETION-LEDGER.md) retain the original workstream status and device blockers.

## Integrity and protection

All 23 signer controls and fresh actual-APK owner/resource gates passed before key access. [Independent downloaded-byte verification](results/signed2103431/INDEPENDENT-VERIFICATION.json) confirms original signatures, four matching component ZIPs, five ordered DEX files, original Infinity module authentication and the protected contract. All stored ZIP members are four-byte aligned.

Infinity ZIP is exact locked **2103427**. Shared executable DEX/classes, manifest identity, persistence, original artwork, all 47 native libraries and unrelated payloads remain frozen. The narrow launcher-resource exception stays under its existing owner. Chooser DEX and second Cobra DEX are unchanged from 429/430; relative to 430, only the component-version class, release metadata, two light XMLs and typed manifest versionCode change. No shutdown code or tests changed, and no uninstall, data wipe or reset occurred.

Approved 2103427 remains `782242090483982c39a78f9c4da932a4751bdafc`; protected 2103425 remains `db730100a3bfea7e06d2e6c3434e89aeb6fa8a15`. Neither lock changed. The user-reported physical success is recorded without automatically creating or advancing an accepted lock.

## SHA256

```text
3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471  Infinity-2103431-Combined-Original-Signer.apk
36ca822a886b5df4443c798c933a2c304a30be002c10b4284f6b2ed7934fe912  CHOOSER_SHELL.zip
98583b7a935103c8d13744fc624a6005f0566b1e3d26a47f240295cafd21cae7  COBRA.zip
16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c  INFINITY.zip
432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8  MINIMAL_ANDROID_CONTRACT.zip
```

[Machine-readable checksums](results/signed2103431/SHA256SUMS). Downloads require repository access and expire on **2027-01-27**; the permanent signing identity is separate from artifact retention.
