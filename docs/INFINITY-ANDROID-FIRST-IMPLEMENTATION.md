# Infinity Android-first foundation — implementation candidate

## Status and provenance

Isolated branch `infinity-android-first`, based on the previously compiled Architecture Audited source at `0270f177fd99832db1047e07be727ac0c58fb922`, not the abandoned G2/#5 staged-Java branch. Upstream remains exact Kodi 21.3 `a3a448d26b8d560a65655dab2cd122994dc4e146`. Original #5 and current #6 FIXED are not modified or uninstalled.

This is new implementation and a CI build candidate, NOT production acceptance. The current #6 dark-mode closure has no matching runtime crash stack; missing uiMode/activity recreation remains a hypothesis, not a proven crash cause. The new source handles uiMode/density/smallestScreenSize explicitly and still needs device tests.

## Implemented boundary

Infinity remains the product; Infinity Controller / bridge remains the integration name. Contract v4 retains v3 endpoints and adds `_infinityGetState()[J`. Engine and Java are built together; do not transplant this into v2 #6. Native decoder/database/add-on architecture remains Kodi, not a TV-core deletion exercise.

The controller publishes window/theme/mode facts. Bounded native state coalesces duplicate dimensions and tracks surface generation, requested sequence and committed sequence. The render owner performs geometry commits; old-generation or superseded requests cannot acknowledge success. Readiness is distinct from an advertised version. Shutdown invalidates requests. The diagnostic array has 16 fields: version, capabilities, active, engineReady, surfaceReady, generation, requestedSequence, requestedWidth, requestedHeight, committedSequence, committedWidth, committedHeight, systemTheme, themeRevision, mode, managed. Capability bits describe geometry/state/theme/PiP interfaces, NOT successful device acceptance.

System theme is published separately to the Kodi Home window property `Infinity.SystemTheme` on its owning loop. Theme-only changes use dynamic skin color variables; they do not request ReloadSkin, display-mode switching or playback reset. The source also publishes device mode and diagnostics. Android manifest orientation is unspecified for phone/window management rather than forced sensor-landscape; rotation and touch need actual-device verification.

## Appearance and feature preservation

The explicit presentation recipe supplies Follow phone (Light / OLED), manual Infinity Light, Infinity Dark and Infinity OLED. Skin settings expose `Infinity appearance`; selected policy persists in skin settings. Full base palette key coverage is checked. This is structural implementation, not evidence of visual contrast on every screen. Video playback overlays retain their existing high-contrast treatment; the original video-lock XML and lock/unlock PNGs remain byte-identical to the approved originals.

The approved Infinity icon is restored in the Android launcher/splash and skin Home branding. The native splash is a padded rendering of the same approved icon. Resume wording changes only the two English resource IDs for Start Over / Continue from; bookmarks/database/native symbols are untouched. Other languages are not claimed translated.

PiP remains the audited event-driven internal-video gate with main-thread Android operations, paused/external-player handling and video aspect. It is not yet device accepted. The original lock interaction/timers and OSD 7999 connection are preserved. Profile-installed Infinity tools/settings are NOT invented or silently claimed bundled; their inventory and migration remain open.

## Build/reuse/signing

`.github/workflows/build-infinity-android-first.yml` runs real SDK Java/DEX checks, host C++ state tests, original contract/packaging regressions and new presentation/signing tests before dependencies and full native compilation. Changed native translation units are compile-checked before the full build. The engine is saved independently before appearance/signing. Presentation changes can use workflow input `engine_run` to reuse an exact matching engine; the hash contract rejects another source/ABI. This is an implemented skin/resource reuse path, not yet an arbitrary Java-layer-only packaging system.

Actual APK version is 2103100 / 21.3-Infinity-Android-First; package stays com.projectinfinity.kodi. Android application debuggability is disabled. Internal base packaging still uses an internal debug-signing prerequisite and retained debug-capable native toolchain; that base artifact is not a user release.

User-facing signing has NO ephemeral-key fallback. It requires securely configured INFINITY_KEYSTORE_B64, INFINITY_STORE_PASSWORD, INFINITY_KEY_PASSWORD, INFINITY_KEY_ALIAS and INFINITY_SIGNER_SHA256. The private key's public certificate must match the pinned digest before signing. Tests use disposable non-runnable fixtures and delete all fixture private material. Actual configured-key possession and update compatibility are not assumed.

All missing signing values produce a clearly blocked status and no signed candidate. Partial/wrong values fail the signing step. Unsigned outputs are not installable. The FIXED #6 certificate differs from the earlier key backup; do not promise install-over or request another uninstall. A safe data-preserving migration/update decision remains required. Artifacts expire after 30 days; this is not permanent archiving.

## Tests versus acceptance

Local checks: actual Java API 34 compilation and D8; 18 inherited source/DEX contract tests; 12 inherited packaging/signing regressions; 8 presentation tests; 5 real-SDK fail-closed signing tests; 4 actual binary-manifest checks. All 47 Python tests passed locally. C++ state tests cover 20,000 concurrent dimension publications, paired snapshots, coalescing, invalid bounds, lifecycle readiness, stale generation/sequence rejection, theme/geometry separation, pause/external/audio PiP policy and shutdown. These host/fixture tests are not a full native engine build or device install.

Production acceptance still requires exact signed package testing: dark/light toggles idle/playing/locked/in PiP; Fold both directions and top/center/bottom touch; rotation/split-screen/keyboard; PiP entry/exit without sliver or pause regressions; original lock and native resume; approved branding and all relevant screens; second same-key in-place update with user data retained. Capture device logs, API and page size. The old native stack remains a 4 KB ARM64 baseline; 16 KB support and secondary TV fullscreen handoff are not established. New render/decoder/security/native capabilities can still require core maintenance.
