# Signed2103440 — Cards Preview restoration testing candidate

[Download signed APK ZIP](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41257728491/artifacts/13063544732) · [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41257728491/artifacts/13063359982) · [Successful original-key signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41257728491)

The signed ZIP contains **Infinity-2103440-Combined-Original-Signer.apk**, the one consolidated testing APK. Package `com.projectinfinity.kodi`, versionCode **2103440**, original certificate. The package identity/certificate/higher version support install over438 or439 without uninstalling or clearing data. Actual installation and final acceptance remain the user's physical Fold test.

Signed source **5967f4803f9c14906ad92d4006e32bf641f65dd1**. Tested/prepared owner source **f15b4e3cdb6b9ecc7bfd718b1f309bda11808d93**; [successful preparation41257408041](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41257408041). Recovery comparison is the latest locked approved **2103438**, source `a5f721578c53e026a26cf21d929fbdad530f6d17`. The delivered439 Display fix remains integrated;439 has not been used to silently replace that lock.

Original certificate SHA256 **d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7**. Independent `apksigner verify` validates v1/v2/v3 and exactly one original signer. Independent16KB alignment check passes.

## Files and checksums

| File | SHA256 |
|---|---|
| Infinity-2103440-Combined-Original-Signer.apk | `c34b466fb335a273331221a2e963c189747f15811f5b75c59862ad71b2719a4c` |
| COBRA.zip | `4acce986f0ae35235de6e835a63217fe32db4aa6039aa057b2f1ed01cae94344` |
| INFINITY.zip | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| MINIMAL_ANDROID_CONTRACT.zip | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |
| CHOOSER_SHELL.zip | `2c6cd13e3c496e681d0b03c355c52ceffc9d3db5597b08e513a71652fcc4f550` |

[Machine-readable SHA256SUMS](SHA256SUMS). The final published component archive was independently downloaded and each ZIP hashed against the source-bound prepared component. The signed APK's two Cobra DEX files match the tested DEX bytes exactly.

## Restored behavior

- Tapping the SMALL Cards preview opens the existing original Preview controls menu. Its real controls, long press, Channel actions and child menus retain their original implementation.
- Repeated native anchored-layout callbacks no longer leave preview-owned sheets transparent. The repair qualifies the actual preview owner, including inherited child-menu anchors.
- The original native Cobra Now Playing emblem is restored and pulses separately from the approved LIVE dot/badge. It uses the existing native state observations, view and1400ms reverse-repeat animator, with existing foreground/reduced-motion/visibility controls. Global effects policy, other view modes and fullscreen pulses retain their prior behavior.
- Explicit Fullscreen, PiP and return-to-preview retain the existing player and channel. Channel selection continues through its original Preview route. The439 fullscreen Display correction is retained.

No redesign, replacement Preview system, new widget, new polling/worker, data migration or unrelated optimization is included.

## Focused results

Eight selected host cases passed across focused runs using actual final owner DEX translated to JVM and Robolectric API35 native graphics. Real Decor-dispatched taps/long presses and original menus/callbacks are exercised; source metadata and decoder-entry/Android-PiP terminal behavior are controlled.

| Check | Host result |
|---|---|
| Preview menu, long press, original controls and nested Channel actions | PASS |
| Native pulse separate from LIVE; pause/resume, foreground and system reduced motion | PASS |
| Fullscreen return / PiP handoff / source-player identity | PASS |
| Channel selection reaches original Preview start exactly once | PASS (controlled decoder entry) |
| All14 existing size settings, front/inner light/dark | PASS:56 menu/pulse/session cases |
| Front/inner palette fixtures including OLED | PASS:6 cases |
| Active cover/inner/orientation/split resizing and live light/dark restyle | PASS:8 cases |
| Mode exit restores native status ownership; other view-mode guards | PASS |
| Signed438 outer Cards geometry and LIVE badge bounds/pixels | EXACT:4 front/inner light/dark cases |
| Release protocol / extra-member rejection / original-source guards | PASS:4 focused checks |

