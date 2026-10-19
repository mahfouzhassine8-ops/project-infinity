# SEVEN-GROUP PROJECT — CONTROL NOTICE (READ BEFORE HISTORICAL TASK 01–19 DETAIL)

**CANONICAL USER WORK UNIT IS NOW GROUP #1–#7**, documented in `repairs/2103390-bugfixes/GROUPED-01-07-BINDING-CONTRACT.md`. The original 01–19 numbers below remain unchanged as fine-grained acceptance subrequirements, not standalone work-order numbers. The old Lyrics repair task 16 is SKIPPED_BY_USER. The NEW **GROUP #6 is Silent Mode inside Infinity's System Hub**; do NOT confuse it with original task 06 (Add-on Browser root), which belongs to Group #2. Group approval does not mean implementation has started.

The user approved the three translucent Playback / Video Settings / Audio & Subtitles menu materials “Prefect bite to bite.” Exact approved design is `repairs/2103390-bugfixes/PLAYER-GLASS-MENUS-APPROVED-20261019.md`, superseding earlier glass visual “approval pending” language below. All real existing player labels, controls, theme tokens, codecs and playback video remain protected. The approved grouped scope and original 01–19 subrequirement contracts must BOTH pass their distinct acceptance checks.

The authoritative actual progress, skipped items, source commits, tests and physical Fold results live ONLY in `repairs/2103390-bugfixes/TASK-STATUS.json` and `repairs/2103390-bugfixes/CONTINUE-HERE.md`. Save both after every green milestone, item and group. **Cobra is never touched.** Original signed 2103390 provisional base and locked 2103384 shutdown remain preserved. No new code implemented from this documentation note.

---

# INFINITY 2103390 — EXACT NEW BUG-FIX CONTRACT (TASKS 01–19)

**THIS FILE IS THE AUTHORITATIVE CONTROLLING CONTRACT FOR THE NEW POST-2103390 WORK (01–19).** It is NOT the historical #1–16 repair list, which is already included in the signed 2103390 experiment. The numbering here is separate. The user will authorize/advance tasks by exact number, one at a time, followed by a single reviewed integration. Never conflate these task numbers with historical repairs.

**User's controlling directives (verbatim):**

> "Okay, well, with that being said, give me a one through whatever so we can start working on each one individually and then combined. Obviously with the preservation of whatever is not to be touched and only touched whatever is approved. And I want it word for word, so when you do it, there is absolutely no fucking mistake. Cobra is not to be touched at all. No reason to touch it."

> "Make sure every time you complete each task, you save it. So if this chat ends and I need to start a new one, the new one knows what we're talking about."

**User's newly approved playback behavior (verbatim):**

> "The video looking think on the menu is empty, that button should toggle video setting and that also should be removed from playback settings. Aslo subtitles and video settings should have a similar pop-up like playback they should not cover the whole screen if anything maybe a little smaller than that"

**Additional user requirement for task 19 (verbatim):**

> "If you look at the video, how we can go from movies to TV shows, and it would be as if, like, they would have to reload going from movies and TV shows. It should not be that way because as soon as I start up Kodi, or I mean Infinity, and everything populates, everything should be there at all times. Unless, obviously, I shut down Infinity and it comes back, and I turn it back on and it reloads, which is fine, but that should not happen."

**Additional user requirement for tasks 12–14, menus (NOT toolbar icons), verbatim:**

> "Also, for the video icon and the subtitle icon, they should be glass to where the video still can be seen through them to a sense. So if you want to mock that so we can approve it, we can do that."

> "I'm referring to the menu, that is."

> "If anything, playback menu should follow the same."

**Meaning:** *Playback*, *Video Settings*, and *Audio & Subtitles* pop-up **surfaces** must inherit the same translucent Infinity liquid-glass material so the moving video remains partially perceptible behind them. The user did **not** request transparent player toolbar/icons or recoloring video. The exact design opacity, material treatment, geometry and layout are to be shown in a mock for visual approval BEFORE skin implementation. Until specifically approved, a generated mock is a **proposal**, not a locked design; all original menu actions, labels, tracks and player state must be retained.


## A. Base and unconditional preservation — applies to EVERY task

