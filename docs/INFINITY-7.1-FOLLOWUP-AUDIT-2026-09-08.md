# Infinity 7.1 follow-up audit — 2026-09-08

## Target and limits

Target: **Architecture Audited Build**, run `34270347697`, engine source commit `79d350a7ac3cc20ff01b56f39a6fc1f13725415c`. This is not G/G2. The working branch was read at `2a674c11cb1dc93002fefd868620f9a5a3d6e396`; its subsequent edits affected the old G2 mapper, not the audited source patch. Snapshot `799ab62c4a94c3d3f7a06a4f9f0141afd25a4d25` was exported through a source-only workflow for executable checks.

The audited source patch remained blob `ae209fcd4e9a0e9691a5a1a7bf213cac86cfef29`. **This follow-up changes validation/signing tooling, not the Kodi source patch or bridge ABI.** It does not cancel or restart the active engine build. An in-flight Actions run uses its existing checkout; these new checks must be applied separately to that run's outputs or by later packaging runs.

At the live status checks during this audit, preflight, dependency configuration and the real cross-compiler syntax checks of the three changed C++ translation units had passed. The full engine/base-APK job was still running; the reusable-engine upload had not yet completed. A successful syntax check is not a successful full link/package or device test.

## Findings reproduced before fixes

1. **Companion JNI gap.** Changing `_onVolumeChanged` in the compiled DEX left the Main-only contract test green. Main must not be treated as proof that the settings observer, input listener or surface callback class is wired correctly. The checker now validates all four relevant classes and their exact native method signatures, requiring exactly one definition of each across all DEX files. These expected signatures were checked against the pinned Kodi Java sources and native registration tables.
2. **Standalone metadata gap.** `verify-overlay` accepted a manifest claiming bridge version 2 while checking a version 3 candidate. The overlay creation path checked this, but the final standalone verifier did not. Both paths now validate schema, package, Kodi commit, bridge version, source-patch checksum and inventory digests.
3. **Missing lock connection.** Removing the lock button from VideoOSD still passed as long as its image/dialog assets existed: VideoOSD was allowlisted but unvalidated. Verification now requires exactly one button `7999` and the approved XML subtree/actions. Missing, duplicate, malformed and incorrectly routed buttons are rejected. Protected engine/DEX/resource members still must remain byte-identical.
4. **Silent signing downgrade.** The original signing script accepted an alias-only stable configuration and produced an ephemeral test signature. The new script rejects every partial configuration before signing. All four signing values must be supplied together, or all four absent for explicitly test-only signing. A supplied invalid key never falls back to a test key. The output's alignment is also checked after signature verification.

These were validation/configuration defects, **not evidence that the active engine compile had failed**.

## Executed tests

The original 18 Python regressions were rerun against the unchanged source postimages and passed. Twelve additional tests passed, including subtests for all 14 partial signing configurations and five invalid engine-metadata cases. The new suite also exercises missing/wrong companion JNI methods, missing/duplicate/malformed lock buttons, wrong lock actions, ephemeral signing, invalid stable keys and two signings with one supplied fixture key.

Java Main/bridge and their source-level supporting classes were compiled against the actual Android API 34 JAR; D8 produced DEX at min API 21. Local Java was OpenJDK 21 targeting Java 8; the independent CI workflow explicitly selects Java 17 to match the build. Existing unchanged collaborator stubs remain compile-only. No claim of full Android-runtime execution is made.

AAPT2 compiled a **binary Android manifest**, and the real `zipalign`/`apksigner` tools signed and verified the test APKs. V1/V2/V3 signature verification succeeded; protected APK members remained identical after signing. Reusing one temporary supplied keystore produced the same certificate SHA-256 on both outputs. These are non-installable integrity fixtures with deliberately fake native bytes, not substitutes for a real Kodi engine. All temporary test private keys are deleted and excluded from artifacts; no repository signing secrets were read.

The host C++ state test passed again, including 20,000 concurrent packed-dimension updates. This is a state-unit test, not a Fold/renderer/device test.

Independent CI workflow: `.github/workflows/audit-infinity-7.1-followup.yml`. It runs only short Java/state/packaging/signing tests, with read-only repository permission and no access to repository signing secrets. It does not invoke Kodi's native build.

