# INFINITY 2103390 — SEVEN APPROVED REPAIR GROUPS (EXACT SCOPE)

**AUTHORITY:** User approves combining previously listed related work into seven groups rather than separately repeating edits to the same system. User additionally states: "Silent mode will be #6." This replaces the **sixth GROUP** (old lyrics-error investigation), NOT the preexisting detailed subrequirement **task 06** (Add-on Browser root). The user wants each group detailed "because this is very broad, and I know you can make a mistake."

**THIS IS THE PRIMARY WORK-GROUP NUMBERING FOR FUTURE USER AUTHORIZATION: GROUPS #1–#7.** Keep the original tasks 01–19 in REPAIR-CONTRACT-01-19.md as protected, precisely testable subrequirements. The user did not ask to discard any of them other than the former group #6, CU LRC Lyrics diagnostic repair, which is **SKIPPED / NOT TO BE MODIFIED**. User explicitly placed NEW System Hub Silent Mode at GROUP #6. No other existing group numbers shift.

**STATUS:** Seven-group scope documented and user-selected. No code implemented, no APK/skin output produced, no actual Fold validation or final lock. Group roster is approval of grouping and desired behavior; start the implementation of a specific group only on the user's specific "Fix/Proceed with Group #N." Each group must pass its OWN tests and GitHub savepoint BEFORE moving to the next.

## 0 — BINDING GLOBAL PRESERVATION RULES, EVERY GROUP, NO EXCEPTIONS

**COBRA MUST NEVER BE TOUCHED. NO COBRA CODE, RESOURCES, UI, PLAYER, PiP, SPORTS, MULTI-VIEW, PROVIDERS, SETTINGS OR DATA.** Avoid shared Kodi/native changes that could change Cobra; if unavoidable STOP, report why, and ask for separate explicit user approval. Do not hide them as "cleanup" or a shared-core helper. NO exceptions inferred from group authorization.

Preserve immutable signed experimental Infinity **2103390**, SHA-256 **778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb** (GitHub workflow 39173982272, source commit 0efb67a0237c8d05ca066c5f893e6a1713bc5e2d), and approved user-locked Essential-First shutdown fallback **2103384**, SHA-256 **b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af**. Original #1–6/#9/#10/#12 from the historical project are ALREADY integrated into 2103390; no downgrading or redoing. Original signer SHA-256 **d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7** and package com.projectinfinity.kodi unchanged.

No shutdown architecture revisions, Essential-First durable owner count/guard changes, native checkpoint bypasses, forced recovery, Version Check edits, Cobra side effects, reinstall from scratch, clearing data, deleting provider/skin settings, database rewrites, or removing user add-ons. Maintain Diggz+Infinity original Home and skin ID, real playback/stream controls, subtitles, PiP, background playback, screensaver, Favourites, Watched, Watchlist, Collection, Resume Hub, Health Center, diagnostic export and all installed user data. service.infinity.compat 0.7.2 stays embedded **UNREGISTERED** as in base; do not activate/replace with staged 0.8.2. Only the explicitly approved file-level changes for the current group are allowed. All other APK members checked for exact preservation.

**BEFORE EVERY GROUP:** reproduce each numbered subdefect, inspect actual native/skin/add-on preimages, specify allowed file change list and protected files, record exact branch SHA. Any new feature or suspected shared fault not in this group requires user permission before writing.

**AFTER EVERY GROUP AND EACH TESTED IN-GROUP MILESTONE:** commit code/tests to the development branch with unique immutable SHA and rollback, retain green tests; save a group-specific completion receipt (approved scope, original/patched SHA list, proof logs, red/green test runs, Fold status and remaining gates). Immediately update TASK-STATUS.json and CONTINUE-HERE.md. Do NOT announce "complete" merely because host or source tests passed. No moving to next group until this save succeeds and user authorizes continuing. Later combine only GREEN, user-accepted group corrections, preserve other pending/skipped groups.

