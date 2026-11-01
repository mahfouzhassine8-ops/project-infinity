# Cobra2103445 rotation and fullscreen audio testing candidate

Original-key signed **2103445** implements the two authorized Cobra refinements: the existing rotation button alternates automatic rotation with locking the exact displayed orientation; the Fullscreen toolbar adds a native-style Mute/Unmute button between Channels and Display. The original player-specific audio owner restores volume and preserves selected Multi-View audio ownership. Existing More and Pro Sports Stats remain accessible after the primary five controls.

**2103444 remains the accepted recovery baseline. 2103445 is not accepted, promoted or locked.** Real Fold sensors, Android lifecycle initialization, audible output, decoder/session continuity and physical fold/PiP/window transitions require user acceptance. No new Android runtime matrix or physical installation is claimed.

## Actual downloads

- [Signed install-over APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470/artifacts/13100188760): extract `Infinity-2103445-Combined-Original-Signer.apk`.
- [Exactly matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470/artifacts/13101240484): `COBRA.zip`, `INFINITY.zip`, `MINIMAL_ANDROID_CONTRACT.zip`, `CHOOSER_SHELL.zip`.
- [Successful original-key signing run41349763470](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470).
- [Signing/preservation evidence artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470/artifacts/13100876195).
- [Successful component producer41349307267](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349307267).
- Exact signed source: [`6cf75639a46ec6b0c858ae32abc102450fdc0974`](https://github.com/mahfouzhassine8-ops/project-infinity/commit/6cf75639a46ec6b0c858ae32abc102450fdc0974).
- Component producer source: `73edb4f25b9e25d67cd8e0c41d44e74931f2b8ef`.

Package `com.projectinfinity.kodi`, versionCode **2103445**, retained versionName `1.0.9-Final-Corrections-TEST0011`. Original certificate and package identity plus higher versionCode support normal installation over2103444, without uninstalling, resetting settings or clearing data. Physical install-over has not been run for445. GitHub artifact downloads require repository access; current artifact retention ends2027-01-30 21:00:54UTC.

## Checksums and original certificate

| File | SHA-256 |
|---|---|
| `Infinity-2103445-Combined-Original-Signer.apk` | `b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400` |
| `COBRA.zip` | `f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8` |
| `INFINITY.zip` | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| `MINIMAL_ANDROID_CONTRACT.zip` | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |
| `CHOOSER_SHELL.zip` | `2a0d5f73a0289f64f2caa8fe8f7ce1f2e3234116ff76e699f2f773bab0aa14ba` |

The independently downloaded APK verifies with v1/v2/v3 signatures, RSA4096 and the original certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. ZIP integrity and `zipalign -c -P 16 4` pass. Actual downloaded component ZIPs match the producer ZIPs; every component DEX and payload matches the actual signed APK. The shared component's original manifest receives only the required typed versionCode during assembly.

See [checksums](delivery445/SHA256SUMS), [static gates](delivery445/STATIC-RELEASE-GATES.json), [original-signature output](delivery445/ORIGINAL-SIGNATURE.txt), [download evidence](delivery445/SIGNED-ARTIFACT-DOWNLOADS.json) and [component-to-APK proof](delivery445/COMPONENT-TO-APK.json).

## Preservation against actual signed2103444

**7,611 payload members remain byte-identical; no payload member is added or removed; all47 native libraries remain identical.** Infinity's entire ZIP and7516 payload members, native Kodi, shared Android/Media3 executable code, resources, launcher icons and chooser executable remain exact. Shutdown implementation is unchanged and was not tested. No physical-device user data was accessed; host QA uses synthetic data.

Only these APK payload members change:

1. `classes4.dex`: reviewed Cobra rotation/audio methods, new helpers and Cobra version metadata.
2. `AndroidManifest.xml`: typed versionCode2103444→2103445 only.
3. `assets/experience-component-updates.properties`: truthful Cobra last-updated metadata; Infinity stays2103437.

Three ZIP signature records and the v2/v3 signing block are regenerated using the same original key. [Every payload-member hash](delivery445/ALL-APK-MEMBERS.json), [exact comparison](delivery445/APK-PRESERVATION.json) and [signature-member hashes](delivery445/SIGNATURE-MEMBERS.json) are retained.

Original fields/annotations,7,175 Cobra class definitions,1,801 unrelated activity methods and all46 unrelated CobraSix methods remain exact. The second Cobra DEX, all Cards/Pro/Pro Sports/Multi-View/theme implementations and the accepted2103444 performance helpers remain exact. [Method allowlist](METHOD-ALLOWLIST.json) and [owner comparison](final-evidence/OWNER-PRESERVATION.json) enumerate the authorized exceptions. `InfinityLiveActivity` and `InfinityCobraDeviceBridge` are Cobra-owned classes despite their historical names; the INFINITY owner is untouched.

Production changes are confined to `runtime/CobraRotationPolicy.java`, `runtime/CobraFullscreenAudio.java` and the exact native-method patches in `patch_native.py`. Build/verification/release files bind these changes to the exact baseline. The sole signer, key ownership, negative release checks, older lock checks and original payload/security protections remain; only the required branch/version binding, new444 lock guard, new Cobra helper ownership and truthful version metadata are adapted. No unrelated feature repair is included.

## Focused verification and limitations

- **6 new feature host tests pass:** five rotation/audio tests plus one Pro Sports toolbar test. Coverage includes all four physical-orientation mappings, repeated auto/current-lock toggles, real native fullscreen button presses, player volume0.37 restoration without a stream restart, external player-volume icon updates, selected Multi-View audio ownership, and all five base modes×two simulated displays×Light/Dark/OLED. Pro Sports preserves Stats alongside the five primary controls on both panes.
- **14 positive preservation host checks:** seven Display tests covering all14 existing size modes/custom settings, four accepted Cards LIVE/Preview/context tests, and three native fullscreen More/visual-menu checks. The host uses Robolectric4.14.1/API35 and controlled ExoPlayer proxies, not a real decoder or physical Fold.
- Four release-protocol negative/guard tests and sole-signer policy pass. Original signing workflow performs full ownership/source checks before key access and independently compares the signed APK with2103444 afterward.
- **Retained failures, not PASS:** the reused historical Preview class has eight tests stopped by its common LIVE-vs-NONE fixture assertion; a representative identical failure reproduces on untouched2103444. One historical delayed-chrome More test also fails on untouched2103444. These do not establish new production regressions. Their original results and baseline controls remain in [evidence](evidence/). The accepted Cards LIVE/Preview fixtures and direct More open/Back/reopen checks pass. Full delayed-chrome runtime behavior remains a physical acceptance check.
- Several initial Maven attempts exhausted storage and reported zero tests or incomplete report writes despite successful exit status. They are explicitly **uncounted**, with failure logs retained. Space was recovered from reproducible intermediate/cache storage without modifying recovery APKs. Only complete XML reports count above.
- The rotation host test supplies the actual compiled Cobra bridge's activity state because its Android directory-sync constructor cannot execute in this host. It tests the compiled rotation path, not native constructor/lifecycle initialization. The workspace has no attached ADB/Android runtime. The previously documented2103444 CI observer failure (2084ms against2000ms) was not rerun unchanged or relabeled PASS. **No Android445 runtime matrix, actual sensor test or audible-output measurement is claimed.**

[Original host results](final-evidence/TEST-RESULTS.json), [post-sign Pro Sports check](delivery445/POST-SIGN-QA-ONLY.json), complete XML/logs and the [physical Fold acceptance checklist](FOLD-ACCEPTANCE.md) distinguish measured behavior from remaining device checks. No performance gain, universal Android acceptance or physical Fold acceptance is inferred from host tests.

Signed2103444 remains unchanged at `lock/infinity-cobra-2103444-user-approved-20261101`, source `1b7a4ef16524854fab77a1c974538aee8a1132bb`. No successor lock or acceptance-pointer update has been made. Only the user may approve this candidate after physical testing.
