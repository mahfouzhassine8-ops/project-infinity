# INFINITY — FINAL CONSOLIDATED CLOSURE RELEASE BRIEF

> **REVIEW-ONLY HISTORICAL SCOPE CHECKLIST — SUPERSEDED FOR GPT-6.1 EXECUTION.**
>
> The single authoritative engineering brief is:
> [INFINITY-GPT-6.1-FINAL-END-TO-END-CORRECTIVE-20261025.md](INFINITY-GPT-6.1-FINAL-END-TO-END-CORRECTIVE-20261025.md).
> Its baseline is the passing-only 2103407 signed-source reference, with a separate passing receipt. **Do not work from this older checklist or treat every listed issue as passed.**
>

**Scope frozen by user on October 25, 2026.** One final corrective, consolidation, speed and visual-polish release for phone Infinity. Complete and physically accept it, lock Infinity, then move to separate Cobra work only upon new explicit authorization. No further feature additions, repeated diagnostics-only releases or speculative redesigns.

**Repository:** mahfouzhassine8-ops/project-infinity
**Frozen, signed working reference:** Infinity 2103407, build commit 0e8739d2d0e1be0ab8f127519b526556426fb160, successful GitHub run 40230842944.
**Permanent signing certificate SHA256:** d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7.
**Working installed component reference:** Command Center 0.3.5.39, Watched Bridge 1.0.20, UI Repair 0.1.22, Skin 1.0.5.243. Existing Rails remains protected.
**Additional signed references:** 2103406 (run 40191243446; SIGABRT recorder improvement); 2103405 (run 40184543219; user-confirmed WatchNixtoons2 Infinity Tracked).
**Final acceptance:** Samsung Galaxy Fold 8 Ultra SM-F976U1, Android 17 / API 37. Verify physical folded/unfolded, portrait/landscape, compatible popup/multiwindow, and Light/Dark/OLED scenarios.
**Current Search result:** User subjected signed 2103407 to about one minute of severe Search overload and reported no crash; a provisional positive physical stress result, not proof every native fault is gone.
**Status:** THIS FILE IS A DESIGN/SCOPE HANDOFF, NOT AN IMPLEMENTATION, NEW APK OR USER ACCEPTANCE.

## 0. Absolute preservation and closure rules

1. COBRA IS 100% OFF LIMITS. No Cobra source, binaries, resources, player, PiP, Sports, Multi-View, activity, settings, shared runtime behavior or styling changes. Independently compare Cobra-affecting APK code and runtime behavior.
2. Preserve signed 2103407 and its corrected global Search request single-flight admission, Search All, provider-specific Search, Search History, provider inventory, selection, keyboard/IME, and user-confirmed Fold test. Do not re-open a working feature without evidence of a regression.
3. Preserve the user-confirmed working WatchNixtoons2 native Infinity Tracked context menu, Kodi/provider native menus, Otaku, Favorites, Resume Hub, Continue Playing/Watching, Watchlist, Collection, custom lists, universal Save for Later, remembered provider routes and watched sync. Never resolve a title by an unverified similar name or stale provider URL. Existing compatibility with future providers is a requirement, not an invitation to add provider-specific exemptions.
4. Keep package com.projectinfinity.kodi, original release signing certificate, profile databases, local watched data, settings, sources and provider installations intact. INSTALL OVER ONLY: no app uninstall, no clearing data, no clean reinstall, no unauthorized migration, no downgrade requiring data deletion.
5. No new features after this freeze. Only previously approved issues in this document and their demonstrated direct dependencies may be corrected. Avoid rebuilding unrelated areas simply because this is labeled final.
6. Develop on a new corrective branch starting from the exact working signed reference, with an allowed-file/member ledger and rollback. This document is intentionally committed only on a separate planning branch, with no current production code changes.

## 1. Unified Command Center — one brain, coherent updates

**User goal:** One Infinity Command Center orchestrates Search, Resume Hub, watched/tracking, Infinity Movies/TV navigation, UI fixes, Rails, user selections and first-party persistence. Updating Command Center-owned Python behavior should normally require one Command Center update, not separate coordinated Watched Bridge / UI Repair / Rails ZIP installations.

