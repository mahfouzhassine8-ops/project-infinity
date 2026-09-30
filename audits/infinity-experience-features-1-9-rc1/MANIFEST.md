# Infinity Experience Features 1–9 — RC1

Parent: locked-infinity-cobra-2103256-no-video-hold-menu-device-passed-20260926
Parent versionCode: 2103256
Parent native/Cobra APK changed: NO

This branch records the companion-layer feature pass only. It does not replace or mutate the protected 2103256 APK baseline.

## Candidate components
- Infinity Command Center 0.3.6.0
  - ZIP SHA-256: fe4db5ce250d16e3b6286ac61532a3d3bb3eef6dda5fdd567adde267bfcf96ce
- Infinity skin target 1.0.5.170
  - delivered through local builder only; full skin binary/assets are not committed or redistributed here
  - accepted reviewed sources: 1.0.5.167 and 1.0.5.169
- Infinity Skin Experience Update 1.0.2
  - ZIP SHA-256: 63c6a94ce95e1248b7269a6945bd680287f916b6af6808052b1270d3e4c2804b
- Health Center remains 2.5.18
- Authorization & Accounts remains 0.5.2

## Features
1. Local-first Resume Hub, extending the existing continue-watching.json. Trakt is optional.
2. Predictive Highlight Preloading after stable focus using Kodi texture loading; no direct downloader.
3. Infinity Command Palette.
4. Smart Source Memory: local reliability profile and recovery guidance; Umbrella source code/ranking remains untouched.
5. Advanced Playback Recovery after actual playback error with explicit choices only.
6. Health Center Status Orb using health-bridge.json.
7. Adaptive Artwork Quality while scrolling, scoped to Infinity Home/Browse only.
8. Full Session Restore for interrupted navigation state.
9. Infinity Ambient Home: Off / Subtle / Immersive, UI atmosphere only; video pixels unchanged.

## Preservation / privacy
- No APK or native engine rebuild.
- No Cobra changes.
- No Umbrella source modification.
- No provider URL replacement.
- No Trakt requirement for Resume Hub.
- No account reset or userdata wipe.
- Resolved HTTP/debrid playback URLs are not persisted by Resume Hub; only replay-safe local/Kodi routes and stable IDs are retained.

## Current automated verification
33 local regression/integration checks: PASS.
- all 549 candidate skin XML files parse
- existing Home non-navigation geometry/actions preserved
- Browse controls preserved
- provider content routes preserved
- both reviewed skin baselines reconstruct the exact same 1.0.5.170 target
- exact rollback is generated for either source baseline
- protected UI recovery contract updated for 1.0.5.170
- predictive preloading, Health status, session clean-stop and source-memory failure paths exercised with deterministic Kodi stubs
- full device rendering/playback acceptance remains pending

Source/evidence bundle SHA-256:
71e5c4296333ce324d5b706958509b7a65564d599de205ae536526f91eab7d34

Status: TEST CANDIDATE — not a stable/device lock.
