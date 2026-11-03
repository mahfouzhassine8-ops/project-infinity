# Infinity Preview 2103451 — User-directed lock and handoff to Infinity Kodi

**Date:** 2026-11-03
**User directive:** "Lock what we have, switching to Infinity Kodi."
**Scope:** Freeze and protect the exact signed Preview 2103451 checkpoint. This is **not** a new build, source change, release signing request, or claim of complete physical Fold acceptance.

## Immutable identity and delivery

- Exact production source signed: `e50e68dad4c50690601bacbe1724507912b70fbd`.
- Signed delivery and independent preservation evidence: commit `b30c9435fd1f5754d89805317573e5d3dd22ba66`.
- APK `Infinity-2103451-Combined-Original-Signer.apk`, package `com.projectinfinity.kodi`, versionCode `2103451`.
- **APK SHA-256:** `d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399`.
- **Original signer certificate SHA-256:** `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- [Original signed APK ZIP artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41568721264/artifacts/13200361701), containing the exact APK.
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41568721264/artifacts/13200925524).
- [Final passing original-signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41568721264).
- [Final passing selected Android test](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41567002286).
- Independent published comparison confirms exactly **7,611 APK payload members unchanged from signed 2103450**, all **47 native libraries unchanged**, complete Cobra component byte-identical, chooser/Splash routing unchanged and unrelated Infinity native/add-ons/skin/shutdown untouched.

## Frozen Infinity Preview functionality

Existing independent external-video route and `Infinity` / `Infinity Preview` labels; own lightweight player process/decoder; external source-return; video-title controls; horizontal scrollable control rail and horizontal seekbar; Play/Pause, Stop, Close/Back, ±10s, Mute and inline volume, audio and text subtitles where supported, Display and rotation, layouts for Fold cover/inner and resizable windows, Light/Dark/System appearance, per-video Resume/Start Over persistence, audio/call focus behavior, request ownership, loading/error/cancel, correct cleanup.

**2103451 new scope:** Fullscreen is present in the horizontally scrollable controls between Display and Auto rotate. It temporarily applies proportional crop to fill the viewing area, hides the app chrome/system bars where supported, and restores the prior Display choice and normal bar policy on exit. Display options include Best Fit, Fill (crop) and optional Stretch, plus Appearance and Done. Preserve all features and functionality, without an independent copy/player/launcher.

## Protected separate owners and next handoff

- **Infinity Preview 2103451 is frozen.** Do not use it as a playground for the next Infinity Kodi changes.
- **Cobra 2103445 is fully protected**. No Cobra/player/UI/behavior modification without new explicit authorization.
- **Infinity Kodi** remains the original Kodi media center, native VideoPlayer, add-ons/providers, skin, Resume Hub, settings and user content. The user's next workstream is **Infinity Kodi**, not Preview and not Cobra. Any proposed change must state its Kodi-only scope, identify exact approved owners and protect the Preview and Cobra compiled payloads, behavior, shutdown, provider data and signing identity.
- Retain signed `2103450` user-approved checkpoint and existing user lock `lock/infinity-cobra-2103450-user-approved-20261102` as recovery. Also keep 2103447 earlier accepted lock and 2103445 original protected recovery. No installation removal or user data reset.
- No need to update any accepted-pointer registry or re-sign/rebuild to create this GitHub lock. Existing packages and locks unchanged.

## Verification limits

The user's instruction approves freezing the **latest available signed state** before switching topics. The independent selected API37.1 emulator tests, original-key signing and all-member comparison passed. The user's device-specific install/playback acceptance for signed **2103451** has not been provided. **Do not invent physical Fold approval** or call it user-run end-to-end QA. Preserve all earlier failed/cancelled runs in the historical record. No shutdown test was run (unchanged code). The upstream release was initially labeled a testing candidate; this freeze makes it a user-directed reference checkpoint, not a retroactive certification of physical QA.

## Lock semantics

Future changes need separate scoped branches, original-signer monotonic install-over versions where APKs are involved, and an explicit new user authorization. Nothing about freezing Preview 2103451 authorizes altering Preview, Cobra, the original Kodi media center or their shared/native owners.
