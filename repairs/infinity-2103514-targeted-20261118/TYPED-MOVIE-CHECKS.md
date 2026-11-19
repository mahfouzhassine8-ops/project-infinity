# Selected Continue Playing typed movie checks

Use the prior synthetic signed-source replay and exact 2103516 production Python with the single reviewed plugin.py change. Compare baseline and corrected legacy movie rows. Verify two launch offsets, original direct playback precedence, disabled or incompatible provider rejection, malformed and missing TMDb identity, missing Helper, exact failed Helper fingerprint, prior failed Helper preference, stale verified route, no other buckets affected, diagnostics and byte-for-byte retained fixture state. The host test deliberately cancels the real Helper selection. Android verification separately selects a real Helper action and checks playback and offsets.

## Verified QA delivery

Production change `c6286ce595fae7ec7f427d180ef53dda876b0ef3` is limited to
`assets/addons/script.infinity.commandcenter/plugin.py` relative to 2103516.
An existing verified direct route takes precedence. A saved movie with a
missing flat TMDb ID can use the existing Helper resolver when its validated
movie identity supplies that ID. The fallback uses the existing failed-route
checks. The repair does not write saved records.

| Version | APK SHA-256 | Original-key signing artifact |
|---|---|---|
| 2103518 QA | `9bfb4c87bc2536a2b806fa995866fd719345fcd575c180aeba93eb02c4303f54` | [Signed APK 44502506009](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44502506009/artifacts/14518117319) |
| 2103519 forward recovery | `297e06aa0070fcaaa9be755cb2bac2a387c605b0e8530cab60584569e2d43450` | [Signed APK 44503168715](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44503168715/artifacts/14518432684) |

Both use `com.projectinfinity.kodi` and the permanent signing certificate
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
The original workflow verified APK v1, v2 and v3 signatures.

- The 17 host cases covered the eight-action chooser, direct playback
  priority, exact failed fingerprints, provider constraints and recovery.
  [Host results](TYPED-MOVIE-HOST.json)
- Android 17 selected real TMDb Helper 6.22.4 actions and decoded three
  synthetic clips using the retained 2103516 ARM64 engine and the signed
  staged candidate module. The missing-scalar fixtures started at 24.000
  seconds for Resume and 0.000 seconds for Play from Beginning. The movie
  IDs, exact playing files and advancing playback clocks matched. An
  earlier API 36 emulator run saw a translated-process SIGSEGV before
  testing playback. The Android 17 run passed. [Playback evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44501589948/artifacts/14518370537)
- The signed 2103514 → 2103518 → 2103519 installation sequence passed
  with the same UID, data directory, installation time and test profile.
  Android activated all three expected signed module manifests. The QA
  package logged interpreter creation, return and bookkeeping completion
  for the same Command Center invoker. [Install-over evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44503787623/artifacts/14518806798)
- The candidate preserves both 2103516 diagnostics and its exact ARM64
  binary. Relative to 2103516, all payload differences beyond the movie
  resolver are version and signing metadata. Relative to 2103514, the
  candidate preserves 7,767 APK members byte-for-byte and the forward
  recovery preserves 7,772. Recovery restores the 2103514 code with
  monotonic Android and module version metadata. The original release
  authority verified the exact member allowlist, including byte identity
  of Cast, Cobra and the other protected components. [Preservation receipts](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44493489263/artifacts/14514102247)

Signed 2103514 remains the accepted baseline. Tests used a disposable
Android profile and local fixture media. The original Fold case and live
provider playback await physical acceptance.