## GROUP #1 — HOME / CONTINUE WATCHING / MOVIES ↔ TV SHOWS / HEADER

**Original detailed subrequirements: tasks 01, 02, 03, 04, 17, 19.** All are related to active Home, content identity, playback-resume routing, scrolling, category transitions or provider health; the task 17 TMDb/SlyGuy investigation is conditional and DIAGNOSTIC ONLY unless its causal linkage to #1 is proved.

**1.1 — TV Shows Continue Watching unavailable source (task 01):** From TV SHOWS → Continue Watching, tapping a saved episode sometimes displays the exact original "Infinity Resume Hub — This source is unavailable or has expired..." popup, while Movies generally work and some TV episodes are playable. Trace each item's source selection, saved route, verified show-vs-episode ID, season/episode, route freshness and installed TMDb Helper eligibility; compare actual failing and working TV item plus working movie. Fix ONLY verified local episode-resolver defects. Do not manufacture IMDb/TMDb identity or launch an unrelated episode; source selection remains original provider owner. A legitimately expired link must still be handled safely.

**1.2 — Insidious double movie card (task 02):** User's same Insidious movie appears twice in Continue Watching. Investigate canonical keys and provider route/record update; distinguish confirmed identical movie ID from lookalike titles. On replay, existing card should update latest genuine progress/time/duration and keep same watched/checkmark/list state; no second card, no database wipe, no title-only unsafe merging. Verify Close/reopen durability and other movies/episodes unaffected.

**1.3 — Home Continue Watching HORIZONTAL scrolling and Resume/Play VERTICAL chooser (task 03):** Accurately map actual touch contact to poster/card during swipe, click and hold on Fold; no missed taps, neighboring activation or scroll offset loss. Keep poster rail horizontally scrollable; choose Resume From [saved time] versus Play From Beginning from VERTICALLY stacked, compact, adequately sized touch rows, without accidental click-through. Preserve actual source and timestamp, Cancel/Back no write/launch; touch and D-pad parity, orientation/theme checks.

**1.4 — Weather moon overlays clock (task 04):** Real Home screenshot shows moon icon intruding into time. Correct only existing Home clock/date/weather graphic anchoring, dynamic longest 12h string (e.g. 12:06 AM), width/spacing/safe area across Fold/theme/font scale; no unrelated logo/header redesign or weather data changes.

**1.5 — TMDb Helper / SlyGuy startup quarantine (task 17):** Compare real logs and dependencies for the TV resolver. Exact root cause of quarantined startup must be proved BEFORE an Infinity-side change. This is read-only/diagnostic by default, not permission to uninstall/reinstall/re-enable addons, change third-party script or disable safety quarantine. Record unknowns, keep test RED if unresolved; don't blame every unavailable episode on quarantine without proof.

**1.6 — MOVIES ↔ TV SHOWS category switch, NO repeat blank/reload (task 19):** In real recording 19049.mp4, TV SHOWS category and add-on tiles are already loaded but top releases strip and Continue Watching go blank/repopulate on switching. After both categories have populated ONCE after cold startup, switching back and forth within SAME RUNNING Infinity instance must immediately show retained verified category rails and artwork without visual blanking or duplicate provider restart/wait. Preserve genuine updated content via nonblocking refresh and atomic swap, manual Refresh, cache memory limits, focus/rail offsets, no stale content presented as proven live. True app Close/reopen may load normally. Prove ≥6 rapid/normal category swaps, screenshot/observer counts, Fold orientations, background/screensaver and memory/performance safety. No new global cache or unbounded storage without explicit separate approval.

**Group 1 success:** ALL approved Home-specific subrequirements pass targeted host/native/Android tests; original movie/TV playback, actual progress and user settings preserved; no Cobra, player menu, Add-on Browser or shutdown edits. Capture physical Fold confirmation separately. Group may not be marked fully complete just because one subrequirement passes.

## GROUP #2 — COMPLETE ADD-ON BROWSER CLEANUP

