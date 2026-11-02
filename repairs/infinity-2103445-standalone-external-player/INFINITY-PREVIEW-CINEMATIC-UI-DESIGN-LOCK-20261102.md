# Infinity Preview — user-approved cinematic UI design lock
**Approval date:** 2026-11-02  
**Status:** Approved visual mockup / design-only lock. **Not implemented, built, signed or physically tested.**  
**Protected executable baseline:** signed combined Infinity/Cobra **2103447**, original user lock \`lock/infinity-cobra-2103447-user-locked-20261102\`.  
**Signed 2103447 APK SHA-256:** \`e94adcbefaee9cd42d25097f779fc28da80bb0cc90b43681a7fe36b12d5cf30e\`.  
**Original signing certificate SHA-256:** \`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7\`.

## Exact approved intent

User reviewed the generated cinematic Infinity Preview video-player mockup based on their real running 2103447 screenshot (\`sample-500mb.mp4\` test-pattern video) and said **"Okay, lock it. But I still want to keep the functionality that the or the horizontal scroll. So everything is preserved."**

**Interpretation to implement literally:** Approve the cinematic **appearance**, NOT a simplification that deletes, hides permanently, or changes existing player functionality. The **horizontally swipeable control strip** remains an essential feature. The **horizontal timeline seek/scrub** remains functional. All original controls remain reachable. Do not misunderstand the image's neat single-row arrangement as a reason to remove horizontally scrolling controls or the off-screen rotation function.

This is a **design-approval checkpoint**, not authorization to overwrite the locked 2103447 binary, approve a newer APK, change playback semantics, or claim this UI already exists in a release.

## Visual reference and design requirements

The approved reference is the image-generation mockup shown in the same user conversation immediately before this lock request (cinematic dark video player with elegant top bar, media centered, near-black environment, subtle cyan highlights, bottom timeline, translucent rounded controls). The test pattern visible in the image is **the video being played**; never add that pattern or decorative video content to the application UI.

1. **Video-first / unobstructed picture:** Maintain correct video aspect ratio and existing Best Fit/Fill semantics, true black letterbox space if necessary. Use a simple refined deep-dark background; subtle cyan accent, not glowing outlines around every button. Never obscure video with permanently oversized panels.
2. **Top header:** Compact translucent charcoal surface; clearly accessible Close/Back; readable filename/title; discreet Infinity Preview brand. Preserve the present Close behavior, accessible when needed. Do not rename the application or external handler labels: launcher/app remains **Infinity**, scoped video handler **Infinity Preview**.
3. **Timeline:** Readable elapsed and total times, accurate horizontal SeekBar with smooth touch drag, existing seek events and position synchronization, adequate thumb size and safe insets. Existing horizontal seek/scrub MUST NOT be removed.
4. **Bottom toolbar:** Modern translucent rounded control rail; lightweight clear icons and optional short labels, appropriate tap targets and accessible descriptions. Show Play/Pause and essential transport controls prominently, while every other original function remains present and reachable.
5. **MANDATORY original horizontal scrolling:** Preserve an actual horizontally swipeable control strip (current implementation uses \`HorizontalScrollView\` for the bottom button rail). The user MUST be able to swipe left/right to reveal any controls that do not fit, especially on the folded narrow screen, smaller Android windows and in landscape. Do not replace the strip with a truncated fixed row, invisible overflow, disabled scrolling or a modal menu that drops controls. If responsive widths fit all actions, still preserve correct overflow behavior whenever needed. Keep gesture separation: swiping toolbar scrolls toolbar, dragging timeline seeks, tapping video toggles controls; no gesture may accidentally close playback or steal another control.
6. **Preserve **ALL** currently implemented player actions and semantics:** Play/Pause, Stop, Back/Close return to originating app, -10 seconds, +10 seconds, Mute/Unmute, volume slider, audio-track selection, timed-text subtitles where supported, Display Best Fit/Fill, Auto rotate / rotation controls, timeline seek, loading/error/retry, natural end/replay, title/time updates, foreground/background position handling, audio focus, media-source access, request replacement and session cleanup. No regression in protected existing features, even if the mockup does not show every button at once. **Do not alter any playback engine method/logic as part of a skin-only redesign** unless separately proven necessary and explicitly scoped.
7. **Control appearance/disclosure:** Reveal controls on a video tap. Refined timed fade/auto-hide during uninterrupted playback is permitted to match the approved mockup, but tap/keyboard/accessible focus must reliably bring the controls back; controls stay accessible when paused or interacting with seek/menus. Never let fade animation interrupt a swipe, seek gesture, dialog or audio/subtitle selection. Preserve existing Back/Close action semantics.
8. **Galaxy Fold layouts:** Design for folded outer display, unfolded inner display, different orientations and resizable/split-screen windows. Buttons do not overlap with Android navigation, hinge/cutouts or subtitles. Fonts readable, proper contrast and tactile ≥48dp controls, not tiny desktop-style hit areas. No changes to video scaling behavior beyond approved visual layout.
9. **Color and style:** Dark charcoal/black player with restrained cyan emphasis (e.g. active Play/Pause and seek progress), white readable text, softened radius and understated panel blur/transparency where supported. Full-width cinematic video should remain the focus, not decorative animations.

## Explicit preservation and source boundary

**The 2103447 executable remains locked exactly as it is.** All functional, navigation, Android external-video-handling, labels, permissions, engine, request ownership, and release behavior is protected. Cobra 2103445, the original Infinity Kodi / native VideoPlayer, all 47 native libraries, full Kodi profile/add-ons/skin/providers, Infinity/Cobra UI not inside this external player, Choose Your Experience, normal launcher, experience persistence, original signer, settings/data and shutdown are **100% off limits**.

A future implementation from this design checkpoint may **change only the new Infinity Preview player's appearance/layout code** (e.g. \`repairs/infinity-2103445-standalone-external-player/runtime/InfinityExternalPlayerActivity.java\` view construction, and tightly scoped new player-only presentation resources if necessary) while preserving player behavior and horizontal scrolling. Any behavioral/engine changes or protected components require separate explicit authorization. Work from original locked 2103447; never restart from rejected 2103446. If an interface change cannot preserve an existing behavior, do not implement that change.

## Implementation acceptance gates for Astra (future targeted UI work)

- Compare and document current 2103447 controls, their commands, orientation and keyboard/touch/scroll behavior *before* edits, then demonstrate **the same action matrix after the new layout**. Source confirms current \`InfinityExternalPlayerActivity.java\` has a \`HorizontalScrollView\` containing Play/Pause, Stop, -10s, +10s, Mute, Volume, Audio, Subtitles, Display, and Auto rotate, with a separate \`SeekBar\` for time scrubbing. Their order/availability can be visually arranged but functionality and horizontal scroll must remain.
- Test long clips and rapid seeks, swiping the **bottom control rail** to its far end to access every button, and separately scrubbing the **seek timeline**, both directions; check control reveal and focus.
- Test front, inner, landscape, short windows, rotation and multitasking with controls safely reachable. Verify Stop/Close and Back return to source; no Kodi process starts for external video; already-running Kodi/Cobra sessions remain unaffected.
- No unselected Kotlin/Java feature rewrites, no Cobra/native/shared changes. Compare exact signed 2103447 with the eventual signed next-version test build, enumerating any changed members. Original certificate, higher install-over versionCode, no uninstall/clear data.
- Only user physical Fold acceptance of the eventual UI APK may promote its functional release status. The approval **here is of the visual mockup plus preservation contract only**. Preserve separately the existing signed 2103447 test artifact and its lock.

## Lock semantics

This record formally freezes **the approved Infinity Preview cinematic UI design and all current capabilities, especially horizontal scrolling and seeking**, for later strictly scoped implementation. No runtime code, signed APK, compiled component, user data or existing acceptance lock was changed by recording this design.
