# INFINITY 2103436 — END-TO-END UNIVERSAL LOADING AND NAVIGATION READINESS CORRECTION

**USER CLARIFICATION (October 31, 2026):** "This should not serve as just a movie specifically it should be end to end infinity that just serves as an example."

**Binding scope decision:** The new user recording `20741.mp4`, featuring a long empty Kodi VIDEOS destination after starting from Infinity Home/TV Shows context, is **ONE REPRODUCTION EXAMPLE** of a **SYSTEM-WIDE Infinity loading/navigation-readiness defect**. It is not permission to implement a Movies-only, TV-Shows-only, POV-only, Videos-only, or one-window special case. Every first-party Infinity navigation and loading surface must be included in an explicit end-to-end inventory, with truthful limitations documented for external providers and native Kodi paths.

## Authority and hard freeze

- Repository: `mahfouzhassine8-ops/project-infinity`
- Engineering branch: `work/infinity-only-from-2103436-20261031`.
- EXACT user-approved signed combined baseline: **2103436**. Source: `7bbe08363b493146ca7ed67cb872e9a98b1d888b`; locked branch: `lock/infinity-cobra-2103436-user-approved-20261031`.
- Signed436 SHA256: `ff8e7ec16cb10028aef50579161de92b205e97ca8131195098753fb3821bdbc6`.
- All Cobra code/resources/logic **ABSOLUTELY FROZEN**, including Cards drawer fix, front and inner displays, all five view modes, Pro/Sports, fullscreen More/sun menu, previews, Multi-View, PiP, settings, user data and performance.
- Preserve chooser executable/navigation, shared/native Android contracts and libraries, icon artwork, user data/persistence/shutdown, original signer/package, approved baselines and existing signed436 APK. No Cobra code or side effects in this Infinity workstream.
- Any shared/native Kodi-engine alteration which could affect Cobra is **NOT preauthorized**. Read-only investigation is allowed; report the exact proven need and ask for separate scope authorization before any implementation outside Infinity's component/skin/service ownership.
- This file documents user-approved **scope**; no new Infinity code, APK, CI result, device acceptance or build is implied.

## 20741.mp4: specific example, NOT the project boundary

The physical Galaxy Fold recording shows a start on Infinity Home with TV Shows context (POV TV highlighted in an add-ons row), followed by transition to a near-empty black generic **VIDEOS** destination for approximately 75 seconds, then a directory with Files / Playlists / Video add-ons. A large native white busy spinner is seen near lower-left. The intended activation path is **not yet proven** to be the highlighted POV add-on, or an intended generic Videos route. Treat exact selection/action, fallback choice, native window ownership, directory-list readiness, spinner lifetime and long delay as questions to trace, not facts assumed from selected focus.

The video demonstrates **missing or disconnected contextual loading feedback** and a long empty intermediate state. It does **not prove** the exact cause of latency, a provider network failure, a Kodi GUI deadlock, or that every destination can be safely prepared before a native transition. Avoid fake fixes that merely paint a border over a 75-second block.

The original MP4 is user-provided conversation evidence but may be unavailable to the Codex workspace; do not claim visual inspection without actual bytes. Inspect accessible still frames and original recordings when possible, otherwise label visual evidence limits and continue source/runtime probes independently.

## Approved end-to-end product behavior

**Primary, user-triggered actions:** On a user tap, remote select or other supported activation, use the **existing selected/focused control border** with a small, restrained cyan traveling perimeter animation while that action has real pending loading work. The selected item should own the cue; avoid global busy graphics when a real local owner exists. Existing selected/focus border, icons, colors, fonts, scroll, gesture and touch geometry remain unchanged. No posters, full-page loaders, fake percentages or arbitrary mandatory waits.

**Secondary, background/global work:** For genuine user-unattached loading or refresh (home widgets, artwork, cache/progress updates, service refresh), animate the **existing upper-left Infinity drawer/menu frame**, coalescing overlapping tracked jobs and terminating as soon as their real work completes. Do not imply provider or network progress unless an authoritative signal exists. Do not show infinite idle animation or duplicate primary+global cues.

**Navigation readiness / empty destination:** Where source ownership and readiness signals permit safe one-time preloading, keep the existing current screen visible and responsive until destination is genuinely ready, then navigate exactly once. Completed-empty pages are valid ready states and should not spin forever. If native Kodi or external add-on routes require navigating before results can load, preserve their normal one-shot action and provide available destination-local/native loading feedback while waiting. Never break navigation or launch the same provider twice for the sake of deferring the transition. A mandatory empty Kodi window must be investigated and handled truthfully rather than concealed with a permanent overlay.

**Root-cause/performance:** Independently trace the real event path from user action → Kodi/Infinity click dispatch → window activation → provider/directory request → first result/empty/error → painted content. Measure dwell time and relevant blocking/main-thread or service/UI delays. Optimize only **proven Infinity-owned** latency/deadlock/redundant work within scope; avoid claims that motion alone improves performance. Do not silently change native/third-party providers or caching contracts.

## SYSTEM-WIDE NAVIGATION AND LOADING COVERAGE MATRIX — investigate ALL categories

A. **Entry/startup/home:** Choose Your Experience → entering Infinity (chooser itself must remain unchanged), skin initialization, Home, widgets/rows, recent artwork, live refresh, return-to-Home, screensaver return, background/foreground; loading until actual usable state.

B. **Top-level navigation:** Movies, TV Shows, Search, Genres, Arcade, Sports destinations where provided by Infinity, Movie Providers/Portal, all corresponding TV/anime/media rails, View All, drawer and power navigation, category switches, favorites/watchlist/collections, Continue Playing and history, recently watched/recommended etc. The selected control's actual route must be tracked, not its appearance or an unrelated focused child.