**Original tasks 05, 06, 07 and 08.** One linked Add-on Browser work package, not unrelated skin polish.

**2.1 — Blue slash artifact (task 05):** Remove ONLY stray cyan curved glyph near ADD-ON BROWSER header shown in user screenshot 1792383561650.jpeg. Preserve Infinity logo, title/subtitle, BACK, all legitimate theme accents and actual layout. Validate Light/Dark/OLED/Fold safe areas.

**2.2 — Root (task 06; NEVER confuse with GROUP #6):** My add-ons; Available updates; Recently updated; Install from repository; Install from zip file; Search must all remain reachable, truthful and functional. Remove/replace irrelevant root instruction that permanently points to ZIP installation, and fix static misleading/redundant footer labels. Focus/selection must not silently execute a destructive action. Preserve exact Kodi functionality; Hide is reversible view state, NEVER equivalent to Disable.

**2.3 — Installed/add-on update lists (task 07):** Clean menus/focus/scroll, item-dependent context choices, Enable/Disable confirmation, update details/settings; keep provider states and permissions, no automatic downloads or uninstalls. Real selected tile (not adjacent) receives event. Back restores parent and selection, right controls accessible.

**2.4 — Repositories/ZIP/Search (task 08):** Preserve actual repository navigator, real Kodi native ZIP file picker and approved compact ZIP preview, native search input/results, keyboard, filters/dependencies/update semantics. Contextual header/help/footer, touch/D-pad access, Back and popup alignment must be correct on Fold. Never insert fake search/install sources or redesign entire drawer.

**Group 2 success:** Every original root/subpath and each visible option proven reachable and accurate, context menus perform only their named action, no stray artwork, no lost add-ons, data or global Kodi navigation regression. Cobra unrelated.

## GROUP #3 — EXACT OPTION B TOP-RAIL MOVIE AND TV DETAILS

**Original tasks 09 and 10.** Fully approved design in repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md, based on USER'S ACTUAL Infinity Home 19035.jpg and their chosen labeled OPTION B MOCK. No alternative new UI.

**3.1 Movies (task 09) and 3.2 TV Shows (task 10):** Short tap unchanged original provider/title open. Long-press exactly selected poster on TOP movie or TV release/featured rail opens ONE centered compact rounded Infinity liquid-glass information modal. Soft dim to existing unchanged Home; thumbnail LEFT, verified title/year/runtime/rating/genres/synopsis RIGHT, close X upper-right; exact bottom action order Play → Trailer → Favorite → More Info. Only supported actual actions; missing metadata remains unknown, no guessing season/episode or scraping/launch on highlight. TV variation uses exact verified show/S/E identity. Long hold suppresses short-tap playback. Back/X restores same Home window/focus and horizontal scroll offset.

**3.3 Themes/motion:** Light pearl, Dark navy, OLED controlled true black, Night Cinema amber; ~150–200 ms restrained fade/small scale (unless reduced/off motion), touch targets inner/outer Fold. **Pixel/design fidelity to approved Option B is a hard gate**, no Option A inline expansion, Home shifting, random new dashboard or extra menu buttons.

**Group 3 success:** Movie + TV identical modal experience and actual existing Home screenshot structure preserved; no Cobra/shared native/auto play or provider side effects.

## GROUP #4 — PLAYER OSD / PLAYBACK / VIDEO / AUDIO-SUBTITLE GLASS

**Original tasks 11, 12, 13 and 14.** User-approved translucent menu material in repairs/2103390-bugfixes/PLAYER-GLASS-MENUS-APPROVED-20261019.md; user means MENU SURFACES, not OSD icons.

**4.1 OSD video/monitor button (task 11):** Existing monitor-looking icon opens/toggles real Video Settings; identify actual control before patch. No new toolbar button, no changes to Rotate/Repeat/seek/PiP, real player or stream.

**4.2 Playback (task 12):** Keep actual original menu options and order; remove ONLY redundant "Video Settings" entry when #11's video icon route works; retain Now Playing, Audio & Subtitles, Chapters & Bookmarks, Playlist, Go To Time, Player Settings, Playback Info and Close Player. Preserve actions, playback and menu location. Make existing popup translucent glass so live picture slightly visible THROUGH it.

**4.3 Video Settings (task 13):** Centered glass popup SLIGHTLY SMALLER than Playback, same look/rounded panel and real controls, internal list scroll if long; never full-screen takeover, never fabricate menu values, change aspect ratio/decoder/stream without explicit selection.

**4.4 Audio & Subtitles (task 14):** Same centered smaller-than-Playback translucent glass; original actual audio/subtitle tracks, enable/disable/delays; no interruption to audio/video or playback session. Track settings apply only from explicit action, Back restores previous player state.

**4.5 Parity:** Live video visible through menu glass; Light/Dark/OLED/Night Cinema; readable contrast, no video recoloring or performance load, normal OSD/back/touch hitboxes, reduced-motion parity. Do not substitute concept art text/menu structure for actual user's Sacrifice screenshot and 2103390 player.

**Group 4 success:** All four related changes implemented together on verified minimal Infinity-only player UI path; genuine player, audio/subtitles, original timestamp, PiP/background and shutdown unchanged. Cobra absolutely untouched.

## GROUP #5 — NATIVE EXIT 139 EVIDENCE-BASED CRASH WORK

**Original task 15.** Reuse existing in-app Infinity Diagnostics, native crash collector libinfinitycrash.so, original 12:55 AM and later exit139 evidence, previous Stop Path A (Stop→choices) and Path B (Stop→choices→Home). Distinguish exact PID/build/time and exit classification, missing native tombstone/stack; SIGKILL/9 is not automatically 139. If evidence is insufficient, keep INVESTIGATING and strengthen only the precisely authorized diagnostics, NOT speculative native fixes. Optional external Mac tools never mandatory/in APK.

**Group 5 success:** Identified actual faulting native stack/component + repro and only proved cause-based fix with physical Fold stability, else honest open diagnosis. No shutdown rework, Cobra, random engine upgrades, protection bypass or force-green test results.

## GROUP #6 — NEW SILENT MODE IN EXISTING SYSTEM HUB (REPLACES OLD LYRICS GROUP)

**USER-EXPLICIT:** “Silent mode will be #6.” “Silent mode will live in System Hub ... the CULRC lyrics and the other redundant notifications that pop up, such as track in, all that bullshit. Activating that and turning it on will cease those from popping up on the screen.” The user wants to stop unsolicited notification popups, **NOT repair/uninstall CU LRC Lyrics or Trakt.**

**6.1 Placement:** Add ONE switch labeled exactly **Silent Mode**, default **Off**, inside the user's EXISTING Infinity **System Hub** (not drawer, Home, Playback screen, Android global notification settings or Cobra). The control must show On/Off state, be reachable by touch/Fold and normal keyboard/D-pad, follow Light/Dark/OLED/Night Cinema, save its setting across app Close/reopen and allow immediate On/Off without restart. Reuse existing Infinity settings store/persistence; do not introduce a separate service or database to remember one toggle.

**6.2 ON behavior:** Stop displaying unsolicited **non-interactive Infinity/Kodi on-screen notification banners/toasts** emitted by Infinity and third-party addons, including CU LRC Lyrics error/status notices, Trakt integration status/progress banners and other redundant info/warning notifications. Suppress any associated *notification alert sound* if emitted by the same in-app notification presentation path, WITHOUT muting player audio, music, subtitle, dialogue or Android system sound. Keep notifications internally traceable in existing logs/diagnostic exports; suppression is PRESENTATION ONLY, not execution/callback cancellation.

**6.3 OFF behavior:** Return ordinary existing notification display and alert behavior immediately; do not replay a backlog of suppressed notifications unless explicitly later approved.

**6.4 Distinguish notifications from interactive actions:** Silent Mode does NOT automatically answer, dismiss or bypass dialogs that require user choice/consent (Resume/Play, Save/Apply/Cancel, install ZIP/permissions, confirm Disable/Remove, actual important errors and diagnostics). It does not suppress Home icons/legitimate status controls, Kodi player transport, progress/state writes, protected Essential-First Close or essential diagnostic records. Before implementation, audit actual CU LRC Lyrics/Trakt popup path to determine whether it is a passive toast or blocking script-error modal; if blocking modal or third-party/system UI requires unavailable/forbidden shared changes, STOP and disclose that exception rather than silently misrepresenting it as suppressed.

**6.5 Architecture limit:** Prefer one guarded Infinity-only notification *presentation* gate, scoped when Infinity is active, applying to Kodi's existing noninteractive notification path; no editing third-party add-on source or blanket JNI/Android notification permissions, no removing CU LRC Lyrics/Trakt or suppressing native crash evidence. **Do NOT globally patch Cobra-shared Kodi notifications unless proven isolated from Cobra and separately authorized.** Must preserve original active provider behavior, update checks, saved watched/Trakt history.

**6.6 Tests:** With Mode Off notifications still appear; On standard simulated native script/Trakt info banners do NOT appear; off re-enables immediately; test multiple sources, background/foreground and Fold views, restart persistence, reduced-motion/theme controls, all interactive dialogs still work and provide confirmations, error logs still record genuine issues, player audio unaffected and no extra work on shutdown/Cobra. If any specified category cannot be suppressed within approved boundaries, report precisely and do not mark fully complete.

**Status:** GROUP #6 user-designated scope and requested behavior captured. Implementation NOT STARTED; no guarantee that every third-party blocking modal is an ordinary Kodi notification without investigation.

**FORMER GROUP #6 (CU LRC Lyrics repair) IS SKIPPED:** Original task 16 now **SKIPPED_BY_USER** as a repair; diagnosis evidence can remain in historical archive, but do NOT modify/uninstall/reinstall/disable that addon without another user instruction. This does not cancel new Group #6 notification UI work.

## GROUP #7 — FINAL COMBINATION, BINDING AUDIT AND PHYSICAL FOLD LOCK

**Original task 18, final only.** After user's acceptance of the individually implemented and SAVED groups, audit exact per-file source/asset/payload diffs against 2103390; preserve Cobra byte-for-byte/noninteractive behavior, all shutdown guards and original service registration, provider data/state, skin IDs, theme parity, crashes/diagnostics and unit/native/Android17 results. Combine ONLY proven successful group fixes into one NEW versionCode >2103390 APK, permanent signer, exact SHA manifests, matching separately installable addon/skin ZIPs with activation instructions when relevant. Verify full install-over (never uninstall or clear data), physical Samsung Fold Android17 One UI9 inner+cover, real playback/Close (16 essential owners, zero blockers)/reopen, recording comparisons and user confirmation. The user must explicitly say LOCK. Never claim final green based solely on host CI/emulator.

## EXECUTION AND SAVEPOINT TRUTH

**CURRENT STATUS:** ALL GROUPS UNIMPLEMENTED, except approved design specs for Group 3 Option B and Group 4 menu material. Historical tasks 01–19 may be DONE only upon verified group subtest and their own saved evidence; original task 16 is intentionally SKIPPED, no code needed. No current user-selected group to implement. User can issue “Fix Group 1” through “Fix Group 7”; each group runs only its own listed functionality. **Do not interpret “Fix #6” as fixing old detailed task 06 Add-on Browser. It means Group #6 Silent Mode in System Hub.**

**After EACH group and any green in-group checkpoint**, save source/tests and exact SHA commit, immutable receipts, TASK-STATUS.json and CONTINUE-HERE.md, and show user explicitly which group/subrequirements passed. No final lock without real physical tests and user approval.
