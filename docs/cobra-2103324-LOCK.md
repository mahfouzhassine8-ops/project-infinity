# Cobra Pro 2103324 — User-Approved Locked Base

Locked by explicit user instruction on **2026-10-07** (America/Detroit): “New bace”.

## Authoritative identity

- Package: `com.projectinfinity.kodi`
- Version: `1.0.9-Chooser-Close-Owner-RC1 (2103324)`
- APK SHA-256: `5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3`
- APK bytes: `157925831`
- Source/build commit: `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`
- Source tree: `dfa37152685c99adac939668198682ef9049528f`
- Successful validation run: `37578532123`
- Validation job: `112652743934`
- Permanent signer SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Skin: `skin.infinity.diggz 1.0.5.201`

## Scope and verification

2103324 is the forward correction built from the exact locked 2103323 APK and source. Its source delta is limited to:

- `tools/android/packaging/xbmc/src/InfinityKodiShutdown.java.in`
- `tools/android/packaging/xbmc/src/Splash.java.in`

The correction requires proof held by the actual Kodi process before a saved close record can be treated as active, and limits the recovery dialog to an Infinity launch request.

Verification recorded **214 passing tests** across 15 suites, with zero failures, errors, or skipped tests. The other 252 source files are identical to 2103323. The 4,168 protected APK entries are byte identical, including native libraries, resources, assets, and skin. The compiled preservation audit reports 8,712 other classes preserved. The package, install-over behavior, permanent signer, preferences, and user data contract are retained.

This lock records the user’s acceptance decision. It does not convert controlled CI into a claim about unrecorded physical-device scenarios.

## Base and rollback policy

- **2103324 is the authoritative base for all future work.**
- 2103323 remains preserved as the immediate rollback.
- 2103322 remains preserved as the preceding rollback.
- Future candidates must branch from source commit `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3` and verify against the exact 2103324 APK above.
- No future change may silently alter Cobra, Sports, playback, providers, native engine, skin, settings, preferences, or user data outside its declared scope.