- Repository: `mahfouzhassine8-ops/project-infinity`.
- Working development branch: `work/infinity-2103390-targeted-bugfixes`.
- **Keep original signed combined APK 2103390 immutable**: `Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk`, SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`. It is the user-designated *provisional development baseline*, NOT a final release lock.
- **Keep locked verified shutdown fallback 2103384 immutable**: SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.
- Android package ID `com.projectinfinity.kodi`, permanent signing certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`, user-installed Diggz + `skin.infinity.diggz`, data, providers and profiles are preserved.
- **ABSOLUTE COBRA FREEZE. NO COBRA WORK AT ALL, UNDER ANY CIRCUMSTANCE IN THIS PROJECT.** Do not open Cobra as a new repair scope; do not edit, remove, rebuild/reimplement, cosmetically polish, relabel, refactor, reroute or reconfigure Cobra-owned features, layouts, resources, player behavior, Sports, PiP, Multi-View, services, or data. Do not alter shared infrastructure in a way that affects Cobra. If any task *requires* a Cobra-owned or Cobra-affecting change, **STOP and obtain an entirely separate explicit user decision**; do not silently expand scope. Passive tests proving preservation are permitted, but zero Cobra modification.
- Preserve **all Infinity functionality not expressly named in the current task**: playback/native engine, video decoder, audio/subtitles/timeshift, player and OSD controls, Home navigation, all rails, skin/theme identity, menu actions, PiP, background playback, screensaver/foreground return, matched providers, PVR, Add-ons, watched/checkmarks, Resume Hub, Watchlist, Collection, favorites, Command Center, Health Center, diagnostic export, saved state, Essential-First Close and protected-write barriers.
- In particular, original **working Essential-First Close** and 16 essential durable owners must not be rewritten. Original `libinfinitycrash.so` and Android exit diagnostics must remain available. Embedded `service.infinity.compat` 0.7.2 stays exactly as in 2103384/2103390 including original **unregistered** status; do not stage/activate 0.8.2. Version Check service remains unchanged; no renewed repair #7/8/11 from previous list.
- No uninstall, no app-data clear, no fresh-start workaround, no provider/watched database reset, no deletion of add-ons, no changed skin/add-on IDs, no unrelated feature work, no silent fallback/reversion.
- Use **existing Infinity Light/Dark/OLED/Night Cinema** colors, Glass effect, themes, responsive safe areas, motion/reduced-motion/off policies. Do not introduce a second theme or rewrite the approved current Home.
- A screenshot, mocked host test or green CI build is NOT a real physical Fold fix. Distinguish evidence review, implementation, host test, Android simulator, physical Fold and user acceptance.

## B. Exact individually tracked tasks (NEW LIST ONLY)

### 01 — TV Shows → Continue Watching: unavailable-source popup

**Observed:** On TV Shows Home → **Continue Watching** poster, some episodes show Infinity Resume Hub message: `This source is unavailable or has expired. Open the title in your provider to resolve a fresh source. Resume Hub kept your local state.` Movies consistently work for user; video shows at least one TV episode can play. Do NOT relabel this as the separate "Continue Playing" menu.

**Required correction:** Trace original Command Center's `_target()` lookup and saved `show_tmdb` verification, typed episode identity, season/episode numbers and provider route freshness. Restore normal per-episode Resume/Play from the existing TV Continue Watching rail when a **verified** source resolver exists. If an episode genuinely cannot resolve, keep a safe, specific non-destructive message; never invent a show ID, episode or stream link.

**Scope locked:** Only necessary TV episode route/identity and this rail's invocation. Preserve movie playback, sources, all progress timestamps, watched state, Watchlist/Collection, providers, TMDb Helper/add-on ownership, shutdown. Verify failing and passing TV cases before/after. **Status: REPORTED; no correction implemented under this new task.**

### 02 — Continue Watching: duplicate film cards / progress updated twice

