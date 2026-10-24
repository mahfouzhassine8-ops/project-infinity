# INFINITY 2103402 — FINAL STABILIZATION, QUALITY GATE & RELEASE CLOSURE

**ASTRA PRO — EXTRA HIGH | AUTHORIZATION: PROCEED ON A SEPARATE WORK BRANCH.**

**Priority:** Critical. This is ONE final, narrowly scoped corrective project, NOT a fresh redesign, feature program, or audit-only assignment. Implement, causally verify, integrate, build, permanently sign, and deliver an install-over candidate and its exact component ZIPs. Do not declare the project complete until the user's physical Fold acceptance.

**Repository:** `mahfouzhassine8-ops/project-infinity`  
**Protected current working baseline:** Infinity `2103401`  
**Approved baseline source:** `1738478709cd8881f7ad4a524e7abbbc82b5d79c`  
**Approved source checkpoint branch:** `lock/infinity-2103401-signed-qa-20261024`  
**Successful baseline signed packaging:** GitHub Actions `40089463702`  
**Candidate target:** `2103402`, *only when implementation and gates pass*  
**Acceptance device:** Samsung Galaxy Fold 8 Ultra, Android 17 / API 37  
**Evidence:** `19999.mp4` and `Infinity-Diagnostics-20261024-152230.zip` (physical Fold, Oct 24, 2026), plus `Infinity-2103401-Fold-Observed-Corrections-20261024.md`. Retain their original hashes and unmodified copies.

## 0. ABSOLUTE AUTHORITY — ZERO SCOPE CREEP

