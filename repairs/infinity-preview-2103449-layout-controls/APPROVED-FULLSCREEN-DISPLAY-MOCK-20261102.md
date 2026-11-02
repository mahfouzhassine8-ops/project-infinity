# Infinity Preview — Approved Fullscreen button and Display dialog mockup

**User approval:** "Perfect" on 2026-11-02 after the user requested: "Lock it but there's no fullscreen option. I do like the setup though and functionality. Also display needs some touching up can you mock it."

**Status:** VISUAL DESIGN APPROVED / FROZEN. **Not yet implemented or released** in signed 2103450. **Do not change the signed 2103450 baseline by creating this document.**

## Protected base

- Functional checkpoint: `lock/infinity-cobra-2103450-user-approved-20261102`.
- Exactly signed APK: `Infinity-2103450-Combined-Original-Signer.apk`, SHA-256 `01cb1b35ded45ca4124a1e0feed5029554fee51ca0f14c1b3d72bf9e50460161`.
- Original signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Preserve signed Preview 2103450 playback functionality/experience, signed 448/449 and earlier 447 recovery, original Infinity Kodi and Cobra 2103445 unchanged.

## Exactly approved visual reference

The image mockup shown to the user immediately before "Perfect" uses their real Infinity Preview vertical player screenshot as visual reference. It shows:
- Near-black **cinematic dark theme** with restrained cyan trim and a softly translucent, centered, rounded Display panel over the video.
- An elegant header with small Display icon and title.
- A selected **Best Fit** row with turquoise radio indicator, line icon, short help text: "Show the entire video with no cropping."
- An alternative **Fill (crop)** row, with an understandable icon and description: "Fill the screen and crop the excess edges."
- An alternative **Stretch** row, with icon and an explicit warning: "Fill the screen without cropping (may change aspect ratio)." Stretch is intentionally a new, opt-in mode; avoid distortion unless the user selects it.
- Footer **Appearance** entry (honoring existing Light/Dark mode and System setting) and a prominent **Done** control to dismiss the panel.
- On the existing horizontally scrollable player toolbar, a compact labeled **Fullscreen** icon/button between **Display** and **Auto rotate**, maintaining existing rotation behavior and the entire scrolling strip. The mockup's portrait sample media is background content; never package it as UI artwork.

**Light-mode companion:** Same layout, readable descriptions, controls and selection state, with pale/neutral light surfaces and contrasting dark text and cyan accents. Do not use dark-only text/icon colors or change video pixels or playback merely to switch theme.

## Exact feature behavior, strictly limited

1. **Fullscreen must be a real, reversible function** and must not be mistaken for Fill (crop): toggle an Android immersive full-player display / maximum available video viewport, hiding external player chrome/system bars as platform APIs permit; reveal on tap and allow leaving fullscreen without changing the media being played, timeline, audio tracks or saved per-video progress. Keep aspect ratio from whichever Best Fit/Fill/Stretch mode is selected, independently of fullscreen. Ensure the existing Close/Back/source-return remains reachable. While fullscreen is active, Back may first leave immersive mode; after exiting fullscreen normal Back retains its established source-return semantics.
2. **Keep the full horizontal scroll behavior:** The toolbar must still swipe left/right, especially on Fold cover screen, and all functions remain accessible at the end of the rail. No invisible or unreachable button, no clipped Fullscreen label, no broken seeking/scrubbing. Do not replace the horizontal rail with a static row or a separate always-visible control panel.
3. **Preserve existing Best Fit and Fill behavior** exactly. Best Fit is default, never stretches. Fill crops only when explicitly selected. Add Stretch only as the extra choice visualized in the approved mock and only with the explicit distortion explanation; restore the original mode on reopening as appropriate without touching per-video resume identity or request ownership. If Android rendering makes Stretch technically unsafe, document exact blocker rather than silently changing Best Fit or Fill.
4. **Improve Display dialog appearance only** without changing unrelated dialogs, system components, global font/theme or playback engine. Show clearly selected state and readable help text, and ensure Appearance works with existing System/Light/Dark choices without a second theme store or conflicting control.
5. **Preserve everything else**: Play/Pause, Stop, Close, -10/+10s, mute, inline volume, Audio, Subtitles, Display fit/fill, rotation Auto/Locked, horizontal scroll, timeline seek, video scaling, resize/fold behavior, rapid video replacements, file permissions, URL/content sources, resume-memory prompt and persistent per-video positions, audio focus/call handling, and returning to originating apps. Do not change Kodi's native VideoPlayer or Cobra.
6. **No unnecessary Kodi startup or separate Android app:** same existing Infinity → Infinity Preview external-video entry; internal player remains isolated. No duplicate launcher/handler, new background worker/service, storage migration or process lifecycle change.
7. **Only targeted UI work** may touch Infinity Preview's own layout/menu/controller with documented controls and the minimum state required for fullscreen and optional Stretch. All other classes/resources/binaries/components are byte-preserved. Do not alter shared native libraries, shutdown, skins, add-ons, Kodi, Cobra, global chooser, or signing policy.

## Selected tests before any signed successor can be accepted

- Run real Android video with app-provided local/content URI; check toggling fullscreen repeatedly while playing, paused, in Light and Dark, with notifications/navigation bars, back gesture, Close and external-app return. Check fullscreen doesn't alter audio, subtitles, playback position or seek action.
- Check fullscreen and Display controls in Fold cover/inner, portrait, landscape, short/resize windows and during fold/unfold, with no overlapping or clipped controls. Verify exact horizontal strip movement and all prior buttons remain reachable.
- Check Best Fit vs Fill vs Stretch on wide, square and portrait media. Show the correct selection, preserve aspect ratio in Best Fit, expected crop in Fill, expected optional distortion only in Stretch. Fullscreen is a separate toggle, not an alias of Fill.
- Display menu theme switch during playback preserves decoder and state; all menu text readable in both variants and Appearance remains accessible. All existing Resume/Start Over and rotation/volume/seek tests remain passing.
- Compare compiled signed successor against **locked signed 2103450**, enumerate every intentional changed method and member, attest to unchanged protected components, and use original-key install-over signature with versionCode above 2103450. The user must physically test and explicitly accept before locking the successor.

## Lock semantics

This document captures **the approved mockup design** and the user's intent to add **Fullscreen** and visually refine **Display**, while treating all signed 2103450 functionality and layout as the preserved baseline. The user has not approved source changes outside this limited feature. No claim that Fullscreen or Stretch exists in signed 2103450. Do not promote or lock a new APK automatically.
