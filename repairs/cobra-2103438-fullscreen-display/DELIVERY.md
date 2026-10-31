# Signed 2103439 — fullscreen Display testing candidate

[Download signed APK ZIP](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41253666016/artifacts/13061773194) · [Exact component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41253666016/artifacts/13061588908) · [Successful signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41253666016)

The signed download contains `Infinity-2103439-Combined-Original-Signer.apk`. It is the single consolidated candidate; no separate diagnostic APK was delivered. Package `com.projectinfinity.kodi`, versionCode **2103439**, same original certificate and higher version than 438, supporting install over the existing app. Actual Fold installation/acceptance remains the user's test.

Signed source **1e067768a63e90d8bd534f8b70ca30d367d6635b**. Owner preparation source **6c51ad9bf665bbcb1d9aa6592a8785441b71cd88**, [successful preparation run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41253421611). Original-certificate SHA256 **d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7**. Independent `apksigner verify` validates v1/v2/v3 and one original signer; `zipalign -c -P 16 -v 4` passes.

## Actual file checksums

| File | SHA256 |
|---|---|
| Infinity-2103439-Combined-Original-Signer.apk | `a38eac273c10247b08a00c629b0f6efa98105153ac6ffd67ecf68515a71cd636` |
| COBRA.zip | `e9d978da201c9ccbe04cdc1a2b15ab083091fc2a3072af37f12e434ec582ab8a` |
| INFINITY.zip | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| MINIMAL_ANDROID_CONTRACT.zip | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |
| CHOOSER_SHELL.zip | `db6f373083ef4db2c06acbe8d1778a939b632ec9a18afbba6c7d0e9109b933b0` |

[Machine-readable checksums](SHA256SUMS). The downloaded final component artifact was independently hashed and each enclosed ZIP matches the prepared component byte-for-byte. Both Cobra DEX files inside the downloaded signed APK equal the tested method-merged DEX files.

## Correction and verification

The original Display touch callback executed once but the original panel stayed transparent. Repeated anchored-layout callbacks restarted its reveal. The existing Cards-specific reveal guard omitted Display; native host selection could also attach it under a retained GONE Multi-View overlay. The exact baseline DEX reproduces both failures on the host. The repair extends the existing guard/visible-player host only to original Display sheet kinds. No replacement menu, timer, forced alpha, video calculation, layout redesign or unrelated feature change is introduced.

Seven selected host cases passed across focused runs using actual candidate DEX translated to JVM bytecode, Robolectric API35 native graphics and controlled ExoPlayer metadata/state. Tests include Decor-dispatched real Display/menu presses, close/Back/reopen, inner viewport/hidden Multi host, D-pad activation, all existing choices and checkmarks, channel inheritance/isolation, custom/global sliders and saved values/reset, PiP safety transform/return, missing/late source dimensions and window resizing without replacing the player/TextureView. All 14 existing modes pass 280 geometry observations over five source ratios/PAR cases and four viewports. [Per-mode results and existing menu differences](MODE-RESULTS.md) identify the 13 default-setting choices versus 14 fullscreen choices. The existing Best Fit label's fullscreen fill/crop semantics are retained and disclosed; no working size policy was reinterpreted.

The early global-default test incorrectly assumed a Custom entry in that defaults menu and used an incorrect preference key; the harness was corrected from signed438 source. Original failures and corrected results remain saved. A preparation-only receipt-order mismatch was fixed by sorting changed class names; strict DEX/class hashes were retained and the rebuilt bytes remained identical. No failed integrity check was waived and no key was used in that failed preparation run.

## Exact preservation

Compared against the actual signed 2103438 APK (`a1907acbcb3a36f5b2312f8a11cd4e38d8fcdbed2f435b6ab45d369adc8e9f35`):

- 7,611 non-signature members unchanged; no added or removed members.
- Payload differences: `classes4.dex` (two existing guards/two private predicates in CobraCardsLayout plus CobraComponent.version), typed app version in `AndroidManifest.xml`, and truthful Cobra last-updated metadata in `assets/experience-component-updates.properties`.
- Signing member differences: `META-INF/INFINITY.RSA`, `META-INF/INFINITY.SF`, `META-INF/MANIFEST.MF`. Certificate identity is unchanged. All six changed ZIP members have exact before/after hashes saved.
- 7,168 of 7,170 Cobra class definitions unchanged; only CobraCardsLayout and required component version differ. Exact method allowlist is enforced. No classes or fields added; two private helper methods added. The second Cobra DEX is byte-identical.
- Infinity ZIP/DEX/assets, shared component ZIP/DEX, all 47 native libraries, resources/launcher icons and chooser executable code remain byte-identical. Chooser metadata alone advances Cobra's version; Infinity stays 2103437.
- Cards State/drawer sizing, two/four-column geometry, theme/tile renderers, all video sizing policies, native player/controls and every other Cobra class remain exact. Negative guard controls cover Mobile/Compact/TV Grid/Pro/Pro Sports. No user data was accessed, migrated, reset or cleared.
- Shutdown remains frozen and NOT TESTED. Historical proofs were read by the existing release mechanism, not rerun.

[Every non-signature APK member](evidence/delivery439/ALL-APK-MEMBERS.json), [signature members](evidence/delivery439/SIGNATURE-MEMBER-DELTA.json), [APK result](evidence/delivery439/APK-PRESERVATION.json), [individual component comparison](evidence/delivery439/COMPONENT-PRESERVATION.json), [class/method budget](evidence/METHOD-DELTA.json), [certificate verification](evidence/delivery439/CANDIDATE-SIGNATURE.txt).

## Device-only limits and acceptance

No Android device/adb runtime is attached to this workspace. Host geometry and state-controlled PiP checks are not Android17/Fold or hardware-decoder acceptance. Real streaming/audio/subtitles, channel retune/return, hinge/configuration continuity and actual Android PiP entry/return must be checked on the Galaxy Fold. The screenshot bytes were unavailable; the report does not claim visual inspection of that recording/screenshot or device playback.

On front and inner displays: enter fullscreen from Cards, press Display, Back/close and reopen; repeat after Multi-View return. Select each existing size mode, verify Custom width/height and inheritance, change channel and return, rotate/resize/fold with playback active, then PiP and return. Confirm captions/audio/player continuity and unchanged neighboring Channels/Multi-View/PiP/More. Use other modes as preservation checks. No shutdown test is requested.

Signed 438 and its lock remain untouched at `a5f721578c53e026a26cf21d929fbdad530f6d17`. The accepted release pointer was not changed. 439 is NOT automatically locked/promoted; only the user can accept it physically.