## Source/lifecycle review and open runtime issues

**PiP:** Existing native lifecycle supercalls remain intact. Playback facts are updated through Kodi Player announcements; the Java adapter switches to the UI thread. An apparent auto-PiP/onPause ordering concern was checked against Android framework source rather than patched speculatively: `ActivityThread.handlePauseActivity` sets `mIsInPictureInPictureMode` before pausing for an auto-enter transaction. Therefore this pass does not claim a proven universal auto-PiP pause failure or change that native path. OEM Home gestures, actual uninterrupted video and audio focus still require the real device.

**Fold:** The current phone/non-Leanback path always manages geometry. Layout/surface requests are coalesced and applied through the render-side MessagePump and Kodi's ApplyModeChange path. This connection is source-reviewed and its small state object is unit-tested; real rendering, touch alignment and hardware-decoder surface recreation remain unverified.

**Known open TV bug — NOT fixed in this pass:** on a Leanback TV, leaving PiP/multi-window changes Java's managed snapshot to zero. Native QueueGeometry ignores zero rather than releasing the old managed request. A state-level reproduction queued and committed `384x216`, simulated the zero fullscreen handoff and retried: the old `384x216` request was returned again. This is a concrete stale-state defect in that TV handoff. Actual screen behavior depends on the device's remaining callbacks; no TV run was executed. It does not follow the normal Fold path, which remains managed in fullscreen. Fixing the handoff correctly needs native/Java protocol work and a new matching engine; do not label this engine TV-verified or universally frozen. This follow-up leaves the active phone-targeted build intact rather than pretending a validator change fixes that runtime behavior.

**Resume and appearance:** stock 21.3 native resume/database code is untouched. The four approved lock-layer members are the only skin changes from overlay packaging. The original 7.0 lock assets and their hashes are preserved. Automatic OLED/light presentation is still not newly activated.

**Android 16 KB devices:** the pinned NDK 21 toolchain and Build Tools 34 signing path are not proof of 16 KB ELF/page compatibility. The script checks 4 KB alignment. Device page size and every real shared-library ELF segment still need examination before claiming support on a 16 KB device. Merely re-signing cannot establish ELF compatibility. No speculative toolchain upgrade was made during the active build.

**Install-over:** the inspected 7.0 donor reports package `com.projectinfinity.kodi`, versionCode `2103000`, versionName `21.3`, min SDK 21 and target SDK 34. A signed artifact still needs the same certificate as the actual installed app and a compatible versionCode to update it. The installed certificate is not known. Secret names existing would not by itself establish this match. Do not uninstall the existing app or risk its userdata to work around a mismatch without a verified backup.

## Primary references

- Pinned Kodi source: https://github.com/xbmc/xbmc/tree/a3a448d26b8d560a65655dab2cd122994dc4e146
- `tools/android/packaging/xbmc/src/{Main,XBMCMainView,XBMCInputDeviceListener,XBMCSettingsContentObserver}.java.in`
- `xbmc/platform/android/activity/{JNIMainActivity,JNIXBMCMainView,XBMCApp}.{h,cpp}`
- `xbmc/windowing/android/{WinSystemAndroid,WinSystemAndroidGLESContext,AndroidUtils}.cpp` and `xbmc/windowing/GraphicContext.cpp`
- `cmake/scripts/android/Install.cmake` and Android Gradle/Makefile packaging sources
- Android PiP: https://developer.android.com/develop/ui/views/picture-in-picture
- Framework auto-enter ordering: https://android.googlesource.com/platform/frameworks/base.git/+/16bf00a05b2c78e604abddfffaaf3b6a5af8289d/core/java/android/app/ActivityThread.java
- Android alignment: https://developer.android.com/tools/zipalign
- Android page sizes: https://developer.android.com/guide/practices/page-sizes
- Artifact archive compatibility: https://github.blog/changelog/2026-02-26-github-actions-now-supports-uploading-and-downloading-non-zipped-artifacts/

## Bottom line

The old G2 post-build mapper is not part of this pipeline. No additional engine build failure was established in this pass. Concrete validator/signing weaknesses were fixed and exercised without modifying the engine. The full native build, real final APK inspection and target-device acceptance are separate gates. The known TV handoff issue remains explicitly open.
