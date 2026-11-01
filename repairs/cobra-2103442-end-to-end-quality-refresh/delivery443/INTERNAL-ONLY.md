# Internal 2103443 — withheld, not the final delivery

The signed artifact below is retained as engineering evidence. Final QA exposed a
confirmed baseline preview placement loop; the final candidate advances to2103444
with its verified identical-placement guard.2103443 was not accepted or locked.

# Cobra quality refresh — 2103443 testing candidate

Signed 2103443 contains two measured Cobra guide-presentation corrections. It
preserves the user-accepted 2103442 experience and is not a new accepted baseline.
Physical Samsung Galaxy Fold 8 Ultra acceptance remains pending. No new lock or
accepted-pointer change was made.

## Download and identity

- [Signed APK download](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41281193811/artifacts/13072564721): GitHub artifact ZIP containing `Infinity-2103443-Combined-Original-Signer.apk`, receipts and preservation evidence.
- [Matching components download](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41281193811/artifacts/13073650329): `COBRA.zip`, `INFINITY.zip`, `MINIMAL_ANDROID_CONTRACT.zip` and `CHOOSER_SHELL.zip`.
- [Successful original signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41281193811).
- Signed source: `5ab8f1b69987a5798352209b4ce77d27c13f4deb`.
- Owner implementation/preparation source: `c0442aeed4da90e11bdfb70e8e6f2b9e86adf810`.
- Package: `com.projectinfinity.kodi`; versionCode **2103443**, higher than accepted 2103442.
- Original certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- RSA 4096, APK v1/v2/v3 signatures and 16 KB alignment verified on the downloaded APK.

The component ZIPs match the actual signed APK. The existing shared component's
manifest receives only the required typed versionCode update during assembly;
that documented assembly operation does not change its protected component ZIP.

| File | SHA-256 |
|---|---|
| APK | `96275280a0bf2bdb360135fd9764515989bdbbe625aab71fb2eef82eb4857d9d` |
| COBRA.zip | `1e8ba8bbca0147d43e5bfa2f8ddfde890474b35c76a9a6b69cb2602e9274e876` |
| INFINITY.zip | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| MINIMAL_ANDROID_CONTRACT.zip | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |
| CHOOSER_SHELL.zip | `4a308f066152cbe388e4bfc5a7d05bb66a7dbd572441492b654c4923eb85fe3a` |

## Implemented changes and measurements

Programme time labels reuse a per-thread formatter while checking the current
timezone on every call. Next-programme lookup reuses the original merge result
only while both input lists, their order and every relevant programme field
remain valid. The cache has hard entry/input limits, weak activity ownership and
no workers, polling, provider changes or saved-data writes. The original merge
routine still determines precedence, deduplication and ordering.

Comparable actual-owner DEX host measurements use the same synthetic EPG, 21
warmups and 42 samples. These are host batches, not physical Fold latency:

| Operation | 2103442 p50 / p95 | 2103443 p50 / p95 | Allocated bytes per batch, before → after |
|---|---:|---:|---:|
| 500 time labels | 1.253 / 3.158 ms | 0.288 / 0.392 ms | 1,580,000 → 780,000 |
| 100 next-programme queries, 168 full + 14 short entries | 4.667 / 12.731 ms | 0.735 / 0.999 ms | 9,136,800 → 36,000 |

No whole-app startup, thermal, battery or native-crash improvement is inferred
from these measurements. No additional production defect was sufficiently
demonstrated to justify changing accepted layout, playback or lifecycle code.

## Verification

37 current focused host checks pass, including 75 mode/screen/theme combinations,
90 font/screen/theme combinations, mutable/replaced EPG freshness and cache bounds,
Cards LIVE/Preview and real tap menus, approved Pro layouts and real controls,
all 11 Multi-View arrangements, all 14 existing display-size modes, custom sizing,
profile/filter freshness, scroll/focus reuse and stale publication protection.
Four release-protocol checks and the existing signer-policy gate also pass.
Six matching full Pro before/after renders have zero changed pixels.

Android install-over verification is being recorded separately. Its final result
must be attached here before this report is presented as the completed delivery.

Historical 440 Preview fixture setup failures were reproduced on accepted 442
and are not counted as passes. Current 442 Preview/menu tests pass. The first
Android baseline attempt failed in QA's fixed-density assertion before inner
tests; the corrected harness preserves that assertion. See [implementation and
test limitations](IMPLEMENTATION.md) for the failures and their evidence.

## Exact preservation

The downloaded signed APK has **7,611 unchanged payload members**. Exactly three
payload members change: `classes4.dex`, `AndroidManifest.xml` (typed version only)
and `assets/experience-component-updates.properties` (truthful Cobra version).
The three JAR signature records and APK signing blocks are regenerated with the
same original certificate; no member is added or removed.

All 47 native libraries, Infinity's 7,516 payload members and DEX, shared Android
code, chooser code, resources, launcher icons and the second Cobra DEX are exact.
Both the Infinity and shared component ZIPs are byte-identical to 2103442.
Shutdown is unchanged and was not tested. No user data was accessed or migrated.

Of 7,174 original Cobra classes, 7,172 are exact. The activity has two changed
methods and one added private lookup; the other changed class contains Cobra
version metadata. Seven new helper/nested classes implement the bounded work.
All 1,801 other activity methods, fields and annotations remain exact.

The production change is isolated to `runtime/CobraGuidePresentation.java` and
its exact-preimage `patch_native.py` injection. Owner build/verification files,
focused QA and release branch/version bindings support delivery; there is no
global UI or engine rewrite. Full source, class/method and APK deltas are saved in
[signed source files](delivery443/SIGNED-SOURCE-FILES.txt),
[owner evidence](final-evidence/OWNER-PRESERVATION.json),
[every APK member](delivery443/ALL-APK-MEMBERS.json),
[signature members](delivery443/SIGNATURE-MEMBERS.json) and
[component-to-APK verification](delivery443/COMPONENT-TO-APK.json).

See the [workstream ledger and physical acceptance procedure](COVERAGE-AND-ACCEPTANCE.md).
Samsung fold transitions, provider-account playback, physical audio/decoder/PiP,
calls, screen off/on, process pressure and extended thermal behavior remain
device checks. Host fixtures and emulator window resizing do not establish Fold
acceptance. Install this single candidate over the existing app without clearing
data; retain signed 2103442 for recovery.