**Observed:** Repeated movie poster apparently appears twice (user's Insidious example) instead of the original card's saved playback position/duration being updated.

**Required correction:** Compare the actual saved media identities, provider routes, canonical keys and update timestamps to prove they represent the **same exact movie** before merging. On another viewing session, update **one existing card's latest durable progress/duration** and scroll/display state rather than creating a duplicate. Preserve distinct films with similar titles/posters, episode identities and history. No title-only blind dedupe, data loss or bulk wipe.

**Scope locked:** Continue Watching movie identity/upsert/presentation only. Confirm exact duplicate with diagnostic evidence. **Status: REPORTED; no correction implemented.**

### 03 — Continue Watching horizontal rail touch + Resume/Play chooser

**Observed:** Horizontal poster rail is hard to swipe/select accurately; Resume/Play chooser has small cramped rows and touches may not reliably select. Keep the distinct phrase **Continue Watching**, not the separate feature "Continue Playing."

**Required correction:** Reliable horizontal swipe and poster target selection; one deliberate tap activates the correct item; no focus-only playback or incorrect adjacent poster activation. Resume vs Play from Beginning chooser uses a compact Infinity pop-up with larger **vertical** touch targets, clear focus, correct title, safe area, Back/X behavior; preserve saved resume point and original poster/scroll position. No blanket global touch rewrite or unrelated Kodi dialogue changes.

**Status: REPORTED; no correction implemented.**

### 04 — Home clock/weather moon icon overlap

**Observed:** Moon/weather icon intrudes into upper-right text clock (e.g. `12:06 AM`, `11:52 PM`) on real Infinity header.

**Required correction:** Keep exact existing header; reserve dynamic space for the widest time/date, reposition/clamp the existing weather icon so never overlaps time/date in cover/inner Fold, orientations, font scaling and all themes. No redesign or loss of weather.

**Status: REPORTED; no correction implemented.**

### 05 — Add-on Browser header stray cyan/blue slash

**Observed:** Stray blue curved slash/accent leaks into the Add-on Browser top header near the title.

**Required correction:** Remove **only the unintended stray artifact** while retaining Infinity infinity-logo, Add-on Browser title/subtitle, Back control, original theme and safe areas. Trace actual decoration/clip; do not globally delete accents elsewhere.

**Status: REPORTED; no correction implemented.**

### 06 — Add-on Browser root screen / nav labels / redundant text

**Observed:** Root instructions permanently say to select Install from ZIP even on other destinations; static bottom navigation INSTALL ZIP/REPOSITORIES/UPDATES/DEPENDENCIES is redundant, appears selected out of context, and contributes to clutter. User requests an end-to-end clean and accurate browser.

**Required correction:** Root page layout, copy, header/root cards, tab/bottom-bar relevance and hierarchy only. Preserve exactly these root capabilities: **My add-ons, Available updates, Recently updated, Install from repository, Install from zip file, Search**; keep each distinct and selectable. Help text must match active destination; never pretend a shortcut is a different operation. Retain Kodi native installer, keyboard/remote/touch parity, correct Back/home and no external add-on state changes.

**Status: REPORTED; no correction implemented.**

### 07 — Add-on Browser My Add-ons / Updates / Recently Updated submenus

**Observed:** Browser subpages and menus are visually/instructionally inconsistent and touch navigation is unreliable (screen recording `19032.mp4`).

**Required correction:** Make **My add-ons, Available updates and Recently updated** subpages consistent with approved current Infinity panels, spacing, focus, item selection, actual relevant actions, scroll, back history and no silent execution on focus. Hide is **view-local and reversible**, never secretly "Disable"; disabling must remain explicitly labeled and confirmed. Preserve all add-ons, metadata, update service and installed versions unless the user explicitly chooses an action.

**Status: REPORTED; no correction implemented.**

### 08 — Add-on Browser Repository / Install ZIP / Search submenus

**Observed:** Repository browsing, ZIP picker and Search have inconsistent header/labels/layout, keyboard/touch selection, and back behavior (screen recording `19032.mp4`).

**Required correction:** **Install from repository** remains real Kodi repository browser; **Install from ZIP** invokes the original/native chooser (including approved compact ZIP preview, if already implemented); **Search** shows relevant input and results. Appropriate destination-specific instructions/labels, scroll/focus and Back behavior; safe navigation without opening wrong add-ons; preserve original developer/provider ZIP files and installation permissions.

**Status: REPORTED; no correction implemented.**

### 09 — Top featured rail Movies: approved Option B long-press info pop-up

**Visual design already approved in a SEPARATE locked document:** `repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md`. User wants **Option B, bite-for-bite; no exceptions** over the actual `19035.jpg` Infinity Home screenshot.

**Required correction:** In **TOP featured/release Movies rail**, normal tap does exactly what it already did; **press and hold** opens **one compact CENTERED Infinity liquid-glass details modal** without also launching a provider. Keep Home positions unchanged; softly dim backdrop, poster thumbnail left, verified movie metadata right (title/year/rating/runtime/genre/synopsis), X top-right, bottom actions **Play, Trailer, Favorite, More Info** in exact approved order. Use source support only; Play uses existing original provider, favorite uses original Kodi favorite. Dismiss restores exact selected poster and horizontal offset. 150–200 ms restrained fade/scale if motion allowed, reduced/off mode parity. Light/Dark/OLED/Night Cinema and Fold safe areas. **DO NOT IMPLEMENT OPTION A INLINE PANEL.**

**Status: DESIGN APPROVED ONLY; implementation not started.**

### 10 — Top featured rail TV Shows: SAME approved Option B

**Required correction:** Exact same compact centered popup style, button order, theme, motion, long-press/no launch, Back/scroll preservation as **09**, now for TOP featured/release TV show posters. Show verified show/episode metadata; use real season/episode/episode title only if actually available; never guess episode IDs, TMDb show IDs or launch inappropriate episode. Short tap preserves provider behavior. Both movie and TV must have equivalent visual fidelity and interaction.

**Status: DESIGN APPROVED ONLY; implementation not started.**

## B.1 — USER-REQUESTED TRANSLUCENT PLAYER MENUS (VISUAL APPROVAL PENDING)

**Applies precisely to tasks 11–14.** The user clarified on October 19, 2026 that they want the **menus themselves** (not little OSD icons) to be **Infinity liquid-glass/translucent**, so the playing video remains visibly discernible THROUGH Playback, Video Settings and Audio & Subtitles panels. Existing Playback actions/ordering must not be replaced with fictional actions from AI mockups; only the redundant “Video Settings” row is to be removed (task 12) after the OSD video button works (task 11). Video Settings and Audio & Subtitles are compact standalone windows slightly smaller than Playback. Exact Light/Dark/OLED/Night Cinema glass opacity/appearance is subject to user approval of the visual mock; **none of tasks 11–14 have been implemented**.

**Controlling design proposal:** `repairs/2103390-bugfixes/PLAYBACK-GLASS-MENUS-VISUAL-PROPOSAL.md`. It records the user's verbatim clarification, full original Playback menu item list, zero Cobra change and nonintrusive video/session safeguards. **Do not lock incidental labels invented by the render.**

### 11 — Player OSD monitor/video-looking button: connect to Video Settings

**Observed:** User points to the **video/monitor-looking icon in the player OSD bottom control strip** (screenshot `1792386488186.jpeg`) as presently empty/inert.

**User-required correction:** Preserve the existing icon's position and current OSD. **One tap on that existing video-looking button must open/toggle the real Video Settings control**. Do not create a new redundant button, change Rotate/Repeat/Display semantics, seek/timeshift, stop, audio/subtitle, PiP, full-screen controls, video or playback session. Opening/closing settings must not stop/recolor/stretch video.

**Status: EXPLICITLY REQUESTED; not implemented. Confirm actual control ID and binding during investigation; never guess the wrong neighboring button.**

### 12 — Playback options popup: remove redundant “Video Settings” entry ONLY

**Observed:** Playback popup shown over video includes: `Now Playing`, `Audio & Subtitles`, `Video Settings`, `Chapters & Bookmarks`, `Playlist`, `Go To Time`, `Player Settings`, `Playback Info`, `Close Player`.

**User-required correction:** Since Video Settings becomes accessible from existing OSD button **11**, **remove only the redundant “Video Settings” menu row** from the **Playback popup**. Do **not** delete its functionality or remove the distinct **Player Settings** entry; do not touch other rows, their order/handlers, Close Player or the video decoder. Existing Player Settings remains what it was. Video Settings must still work through OSD and the new dedicated popup **13**.

**Additional approved styling requirement:** The Playback popup itself must use Infinity's **translucent glass menu surface**, where the playing video is subtly visible behind/through it. **Do not add/remove/reorder actions except the specifically requested removal of the redundant Video Settings row.** Do not apply transparency to the icons; this is the *menu surface*. Final material opacity/visual styling awaits the user's mock approval.

**Status: EXPLICITLY REQUESTED; exact glass design mock PENDING APPROVAL; not implemented.**

### 13 — Video Settings: compact Infinity playback-context pop-up

**User-required correction:** When invoked by OSD video icon **11**, Video Settings uses a **standalone compact centered Infinity modal**, visually consistent with the existing Playback options popup, but **slightly smaller**, **never replacing/covering the entire screen with a new full-screen menu**. Maintain existing real video settings, focus/scroll, adjustment previews and correct apply/cancel/back behavior; keep live video context visible. Use actual safe-area space and internal scrolling if content exceeds available height; support Fold cover/inner, themes and large touch targets. Do not silently reset settings or recolor video. No extra shared dialogue redesign.

**Additional approved styling requirement:** Use the same Infinity translucent liquid-glass material as Playback, with the real moving video partially visible THROUGH the compact menu background; text and sliders remain readable and accessible; do not make the OSD video icon itself translucent. Share original theme colors (Light, Dark, OLED, Night Cinema), safe areas and reduced motion. Exact mock-style approval pending.

**Status: EXPLICITLY REQUESTED; exact glass design mock PENDING APPROVAL; not implemented.**

### 14 — Audio & Subtitles: compact Infinity playback-context pop-up

**User-required correction:** Playback → **Audio & Subtitles** must use a **standalone compact centered Infinity modal** in the SAME established Playback-glass style, **slightly smaller than Playback**, **not full-screen**. Preserve all real audio track/subtitle track selections, enable/disable, delays and other existing player options; if too many choices, scroll inside popup, never clip controls or move to a full-screen replacement. Focus, taps, Back/X and theme parity; do not interrupt audio, playback session or subtitle synchronization. **Do not remove “Audio & Subtitles” from the Playback popup.**

**Additional approved styling requirement:** Same translucent Infinity glass surface as the Playback and Video Settings popups, showing some live video THROUGH the popup without reducing label legibility. No icon transparency redesign, audio track list replacement, forced track changes, or global dialog system restyle. Mock for exact visual opacity/placement approval pending.

**Status: EXPLICITLY REQUESTED; exact glass design mock PENDING APPROVAL; not implemented.**

### 15 — Native exit 139: evidence and targeted cause-based correction

**Observed:** Repeated native Kodi engine abnormal exit with historical self-exit code 139, first around Oct 18 00:55 EDT; source of native fatal instruction unproven. Existing in-app Health Center/Infinity Diagnostics was used. **Do not confuse this with normal Close, an intentional signal-9 process kill, ANR, or proven earlier Graphics/Directory deadlock.**

**Required investigation before fix:** Reuse existing #12 Stop → Movie Choices and Stop → Movie Choices → Home source traces, PID/time/lifecycle native crash recorder/Android tombstone/stack evidence, and physical Fold conditions. Investigate missing crash-time `native-crash-last.txt` evidence; preserve existing in-app diagnostic export and crash recorder. Implement only a faulting-component repair when actual matching evidence proves it. Never add mandatory Mac scripts, bypass close guards or speculate from code 139 alone.

**Status: INVESTIGATION OPEN; NO PROVEN CRASH FIX.**

### 16 — CU LRC Lyrics Python script exception (triage only)

**Observed in earlier diagnostic:** `script.cu.lrclyrics` 6.7.1 reported a `TypeError` resembling `Operation.__init__() takes 2 positional arguments but 4 were given`. This is an independent lyrics add-on fault and not proof of native crash or TV Continue Watching cause.

**Required investigation:** Capture original traceback, identify version/API mismatch, verify whether it affects user-visible lyrics. **No automatic add-on replacement, upgrade, disabling, removing, or edit** without a later task-specific user's authorization. Preserve playback and saved data.

**Status: REPORTED / TRIAGE ONLY; NOT AUTHORIZED FOR A SPECULATIVE REPAIR.**

### 17 — TMDb Helper / SlyGuy quarantined service starts (triage only)

**Observed in earlier diagnostic:** Kodi quarantined/suppressed startup for `plugin.video.themoviedb.helper` and `script.module.slyguy`. Might relate to TV resolver but causality is NOT established.

**Required investigation:** Verify current installed versions and true failing startup traces, service permissions and impact. Establish whether this failure actually affects **01**. Do not independently disable/reinstall/overwrite helpers or providers, clear data, bypass quarantine, re-enable Otaku or reactivate skipped legacy Version Check functionality without user permission.

**Status: REPORTED / TRIAGE ONLY; NO ROOT CAUSE OR CORRECTION CONFIRMED.**

### 18 — User-selected completion / combined APK / stringent final verification

**This is a distinct GATE, not permission to implement unrelated features.** After user-approved individual fixes have been implemented, source-reviewed and checkpointed, combine **only the explicitly accepted task numbers** atop immutable 2103390 into one higher-version experimental signed APK. Individually skipped/unresolved items remain clearly marked, not mislabeled as green or quietly altered.

Verify: signed package ID and permanent signer; full byte-level added/removed/changed APK-member inventory; original Cobra untouched; original 2103384 shutdown protections unchanged, 16 durable essential saves and true Close/reopen, original providers/skin/Command Center/Health Center/diagnostics preserved, reliable movie/TV playback, watched/progress, PiP/background/screen saver/fold, no playback regression, theme and popup parity; device **install-over** with original Diggz+custom Infinity skin and user data retained; Android 17 and **physical Samsung Fold** (not just emulator); actual click/hold/close tests and original issues reproduced/not reproduced.

**DO NOT FINAL LOCK, CALL EVERYTHING FIXED OR ISSUE AS USER-APPROVED INSTALL until the user sees honest test outcomes and explicitly approves.**

**Status: NOT STARTED.**


### 19 — Movies ↔ TV Shows: keep fully populated Home content resident after initial startup (NO RELOAD ON TAB SWITCH)

**Observed and user-reproduced in `19049.mp4`** (approx. 76.9-second physical Fold screen capture): After normal Infinity startup and populating Home, navigating between **MOVIES** and **TV SHOWS** can leave a category's top Umbrella Latest Releases poster strip and **Continue Watching** tiles temporarily empty while the display repopulates, even though they previously loaded in the same running session. In the supplied capture TV SHOWS navigation displays already-rendered category/menu/add-on tiles while the hero strip and Continue Watching content are absent for multiple captured frames; later the poster strip and watched rail reappear. This is user-visible repeat loading when switching categories, **not** a deliberate shutdown/restart. The exact underlying provider request/cache invalidation/root-cause is not yet proven.

**User's precise behavior requirement:** Once Infinity opens and the applicable Movie and TV Home data have initially populated, **the complete relevant content stays available during that running application session**. Moving MOVIES → TV SHOWS → MOVIES → TV SHOWS must **immediately** show the previously populated top poster rail, provider/content/add-on rails, Continue Watching entries, and their artwork without visible blank panels, reinitialization/refresh loading, unwanted scroll resets or repeat initial-start wait. **Normal content initialization after quitting and reopening Infinity is explicitly acceptable.**

**Proposed safe diagnostic scope (implementation requires targeted authorization):**
1. Reproduce on actual installed Infinity `2103390`/skin `1.0.5.228` using the **actual** `19049.mp4` Movies↔TV Shows sequence, log item counts, frame/UI visibility, Home category transitions, directory provider lifecycle, skin conditional content paths, and Command Center read-only list snapshots. Determine what is invalidated on tab changes; do not guess a failing provider.
2. Keep each already fully populated Movies/TV Shows Home category snapshot and local poster artwork mapping alive across ordinary Home tab switches **for the current app session**. Reuse existing Kodi/Infinity provider cache and Home rendering state when possible, not a second database, unrelated global cache, broad add-on edit or extra daemon.
3. Any legitimate content updates/expiry may run **nonblocking** in the background and atomically replace the already visible content WHEN proven ready. Do not freeze content forever, show obsolete data as guaranteed live, or suppress explicit manual Refresh. Do **not** cause blanking/disappearing/reloading on routine category navigation.
4. Preserve initial startup responsiveness and memory budget on Fold: do not block Home while warming every add-on, make duplicate requests or keep unbounded textures/objects indefinitely. Reuse existing cache bounds, laziness and art cache; no prohibited resource leak, ANR, native/persistence race or increased memory pressure.
5. Keep title identities, focused poster, category selection/rail offset, user settings, original provider route, watched/progress, source freshness, Download/Playback state unchanged. Do not touch Cobra shared sessions, OSD, background playback/PiP, Essential-First shutdown, protected write owners or native crash collector.

**Acceptance:** After cold launch, wait until both categories have genuinely populated once. In the **same live process**, perform at least six alternating Movies↔TV Shows transitions, including quick switches and return after playback; previously displayed items should render immediately from retained verified state each time, no empty rails/re-render wait, no accidental duplicate Continue Watching rows, no stale taps, same item counts/focus except genuine asynchronous upstream updates. Test disconnected/slow provider availability with cached already-loaded content and transparent background refresh behavior, Fold cover/inner/rotation, all Infinity themes, screensaver/background return, legitimate explicit refresh and normal new startup after full Close/reopen. Inspect logs for unexpected provider re-resolution and memory impact. Compare actual screen recording and Android17/Fold evidence. Do not mark fixed before physical testing and protected-fallback regression tests pass.

**Status: USER-REPORTED / REQUIREMENTS CAPTURED ONLY. NO CODE CHANGE OR ACCEPTED FIX YET.**

## C. Per-task approval, testing, savepoint and handoff contract (MANDATORY)

All 19 new tasks start **OPEN**. “Option B” is **design-approved only**, not implemented. The user must authorize task-specific implementation (e.g., “Fix 01”, “Proceed 11”) before source changes for that item. An authorization for one number cannot modify other tasks.

For EACH approved item, in this precise order:

1. **RECONFIRM SCOPE:** read this document, baseline and any user-approved visual reference; record a concise exact allowable-file/source list, reproduce the defect using actual user/CI evidence and pick minimal implementation. If another module is implicated, explain it BEFORE touching it.
2. **SAVE BEFORE EDIT:** record immutable pre-change commit/SHA and rollback point on a dedicated task branch/commit; ensure original 2103390 artifact and 2103384 fallback remain intact.
3. **IMPLEMENT ONLY THAT NUMBER:** explicitly diff every changed file. If touching anything forbidden/unapproved—including Cobra or a shared Cobra path—**STOP**. Never waive protected-write/durability safeguards, silently disable services or change provider DBs.
4. **TARGETED VERIFY:** write tests that reproduce old behavior (RED) and corrected behavior (GREEN) where feasible; run actual unit/native/Kodi/app UI tests relevant to item. Note what has and has not been physically verified. No false pass if only mocked tests ran.
5. **SAVE AFTER EACH TASK:** commit/push the working fix + tests to GitHub, update `TASK-STATUS.json` and `CONTINUE-HERE.md`, link exact commit, branch, changed-file list, test/run IDs, artifacts/checksums, what passed/failed, and exact next item. Make the record safe to resume from another chat; never rely on conversation memory as the sole save.
6. **USER-FACING RESULT:** report exactly `Task XX — Implemented / Targeted Tests Green / Integrated / Fold Verified` (separately); check it off only when evidence meets the named gate. Do not claim “complete” prematurely.
7. **PROGRESS TO NEXT ITEM ONLY ON USER INSTRUCTION:** prior fixes preserved exactly; unresolved steps carried as OPEN/RED, never restarted/overwritten or dropped. Do not combine until user explicitly orders combination.

Every new chat must open `CONTINUE-HERE.md` and `TASK-STATUS.json` first, then the exact task document and linked immutable baseline, and **continue instead of starting over**.

## D. Current initial status summary (2026-10-19)

- **01–08:** User-reported problems; no fixes implemented in this new project.
- **09–10:** **Exact Option B design approved and separately locked**, no implementation yet.
- **11–14:** User explicitly requested these precise player-menu/OSD changes; no implementation yet.
- **15:** Previous diagnostics/source investigation exist; actual underlying native crash unresolved.
- **16–17:** Diagnostic findings only, no independent repair authorization.
- **18:** Consolidation/audit gate, not started; run AFTER all user-selected individual tasks, including #19 if authorized.
- **19:** Keep Movies and TV Shows Home content resident across normal tab switches; initial launch/restart reload permitted, no repeated visible blanking.
- **Cobra:** 100% prohibited from modifications; no exemptions.
- **2103390 APK:** preserved as signed provisional base; no new bug-fix APK created from this tracker.

**NEXT ACTION: Ask user which specific task number (01–19) to implement first. This documentation-only step does not authorize implementation.**