- Inventory current first-party addon entry points: Kodi script/plugin/service/context menu declarations, Rails, UI Repair, Watched Bridge, related windows, controller preimage hashes, native immutable source hash slots, data owners, installed aliases and icon/XML references. Preserve compatibility with installed data and Kodi entrypoint requirements.
- Integrate capabilities as independent internal submodules and bounded execution owners under Command Center, not one fragile monolithic long-running task. Eliminate duplicate app services, competing persistence writers, duplicate menus and helper version skew.
- Migrate existing progress/watched/favorites/watchlist/custom lists/Rails order/search selections/settings safely in place with checked reversible contracts. Never drop data or reset a profile when a compatibility check fails.
- The actual 2103407 native engine contains immutable source hashes, and Watched Bridge/UI Repair verify full Command Center source preimages. Design an authenticated, versioned compatibility manifest that retains **real** source integrity. Never disable the native ownership guard or accept arbitrary unknown Python files just to ship one ZIP. Change native verification only with reviewed, compiled, signed native code when indispensable.
- Distinguish user-facing Command Center version from stable **shutdown protocol** version; a minor Command Center revision must not silently invalidate the resident shutdown participant.
- Retain the Infinity Skin as an independently versioned visual/XML layer, updated only when an authorized skin correction requires it. Keep the Kodi native APK independent. During the one-time integration, any still-required Kodi shim may remain internally coordinated without a recurring multi-ZIP manual install burden.
- Acceptance: every old route, registered menu, rail, tracked action and native data owner works; no double starts or duplicate active writers; one coherent version contract and install/update path. Full Fold persistence/shutdown coverage is mandatory.

## 2. UNIVERSAL system-wide touch, focus and context menu

**This is an ALREADY APPROVED system-wide contract, not a new feature and not a separate patch per screen.**

Applies to actual **Infinity Movies and Infinity TV** views and their content cards (not Kodi standard Movies / TV Shows library views; not the separate 32-bit onn television fork); also Home rails, Continue Playing, Continue Watching, Watchlist, Favorites, Save for Later, custom lists, Search results/provider tiles, Latest Releases, Video Sources/All Add-ons and applicable addon/provider listings including Otaku and WatchNixtoons2. Cobra inputs remain wholly untouched.

Contract:
1. First touch/tap focuses and highlights the EXACT touched item, without opening playback or a neighboring tile.
2. Second deliberate tap activates that selected item's EXISTING route. For Search provider tiles, retain approved provider selection vs explicit Search submission; selecting a History query repopulates the field without auto-running it.
3. One press-and-hold selects the exact touched item and opens its correct Infinity/Kodi/provider context menu ONCE. Never accidentally play, dispatch two contexts, open an unrelated generic narrow black popup or dismiss to a different item.
4. The menu exposes **all applicable authorized actions**: Infinity Tracked, watched/unwatched, Watchlist, Collection, Save for Later, Favorites, custom lists and original provider-native operations where supported. Action visibility must be based on verified media identity/provider capabilities: do not fabricate IDs/routes or remove otherwise valid generic context actions merely because TMDb metadata is absent.
5. Dismiss/Back restores exact title/source, typed selection, list index, scroll and prior window/provider. Preserve stability after rotate/fold, touch scroll, dialog dismissal and re-entry. Keyboard/D-pad semantics remain compatible.
6. Implement ONE policy/dispatcher with per-control adapters for native touch translation, Kodi container/window dispatch and Command Center's media capability routing. Testing a helper function by itself does not count as physical UI acceptance.
7. USER-CONFIRMED FAILURES: press-and-hold NOT WORKING inside Infinity Movies and Infinity TV. Other previously reported issues: tall/narrow black popup on Rails; inconsistent provider/Favorites/All Add-ons hold, wrong focus after dismiss, context menu placement/overlap and first-tap premature activation. Do not confuse the named Infinity routes with Kodi generic library screens.
8. Preserve user-confirmed working WatchNixtoons2 native Infinity Tracked context registration exactly, and preserve other successful provider menus. Any narrow native input change requires independent proof Cobra behavior is completely identical.

Acceptance: use real Android 17 touch gesture tests on every listed view, positive/negative controls, slow/fast taps, scroll-then-hold, long hold after fold/rotation, exact selected data identity, no accidental player launch, all appropriate actions and correct return focus. Test physical menu, not just source callback.

## 3. Loading speed, content refresh, frame pacing and high-refresh display

Both requested senses of refresh are in scope: **provider/data refresh correctness** and **display refresh/frame smoothness**.

