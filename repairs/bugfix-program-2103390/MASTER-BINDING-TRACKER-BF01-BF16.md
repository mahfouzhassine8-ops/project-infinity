# ARCHIVED BF DRAFT — NOT THE CONTROLLING TASK NUMBERS

**IMPORTANT NUMBERING CHANGE:** This BF-01–BF-16 document is preserved as a detailed historical acceptance/symptom reference ONLY. Its numbering and its status table are SUPERSEDED by the more complete canonical **01–18** tracker: repairs/2103390-bugfixes/REPAIR-CONTRACT-01-18.md. Actual live progress and saved commits are ONLY in repairs/2103390-bugfixes/TASK-STATUS.json, with current-session directions in repairs/2103390-bugfixes/CONTINUE-HERE.md. Exact draft-to-canonical mapping: repairs/bugfix-program-2103390/DRAFT-BF-ALIAS-TO-CANONICAL-01-18.md.

**Do not authorize a code fix using a bare BF number without translating to the controlling task ID. Do not update the stale table below after this notice. Nothing here authorizes Cobra edits.**

---

# INFINITY 2103390 — NEW BUG-FIX MASTER BINDING CONTRACT (BF-01 THROUGH BF-16)

**Date:** October 19, 2026.
**Repository:** mahfouzhassine8-ops/project-infinity.
**Development branch:** work/infinity-2103390-targeted-bugfixes.
**Purpose:** USER-DIRECTED repair-by-repair execution, mandatory preservation, tested checkpoints, and eventual combined signed APK.
**Separate numbering:** BF-01 to BF-16 are NEW bug-fix IDs and must NEVER be confused with the OLD #1–16 project whose approved #1–6, #9, #10 and #12 were combined into 2103390.
**Initial status:** This document defines and saves the scope only. ZERO new fixes are claimed implemented. Design for BF-09 was approved separately. No user final release lock.
**User binding directives:** "with the preservation of whatever is not to be touched and only touched whatever is approved"; "I want it word for word, so when you do it, there is absolutely no fucking mistake"; "Cobra is not to be touched at all. No reason to touch it"; "every time you complete each task, you save it... if this chat ends... the new one knows what we're talking about."

## A. ABSOLUTE PROTECTION — APPLIES TO EVERY TASK

### A1. COBRA IS COMPLETELY OFF LIMITS

**NO COBRA WORK. NO EXCEPTIONS WITHOUT A NEW USER INSTRUCTION.**
Do NOT edit, recompile, repackage a replacement for, redesign, enable/disable, change settings, remove, migrate, refactor, hook, reroute, or modify any Cobra component. This includes Java, native Kodi/Cobra interaction code, skins, resources, logos, playback/OSD, Sports, Multi-View, PiP, providers, native engine changes that reach Cobra, and Cobra user data. If a shared file or API would potentially affect Cobra, STOP, isolate an Infinity-only solution, explain the boundary, and obtain explicit user authorization before changes. No assumption that shared Kodi files are safe.

### A2. PREVIOUSLY APPROVED BASES

**Provisional development base** (must be saved and kept): permanently signed APK 2103390, exact filename Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk, SHA-256 778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb; compiled source commit 0efb67a0237c8d05ca066c5f893e6a1713bc5e2d; passed combination workflow 39173982272 and artifact 12153970810. This is a **development checkpoint, not a final Fold lock**. Never overwrite it or replace it with an older, less complete source.

