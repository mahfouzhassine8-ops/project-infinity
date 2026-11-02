# Infinity Preview 2103450 — User-approved frozen functional checkpoint
**Date:** 2026-11-02  
**Authorization:** User explicitly said “Lock it” after testing the newly signed player on their Samsung Galaxy Fold, stating “I do like the setup though and functionality.” The user then approved the subsequent fullscreen+Display mockup with “Perfect.”

## Frozen signed binary and source

- APK name: `Infinity-2103450-Combined-Original-Signer.apk`.
- APK SHA-256: `01cb1b35ded45ca4124a1e0feed5029554fee51ca0f14c1b3d72bf9e50460161`.
- Package: `com.projectinfinity.kodi`; versionCode **2103450**.
- Original signer certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Original-key signed source: `f372d25e5e3b23634895ef2e9c9ed60e5246d123`.
- Delivery and independent published-byte evidence: `bfbce5de925caede200573a74388480323d76597`, `repairs/infinity-preview-2103449-layout-controls/DELIVERY.md`.
- Signed GitHub artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41541654995/artifacts/13186062986
- Exact matching component ZIPs: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41541654995/artifacts/13185429405
- Android layout test: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41539406515

## What is approved and preserved

**Freeze the exact signed 2103450 player and all approved Infinity/Cobra experiences.** User positively evaluated the existing 2103450 playback layout and functionality on the physical Fold and wants them preserved. This includes independent Splash-to-Infinity Preview external video routing, playback engine, resume memory, seeking (timeline and ±10s), horizontally swipeable control bar, mute and inline volume, Audio, Subtitles, Display Best Fit/Fill, rotation Auto/Locked, Close/Back/source return, responsive sizing, cinematic light/dark appearance and all accepted navigation.

Protect **Cobra** 2103445, its view modes and controls; full Infinity Kodi and its native VideoPlayer; Kodi native libraries, skins/add-ons/providers, search/tracking/Resume Hub; Choose Your Experience and Splash normal launcher, Android external-app handler identity `Infinity` / `Infinity Preview`; original signer, settings and profile data, permissions, shutdown and unrelated shared components. Do not make any runtime/source/build change to lock this baseline.

Signed 2103450 vs 2103449 published comparison: **7,611 unchanged payload members** including all 47 native libraries, Cobra/shared components, Splash routing and shutdown; modified production sources limited to `InfinityExternalPlayerActivity.java` and `InfinityPreviewChrome.java` selected presentation methods. The existing user-locked 2103447 and signed 2103448/2103449 recovery artifacts are retained, not overwritten.

## Explicit unresolved visual requirement (a *future* scoped change)

User reported **there is no Fullscreen button** and requested a cleaner **Display** dialog. Their later “Perfect” approves the separately captured **Fullscreen + redesigned Display** *mockup*, not a claim these additions already exist in signed 2103450.

The approved future design and implementation requirements must be recorded on a separate design-only branch/document; do not silently modify signed 2103450 or claim Fullscreen is in this APK. Any future implementation branches from this lock and produces a new original-key-signed install-over testing APK with higher versionCode, no uninstall/clear data, and strict unrelated-byte preservation.

## Acceptance truth

User explicitly locked the 2103450 **functional checkpoint** and expressed approval of its current layout and functionality. This is a user-directed freeze, **not** evidence that every physical device, Google Drive, codec, carrier-call, or regression scenario has been executed. CI/host/API37 selected checks passed, and the user supplied a photo of the real device displaying the player/Display dialog. Do not rewrite historical delivery evidence or invent a complete physical acceptance checklist.
