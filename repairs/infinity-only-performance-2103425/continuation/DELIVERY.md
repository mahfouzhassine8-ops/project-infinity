Signed combined **2103427** is delivered for installation over the existing app
and the user's physical Fold acceptance. This is one consolidated candidate,
retaining signed 2103426 and adding the two P0 corrections and further Home/TV
projection optimizations. The full original task remains partially blocked;
see the [completion ledger](COMPLETION-LEDGER.md).

- [Signed APK and verification receipts](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40769526963/artifacts/12852945082)
- [Exactly matching four owner component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40769526963/artifacts/12852670776)
- [Successful original-key combined build 40769526963](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40769526963)
- [Checksums](results/SHA256SUMS), [implementation](IMPLEMENTATION.md), [independent downloaded-file verification](results/INDEPENDENT-DELIVERY.json), [CI receipt](results/FINAL-CI-RECEIPT.json)

APK: `Infinity-2103427-Combined-Original-Signer.apk`, **778,042,092 bytes**,
package `com.projectinfinity.kodi`, versionCode **2103427**.
Signed source: `782242090483982c39a78f9c4da932a4751bdafc`.
Infinity component: `2103420.isolation.1.performance.2`;
Command Center **0.3.5.51**, native-authenticated 75 files/11 entries;
skin **1.0.5.248**. Chooser update labels: Infinity 2103427, Cobra 2103423.

| Exact file | SHA256 |
| --- | --- |
| Infinity-2103427-Combined-Original-Signer.apk | `cd0c8ab5c77067e508baea0ad7d5207b3d6c73775b86387d4099a67cfe4215ca` |
| INFINITY.zip | `16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c` |
| CHOOSER_SHELL.zip | `268fdbad636fdef3f1a010cd1d8cdd84c5342184c1da906a232796f834ed04af` |
| COBRA.zip | `eb30afa0e1ab9f50da897db27a604cb79a47059ff355c763dc7d7c955ddbcb6b` |
| MINIMAL_ANDROID_CONTRACT.zip | `6e93a1eb8e47f7fc9bc6f1dbc9208b555e2e62445ca2a3065d4e17a3b473ba33` |

Original certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
APK v1/v2/v3 signatures passed CI apksigner and independent verification of the
downloaded APK with Google's official apksig 8.7.3. The actual downloaded module
also passed the original native RSA/source verifier. Downloaded artifact ZIP
digests were checked separately; their hashes are in the CI receipt.

The production changes isolate Trakt/Infinity source instances for every affected
movie/TV row and Home mode, align related art/details/focus with their owner, and
retain source-specific native selection/cache state. Exact action/url matching
and generated aliases correct TV Progress Shows separately from Next Episodes.
Local Home now builds 20 cards rather than 100; View All retains100. TV projections
copy only displayed metadata, and Home counts stop copying nested title metadata.
The four 2103426 improvements remain included and regression-checked.

Actual same-host before/after measurements from
[focused CI 40768569301](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40768569301),
using actual production functions, 1000 synthetic records with nested metadata,
nine samples each (p95=nearest rank, n=9):

| Host measurement | Signed2103426 source | Delivered2103427 source |
| --- | ---: | ---: |
| Progress Shows median / p95 | 118.935 /130.085 ms | 22.323 /22.671 ms |
| Progress Shows traced peak / private copies | 4,548,963 bytes /999 | 480,571 bytes /20 |
| Next Episodes median / p95 | 68.024 /79.064 ms | 19.652 /19.841 ms |
| Next Episodes traced peak / private copies | 4,493,442 bytes /499 | 480,114 bytes /20 |
| Home counts median / private copies | 125.098 ms /999 | 22.228 ms /0 |
| Actual local Home listing card-builder limit | 100 before panel truncation | 20 |
| View All listing limit | 100 | 100 |

Raw samples are in [CI-HOST.json](results/CI-HOST.json). These are function/allocation
measurements, not Android startup, first-card paint, native queue, FPS, RSS/PSS,
battery or thermal results. A separate [URL-binding host model](results/URL-REUSE-HOST.json)
counts 12→4 directory URL changes over twelve source/media visits, assuming
completed valid caches and unchanged revisions. It does not execute native jobs
or measure the device queue.

Focused verification passed: **9** generated-layout/route/production-function
integration cases, **14** retained Search/inventory negative/race controls,
**12** retained projection equivalence cases and **13** release-gate controls.
The delayed-completion fixture checks distinct generated destinations and cached
selection keys; it is not an Android screenshot or native callback execution.

The final download comparison checked **7598 component members** against the
APK. All 34 changed non-manifest members relative to2103426 are explained:
33 Infinity members and the sole authorized chooser metadata member. Android's
manifest differs only in versionCode. All **47 native libraries and 5 DEX files**
are byte-identical to protected 2103425. Cobra and the minimal Android-contract
ZIPs are exact originals. Chooser code, resources, settings and behavior were
not changed. Save/sync/publish/service and protected shutdown code remain exact;
the newly authenticated manifest reflects only the reviewed source generation.

Package identity, higher versionCode, permanent signer and unchanged data paths
support installation over2103425 or2103426. Physical installation was not performed
here. Extract and install only the combined APK; component ZIPs are matching build
inputs. No uninstall, data clear, database reset, migration or diagnostic device
installation was performed.

Remaining limits are explicit in the ledger. Current Fold startup/Home latency,
Search Enter/IME/provider cancellation, scrolling, Back/long-press/View All,
playback return, profile/fold/orientation, frame pacing and long-running resources
need device verification. Native queue 40–114 and physical SIGBUS/SIGSEGV/ANR causes
are not claimed repaired. The current emulator's unchanged native constructor
crashes before Kodi/Python; no new identical attempt was run. Existing 4-KiB ELF
alignment remains, and ZIP alignment does not establish strict 16-KiB native
compatibility. Separate source caches have a finite extra native item/control
cost whose device memory/offscreen-refresh effects are unmeasured.

Shutdown was frozen and **NOT RUN**. No accepted pointer or protected lock moved.
Approved 2103425 remains available from
[recovery run 40606707330](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40606707330),
and signed 2103426 remains preserved. Only the user can grant final release
acceptance after physical Fold testing.
