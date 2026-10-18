# Infinity — Resume full feature restoration on locked 2103384

**Authorization:** user approves `2103384` as the new, user-locked **APK shutdown baseline**. This document is a preservation/continuation handoff only. **Do not implement, package, install, or lock any new feature candidate without separate feature authorization.**

## Pinned sources and binary

- **Locked reference branch:** `locked-infinity-apk-2103384-user-passed-20261017`, initial lock-manifest commit `5389b4572cd32037fedf0e7d88b7f79abb120952`.
- **Locked artifact:** `Infinity-2103384-Optional-VFS-Shutdown-TEST1.apk` (SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`).
- **Native engine:** unchanged engine family, in-APK `libkodi.so` SHA-256 `f47c6f3473a45438a533ecfa57dd196bac6d794227b16c4fb7888636e8f4408d`.
- **Package and signer:** `com.projectinfinity.kodi`, original permanent signing certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- **Full lock certificate:** `repairs/locked-baselines/INFINITY-2103384-SHUTDOWN-LOCK.json` on locked branch.
- **Reusable backup:** user's private ChatGPT Library `/Infinity/Locked Baselines/Infinity-2103384-Optional-VFS-Shutdown-TEST1.apk`. The private Fold diagnostic ZIP is NOT to be uploaded to public GitHub.
- **Native build source:** `3795b1b03731cba567e091913299c1888805373c`; **actual signed APK Android** test run `39091870631` green in fresh and loaded/upgrade cases.
- **Real Fold:** the approved shutdown receipt reports `COMPLETE`, 6627 ms, 16 essential save owners, no essential write blockers, data sealed/durable, engine death. No full UID death proof. User explicitly accepted and requested lock.
- **Skin distinction:** installed `skin.infinity.diggz` 1.0.5.225 was observed in diagnostics; 1.0.5.223 is still the previous locked skin. **Locking APK 2103384 does not automatically lock skin 1.0.5.225.** Preserve user's currently installed skin and data; do not revert it.

## Continue all five approved workstreams — do not shrink the scope

1. **Native stability/player continuity:** Preserve corrected OnJobComplete Graphics/Directory lock cycle, background return, screensaver dismissal, foreground restoration, session continuity, PiP, background playback, player functionality. Do not touch locked shutdown code as a side effect.
2. **Watched / Resume Hub / Watchlist:** Universal blue watched checks, explicit Mark Watched/Unwatched, accurate Continue Playing, optional Trakt, movie/episode identity, Collection/Watchlist across compatible add-ons, intact Command Center progress/DB.
3. **Add-on touch, long-press, recovery:** Fix black narrow context-menu panel / Rails Options activation, Movie and TV rail gestures, consistent long-press everywhere, disabled-add-on recovery, Otaku reenable **without** clearing add-on data.
4. **Comprehensive skin/UI/player polish:** Continue Phase D across Home, dialogs, add-on browsers, Rails, Resume Hub, Health Center, Command Center, Settings, Light/Dark/OLED/Ambient, Fold layouts, smooth transitions. Restore the previously requested **Rotate OSD button** without replacing it with Repeat. Preserve working Cobra, sports, Mini-Player, playback controls, native engine, and installed Diggz ecosystem; no blanket redesign.
5. **Essential-First shutdown / save state:** **Now frozen as 2103384 user-approved reference**. Keep its exact verified writer-path classification, protected file fsync, 16 essential-owner proof, 25-second deadline safeguards, no optional addon completion dependency, permanent signer, and refusal to certify risky writes. Treat startup/early-close remaining edge cases and full app package death proof as future targeted work that requires explicit approval, not silent rewrites.

## Mandatory promotion gates for every new feature candidate

- The new **feature work** must begin at this locked reference; never reset to 2103377/2103382/2103383 or stock Kodi.
- Every push runs `.github/workflows/infinity-2103384-locked-feature-guard.yml`. It asserts the user-locked JSON receipt is unchanged, verifies protected native baseline files, and executes real C++ file-writing regression tests. A red host guard BLOCKS promotion.
- Build a complete native engine only if a feature truly requires it. If only skin/helper files changed, avoid recompiling the native engine. **Never install multiple Infinity packages** or demand clean installs.
- Require a **new, permanently signed actual Infinity APK** with the exact same package ID and signer, `versionCode > 2103384`, and a verified `libkodi.so` lineage from this locked reference.
- Run **the new exact signed APK** on a disposable Android emulator in **fresh and loaded/upgrade** modes. Require actual `COMPLETE`, checkpoint saved, authorization consumed, sealed/durable essential writes with ZERO blockers, engine/package death receipts, reopening, and existing test data intact. Green compilation or host tests are NOT Android approval. Neither Android result alone constitutes Fold approval.
- Test real Fold with **normal Close**, immediately after startup and after add-ons have loaded, during realistic background-service activity, and after background/screensaver return. Confirm Resume Hub, watched/favourites/settings/Command Center DB, PiP/player and skin survive reopening. Capture Health Center diagnostics without putting private data in the repository.
- **User's explicit approval** is required before changing the locked base. Any feature candidate that regresses Close is rejected; locked APK remains untouched and usable. **Never clear app data or uninstall** as a workaround.
- An exact replay of The Crew's previous `vfs_write_exception` was NOT observed in the Fold success. Keep that case as an open fault-injection/real-device verification item; do not claim universally eliminated failure modes.

## Work boundary

This separate development branch is a staging area for future restoration only. The locked branch and locked APK must remain unchanged. The preexisting five-workstream project stays alive, and restored features must be additive to the approved native shutdown foundation.
