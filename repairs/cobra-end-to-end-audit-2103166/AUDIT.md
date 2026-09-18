# Cobra 2103166 — End-to-end UI / lifecycle audit

## Baseline and scope

2103166 starts **only** from the user-locked Cobra 2103165 baseline:

- locked branch: `locked-cobra-2103165-inner-insets-pip-return-player-consistency-passed`
- commit: `6148e34be3024c5939c736a7b4316572d7bd50c0`
- successful build/run: `35343195748`
- versionCode: `2103165`

The locked branch is not edited or moved. Candidate 14, locked 2103164 playback stability, the approved player presentation, native Kodi engine, signer, resources, provider data, EPG logic, theme ZIP contract and user data are protected.

## Why another pass was needed

Physical-device testing exposed a remaining structural safe-area defect on the Settings screen: the ordinary Cobra shell could still render beneath the Android top system area, clipping the `COBRA • SETTINGS` header. The previous 2103165 work correctly separated normal browsing from fullscreen-player status-bar ownership, but merely showing the status bar is not enough on modern Android edge-to-edge layouts. The browse content must explicitly consume current system-bar and display-cutout insets.

A screen-specific Settings margin would be the wrong fix. Settings, Sources, Profiles, Health Center, Live/Guide and VOD all share the same browse root, so the correction belongs at that root.

## End-to-end audit and corrections

### 1. One safe-area owner for every ordinary Cobra screen

`buildShell()` installs one idempotent window-insets listener on `mRoot`. It uses the maximum of:

- Android system-bar insets;
- display-cutout safe insets.

It applies left/top/right/bottom padding by replacement, never accumulation. That protects the Settings header, rail, TV Grid, guide, internal screens and the bottom gesture/navigation area from the same source of truth.

The Experience chooser keeps its separate, already-tested Splash safe-area contract.

### 2. Fullscreen ownership remains isolated

The approved 2103165 rule remains:

- normal Cobra surfaces: status bar visible;
- fullscreen video / Multi-View: status bar hidden;
- Android navigation/gesture bar is never deliberately hidden here.

The browse safe-area padding lives on `mRoot`; fullscreen player surfaces remain direct decor children and therefore stay edge-to-edge.

### 3. System-bar appearance is deterministic

Browse status/navigation bar colors track the active Cobra background. Icon contrast is derived from background luminance. Fullscreen video uses black system-bar color/light icons. This avoids invisible status icons when switching between Light, Dark and True OLED Black appearances.

### 4. Existing behavior is protected, not reimplemented

The repair hashes and proves byte-identical a broad set of working owners including:

- approved player chrome, drawer, settings, track picker, lock and preview;
- PiP return / expansion lifecycle;
- onStart/onResume/onPause/onStop/onUserLeaveHint/configuration ownership;
- mini-player background media ownership;
- Settings, Sources, Profiles, Health Center, guide, VOD and primary navigation;
- provider loading, M3U/Xtream parsing, channel filtering and directory grouping.

Only `buildShell()` and `cobraApplySystemBarsForSurface()` are allowed to change, plus two new safe-area/contrast helpers.

## Acceptance

The CI pipeline reconstructs the exact 2103165 source chain, applies only 2103166, packages/signs the Android shell, and compares protected APK payloads against both locked 2103165 and Candidate 14.

Delivery requires:

- exact locked 2103165 APK identity;
- permanent signer unchanged;
- Kodi/native libraries unchanged;
- assets/resources/resources.arsc unchanged;
- 46 inherited navigation/Health/theme/experience tests;
- 16 Candidate 14 tests;
- all 26 locked 2103164 playback-stability tests;
- all 6 locked 2103165 status-bar/PiP-return tests;
- 8 new 2103166 shared-root/Fold/system-inset tests;
- static source audit proving one browse content root, no global fullscreen, no navigation-bar hiding, shared safe-area ownership, and protected-method byte identity.

Expected total: **102 Android tests**, plus static/source/native/signer gates.

Physical Samsung Fold acceptance remains a separate final check. Automated tests do not claim OEM SystemUI, hardware decoder, real provider network or installed-device behavior.

CI trigger note: this branch must pass the complete 2103166 reconstruction, protected-payload, inherited, locked-baseline and new end-to-end gates before any APK is accepted.

Audit harness note: fullscreen ownership detection distinguishes an intentional `clearFlags(FLAG_FULLSCREEN)` from any call that sets/adds the fullscreen flag.
