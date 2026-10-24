# Infinity 7.1 actual APK verification — 2026-09-08

## Confirmed outcome

The Architecture Audited Build, run `34270347697`, completed successfully at `2026-09-08T20:36:38Z`. Preflight, the real changed-C++ translation-unit compiler gate, full native build/base APK, independent engine upload, presentation overlay, signing, signature verification and final candidate upload all succeeded. This is the audited replacement, not G2.

Engine source commit: `79d350a7ac3cc20ff01b56f39a6fc1f13725415c`.
Kodi source commit: `a3a448d26b8d560a65655dab2cd122994dc4e146`.
Validation/signing-tool follow-up commit: `68652eb268d2a86d1bf92b0c3daa0d00713f7697`.

The follow-up did not change the native/Java source patch, stop the existing engine job or start another full Kodi build. Its independent validation run `34276343518` also succeeded. Its actual job log confirms 18 original plus 12 new regression tests passed, alongside the host C++ state test including 20,000 concurrent packed-dimension events. Test-fixture signing used temporary keys, not repository secrets.

## Actual artifacts downloaded and checked

Both archive digests were checked against GitHub's artifact metadata before extraction.

- Final candidate artifact `10075630878`, `Infinity-7.1-Audited-Candidate`: ZIP SHA-256 `1e3de041a5bbaa1e722e6d9390910c55c8412be4fb0f43816c0316608f17bd2a`.
- Reusable engine artifact `10075585963`, `Infinity-7.1-Audited-Engine`: ZIP SHA-256 `29c3808209df4b58afa1d1d464da270f3db777d75792d32846f251cd310bcce6`.
- Final `Infinity-7.1-Audited.apk`: SHA-256 `6478b8bab2c77dca6b55a8fcdb7b5f940c6b9602d59636c497eb2cb45109c4d0`, matching the supplied checksum.

The actual base APK passed the hardened `check_engine`, and the actual signed candidate passed hardened `verify_overlay` from follow-up commit `68652eb...`. The two artifacts contain identical engine.json metadata. All 45 native shared libraries and all seven DEX files remain byte-identical between the base engine APK and signed candidate. The binary manifest, binary resources and every other protected member also match.

Exactly four non-signature APK members changed: the lock PNG, unlock PNG, preserved original lock dialog and VideoOSD button insertion. The stronger verifier checked the actual lock button XML/actions and the exact native method declarations in Main, XBMCSettingsContentObserver, XBMCInputDeviceListener and XBMCMainView across the real DEX files.

These extra checks were applied independently after download. The original successful run used its original checkout; it did not magically receive the later tool changes while running.

## Actual signing result and update caveat

Android Build Tools 34.0.0 `apksigner verify --verbose --print-certs` independently confirmed valid V1, V2 and V3 signatures. `zipalign -c -p 4` succeeded. The report has five META-INF/JAR-entry warnings; verification still succeeds, and these warnings are not an unsigned-APK error. V3.1, V4 and SourceStamp are not present; this report does not claim otherwise.

Actual signing mode: **ephemeral-test-only**.
Certificate DN: `CN=Infinity Test Only, O=Project Infinity, C=US`.
Certificate SHA-256: `4ec5a65a6cf6fec8312bef7794653460926135e9ace20732b01f2e0c7322cc7b`.

The real 7.0 donor's certificate SHA-256 is `866100cc494057a7856a39e677a39966b5f70e9ce13aaf9e4de440c8af508c19`; it differs. Both APKs report package `com.projectinfinity.kodi`, versionCode `2103000`, versionName `21.3`, minimum SDK 21 and target SDK 34. Therefore this candidate is not a normal in-place update for that donor installation. The certificate of the user's currently installed app has not been obtained. Do not uninstall the existing app or risk its userdata to bypass a certificate mismatch without a verified backup. No stable production signing key was configured or recovered during this audit.

## Open issues and device scope

**No device acceptance has been performed.** Cold boot/JNI loading, playback, Home PiP, Fold touch alignment, surface recreation, normal resume and lock interactions still need testing on the intended device.

**Known Leanback TV handoff defect remains open.** The follow-up audit reproduced stale managed dimensions when returning from TV PiP/multi-window to normal fullscreen. The phone/non-Leanback branch uses a different, continuously managed geometry path. This is not a universally TV-verified engine. The native/Java fix was not silently added or claimed complete.

**16 KB compatibility is not established, and actual ELF inspection found a concrete alignment limitation.** All 45 shared libraries are ELF64 little-endian AArch64 (machine 183). All 91 PT_LOAD segments declare alignment 4096, not 16384; none of the 45 libraries passes the 16 KB segment-alignment criterion. The current 4 KB zipalign check does not resolve this native-binary issue. A 16 KB device may require compatibility mode where available, or a properly rebuilt native stack; its behavior is not guaranteed. The user's device page size has not been measured. This does not establish a failure on a 4 KB device.

The stock native resume/database remains unchanged by this follow-up. Automatic OLED/light theme presentation is not newly activated. Skin/presentation-only changes can reuse this saved matching engine; changes to its native/Java contract or page-size support still require the corresponding build and testing.

## Verification sources

- Build: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/34270347697
- Independent tests: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/34276343518
- Independent test log: job `102230181194`; results artifact `10075866389`.
- Actual candidate and engine archives listed above, checked locally with the hardened repository scripts and real Android SDK tools.
- Android signing/update identity: https://developer.android.com/studio/publish/app-signing
- Android ELF/page-size requirements and compatibility mode: https://developer.android.com/guide/practices/page-sizes

**Conclusion: full build and signed-APK integrity checks passed. A real signed candidate and reusable engine now exist. Runtime/device acceptance is pending, with the TV handoff and 16 KB alignment limitations explicitly recorded.**