- Cold launch: measure elapsed to first usable Home, posters, rails, Search, provider inventory and responsive tap; trace only necessary stages (Kodi UI init, metadata, artwork, provider inventory, Python worker queues, layout/focus and pending refresh).
- Warm return after movie play/stop/back: retain valid Home posters/list data/scroll/selection; re-render without a redundant full provider query, blank rails or 45-second poster reload previously reported. Target 1–2s usable warm Home where physically possible, but record actual latency and failure rates instead of claiming it.
- Refresh provider registry on install/enable/disable/update/uninstall, and update recently watched/resumed, Save for Later, Latest Releases, Search result metadata, rail and artwork changes without stale or mismatched identity. Use accurate cache invalidation, bounded in-flight work and per-view diff refresh, not disabling necessary provider verification.
- Optimize actual scroll/gesture response, popup transitions, keyboard appearance, orientation/fold reflow and theme parity without UI-thread waits, background request storms, repeated cache misses or unbounded worker pools.
- Measure supported and actually active Android refresh modes, real frame times/dropped frames/jank under light/dark/OLED, Fold orientations, power/thermal limitations. Improve pacing at the real permitted panel mode, including higher-refresh modes when available. Do **not** force 120Hz, override power saving, artificially speed video, recolor playback or assert an FPS metric without measurement.
- Compare equivalent baseline vs candidate: first usable card, poster-ready, warm return, cold launch, provider inventory, input-to-feedback, frame p50/p95, dropped-frame percentage, CPU/RSS and memory growth. Attribute regressions to specific work, no synthetic "buttery 120fps" claims.
- Gate: at least 30 playback/Home cycles, 20 fold/rotation/window changes, both cold/warm paths, substantial scrolling/gestures and provider change/freshness tests. No user-visible blank Home or regressions under ordinary use.

## 4. Essential-First Shutdown 2.0 — strengthen ownership, universal provider isolation

Required final release gate, notwithstanding the user's earlier decision to defer shutdown until other polish. Current 2103407 shutdown has NOT PASSED.

- FIRST repair the **confirmed Command Center mismatch**: Command Center addon.xml is 0.3.5.39 but the installed checkpoint_runtime.py expects 0.3.5.38. Prove registration/prepare/finalize/receipt against the native Android checkpoint after installing unified Command Center. Prevent recurrence with explicit capability-based shutdown protocol negotiation rather than exact user-facing addon version equality.
- Essential first: block **new optional** work without blocking accepted essential saves. Capture final playback position and watched/completion before releasing player state. Durably save Command Center/Resume Hub, watched/favorites/watchlist/history/custom lists, Kodi and skin/addon settings, profiles, source/playlist changes and required native databases/SQLite WAL under checked write admission and transaction/barrier owner proof.
- Rework stage ordering so an optional third-party Python interpreter that is merely alive does NOT have to exit before native/settings/first-party essential checkpoint phases. Separate service lifetime from actual protected write ownership; use a universal observer and durable ledger across any newly installed addon.
- Differentiate (A) required/shared protected transactions, (B) optional third-party private user state, (C) disposable provider cache/network/metadata/EPG activity and (D) unknown/unobserved writes. Do not promote (D) to harmless. A third-party active service alone is not proof that essential state is unsafe; a third-party outstanding **shared protected** write must still block or be safely drained.
- When genuine essential and shared writes are safely sealed, native/Android can authorize whole-process termination without waiting for idle third-party threads to finish. Do not destruct Kodi C++ state underneath active foreign Python threads. Document the unavoidable caveat that terminating a process can interrupt unsaved *private* third-party data; it is impossible to promise arbitrary unknown third-party add-ons perfect data durability.
- Preserve exact authoritative PID/engine owner/session/generation, one-shot authenticated Android termination, actual process-death verification, correct WAL/db/fsync/readback receipts, failure/rollback and truthful reporting. **Never** increase the 25s deadline as the substitute for correcting ownership; never mark 17/17 saved when only the essential subgroup is proven, never bypass unknown shared writes or silently kill essential data.
- Keep a truthful distinction between essentials safely committed with optional work unfinished and full graceful all-participants completion; failed or unverified essential save must fail closed with precise path/operation/owner.
- One unified Command Center persistence participant, no extra independent UI Repair/Watched Bridge/Rails essential owners or duplicate writes.
- Mandatory physical Fold: at least three close/reopen sessions after real mixed use, idle/active provider, rapid Search, active playback, watched progress, settings/favorites edits, third-party optional hang, shared database write and injected failed commit/fsync. Confirm real protected data identical after reopen and native one-shot authorization + actual PID death only when safe.

## 5. Already discussed final UI corrections, no redesign