**Original user-locked shutdown fallback**: signed APK 2103384, SHA-256 b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af. Preserve its Essential-First Close architecture, 16 durable essential owners, barriers, guards, zero-blocker requirements and process-death/reopen design EXACTLY. Do not touch those files or try watchdogs, bypasses or exemptions for convenience. Preserve previously fixed OnJobComplete directory/graphics lock-inversion correction (#9), background playback, PiP, fold stability paths.

**Signing/installation identity**: package com.projectinfinity.kodi, permanent release signing certificate SHA-256 d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7. Never uninstall, factory-reset or clear data. User always installs updates over prior Infinity with Diggz build + custom Infinity skin + all saved settings/add-ons.

**Current protected components**: skin.infinity.diggz ID and approved 1.0.5.228 styling; existing Phase D, Light/Dark/OLED/Night Cinema and Ambient Home; script.infinity.commandcenter 0.3.5.20 as SOLE existing owner of Continue Watching/Watched/Watchlist/Collection/progress databases; script.infinity.uirepair 0.1.2; script.infinity.rails 0.2.7; script.infinity.watchedbridge 1.0.1; existing Kodi providers (Umbrella, POV, TMDb Helper, Seren etc.), PVR/settings/profiles and all user data; original source chooser, playback/player controls, subtitle/audio, rotation, Home layouts, file picker, native in-app crash diagnostics libinfinitycrash.so, Health Center, shutdown. No background source scrape on poster focus. Never guess title IDs.

**Existing services**: 2103390 inherited service.infinity.compat 0.7.2 embedded but UNREGISTERED. No new registration, no substitution with external staged 0.8.2. service.xbmc.versioncheck unchanged; no speculative alterations. Old #7, #8 and #11 were user-skipped as NEW development work; do not resurrect or modify them and do not erase existing functionality.

### A3. WORK APPROVAL BOUNDARY

Listing a bug here means it is captured for planning, NOT authorization to change unrelated files. Implement ONE explicitly approved BF task at a time, only its listed symptoms/actions. When a task reaches third-party code, shared native engine, shutdown/Cobra boundary or a new functional behavior not approved here, STOP and ask before changing it. If user skips an item, mark SKIPPED_BY_USER and retain all old implementation. NO new APK build, install, promotion or lock unless user authorizes that stage. No speculative global cleanup.

## B. EXACT NEW NUMBERED TASKS (USER-EVIDENCED)

### BF-01 — TV SHOWS → CONTINUE WATCHING UNAVAILABLE EPISODE ROUTE

**Evidence:** Under TV Shows → Continue Watching, the click on some episode cards displays the popup titled "Infinity Resume Hub" with the EXACT words "This source is unavailable or has expired. Open the title in your provider to resolve a fresh source. Resume Hub kept your local state." Movie Continue Watching succeeds; 19042.mp4 also showed another TV episode opening a working Resume chooser. The issue remained after the 2103390 skin and all add-on installers were installed. **This is Continue Watching, NOT the separate Continue Playing action menu.**
**Allowed:** Trace only Command Center plugin target routing, show vs episode verified identity, episode season/number, saved source route and freshness/failed-source policy, compatible existing provider routes and TMDb Helper availability; identify precise failing reason per episode. Restore existing verified path or user-approved provider chooser, no fabricated stream/IDs or scraping while browsing.
**Must pass:** A verified, playable saved episode opens the CORRECT show/season/episode and retains resume position, watched and list state. Genuinely unavailable routes still give an honest message. A working TV episode and movie show no regression, and original databases remain untouched except exact authorized updates.

### BF-02 — TMDb Helper / SlyGuy STARTUP QUARANTINE DIAGNOSIS

**Evidence:** Kodi Diagnostics identified startup quarantine for plugin.video.themoviedb.helper and script.module.slyguy. Relationship to BF-01 is NOT PROVEN.
**Allowed:** Inspect precise addon IDs/versions, service startup ownership, failed traceback and quarantine reasons. Restore a falsely rejected Infinity-owned path ONLY if proved, otherwise propose a separate third-party remediation and seek explicit permission. Never blindly enable/reinstall/replace unrelated services or weaken quarantine.
**Must pass:** Evidence-based reason identified; no unapproved addon writes or provider changes. If not proved, leave INVESTIGATING, not fixed.

### BF-03 — DUPLICATE INSIDIOUS MOVIE IN CONTINUE WATCHING

**Evidence:** 19035.jpg shows the same Insidious item twice in Movies → Continue Watching. User expects watching again to UPDATE ORIGINAL watched time/duration/progress instead of adding a second card.
**Allowed:** Trace duplicate identity keys (verified IMDb/TMDb etc.), source aliases, observer saves, canonical join and Command Center one-writer state. Merge/update ONLY records confirmed to be the same unique movie, keeping newest authentic resume progress, duration, watched/checkmark, list memberships and other data. Do NOT deduplicate solely by title/poster or clear the whole list.
**Must pass:** Two plays of same proven movie produce exactly ONE logical current Continue Watching card; updated time/progress survives Close/reopen; distinct movies and all other saved records stay intact.

### BF-04 — CONTINUE WATCHING HORIZONTAL POSTER SWIPE / TOUCH

**Evidence:** 19042.mp4 shows poor touch response/selecting along horizontally scrollable Continue Watching cards. Horizontal scrolling applies to the RAIL, not Resume/Play choices.
**Allowed:** Repair selected-poster identity, drag/swipe vs tap/long-press gesture mapping, hitboxes, focus and horizontal offset in those existing Home containers. Preserve earlier approved Video Sources input, Rails Mocha behavior and normal provider launch.
**Must pass:** Fluid one-finger horizontal scroll; tap acts on actual tapped poster once; hold acts only on that title; Back retains offset; inner/outer Fold, rotation and themes. No accidental launches and no off-row focus.

### BF-05 — CONTINUE WATCHING RESUME / PLAY VERTICAL DIALOG TOUCH

**Evidence:** 19042.mp4 shows a poorly positioned vertical 2-choice Resume/Play-from-beginning chooser with difficult touch selection. It is NOT a horizontal-scrolling menu.
**Allowed:** Target only this Infinity use of the original Kodi chooser: safe vertical placement, larger hitboxes, focus/press accuracy and correct time label; don't rewrite all native dialogs or playback controller.
**Must pass:** "Resume from [correct saved timestamp]" and "Play from beginning" reliably respond to ONE intended press, not focus alone; Cancel/Back no playback/write; no clipped bottom edges, long labels, orientation and Fold safe area verified.

### BF-06 — ADD-ON BROWSER ROOT CONTEXT, ACTIONS AND FOOTER

**Evidence:** Screenshot 1792383561650.jpeg shows root ADD-ON BROWSER (My add-ons, Available updates, Recently updated, Install from repository, Install from zip file, Search). Instruction about "Install from zip file" is displayed on unrelated navigation; root footer repeats INSTALL ZIP/REPOSITORIES/UPDATES/DEPENDENCIES irrespective of actual context.
**Allowed:** Fix only root screen title/help text, visible tile interactions, relevant bottom navigation and truthful action labels. Preserve every installed native Kodi function; do not remove a working operation or change access/permissions to add-ons without approval. Do not alter Home design.
**Must pass:** Every original root tile reachable and working; accurate contextual instructions, footer not misleading/redundant, touch and remote selection/Back correct, no accidental service disable or navigation to retired layouts.

### BF-07 — ADD-ON BROWSER ALL CHILD MENUS AND ZIP PICKER (END TO END)

**Evidence:** User's video 19032.mp4 shows inconsistency across repositories, My add-ons, updates/recently-updated, dependency listings, Search, installed add-on actions and Install from ZIP native picker; focus on right-hand buttons only after unexpected Back/launch; irrelevant controls and inconsistent popups.
**Allowed:** Explicit per-view/per-action audit and precise correction of current Infinity presentation: contextual footer, every visible menu item, proper selected-item popup, touch hitbox/long-press, focus, Back and Fold response. Reuse original Kodi functionality and approved existing ZIP preview. No global rewrites or deletion/reinstallation of add-ons.
**Must pass:** Full path-by-path matrix: My add-ons → details/settings; Available updates; Recently updated; Install from repository; Install from ZIP picker; Search; Dependencies; keyboard; Back; touch/D-pad parity; each action relevant and no invisible focus traps, overlap, accidental launch or disable.

### BF-08 — STRAY BLUE SLASH IN ADD-ON BROWSER HEADER

**Evidence:** 1792383561650.jpeg shows stray bright blue curved/slash glyph above and right of ADD-ON BROWSER header.
**Allowed:** Remove ONLY unintended accent or clipped visual in that header, not native icons, Infinity logo, BACK, theme, animation system or unrelated headers.
**Must pass:** Zero slash in Light/Dark/OLED/folded/unfolded while header/title/back/theme remain identical.

### BF-09 — EXACT USER-LOCKED OPTION B: LONG-PRESS TOP HOME POSTER INFO (MOVIES + TV)

**STATUS: VISUAL DESIGN LOCKED; NO IMPLEMENTATION COMPLETED.**
**Controlling approved contract (read first):** repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md. Approved mock: panel "3. OPTION B – LONG-PRESS POP-UP" over user's EXACT CURRENT real Home image 19035.jpg; user rejected generic alternative dashboards; user explicitly said "simple and elegant ... bite for bite no exception."
**Allowed:** Normal single tap launches exact present original provider route; press-and-HOLD a poster from TOP movie/TV featured/latest release rails opens ONE centered compact, rounded Infinity liquid-glass modal over dimmed but UNMOVED original Home. Poster LEFT, title/rating/year/runtime/certification/genre/synopsis RIGHT based on genuine metadata; Close X top-right, bottom actions exactly ordered PLAY → TRAILER → FAVORITE → MORE INFO. Only enable supported real actions; correct show episode IDs when known; no source scraping on focus.
**Themes/animation:** Light pearl/glass, Dark navy/glass, true black OLED and amber Night Cinema follow existing theme tokens. Smooth subtle fade+96%-to-100% scale ~150–200ms/reverse (reduced motion/off honored). Large touch hitboxes and safe-area adaptations on both Fold displays. No Option A inline panel, Home rows shifting, changed normal single tap, new unrelated pages or provider/engine changes.
**Must pass:** MOVIES and TV SHOWS, real title data, select/hold vs tap no double dispatch, popup buttons, Back and X recover exact original poster/category/rail offset, approved screenshot fidelity, Light/Dark/OLED/Night Cinema and Fold proof. Preserve Cobra absolutely.

### BF-10 — MOON / WEATHER ICON OVERLAPS CLOCK

**Evidence:** 19035.jpg/19028.jpg show moon symbol overlapping time at about 11:52 PM / 12:06 AM near Home top-right.
**Allowed:** Adjust only Infinity Home clock/date/weather icon safe layout/anchors/spacing for long AM/PM time strings and Fold layout. Preserve weather values, location/time logic and original header style.
**Must pass:** No icon/time/date collision or clipping at 12:06 AM, 11:52 PM, standard clock texts, different text scaling, all themes, both Fold modes, rotation.

### BF-11 — CU LRC LYRICS SCRIPT FAILURE (DIAGNOSE ONLY UNTIL USER APPROVES ADD-ON EDIT)

**Evidence:** Kodi Diagnostics identified script.cu.lrclyrics 6.7.1 TypeError: "Operation.__init__() takes 2 positional arguments but 4 were given." This is NOT automatically a native crash or TV episode problem.
**Allowed:** Explain/reproduce exact traceback and identify version/API mismatch; no modification of third-party lyrics add-on, playback/audio, Python runtime or app until user explicitly approves.
**Must pass:** Verified root cause, and if user later authorizes targeted correction, only lyrics-path tests pass; otherwise retain DIAGNOSE_ONLY.

### BF-12 — RECURRING ENGINE EXIT STATUS 139: IN-APP CRASH EVIDENCE AND ROOT CAUSE

**Evidence:** Original in-app Infinity-Diagnostics-20261018-005618.zip self-exit 139 October 18 at 00:55:31 EDT; later Infinity-Diagnostics-20261018-233542.zip includes another 139 historical exit circa 19:07 EDT. THESE MAY BE SEPARATE CAUSES; no matching native stack/tombstone proven and the exit-history record by itself does not cryptographically identify the original APK. Existing script STOP-TRACE.md traced Stop → movie choices (A) and Stop → choices → Home (B).
**Allowed:** Preserve and reuse built-in libinfinitycrash.so / InfinityExitDiagnostics / Health Center exports; investigate missing native-crash-last.txt handler registration/ownership, tombstones, exact PID/time/build and user sequence, original native player cleanup. External Mac ADB capture scripts are OPTIONAL and never integrated into APK. Do NOT guess render/decoder/addon or change protected native shutdown paths without causal evidence.
**Must pass:** Exact correlated stack/failing component and smallest specific native fix only after proof and user authorizes it; original sequence and independent background/screensaver, PiP, Close/reopen/Fold tests. Without evidence mark INVESTIGATING, NEVER fixed.

### BF-13 — SIGNAL 9 / OS PROCESS DEATH CLASSIFICATION (DO NOT CONFLATE WITH BF-12)

**Evidence:** Kodi_Diagnostics_20261019T042154Z-2eaea0ee.zip reportedly contains Android signal 9 process-termination evidence; SIGKILL may be deliberate OS reclaim, normal close or separate abnormal event. Not automatically SIGSEGV.
**Allowed:** Read-only compare PID/timestamp/exit reason vs saved Essential-First Close receipts and process lifecycle; propose a targeted correction ONLY if user evidence proves a defect and user approves. No changes to working shutdown/native process policy.
**Must pass:** Accurate normal/OS-killed/abnormal/unknown classification. If unproven, remain investigation only. Never bypass guards to obtain green.

### BF-14 — INTEGRATED PRESERVATION + BINDING AUDIT (MANDATORY GATE, NOT A REPAIR)

**Allowed only after individual tasks accepted:** run exact source/file/payload change whitelist; all original nine-number repairs from 2103390; all individually approved BF items; Cobra ZERO changes, shutdown policy byte-preserved, existing service.identity and startup registration, provider/service data and ZIP inventory, Android17 playback/UI/native progress, comprehensive per-screen and theme/fold regression. Reuse test passes but never assume prior source-only GREEN qualifies a new APK.
**Must pass:** All binding requirements and relevant native/Android run receipts, no false-green or missing package member, no unwanted UI changes or data loss. If any fail, reject candidate; preserve earlier completed task checkpoints.

### BF-15 — COMBINE APPROVED & SAVED BF TASKS INTO ONE NEW PERMANENTLY SIGNED APK (GATE)

**Allowed after BF-14:** combine ONLY user-approved individually implemented-and-saved tasks. Reuse original 2103390 complete source and signed APK, do not downgrade/redo existing fixes; assign NEW versionCode greater than 2103390; permanent original signer, hash each included add-on ZIP/source, verify original/added/removed/changed APK members byte-for-byte. Supply matching separately installable add-on ZIPs IF running Kodi requires activation separately, with exact install order.
**Must pass:** One verified signed new experimental APK, manifest and artifact hashes, fresh/loaded runtime component verification, install-over proof. Not called release-locked.

### BF-16 — PHYSICAL GALAXY FOLD ACCEPTANCE / USER-ONLY FINAL LOCK (GATE)

**Allowed after signed candidate:** physical Samsung Galaxy Fold 8 Ultra Android17/One UI9 test without uninstall/clear/skin wipe. Compare inner/cover and rotation, Light/Dark/OLED/Night Cinema, long-press UI, all browser menus, horizontal rails/resume popup, movies/episodes, sources/progress/duplicates, installed add-on versions, playback/PiP/background/screensaver, native crash diagnostics, Cobra untouched, actual Essential-First Close with 16 durable essential owners and full process death/reopen.
**Must pass:** User confirms correct behavior and no regression from diagnostics/screenshots/recordings. Final LOCK only after explicit user's word; a signed APK by itself is NOT a physical acceptance.

## C. LIVE STATUS TABLE — DO NOT CLAIM COMPLETION WITHOUT RECEIPTS

| BF | Item | Status now | Implemented and tested? | Saved implementation receipt? | Physical Fold? |
|---|---|---|---|---|---|
| 01 | TV Continue Watching source | NOT_STARTED | NO | NO | NO |
| 02 | TMDb/SlyGuy startup quarantine | INVESTIGATION_PENDING | NO | NO | NO |
| 03 | Duplicate movie/progress | NOT_STARTED | NO | NO | NO |
| 04 | Horizontal rail touch | NOT_STARTED | NO | NO | NO |
| 05 | Vertical Resume/Play dialog | NOT_STARTED | NO | NO | NO |
| 06 | Add-on Browser root | NOT_STARTED | NO | NO | NO |
| 07 | Add-on Browser subviews | NOT_STARTED | NO | NO | NO |
| 08 | Header blue slash | NOT_STARTED | NO | NO | NO |
| 09 | Option B top poster details | DESIGN_APPROVED_ONLY | NO | DESIGN SPEC SAVED, NO CODE | NO |
| 10 | Clock/moon collision | NOT_STARTED | NO | NO | NO |
| 11 | CU LRC Lyrics exception | DIAGNOSE_ONLY | NO | NO | NO |
| 12 | Exit139 investigation | INVESTIGATION_PENDING | NO | Earlier #12 groundwork only | NO |
| 13 | Signal9 classification | INVESTIGATION_PENDING | NO | NO | NO |
| 14 | Binding/preservation audit | NOT_STARTED | N/A | NO | NO |
| 15 | Combined signed APK | NOT_STARTED | N/A | NO | NO |
| 16 | Fold test/final lock | NOT_STARTED | N/A | NO | NO |

**First task to approve:** BF-01, unless the user selects another number. NO current implementation is authorized by this list alone. Do not silently start BF-02 or later.

## D. SAVE EACH TASK PERMANENTLY — NONNEGOTIABLE CHECKPOINT PROTOCOL

**Before starting BF-XX:** read this tracker, the separately saved 2103390 baseline document, the Option B visual contract (for BF-09), the latest CONTINUATION-HANDOFF.md and any completed task receipts. Record current Git commit/HEAD, affected files' SHA-256 and exact allowed scope. Confirm protected files, Cobra and shutdown. Ask before crossing protected boundaries.

**Work:** one BF number only; user says "Fix BF-XX"/"Proceed with BF-XX"; actual code change minimal and localized. Host tests include a positive reproducer, a negative control, and preservation regressions. Internal pass is not real Fold proof. If failed, keep status FAILED/BLOCKED and previous good commit intact.

**Immediately after an individual implementation and green targeted tests, BEFORE MOVING ON:**
- Save full source code, tests, and any build changes to a real GitHub commit on the development branch or a documented item branch. Record complete exact commit SHA and predecessor rollback SHA. No unsaved work remains only in chat.
- Create a uniquely named immutable task evidence record inside repairs/bugfix-program-2103390/receipts/BF-XX-YYYYMMDD-RCxx.md, including symptom/reproduction, approved edit scope, changed/unchanged file list with hashes, original/new component identity, test IDs/run URLs, actual pass/fail, any APK/addon ZIP SHA, Fold status and remaining validation.
- Update THIS master table with honest gate-specific states (INVESTIGATING, IMPLEMENTED, TARGETED_GREEN, INTEGRATION_GREEN, FOLD_VERIFIED, COMPLETE, BLOCKED, FAILED, SKIPPED_BY_USER); never mark COMPLETE for proposed/mock/source-only work. If the user says "Complete one and put a check" mark the individual proof status AND outstanding integrated/Fold gates separately.
- Update CONTINUATION-HANDOFF.md with exact current HEAD, last completed saved BF receipt, next requested number, failures and how to resume. Do not begin the next BF until all saves are confirmed. Announce "BF-XX implementation saved" with commit link and remaining real-device gates.
- NEVER force-push or delete previous green checkpoints. Preserve every previous signed APK and original data. A downstream failure means fix downstream only, not reset or redo prior items.

**Combination:** BF-14 audit → BF-15 signed combined APK → BF-16 physical Fold and explicit user LOCK. If any audit requirement fails reject the candidate; save failure evidence and preserve previous good state.

## E. USER EVIDENCE & REFERENCES FOR NEW CHAT

Screenshots and recordings from current conversation: 19035.jpg (real Home, duplicate Insidious and moon/time overlap); 19021.jpg and 19028.jpg (episode unavailable popup); 19042.mp4 (rail swipe and Resume/Play chooser); 19032.mp4 (Add-on Browser all menus); 1792383561650.jpeg (blue slash); 19043.jpg (stock Kodi metadata example); 19045.mp4 (top poster rail); labeled Option B mock infinity_ui_interaction_options_mockup.png (use ONLY design panel B on REAL Home 19035.jpg).

Diagnostic archive filenames: Infinity-Diagnostics-20261018-005618.zip; Infinity-Diagnostics-20261018-233542.zip; Infinity-Diagnostics-20261019-000835.zip; Kodi_Diagnostics_20261019T042154Z-2eaea0ee.zip. These may not be automatically retrievable in a future chat: if bytes are absent do NOT pretend to inspect them, request the needed original evidence.

Protected saved references: repairs/baselines/INFINITY-2103390-PROVISIONAL-BUGFIX-BASE.md; repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md; repairs/integration-20261018/COMBINED-2103390-RESULT.md; repairs/four-repair-20261018/STOP-TRACE.md.

## F. CONTINUATION SAFETY

In every new conversation, FIRST fetch THIS document and repairs/bugfix-program-2103390/CONTINUATION-HANDOFF.md from the development branch, compare to latest actual HEAD, then any linked receipts. Do not guess tasks from earlier summaries. Do not touch Cobra. Preserve 2103390 and 2103384. Ask which BF number the user wants next if none is approved. Never claim saved, tested, installed, fixed, or locked without actual proofs.

**END OF BINDING PLAN — DOCUMENTED, NOT IMPLEMENTED.**
