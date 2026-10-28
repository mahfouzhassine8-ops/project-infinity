Signed combined **2103426** is ready for the user's physical Fold acceptance.
Install over the existing 2103425 package, preserving application data.

Subsequent verification checkpoint: [Android17 investigation and requirement status](runtime/OUTCOME.md).
The SDK prerequisite was corrected, but the current emulator attempt crashed in
unchanged shared native code before Kodi/Python and feature assertions. The signed
delivery is unchanged; the broader performance assignment remains partially complete.

- [Signed APK package, signature and verification receipts](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40647343407/artifacts/12798018789)
- [Exactly matching four owner component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40647343407/artifacts/12798318054)
- [Successful original-key combined build](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40647343407)
- [SHA256 checksums](results/DELIVERY-SHA256SUMS), [actual APK preservation verification](results/DELIVERY-VERIFICATION.json), [implementation report](IMPLEMENTATION.md)

The APK is `Infinity-2103426-Combined-Original-Signer.apk` (777,992,940 bytes),
package `com.projectinfinity.kodi`, source commit
`ea7c8bcc8a69853401e4d55c557fbfe0f1aae33c`.

APK SHA256:
`5a9e5702a99606cc51b094f9f786edf091b6852306d9a70eaab2787f256e7f39`.

Original certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
APK v1/v2/v3 signatures passed both CI `apksigner` and independent downloaded-file
verification using Google's official `apksig` library. Downloaded artifact ZIP
digests and all individual APK/component checksums match. The actual new module
also passed independent native authentication: **0.3.5.50, 75 files, 11 entries**.

Production corrections:

- Resume/Home projection sorts, filters hidden rows and groups complete typed
  identities before copying only the displayed 20/100 cards' nested metadata.
  Full-list callers retain complete results and private copies.
- Directory cards are submitted in one native API batch with their original
  order, targets, metadata, playback offsets, context actions and folder flags.
- Selected-provider Search verifies that selected provider before dispatch,
  while the chooser and Search All still discover the complete inventory.
- Search answers invalidate on observable profile, source/dependency, settings,
  watched/progress and revision changes. An answer overtaken by a tracked-state
  change is not published or cached; the UI reports “State changed; search again”.
  Original source checks, leases, cancellation cleanup and cache caps remain.

Measured before/after on the **same CI host**, actual production projection
functions with a synthetic 1,000-row saved-metadata fixture, nine samples each:

| Measurement | Baseline 2103425 source | Delivered source |
| --- | ---: | ---: |
| Projection median | 117.676 ms | 21.392 ms |
| Projection p95, nearest rank, n=9 | 141.527 ms | 21.556 ms |
| Traced peak allocations | 9,361,080 bytes | 1,041,712 bytes |
| Private entry copies for 20-card view | 1,000 | 20 |
| Python/native submission calls for 20 cards | 20 | 1 |
| Provider recognitions for selected Search, four-provider host transport | 4 | 1 |

These are host function/allocation and transport counts, **not** Android
startup, first usable Home, native queue depth, frame rate, RSS/PSS, CPU,
battery or temperature measurements. Raw samples are in
`results/CI-BASELINE-HOST.json` and `results/CI-CANDIDATE-HOST.json`.
Twelve projection comparisons, fourteen focused race/negative controls and
thirteen release-gate controls passed. The source comparison workflow is
[40645958376](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40645958376).
At delivery, no Android runtime test had executed. A subsequent focused emulator
attempt is recorded above; it did not reach application feature verification.
No unrelated stress matrix or shutdown test was executed in this performance task.

Preservation and release coherence:

- The exact Cobra and minimal Android-contract ZIPs remain byte-identical to
  2103425. All **47 native libraries and five DEX files** remain byte-identical.
- All chooser code, resources, layouts and settings are unchanged. The sole
  user-authorized chooser difference is its Infinity last-updated metadata:
  **Infinity 2103426; Cobra 2103423; combined app 2103426**.
- Seven Infinity APK members changed: five source/version files plus their
  original-key authenticated manifest/signature. The other authenticated
  first-party source files and protected persistence/shutdown functions are exact.
- The Android manifest differs only in its typed versionCode. The package,
  permanent signer and data paths support installation over 2103425. Physical
  installation itself has not been performed here.
- Both protected recovery refs still resolve to their original commits. The
  2103425 APK remains available from [original run 40606707330](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40606707330).
  No accepted pointer or final release lock has been advanced.

Remaining issues and unverified behavior:

- The physical Fold's cold/warm Home and first Continue card, playback return,
  Search/IME, scrolling, fold/orientation, frame pacing, CPU/PSS, battery and
  thermal behavior need physical verification. The historical 0.55–10.23-second
  first-card samples were from earlier builds and are not current measurements.
- The earlier 40–114 native-job queue is not remeasured or claimed fixed.
  Global scheduling and native worker limits remain unchanged. Source work and
  API-call reductions do not establish an equivalent native queue reduction.
- Earlier native SIGBUS/SIGSEGV incidents lack a matching current-build causal
  trace. No speculative allocator, signal-handler, threading or timeout patch
  was added. Existing ELF alignment remains the baseline's 4-KiB limitation;
  ZIP alignment alone does not establish 16-KiB ELF compatibility.
- Provider-side/network/account changes still use existing provider refresh and
  the original cache TTL where no local notification/revision is observable.
- No user data was cleared, reset or migrated, and shutdown was frozen without
  retesting. Final release acceptance belongs solely to the user after Fold QA.

Component ZIPs are exact build inputs, not separately installed applications.
Only the combined signed APK should be installed.