- Preserve liquid-glass Light/Dark/OLED themes and correct small Infinity Home logo to right of title (without legacy numbers next to Infinity).
- Home clock/time truncation after playback/rotate; preserve date/weather, supported fold/orientation reflows and selected Home item.
- Option B Information: correctly sized synopsis and actual vertical scroll, no phantom/double scrollbars or wasted tall empty region; Back restores exact title and scroll.
- Provider chooser and popup: compact height; full Cancel labels; prevent literal markup like [/B]; correct touch bounds/anchor and focus; no colliding Add-on Information, Health Center or ZIP-preview panels.
- Restore approved clear/lightly translucent Play/Pause OSD, not dark/cyan filled circle; correct Rotate button if replaced by Repeat, remove previously rejected Display Mode option, make elapsed/duration seek numbers readable in all orientations and themes, preserve upper-right time after stopping.
- Universal watched state, Continue Playing and Continue Watching navigation, saved-list identity, select/dismiss focus, provider source route and already-approved Ambient Home need complete regression coverage, NOT speculative rewrites.
- Keep Health Center useful/low-overhead for native/ANR/Search/close evidence; missing tombstone = unavailable, not healthy; atomic redacted partial export; preserve crash history and do not overload UI or weaken shutdown protection.
- When an earlier defect is already physically fixed in 2103407, classify it as PASS/PRESERVE, not another task to rewrite.

## 6. Full release verification and lock

1. Preserve user-accepted signed 2103407 reference, source, components and SHA/cert, and compile on separately isolated final work branch; keep signed 2103405/2103406 references for troubleshooting. Report permitted changed APK members and true native code deltas.
2. Gate each item in a ledger: SOURCE CONFIRMED -> REPRODUCED -> FIX IMPLEMENTED -> HOST VERIFIED -> INTEGRATED ANDROID17 VERIFIED -> FOLD PASSED. A source commit or GitHub success is not a device PASS.
3. Universal long hold: exact item and menu across all approved named Infinity views, 2-tap launch, provider context and focus; Search: 50 repeat/overlap/busy/History/provider cycles; UI: fold/reflow and menu negative controls. Preserve WatchNixtoons2 Infinity Tracked.
4. Speed and visual: 30 play/stop/back Home tests, 20 fold/rotate/multiwindow cases, real warm/cold load timing, native frame-time/jank/Hz readings and Light/Dark/OLED OS D visual checks. No invented performance improvements.
5. Shutdown: three or more real essential-first close/reopen cycles, safe and injected error paths, third-party optional idle/hang vs shared write obligations, correct one-shot process-death evidence and durable saved state. Exact owner receipts mandatory.
6. Zero Cobra changes; no broken player, skin, providers, Search, watched, Favorites, data, essential protections or forced reinstall.
7. Build one full permanently signed ARM64 install-over APK IF native/Android changes are required; migrate helpers to a **unified Command Center** and deliver its one coherent ZIP (separately only if needed). Skin ZIP only if the user's approved visuals require a changed skin. Do not force user to manage old Rails/UI Repair/Watched Bridge ZIPs for every new Command Center Python fix after migration.
8. Release needs the original certificate, APK/component source-integrity receipts, native compilation and signature verification, physical Fold acceptance, measured before/after performance and exact remaining limitations; explicitly report if any gate is unverified.
9. No final label or lock until user says physical PASS. Then tag immutable release source/assets/checksums, retain rollback, freeze Infinity feature development and start Cobra only under a separate directive. A branch named lock is not proof that repository branch protection exists.

## 7. Honest workstream ledger as of scope freeze

| Workstream | Present state | Final acceptance requirement |
|---|---|---|
| Search under overload | Signed 2103407 single-flight correction; user reports ~1 minute stressful Search without crash | Extended no-crash Fold stress/regression, preserve current behavior |
| Unified Command Center | Not implemented; helper ZIPs remain separate | Single brain, coherent update and integrity contract, zero data loss |
| Press-hold and contextual options | User CONFIRMS broken in Infinity Movies and Infinity TV; fragmented elsewhere | One system-wide touch/context contract across real views |
| Loading speed and provider refresh | Partial earlier cache improvements; end-to-end speed not physically quantified | Faster verified cold/warm readiness, accurate freshness and smooth UI |
| Physical refresh and frame pacing | No trusted physical FPS/frame metrics yet | Real frame/refresh improvement measured on Fold |
| Essential-First Shutdown | Confirmed Command Center 0.3.5.39 vs 0.3.5.38 mismatch and lingering Python writers; recurring 25s deadline | Stable protocol, essential-owner real writes, safe optional worker isolation, successful Fold close/reopen |
| Previously approved UI polish | Some corrections previously shipped, incomplete final on-device matrix | Restore identified visual/OSD/popup/focus regressions, no redesign |
| Final package and lock | Not built / not accepted | Full signed integration, device QA, user approval, source lock |

**FINAL FENCE:** This document consolidates previously authorized corrections and the user's explicitly requested loading speed/refresh smoothness. No further Infinity feature program or scope additions are authorized. Creating this file modifies no runtime code, APK, addon component, or user data.
