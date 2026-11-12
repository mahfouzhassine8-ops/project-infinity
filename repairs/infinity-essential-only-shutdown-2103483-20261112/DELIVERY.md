# Essential-only shutdown repair — 2103486

This contains functional shutdown changes, not a logging-only diagnostic. Protected 2103483 and diagnostic 2103484 remain preserved. Physical Galaxy Fold acceptance is pending.

| Installer | Download | APK SHA-256 |
| --- | --- | --- |
| Repair 2103486 | [Original-signed APK bundle](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43200317103/artifacts/13935631408) | `550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197` |
| Forward recovery 2103487 | [Original-signed recovery bundle](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43201341671/artifacts/13936225410) | `a0962db899df2256f74935a35cf7ced32193437497f6cb48a2781c42a1cc4a0c` |

Download the bundle through the repository account and extract its `.apk`. The SHA-256 above is for the APK, not the surrounding GitHub artifact ZIP. Each bundle includes its actual signing and preservation receipts.

Package: `com.projectinfinity.kodi`. Both have the existing permanent certificate, SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`, with Android v1/v2/v3 signature verification passed. No replacement signer or certificate was introduced. Version 2103485 was already reserved during earlier recovery preparation and was not reused.

## What changed

[Implementation and source evidence](IMPLEMENTATION.md) explains the three-header native correction. The existing coordinator already treats third-party services as optional. The correction prevents completed metadata operations and known pre-execution rejected native loads from leaving false permanent protected-writer vetoes. Actual inflight protected writes, uncertain native execution, essential saves, admission fences, and durability checks remain enforced. Core is not disabled and its original library-loading path is unchanged.

Native source: `9ce852ebb044a82853ef93af24e34a07ed96daff`.
Repair engine SHA-256: `b75747363c83a548d61463c2fd434be909f27c07d4872fa9d9c61642a3757635`.
Repair signing source: `fe44ec40cd3e43fb5498084dec24c59dd63c3f3a`, authority generation 71.
Recovery signing source: `87d65d642f9054ddd8390038ade3de72168c1695`, authority generation 72.

The repair changes only the native engine plus required Android version and Infinity version-label metadata relative to signed 2103483. All 7,766 other APK payload members are byte-identical. Cobra, Java/DEX, providers, authenticated add-ons, Search, skin, tracking, networking, settings defaults, and the chooser implementation remain unchanged. User profile data is not replacement payload.

Recovery restores the exact protected 2103483 engine and all its payload, with only the two required version metadata members advanced. Its engine is `f14ff78865158337eb6fd19dfe549912d57f2a6a912e5b3440ed28880ee0cb0c`; 7,767 other payload members are identical to 2103483. It restores the baseline's behavior, including its original shutdown limitation, without downgrading the Android version.

## Engineering evidence

- [43186634362](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43186634362): focused native/CPython cases, actual Android ARM64 full compilation/link, baseline ABI and exact source scope passed. 71,213 global exports and 11 native dependencies retained.
- [43196958708](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43196958708): actual normal Close completed, all 16 essential owners durable, zero protected blockers, two optional writers unfinished, no app-UID processes remaining. The original workflow failed afterward on an obsolete single-UUID test assertion; its receipt passes the unchanged baseline's actual three-owner Java seal contract. Raw failure retained.
- [43198525179](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43198525179): actual Core namespace rejection, local Python execution, normal Close, app-UID death, seven database integrity checks, same-profile relaunch/new process owner, saved favourite and Python-record retention, and Python execution after relaunch completed. This used the real repair engine injected into a fresh installation of exact signed 2103483 on a disposable API36 VM. It is not a signed-2103486 runtime or physical Fold acceptance claim. The final APK-file hashing command exceeded its 12-second harness limit; the overall workflow remains failed and that final read is NOT VERIFIED. Packaging and signed-install checks separately verify exact APK bytes.
- [43200317103](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43200317103): original repair signing and complete signed-payload preservation passed. Download archive, APK and embedded engine were independently rehashed after download.
- [43201341671](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43201341671): original forward-recovery signing and exact-2103483 preservation passed. Download archive and APK stream were independently rehashed after download.
- [43202390845](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43202390845): the dedicated job **passed** actual original-signed84 → repair86 → forward87 installation, exact installed APK/native hashes, unchanged UID/data directory, and byte-identical synthetic private/external profile records. It did not launch the application or run shutdown. The overall workflow remains **failed** solely because the separate legacy generic job refused the new selection; no application/device setup ran in that legacy job. The unrelated legacy generic job refused the new selection before artifact/device setup; this routing error is retained and corrected in `6be3c60e`, with 126 focused routing comparisons passed. No repeated application cycle is authorized by that routing correction.

The inherited `talloc_lib_init+32` startup SIGSEGV in the emulator/native bridge remains unresolved and is recorded in `evidence/MATCHED-TALLOC-STARTUP-LIMITATION.json`; unchanged signed 2103483 reproduced the same failure. It was not suppressed or converted into a passing test. Successful unknown native-library execution still requires genuine persistence/drain evidence; this repair does not exempt unknown active writers.

## One controlled Fold acceptance

1. Verify the repair APK checksum and install 2103486 over the current 2103484 installation using Android's normal update flow. Keep the existing application and data.
2. Open Infinity with the existing profile, confirm normal functionality, then use the existing Close action once. Confirm the entire Kodi process exits, reopen, and confirm the same profile, saved lists/settings, and normal functionality remain.
3. If recovery is needed, install 2103487 over 2103486 without uninstalling or clearing data. Recovery advances the Android version and restores protected 2103483 functionality. It is not part of the routine acceptance installation.

Only the owner can record final physical-device acceptance. No production-accepted pointer was changed.
