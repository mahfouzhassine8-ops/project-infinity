# Infinity 2103514 combined QA delivery

The protected 2103514 APK remains the rollback baseline. Production acceptance
remains pending. The original signing certificate SHA-256 is
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

| Package | APK SHA-256 | Artifact |
|---|---|---|
| 2103516 candidate | `c1d206e5b74d8328834c0e582e48c7deaafc0e45439c412ed6890a43086fff64` | [Original-signed candidate](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44476411137/artifacts/14506591970) |
| 2103517 forward recovery | `3b4ca2171ac58303bff0379a74a6f8790ac685237f998c7b0049c03a032db515` | [Original-signed recovery](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44476964647/artifacts/14506971649) |

## Engineering verification

- Eight focused host fixture groups passed for Continue Playing. The fix
  prevents an invalid remembered destination from poisoning the render cache
  for a valid destination using the same verified provider contract. Exact
  failed fingerprints, provider trust, and Resume and Play from Beginning
  offsets are preserved. The reason for the owner's original Fold selection
  remains unresolved. [Host receipt](CONTINUE-HOST.json)
- The Empty Shell instrumentation records the add-on identity and the separate
  interpreter creation, return, and bookkeeping boundaries. The ABI-compatible
  port passed the host checks for these boundaries, cancellation and overflow.
  The cause of the intermittent field stall remains unresolved.
  [Native host receipt](STARTUP-ABI-HOST.json)
- The complete Android ARM64 engine compiled and linked with exact 2103514
  exported ABI and dependency checks. The run verified 9,415 unchanged native
  sources and exactly three scoped changes. The first completed link
  exposed four logger templates. The corrected logger retains the baseline
  argument types. [Passing ARM64 run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44468436486)
- Android API 36 verified install-over through 2103514, 2103516, and 2103517
  with the same package UID, data directory, first-install time, and profile
  sentinel. On the disposable x86_64 emulator with ARM64 translation, the
  test began from the exact authenticated 2103514 module fixture.
  Android activated each expected signed module manifest. The candidate
  logged interpreter creation, successful return, and bookkeeping completion
  for the same Command Center invoker. Physical Fold verification remains
  pending. [Android receipt](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44480740328/artifacts/14508297556)

## APK preservation

The signed candidate changes ten payload members from 2103514, preserving
7,767 byte-for-byte. The signed forward recovery changes five metadata
members and preserves 7,772 byte-for-byte. The original package, Cobra
2103445, casting, Search, provider code, Trakt, skin and screensaver payloads
are preserved. The original installer requires monotonic Command Center
module versions, so the candidate uses 0.3.5.85 and recovery uses 0.3.5.86.

The preservation artifact lists exact paths and before/after SHA-256 digests
for both packages. Each signed APK artifact also includes its signed
preservation receipt. [File-level preservation](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44475378678/artifacts/14506173114)

[Privacy-safe capture instructions](COMBINED-QA.md#capture-during-normal-use)
