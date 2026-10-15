# Infinity Shipping Audit RC2 — installable delivery record

Status: TEST CANDIDATE. No stable promotion. Physical-device acceptance and historical FD_SET root cause remain open.

## Android artifact actually built

- Run 36230424118: success; final job android-package-audit.
- APK-producing source commit: 1407750afd4bbe70e0991d49b108269bab0337bf.
- VersionCode 2103255. Java lifecycle cleanup; exact 2103254 native engine reused.
- APK delivery filename: Infinity-2103255-Shipping-Audit-RC2.apk.
- APK SHA-256: 273c7d0a88196cd9f00121b51fe5ac54a4328558c34d5c3c79a74e85a29176be.
- Native SHA-256: c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d.
- Permanent signer SHA-256: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7.
- 4,166 protected APK members byte-identical; JNI declarations identical. Shared Java host lifecycle changes are intentional; not all DEX bytes are claimed identical.
- 18 actual-method Java harness assertions passed and real Android compilation/signing/preservation gates passed.
- Original 2103254/2103229 rollback and audit source branches not modified by this branch.

## UI and companion deliverables

Prepared locally from exact Library-owned skin 1.0.5.167 and Command Center 0.3.5.15. Not misrepresented as a GitHub skin render or UI test run.

1. Infinity-Skin-1.0.5.169-Installer-RC2.zip
   SHA-256 d3470e121ca874152523d005865694150daa30ae6fcbf4b389dcfebc911d0b4f
   Installs script.infinity.shippingupdate 1.0.0. It SHA-checks the reviewed source delta and the installed 1.0.5.167 source, creates complete 1.0.5.169 and rollback ZIPs using existing local assets, verifies them and offers the native Kodi InstallFromZip picker. No direct installed-skin/userdata overwrite and no bundled font files.
2. Infinity-Command-Center-0.3.5.16-Shipping-Audit-RC2.zip
   SHA-256 161cda0d083d3132f68a8bde0d674330e67d03d76ec98dd192f1b0459551fc85
   Data-aware optional-rail release, bounded Continue Watching validation and exact current-version UI recovery contracts. Old conservative timing, settings, providers and recovery implementation retained.
3. Infinity-Shipping-Audit-RC2-Source-and-Evidence.zip
   SHA-256 32df417700ffac4e78757b3c817d2560bfbdc6b1be1a9a7cd9106922c953249f
   Contains all new Python modules, candidate companion source, exact skin source delta, patch/build scripts, test sources, the source-window inventory and source/package verification receipts. Delivered as a conversation artifact, not a GitHub workflow artifact. Does not contain user diagnostics, credentials, fonts or native binaries.

Skin source delta SHA-256: a72fd11fc59837f4ba8ea82176dbb965e89f9558d030cb98bdb5c8df0ff946d8.

Skin source: 53 existing files edited, 21 common custom-window files moved unchanged to the correct default folder, one seek helper added. Original 1,361 members become 1,362. 1,287 same-path members plus 21 moved members retain exact bytes. 549 XML files parse. Five responsive active profiles each resolve 120 window definitions and 32 unique custom IDs. Added 310 directional links without moving existing buttons; corrected 24 doubled volume steps, two downward-page actions, the existing Go To Time command, conditional weather header/forecast bindings and 240 poster fallbacks. Home menu/widget geometry, provider URLs, assets and animations preserved.

## Actual tests and limits

85 local automated tests passed: parsing/resolution, preservation, focus graph including disabled cards, real helper/listing/tick/recovery code with simulated Kodi boundaries, package failure/cancellation safeguards and utility UI routing. The complete skin ZIP and rollback were built locally and every member compared with the intended target/input. This does not establish Android storage permission behavior, a phone install or rendered UI quality. The earlier RC1 113 tests are not counted again.

Keep Health Center 2.5.17 and Authorization & Accounts 0.5.2 from RC1; no account reset or reauthorization requirement introduced. Cobra feature source/native/assets and the separate 32-bit TV work are unchanged. A shared-host device smoke test is still required.

The historic FD_SET abort is NOT fixed by Java lifecycle cleanup. Original native caller attribution/resource ownership are unresolved. No full shipping acceptance or stable lock is claimed until device navigation/rendering/provider/playback/lifecycle and native-resource tests pass. Retained crash history must not be deleted to produce a clean-looking result.