The stock Robolectric animator shadow caps INFINITE to one repeat. The corrected QA-only shadow preserves Android's requested repeat semantics while tests advance bounded frames. Production timing/assertions were not weakened. The channel fixture's decoder-entry spy was corrected to match boxed loose signatures; no APK dependency was changed to satisfy host execution. Historical failures and their corrected results remain saved. Unchanged size-math source is compared exactly; the earlier439 geometry evidence is retained rather than rerun as a new size-policy repair.

## Exact source/component/APK preservation

Actual signed438 APK SHA256: `a1907acbcb3a36f5b2312f8a11cd4e38d8fcdbed2f435b6ab45d369adc8e9f35`.

- **7,611 non-signature APK members unchanged**, no members added/removed. Payload changes are `classes4.dex` for scoped Cobra methods/component version, typed app version in `AndroidManifest.xml`, and truthful Cobra version metadata in `assets/experience-component-updates.properties`.
- Signing-member changes are `META-INF/INFINITY.RSA`, `META-INF/INFINITY.SF`, `META-INF/MANIFEST.MF`. Original certificate identity is verified. All six changed ZIP members have before/after hashes.
- **Infinity437 ZIP/DEX/assets and shared ZIP/DEX byte-identical**, all47 native libraries and resources/launcher icons unchanged. Chooser executable code/design is exact; version metadata alone advances Cobra to440, Infinity remains437.
- **7,165 of7,170 Cobra class definitions exact**, no classes or fields added. The allowlisted definitions are CardsLayout/PreviewBadge, Cobra-owned Activity's two preview methods, PulseView's scoped restart guard and required component version. Baseline438 method budget includes the retained439 Display helpers. All other methods, field sets and static defaults are preserved by the original writer and full post-build canonical comparison. Second Cobra DEX is byte-identical.
- Native Activity's actual class name `InfinityLiveActivity` belongs to the COBRA module/classes4.dex, not the protected Infinity owner. No Kodi/shared/native-library changes are present.
- Cards State/geometry/drawer, theme/tiles, global effects classifier/enum and all display sizing policies are exact. Pro/Pro Sports/Mobile/Compact/TV Grid/Multi-View and unrelated controls retain their implementation. The three439 Display host/private predicates are exact; only the existing reveal guard gains a preview-owner condition.
- User data, settings, profiles and databases were not accessed/reset/migrated. Shutdown is unchanged and NOT TESTED.

Evidence: [every non-signature APK member](evidence/delivery440/ALL-APK-MEMBERS.json), [signature members](evidence/delivery440/SIGNATURE-MEMBER-DELTA.json), [APK comparison](evidence/delivery440/APK-PRESERVATION.json), [component comparison](evidence/delivery440/COMPONENT-PRESERVATION.json), [retained439 controls](evidence/delivery440/RETAINED439-CONTROLS.json), [exact class/method delta](evidence/METHOD-DELTA.json), [geometry/pixel parity](evidence/GEOMETRY-PARITY.json), [original-certificate verification](evidence/delivery440/CANDIDATE-SIGNATURE.txt).

## Physical acceptance still required

No physical Fold/Android17 runtime or hardware decoder acceptance is claimed. Host viewport resizing is not a real hinge transition; controlled-player PiP handoff is not an Android PiP session. Real stream/audio/subtitle continuity, actual cover/inner transitions and background/foreground behavior remain device checks.

On the Fold, in light and dark Cards: select/change a channel, tap the small preview to open the original menu, exercise Play/Pause and Channel actions, close/reopen, then enter Fullscreen and return. Confirm the separate Now Playing pulse and LIVE dot, preserved scrolling/selection and unchanged layout; unfold/refold/rotate, then PiP and return. Check the existing size options without treating normal letterboxing as a defect. No shutdown test is requested.

438 remains locked at its original source and its signed recovery APK is retained. Signed439 remains intact. **440 is a testing candidate, not automatically locked or promoted. Physical acceptance belongs to the user.**
