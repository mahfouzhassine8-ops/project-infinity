# INFINITY PLAYER — THREE MATCHING TRANSLUCENT GLASS POPUPS (DESIGN PROPOSAL)

**State: VISUAL MOCK FOR USER REVIEW, NOT USER-APPROVED EXACT DESIGN, NOT CODE IMPLEMENTED.**

**Source of truth: user's real Infinity player screenshot `1792386488186.jpeg`, playing `Sacrifice`.** Original player shows:
- existing top Sacrifice title/runtime/chapter bar,
- a single centered `Playback` popup with exact original labels,
- progress/seekbar beneath,
- original bottom video OSD controls with the empty video/monitor button and subtitle-related controls.

**User's words (verbatim):**
> "Also, for the video icon and the subtitle icon, they should be glass to where the video still can be seen through them to a sense. So if you want to mock that so we can approve it, we can do that."
> "I'm referring to the menu, that is."
> "If anything, playback menu should follow the same."

## WHAT TO MOCK — NOT WHAT TO REBUILD

The user wants **three menu BACKGROUNDS**, NOT the icons, to appear as **translucent Infinity glass**, so the playing film can be **partially seen THROUGH the pop-up surface**. The three panels must visually match in existing Infinity Light/Dark/OLED/Night Cinema themes, restrained cyan/amber accent, readable text, glass rim and rounded corners, and respect reduced motion/Off. Actual video pixels must never be recolored or post-processed by the menu.

1. **Playback popup**: keep same real existing `Playback` modal and every option in its real previous order, *except* the separately requested removal of only `Video Settings` because dedicated OSD video icon opens it. Preserve `Now Playing`, `Audio & Subtitles`, `Chapters & Bookmarks`, `Playlist`, `Go To Time`, `Player Settings`, `Playback Info`, `Close Player` verbatim. Never invent Play/Pause, Repeat, A-B Repeat or settings not in the user screenshot. Make the surface translucent glass, with actual film visibly muted beneath. The original playback controls/seekbar stay in place.
2. **Video Settings popup**: triggered by the user's existing monitor/video OSD button (#11), slightly smaller than Playback, separate centered glass dialog not full screen, same material and movie-visible translucency; all REAL Kodi/Infinity video options/labels/values must be preserved as they actually exist, not replaced with sample concepts.
3. **Audio & Subtitles popup**: triggered by existing Playback → Audio & Subtitles, slightly smaller than Playback, same movie-visible translucent glass, preserving real track selections, subtitle on/off, delays and audio behavior. No full-screen takeover or reformat of unrelated dialogs.

**Visibility priorities:** background film discernible but softened; text remains readable in bright/dark video scenes. Prefer a translucent dark navy/black glass plate over harsh full-screen dim; subtle blur only within panel if native/skin rendering supports it efficiently; preserve video session, OSD and performance. On OLED, preserve true-black aesthetic outside panel while allowing limited translucent film pixels under the panel. Honor Night Cinema warm amber selection styling, not colorizing video.

**Interactivity:** reliable large touch targets; compact panel within physical Fold cover/inner safe areas, portrait/landscape, no overlap with progress slider/bottom nav; close restores playback/focus; no pause, stop, seek, recalculation or restart caused by opening settings. Internal scrolling only if needed. Same animations/motion restrictions as existing Infinity.

## IMAGE FIDELITY WARNING / USER APPROVAL GATE

Automated demonstration images were generated while discussing this; some show **John Wick** and **invented Playback menu options** rather than the user's exact `Sacrifice` player screenshot. **These are only conceptual glass-material references. They are NOT approved layout or item inventories. Do not treat these sample movie/OSD/button texts as implementation requirements, and do not replace the actual player screenshot/UI with invented layouts.**

**Before writing real code for #11–14, ask the user to visually accept an accurate mock over the actual Sacrifice player UI, confirm exact opacity/size and real menu labels/positions, then implement ONLY the named task by number.** Treat hereto requested translucent material as desired behavior but the visual execution as PENDING approval. No invented product UI, no full-screen screen redesign.

**Preservation:** signed 2103390 provisional baseline + 2103384 shutdown fallback unchanged; no Cobra modifications whatsoever. No new work on #19 caching except independent user authorization. No code/skins/APK/user data modified by this design note.
