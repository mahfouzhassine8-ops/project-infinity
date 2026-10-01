# Infinity 1.0.5.176 — Ambient Home Drawer Placement

## User-authorized lock

Locked at the user's direction on 2026-10-01.

This is a skin-only forward lock. It places the existing `AMBIENT HOME`
selector directly below `SETTINGS` and above `POWER` in the Infinity drawer.
The selector keeps the existing `Off / Subtle / Immersive` modes and calls the
existing Command Center `ambient-home` action.

## Locked source

- Locked source branch: `locked-infinity-2103282-native-ambient-settings-drawer-user-approved-20261001`
- Locked source commit: `16f22d143f076976f55c0e2d9ac3ffabfbbd931b`
- Candidate source branch: `candidate-infinity-native-video-ambient-settings-drawer-20261001`
- Android parent: Cobra/Infinity APK 2103282 (unchanged)
- Command Center: 0.3.5.17 (unchanged)
- Skin candidate: `Infinity-Mobile-1.0.5.176-Native-Video-Ambient-Settings-RC1.zip`
- Skin SHA-256: `4263de3906ea0dc6e24f3c6f04c2f779b0c7a8bbdd31656b82e221402063d1c9`

## Rollback references

- Immediate skin rollback: 1.0.5.175 Native Video Ambient RC1
- Immediate rollback SHA-256: `9c34f0b158fbdcc2aae5b74c29f86d0f1b6e6844e56bd8b7ddd677ef49dc9b72`
- Original locked .173 skin SHA-256: `e70cbcc974dbb646c4061432ce458d513911108aad943cddcc663dc7b937b98e`
- Older .172 skin remains the historical rollback baseline.
- APK rollback 2103281 SHA-256: `4c119343d623be5c15233e7b1ed7fa82e3d1f92c3a5ec56f7d3f85b0707cbfe5`

## Verification boundary

- Drawer placement contract: passed across 16x9, 20x9, 6x5, 5x6 and portrait profiles.
- Existing Command Center and ambient owner: unchanged.
- APK/native playback behavior: unchanged.
- Physical Galaxy Fold visual acceptance: **pending**.

This is a user-authorized source lock, not a claim of device-passed,
production-final or fully verified status. Install over the existing skin/app
without uninstalling or clearing data, then perform the Fold acceptance pass.
