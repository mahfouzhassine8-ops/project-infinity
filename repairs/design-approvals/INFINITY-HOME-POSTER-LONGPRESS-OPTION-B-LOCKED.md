# INFINITY — USER-APPROVED OPTION B LONG-PRESS DETAILS (EXACT DESIGN LOCK)

**Approval:** YES — user explicitly chose **Option B**: “Yeah im siding wjth that too simple and elagent I want it bite for bite no exception.”  
**Approval type:** **VISUAL + INTERACTION DESIGN ONLY.** This is **not** authorization to change/build an APK or a final APK/skin release lock.  
**Base:** protected signed experimental Infinity APK **2103390**, SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`.  
**Work branch:** `work/infinity-2103390-targeted-bugfixes`.  
**Locked proven shutdown fallback:** APK **2103384**, SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.  
**Protected:** **Cobra NEVER TOUCHED**; existing Infinity Home, skin IDs, active providers, playback, PiP, background sessions, screensaver, Resume/Watched state, Command Center, Add-on Browser, Rails, Essential-First Close, and user data remain unchanged except for specific separately authorized defects.

## Controlling visual references in the user conversation

1. **User's ACTUAL Infinity Home screenshot** (file named `19035.jpg`): current `INFINITY 1.0.5` header, Umbrella Latest Releases top poster strip, middle Infinity navigation, Movie Addons row, Continue Watching row and bottom status strip. **This precise existing Home UI is the background.** Do not replace it with a new dashboard, sidebar, alternate navigation, or a stock Kodi layout.
2. **User-approved marked comparison mock** (`infinity_ui_interaction_options_mockup.png`): **panel 3 — OPTION B / LONG-PRESS POP-UP**, NOT panel 2 Option A. It depicts the existing Infinity Home dimmed behind a compact **centered** details modal.
3. Stock Kodi reference was provided for *type of metadata displayed*, not its typography, menus, theme, screen structure or layout. **No stock Kodi skin transplant.**

**Design priority:** match option B's **structure, placement, shape, visual hierarchy, compactness and controls bite-for-bite** with Infinity's existing palette; use actual title metadata, not the sample/movie values from a mock image.

## Exact approved appearance

- Current Home remains in its **original positions**, unshifted and scroll position preserved.
- Long-press **one poster in the TOP content/release/featured movie or TV show rail** (e.g., Umbrella Latest Releases) to reveal a **single centered, compact, rounded-rectangle glass details pop-up**. Do not create an inline expanding panel, full-width page, or another Home design.
- Soft backdrop dim behind pop-up; selected poster/rail remains visible as visual context. No blurring away the whole page, unnecessary banners or moving tiles.
- Same Infinity cyan/blue restrained rim/glow as the approved B screenshot, same thin border, same dark glass depth for dark theme; avoid heavy neon effects.
- **Poster thumbnail at left**; details on right: prominent title and release year, small metadata chips/tokens (certification, runtime, rating, genres **when available**), concise synopsis/wrapped description. No duplicate movie poster strip in the modal.
- **Close X at top-right.** The B mock's bottom action row is **Play**, **Trailer**, **Add to Favorites/Favorite**, **More Info**, in that order; preserve icon/label sizing and restrained cyan-filled primary Play emphasis. Do not insert unrelated actions. Only display or enable a secondary action when its real backing capability exists. Play always retains the existing intended provider route/chooser.
- Text/layout adapt to true information length rather than crop necessary content; responsive compact safe-area measurements on Galaxy Fold cover/inner, portrait/landscape and rotation. Where the screen is too narrow, compact/reflow these *same* elements without changing feature semantics; touch targets must remain large and correctly mapped.
- **TV shows get the SAME exact Option B modal**. Use **real** show/episode metadata: show title, validated season/episode and episode title when available, show or episode plot, rating/runtime/certification if supplied. Play may say **Play S2 E3** when episode identity is verified; do not hardcode episode numbers or infer incorrect show IDs.

## Exact approved interaction

1. **Normal single tap:** leave current Home poster behavior unchanged; opens current original title/provider path. No new mandatory double tap, preselection or autoplay.
2. **Press-and-hold on that poster:** open Option B modal, **without also activating playback or navigating**. Only after identity validation for the actual selected poster; never borrow a neighboring focused item or background tile.
3. **Touch action buttons:** one reliable tap activates that button alone; focus/highlight never triggers an action on its own; cancel does nothing. Play uses original explicit click route; Trailer uses existing supported trailer path; Favorite uses original Kodi Favorite mechanisms; More Info launches existing supported full information view. Do not invent provider stream URLs or new databases.
4. **Close:** X, system Back, or appropriate outside dismiss returns to **the same Home window, category, selected poster and horizontal rail offset**. Do not open a retired screen, duplicate context menu or change play state.
5. **No accidental double-dispatch:** long-press must not send a subsequent short-tap/open event; avoid global touch or Cobra input changes. No overlay leaking to multiple panes. One modal maximum, safely closed across fold/unfold/rotation.
6. **Missing metadata:** present only reliable fields, use existing title/art if available, omit unsupported actions, never label a guess as verified. Info browsing must not start scraping, source selection, playback or background network metadata fetches solely due to focus.
7. **Smooth short animation**: approximately 150–200 ms subtle opacity fade and small scale (roughly 96% → 100%) with gentle cyan border/focus settling; reverse on close. No heavy bounce or full-screen transition. Follow Infinity's existing motion/reduced-motion/off preferences; instant/near-instant for reduced/off modes; never block GUI, touch or native playback waiting for an animation.
8. **Theme parity:** Light = Infinity pearl/glass and dark legible labels; Dark = established navy/charcoal glass; OLED = true black/high contrast minimal glow; Night Cinema = existing warm amber emphasis where applicable, without recoloring videos. Use existing theme tokens and focus control. Match current skin's backgrounds, typography, rounded corners, icon pack and modal layering; **no independent theme framework**.

## Specifically NOT approved

- **Option A** inline panel, inserting extra rows/shifting Home sections, a stock Kodi skin replica, permanent full-page details dashboard, editing the existing layout globally, converting normal tap to select-then-tap-again, scrolling nav strip changes, new source scrapers, native playback mutations, guessed metadata, new data stores, or blanket add-on/provider edits.
- General skin polish, cleanup outside this exact Home top-rail scope, any Cobra changes, any shutdown changes, source/watched state reset, install/uninstall/data wipe or extra APK packaging are NOT authorized by this design choice.

## Acceptance and fidelity gates (future implementation only)

- Compare **screenshots from the actual Fold** (cover/inner, rotation, Light/Dark/OLED/Night Cinema where present) against the **approved B mock displayed over the original 19035 Home**. A functional menu with a different layout is a **fail**.
- Repeat movie AND TV show cases; test long-press vs short tap, selected identity, title/episode and poster mapping, correct title metadata, optional Trailer/Favorite/More Info, close/Back focus+offset, source route unchanged, and no provider side effects.
- Verify original #1–6/#9/#10/#12 functionality, Home rails, Resume Hub Continue Watching, touch responsiveness, background playback, PiP, Essential-First Close/reopen and crash recorder. Cobra unchanged.
- Do not mark implemented, Android-pass, Fold-pass or final locked without real evidence and user approval.
- Any future requested visual adjustment is a separate explicit user approval; **no unrequested redesign or substitutions**.

**Current status: DESIGN APPROVED AND RECORDED. IMPLEMENTATION/BUILD: NOT STARTED BY THIS DOCUMENT.**