1. **COBRA: ABSOLUTELY OFF LIMITS.** ZERO modifications to any Cobra source, resources, compiled classes/binaries, features, player, Sports, PiP, Multi-View, navigation, settings, data, or shared behavior. Verify its boundaries before/after, not just its directory name.
2. **EVERYTHING ELSE IN INFINITY IS EQUALLY PROTECTED UNLESS EXPLICITLY IN THIS BRIEF.** No broad refactors, speculative tuning, redesigns, migrations, component updates, service changes, new providers, feature removal, default changes, alternate menu behavior or generalized rewrites.
3. Changes to an adjacent/shared dependency are permitted **only if indispensable to an approved correction**, with exact producer/caller evidence, a minimal diff, before/after behavior proof, and no changes to unowned callers. If work would require modification beyond this narrow necessary dependency, STOP that particular modification and request specific authorization. Do not stall independent approved work.
4. Preserve all existing working features and approvals: Cobra, TrackIt and remembered provider routes, Search selection semantics, Search History, Search All, Universal Save for Later, Resume Hub, Continue Playing/Watching, watched state, Watchlist, Favorites, Collection, Custom Lists, Latest Releases, Quick Actions, Option B, Ambient Home, themes, rotation and playback, PiP, background-session retention, plugins/providers, Home/Diggz, UI Repair, Rails, Health Center existing features, and Essential-First durability. Existing defects within these are addressed ONLY where explicitly listed below.
5. **NO data wipe, uninstall/clean-install requirement, database reset, schema mutation, provider purge, clearing caches as a user fix, unsigned/re-signed certificate switch, unsafe version downgrade, or accidental overwrite of user profiles.** Preserve Kodi package `com.projectinfinity.kodi`, signing identity/certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`, and install-over compatibility.
6. Keep existing signed `2103401` APK, exact four delivered ZIPs, rollback notes and component receipts untouched. Current matching set: Command Center `0.3.5.35`, Watched Bridge `1.0.16`, UI Repair `0.1.18`, Infinity skin `1.0.5.242`; Rails `0.2.7` stays unchanged unless its own defect is proven to be directly within this authorization. Preserve all other active components unless a narrowly approved repair requires their update.
7. Develop only from the exact protected source on a new work branch. Do not move, reset, force-push, delete, or amend either the user's locked checkpoint or their working production branch. Keep failures and genuine measurement evidence, never manufacture a PASS or disable a gate.

## 1. SEARCH — REPRODUCIBLE NATIVE PROCESS TERMINATION (CRITICAL)

The physical recording reproduces Search History restoring **`relationship rehab`**, then Search All interaction, followed by departure to Android. The paired Android diagnostics include a **15:22:18, Oct 24, 2026** `com.projectinfinity.kodi:kodi` process exit with `Reason: signal; Status: 7`. Native last-crash text in that archive is empty. This is signal-based process failure evidence, **NOT** proof of the underlying crashing function, Scudo, or pure-virtual failure.

- Reproduce the exact History → restored query → Search All / Enter path, then individual-provider search and explicit Search-button path separately.
- Obtain Android tombstone, native crash frames, process/thread and mapped engine symbols. Distinguish SIGBUS, previous pure-virtual/Scudo patterns, GUI/Directory lock issues, and failed provider route independently. Never guess a memory-lifetime patch without stack/owner evidence.
- Fix the actual verified fault with a minimal target-only change. Preserve first-tap select, second-tap launch, hold/context semantics where applicable, explicit Search submission, query History restore without auto-run, Search All attribution and supported provider verification. One broken provider must not terminate or freeze Home.
- Preserve automatic provider inventory refresh on add-on install/enable/disable/update/remove, without stale or unverified provider routes.
- **Gate:** minimum 50 repeat Search submit/history/back cycles across representative Movies/TV/Search All/single provider scenarios on Android 17; zero reproductions of the targeted crash or Home freeze. Retain real negative controls and failure traces.

## 2. HOME LOADING & RETURN FROM PLAYBACK — VISIBLE END-TO-END PERFORMANCE (CRITICAL)

Recording: initial Home rails remain mostly blank before posters load; after Play → Stop/Back → Home, previously viewed posters vanish again and take roughly **45 seconds** to return. Brief landscape-shaped Home then portrait reflow was observed. Prior host-function speedups are valuable but do not establish screen-readiness.

- Instrument full lifecycle path: home window show/hide/onload, directory/provider refresh, card identity, artwork pipeline, job queue, caching, invalidation, orientation/reflow, and first usable/visible content timestamps. Differentiate **re-entry, new content, stale data, cold launch, genuine source change**.
- Reuse last valid in-memory/rendered Home state where safe; show existing posters/rails immediately on return, retain typed selection and scroll, and refresh only data actually invalidated (e.g. new watched progress). Do not invent stale cache or disable essential provider-refresh correctness.
- Prevent redundant reinitialization, duplicate directory jobs, repeated expensive provider verification, GUI-thread stalls and redundant artwork work **only when measured and directly linked to approved Home/Search/return defects**. Keep asynchronous artwork and bounded watched membership improvements already integrated.
- On fold/unfold, rotation, split/popup supported modes, adapt existing controls in-place rather than abandoning still-valid content. Preserve session and playback behavior.
- **Gate:** at least 30 Play → Stop/Back → Home cycles, both cold/warm paths, no unnecessary full poster blanking on warm return; target existing cached Home usable within 1–2 seconds if physically feasible (record actual percentiles, not claims). Measure comparable baseline vs candidate on the physical Fold; retain actual frame pacing and responsiveness, no frame-rate fabrication.

## 3. HOME CLOCK/TIME & POST-ROTATION REFLOW

Recording: initial Home clock displays complete `3:19 PM`; following playback/rotation it truncates `3:21…` / `3:22…`. Correct **label width, auto-width group, safe area, font metrics and reflow** for the exact user-visible clock. Preserve correct real time, updates, weather/date, moon/health indicators, theme, navigation, focus, 12/24-hour settings and every other Home element. Test folded/unfolded portrait and landscape, Stop/Back/return, supported multiwindow.

## 4. OPTION B INFORMATION — VERTICAL SCROLL & COMPACT LAYOUT

Recording shows large unused vertical space plus two scroll tracks beside the synopsis and details, including short content. Implement actual synopsis/details vertical touch/pointer/D-pad scrolling when content overflows; ensure native scrollbar controls and the Python wrapper geometry genuinely control their intended text regions. Hide/de-emphasize *unused* tracks when there is no overflow; fit short descriptions gracefully without the dead area. Preserve the complete original synopsis (no truncation), poster, title, runtime, metadata, Play/Resume/Trailer and selected-title identity. Dismiss Information back to the correct parent popup or rail with focus/scroll/selection intact. Do NOT replace generic Kodi dialogs or change Cobra.

## 5. PROVIDER CHOOSER — SIZE, LABELS & SELECTION

Recording: a short, seven-provider chooser uses near-full-height layout, cuts `Cancel` to `Can...`, and leaks literal `[/B]` markup into a provider label. Correct only the owned chooser's content-responsive height/width, wrapped/complete labels, valid markup rendering and overflow scrolling. Preserve exact verified provider identity, sort/order, tap selection/second activation and hold/context contract, cancellation semantics and focus restoration. No provider substitutions or generalized menu redesign.

## 6. PLAYER SEEK TIMES — READABILITY

Recording: elapsed and duration seek-time labels are too dark against the playback surface. Restore legible, appropriately contrasted numbers, including during seek and post-rotation, across Light/Dark/OLED and all active portrait/landscape OSD variants. Preserve seek behavior, current media/video pixels, scrub position, player rotation and existing control layout. Do not recolor the video.

## 7. PLAYER PLAY/PAUSE APPEARANCE — RECURRING REGRESSION

This is an explicitly authorized style **RESTORATION**, not a new player design. The user rejects the almost-black, dark/cyan filled Play/Pause circle and requires the previously approved clean/clear/lightly translucent control with, at most, a subtle focus glow, readable icons and consistent states.

**Source evidence:** the exact delivered skin `1.0.5.242` ZIP contains **14** `VideoOSD.xml` variants with Play/Pause control `id=202` hard-coded to `infinity_reference/button_dark.png` for both focus and nonfocus. This texture is ~241/255 opaque at its center, unlike neighboring theme-aware controls.

Restore the correct approved treatment for **all 14 actual, live** variants; verify focus and nonfocus, playing and paused, folded/unfolded, orientation and themes. Preserve control IDs, icon behavior, `PlayerControl(Play)`, accessibility and all other OSD controls. Pin exact member-level image/XML tests so a later skin update cannot silently reintroduce the dark button. Do not replace the button with an indiscriminate cyan solid circle.

## 8. SELECTED-ITEM FOCUS RETURN & CROSS-SURFACE ACCURACY

Recording suggests the focused cyan poster selection no longer visibly restores after returning from Information. Verify actual typed selected media ID, list index, scroll offset and focus—not screen coordinates. Restore the exact selection without opening a neighbor or destroying the list. Cross-check relevant Home and Latest Releases, Search results, Continue Playing/Watching, Watchlist and Save for Later **only for regressions tied to this approved focus/return contract**. Keep prior provider-independent Save for Later and TrackIt remembered-route behavior; do not rewrite those systems.

## 9. HEALTH CENTER — SPECIFICALLY AUTHORIZED RELIABILITY UPGRADE

The user **explicitly authorizes improving Health Center** so that after release it is the reliable, low-overhead source of diagnostics when an occasional bug occurs. This does not authorize changing unrelated app behavior or weakening shutdown.

- Preserve crash/ANR/native/Python diagnostics when available, including native signal exits, last active screen/action, process and version identity, and timestamps. Mark missing tombstones **UNAVAILABLE**, never 'healthy'. Avoid fabricating stack traces or silently catching fatal faults.
- After a process crash, the next successful app start should recognize an incomplete prior session without misclassifying normal Android background kills, explicit normal Close, or a successful Essential-First checkpoint. Retain abnormal-exit evidence without touching provider data.
- Make diagnostic export robust against absent/corrupt/oversized individual sections, interrupted exports, low storage, and exporter failures. Use atomic bounded collection; complete unaffected sections, report omissions and integrity checks, no unsafe recursive scanning or UI stalls. Preserve existing manual export UX when already working.
- Include bounded, useful Home/load/return/Search timing data, job queue snapshots, lifecycle transitions, player state and health receipts when available. Capture diagnostics efficiently and on demand; no always-on high-cost instrumentation. Correlate original event/session/PID, not guessed timestamps.
- Distinguish actual process exit, engine-only termination, SQLite/protected-write failures, successful Close, pending optional workers, incomplete Close and absent evidence. Retain honest status transitions and prior receipts.
- Protect privacy: no credentials, authentication tokens, provider passwords, complete user-media histories or indiscriminate account records in exports. Preserve databases and user's stored data.
- **Never relax Essential-First ownership, admission/late-write policy, protected VFS, SQLite durability, termination authorization, current anti-wipe safeguards, or timeout deadlines to make a report green.** Changes to Health Center integration must be independently bounded, justified and tested for no performance impact.
- Gate via simulated partial/crash/missing-log conditions plus real Android17 Health Center export and next-launch evidence, including one verified normal Close; do not intentionally destroy live user data or induce unapproved crashes.

## 10. COMPREHENSIVE VERIFICATION WITHOUT UNAUTHORIZED MODIFICATION

Audit the *entire* installed Infinity experience for regressions, but **fix only the nine workstreams above or indispensable direct dependencies**. In particular, preserve and test previously approved universal Search/provider refresh, Quick Actions shared selection, Option B, saved-list speedups, universal Save for Later, TrackIt remembered provider, Resume Hub/watched progress, Ambient Home, lightweight background behavior, player controls, native deadlock repair and Essential-First normal Close. Do not relabel historical known stable behavior as an unimplemented workstream.

Required testing:

1. Baseline inventory and signed source/member hashes, active versions and exact source ownership; record a change budget with permitted file paths and reason BEFORE editing any runtime code.
2. Targeted host/native/Java/DEX tests, negative controls, XML validity, independent package-diff validation; reject any unplanned source or APK member changes. No signature weakening, broad overlays or skip flags.
3. Rebuild full verified matching ARM64 native engine if native bytes change; maintain permanent signer and source provenance. Android 17 / API 37 component and integrated execution, no Android 15/11 replacement for the physical gate.
4. End-to-end Fold matrix: 50 Search cycles; 30 Playback→Home return cycles; 20 fold/rotation transitions; short and long Option B content scroll; 14 OSD variants checked by source and representative runtime modes; provider chooser labels, clock, seek contrast; preserved data and normal Close/reopen. Repeat varied conditions (themes, time, content, warm/cold, ambient Off/Subtle/Immersive where already supported) without resetting user data.
5. Measure input-to-feedback, Home usable-content readiness, cached return, frame presentation, CPU/RSS/queue and memory growth. Compare equivalent content/network/temperature/displays to 2103401; record raw measurements, median/95th percentile and failures. Use realistic sustained testing; no invented 'buttery 120fps' metrics or video forcing.
6. **Release fails if any reproducible critical crash, confirmed data loss, protected-writer bypass, Cobra/unowned diff, unwanted visual regression, major blank/Home reload, or mandatory physical check fails.** Failures stay recorded and fixes retested; do not repeatedly relabel QA packages as final.

## 11. BUILD & DELIVERY — HARD RELEASE GATE

- Only after passing the scoped repair and integration gates, deliver **one actual signed ARM64 APK** identified as candidate `2103402`, together with the **exact matching individual ZIPs** for every component changed, hashes, installed component order, build/run IDs, root cause summaries, measured before/after results, preservation receipts, and remaining explicitly unverified items. Do not distribute mismatched old component ZIPs.
- Installation must be install-over; user data and current 2103401 rollback evidence preserved. No uninstall. If a proposed rollback would require a downgrade, do not wipe data or imply that downgrade is straightforward.
- The user's physical Fold PASS is required to promote the new candidate as the final accepted production release. The user previously accepted **2103401 as their working baseline**, which does not automatically accept new 2103402 changes.
- At final PASS, commit an immutable source identity, tag/branch and separate durable downloadable artifact retention with SHA-256 manifests; report whether GitHub branch protection is actually enabled (creating a lock branch alone does not enforce branch protection). Capture a closure inventory for future narrowly scoped Health Center bug fixes.
- After acceptance, freeze feature development. The maintenance process is: observe → Health Center evidence → reproduce/attribute → smallest authorized patch → regression test → signed install-over → user PASS. **No new features or unrelated optimizations.**

## 12. REQUIRED TRACKING & REPORTING

Maintain a nine-row ledger with **EVIDENCE → ROOT CAUSE → IMPLEMENTED → TARGETED TEST PASS → INTEGRATED ANDROID17 PASS → FOLD PASS** separately. Show only true completed stages; preserve failing tests/logs. Distinguish the user-observed 2103401 Search signal exit from previously unreproduced pure-virtual/Scudo cases. Do not claim 'done' merely because source files exist or GitHub Actions packaged an APK. No speculative bypass, no starting over, no touching Cobra, no changes outside exact authorization.

**Immediate next execution:** freeze this scope and baseline identity on a new branch; import/pin the actual Oct 24 recording and redacted diagnostic evidence privately (never commit personal raw diagnostics publicly); select/reproduce the Search fault and Home readiness problem; map the exact ownership and changes; implement the smallest corrections, then proceed through the remaining approved workstreams and gates. Only authorized code is changed.