C. **Deep hierarchy:** genre/list/detail pages, Movies/TV/Anime categories, seasons, episodes, source selection, add-on-specific folders, media metadata/trailers, filters/sort, local folders and fallback pages. Include Kodi's generic VIDEOS and other file/media windows as representatives of **window classes**, not a special hard-coded target.

D. **Search and providers:** global/local search, provider-selection first-tap SELECT only/second-tap SEARCH, Search All, history, keyboard, query submit, in-progress/result/empty/error states, third-party providers (POV, Umbrella, Fen/Fen Light, Seren, Otaku, Nixtoons/WatchNixtoons and other installed add-ons) where compatible. Honor add-on ownership and preserve native cancellation, sheet geometry, auth/status/error paths. Do not create phantom loading on mere focus/selection.

E. **System features and overlays:** Command Center/Command Palette, Health Center, Resume Hub/Continue Watching, background tasks, Settings/System Hub, profile/add-on browser, sync/cache updates, dialogs and supported filesystem sources; where there is real work, expose truthful loading without breaking dialog modal rules.

F. **Playback-adjacent navigation:** source resolution, play/resume/recovery, video startup/return, subtitle/audio choices, fullscreen, PiP/background, watchlist/watched actions, available live TV/sports paths (not Cobra), remote/touch and fold/window reflow. Preserve active native session continuity; no second decoder, autoplay, source duplication or spurious navigation.

**This list is illustrative, not exhaustive.** An end-to-end inventory must map the actual 2103436 Infinity accessible controls and window classes and mark each with *owner, action path, readiness signal, indication location, success/empty/error/back behavior, and safe fallback or limitation*. Do not claim total coverage just because 20741, Movies and Search pass.

## Correctness and guardrails

1. Resolve actual signed436 Infinity component versions, source/skin variants, Kodi window IDs and owner code. The older 2103433 specifications are historical intent, **not the new baseline**. Existing signed435/436 loading is current behavior to correct, not discard/rebuild.
2. Each loading lifecycle must have identity: action/source/target/current view, task state, authoritative readiness, error/timeout/cancel, bounded cleanup and stale callback rejection. Cross-screen/profile/fold/rotation/Back/supersession must not leave cyan ghost activity.
3. Preserve every native Kodi action exactly once and in the original order. Distinguish click from focus, selecting from executing, keyboard prep from search, and page activation from result readiness.
4. No new blocking work on main/UI thread, animation-driven layout thrash, aggressive polling/threads, fake timers, indefinite waiting, duplicate network/provider calls, worker churn or cache wipes.
5. Keep approved Light, Dark, True OLED Black and glass visual geometry, reduced-motion and accessibility behavior, Samsung Fold cover/inner, rotated/split/pop-up windows and touch/remote focus. Respect PiP/background/screen off and audio/video lifecycle.
6. Never globally suppress essential Kodi progress, safe error/sheet controls, native busy lease, or provider-owned modal dialogs without proving an equivalent accurate non-blocking lifecycle. No black-page camouflage as a substitute for fixing the actual stall.
7. Preserve Infinity watched/resume databases, provider registrations, authorization, skins/data, Essential-First shutdown, undo/recovery, signed original key and all 2103436 approved Cobra components. No data clear/uninstall/migrations.

## Mandatory tests and evidence before delivery

- Create actual inventory/matrix across all first-party Infinity navigation/action classes above. Mark **implemented+tested**, **safe fallback**, **blocked by external/native owner**, **not applicable**; never turn gaps into implied PASS.
- Instrument independent cold and warm entry paths and representative cross-category transitions (Home→Movies; Home→TV Shows; Home→Search→selected provider→results; Favorites/Continue; Add-on category→folder; details→season/episode; Settings/Health/Command; return/Back; background refresh). Include the recorded generic VIDEOS delay route, but do **not** restrict testing to it.
- Test genuinely slow, fast, completed-empty, failed, canceled, very long, repeated taps, overlapping jobs, late callbacks, change of window/source and fold/rotation. Verify selected item cue appears only when actual work exists and disappears when complete. Test global drawer cue only with authoritative global work.
- Measure real readiness vs viewport painting, event latency, callback count and any UI hangs. If the 75-second delay is not reproduced, report exact conditions/evidence and do not fabricate performance improvement.
- Exact source/DEX/module/package comparison to the originally signed 2103436: **Cobra owner ZIP/DEX/resources byte-identical**, Minimal Android / chooser behavior / original cert unchanged; only approved Infinity code/resources and required truthful version metadata may differ. If a shared/native modification seems necessary, STOP and report it separately.
- Reuse valid focused tests; no indiscriminate broad suite or shutdown stress. Physical Samsung Galaxy Fold Android 17 is final user acceptance, not a property of host-only tests.
- Only after successful relevant gates should a **single** original-key install-over Infinity-only candidate be signed and delivered, with matching ZIPs, hashes, tested source, run IDs, stated limitations and no auto-promotion. Preserve signed436 as working fallback.

## Codex execution interpretation

The required deliverable is **system-wide diagnosis and coherent Infinity-only implementation**, **not a patch for one movie tile, add-on, or generic Videos window**. Review the real active code for common navigation/readiness ownership and fix those shared Infinity-owned mechanisms in a bounded manner. A test that only covers the supplied recording is inadequate. Never claim universal "stay on Home until everything loads" for third-party Kodi routes with no safe readiness signal; retain native routes with clearly documented, truthful local/global loading fallback instead.

**STATUS:** Scope clarified and documented; no production changes or new APK from this document. Await separate actual engineering execution and device verification.
