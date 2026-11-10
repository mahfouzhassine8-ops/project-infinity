# INFINITY — Owner-authorized end-to-end performance, refresh-rate, loading, UI animation and stability refresh
Date: 2026-11-10
Repository: `mahfouzhassine8-ops/project-infinity`
Work branch: `work/infinity-2103477-full-performance-ui-stability-20261110`
**Original-signed protected functional baseline: Infinity APK versionCode 2103477**
Baseline source checkpoint: `80f9c78e5c133ef63abe95af359c3e4e7366153f`
Signed77 preservation/provenance receipt: `af727772453ee32ead0e20e26d7968d2ce88142f` (read-only reference; compare exact original-signed APK members and 80/80 authenticated Command Center modules; this branch does **not** contain a rebuilt APK)
Baseline components: Command Center **0.3.5.75**, Infinity Skin **1.0.5.270**, Cobra **2103445**.
**Project status: scoped handoff + isolated branch created; implementation/build/QA NOT RUN.**
Owner intent: **Full Infinity-only** end-to-end loading, frame pacing/refresh-rate behavior, transition animations, UI refinement, speed and stability; preserve approved appearance/functionality and Cobra completely.

## Engineering authority and work separation
- **Codex** is sole source implementation, integration, focused testing, signing and delivery owner. Work from verified signed77 source/payload; measure first, then narrow/justify real changes. Changes must remain on this isolated work branch. Do not alter accepted refs or user device data.
- **GPT-6.1** independently reviews render/display refresh architecture, native/UI correctness, lifecycle, scheduler timing, cancellation, and performance claims.
- **Astra** independently reviews exact visual/layout preservation, Cobra noninterference, source+member inventories, runtime leakage/stability, original signer/package, and release/recovery evidence.
- Reviewers provide findings; no conflicting parallel edits. Do not confuse this broad *audit target* with blanket permission to modify all shared/protected components.
- Do not cherry-pick unreviewed newer networking/proxy source, rejected candidates or older UI patches.

## Critical scope boundary
- **Cobra is completely off-limits:** no source, resources, Java/DEX, player, settings, network, data, appearance, tests, dependencies or indirect shared-runtime effects affecting Cobra. The two experiences share one Android package; demonstrate ownership before changing native or Java/graphics code. **Stop and report** if proposed display, renderer or native changes cannot be proven isolated from Cobra.
- All approved Infinity 2103477 Search / Search All, native provider searches, Trakt/Watchlist, Next Episodes, Progress Shows, Continue Watching, Resume Hub, Favorites, skin layout, chooser, gestures, player/PiP/audio/subtitles, accounts, libraries, Command Center, Health Center, and persistence/shutdown **remain functionally protected**. Correct only verified defects belonging to performance/UX refresh; no rewrite of provider logic, no incompatible media/codec changes.
- **Network project remains separate and frozen.** Signed 2103478 networking and 2103479 forward recovery are issued **internal QA evidence, not approved baselines**; keep byte-identical, do not merge its IPv4/IPv6 experimental code, proxy work, DNS hooks, or its unresolved startup crash into this performance branch. Network/Wi-Fi/VPN connectivity is outside scope.
- No uninstall, clear app data, purge user/provider caches, destructive database migration, provider update, global platform settings or changes to signing identity.

## Reuse existing Infinity-only history, without assuming it shipped in signed77
- `repairs/infinity-only-performance-2103425/IMPLEMENTATION.md` on historical branch `work/infinity-only-stability-speed-from-2103425-20261028` documents bounded list projection copies, batched ListItem submission, provider inventory filtering for selected native searches, and source-aware Search cache invalidation. Some host measurements were **78.2→11.6 ms**, explicitly **host projection only** (NOT real device FPS/startup or proof of current77 behavior). Inspect signed77 current source and retain already-implemented improvements; don't duplicate or roll back.
- `repairs/infinity-seamless-loading-2103433/APPROVED-UNIVERSAL-ACTION-LOADING-20261030.md` documents **owner-approved** restrained cyan perimeter loading on the actually selected item, with top-left drawer/menu cyan-frame fallback for background work. No giant center spinner, floating busy panel, fake percent/ETA, or layout redesign. `CHECKPOINT-REJECTED434.md` retains why rejected loading snapshots failed; do **not** revive rejected designs.
- 2103477 has newer approved skin, Command Center, resume/search/tracking and UI; older branches are **references**, never production source of truth.

## Stage 1 — one genuine signed77 baseline audit, not assumptions
Inventory actual operating paths and measure reproducibly on *the signed77 input*, not the unaccepted network78 or host-only old snapshots:
- Cold and warm launch to first usable Home, skin initialization, splash, first drawn UI, first artwork, async worker occupancy and blockers. Separate codec/source/network variability from UI readiness.
- Frame pacing in Home/rails, fast vertical/horizontal scroll, drawer, System Hub, menus, modal details, search results, seasons/episodes and transitions; distinguish latency, stutters/dropped frames, long frames, FPS and display **Hz**. Record front vs unfolded Fold dimensions, rotation/fold and light/dark where test environments support them.
- Measure selected views' input-to-feedback latency, native queue depth, memory PSS/RSS, temporary allocations, FD/thread/task growth, CPU/battery impact and thermal-limited behavior where measurable. Report missing sensor/device measurements as NOT RUN, never estimate a PASS.
- Capture present loading ownership: user-selected tile vs global drawer, loading visibility, source-ready/completed-empty/error/timeout/cancel/Back, fast repeated taps, stale result callbacks, artwork/list updates. No extra polling services.
- Inspect actual 2103477 problems before deciding what to change. Baseline evidence and comparison must identify file/function or UI control and affected feature. Do not treat normal provider latency or old DNS cleanup as app rendering fault.
- Produce a prioritized before/after measurement matrix and proposed minimal patch diff, with no decorative redesign.

## Stage 2 — authorized Infinity-only improvements, only where evidence supports
1. **Refresh-rate / frame pacing:** Query device-supported Android display modes rather than hardcode 120Hz. Optimize GUI scheduling, render invalidation/coalescing, animation frame pacing and interaction latency. Avoid busy frame loops, forced high refresh in idle/background, battery/thermal regression, and changes to movie/TV 24/30/60fps cadence or video auto-refresh-rate matching. Do not change Android-wide refresh defaults. When only a shared renderer can change, stop until Cobra isolation is proven or owner grants a narrower exception.
2. **Loading:** Use approved cyan perimeter on selected Infinity elements; drawer frame for background/global work only; no misleading percent or artificially delayed navigation. Require real owner token, completion/error/cancel/late-callback cleanup; keep original provider routing/action semantics, avoid double invocations, prevent indefinite spinners, keep Home touch responsive.
3. **UI/motion polish:** Smooth **existing** transitions, selection/focus feedback, modal opening/closing, scroll and list/card animations within current locked layout, sizing, theme and Fold responsive geometry. Respect reduced motion/power savings when available. Do not remove or rearrange approved controls, change posters/cast/synopsis, or replace existing icon/theme colors unless a measured/visible defect requires a scoped correction.
4. **Performance:** Remove confirmed redundant work; reduce critical-path synchronous I/O/duplicate ListItem creation/cache misses or unnecessary artwork decode only after validating behavior. Keep cache correctness and provider settings-sensitive invalidation. Do not silently change network timeouts, source selection, provider request volume, playing-item construction or watched/tracking semantics.
5. **Stability:** Fix demonstrated Infinity-only ANR, stale callback, cancellation, resource leak or race within authorized paths. Preserve pending operations and authenticated module/persistence rules. A crash with no causal stack is an investigation, not license for speculative native allocator/thread/lifecycle patches.
6. **User-facing error behavior:** Preserve actual error messages and Retry/Back, don't bury failed fetches under endless animations.

## Stage 3 — focused *end-to-end* selected-feature acceptance
Owner authorized this **Infinity performance/UX scope**, not indiscriminate testing or mutation of unrelated modules. Register the exact selected cases before executing, use the permanent `AGENTS.md` + `docs/INFINITY-FOCUSED-TESTING-POLICY.md`:
- Cold/warm home usable, one/two background artwork/list refreshes, front/inner transitions, pre-/post-scroll frame pacing in selected screens, input latency after rapid taps, zero double navigation, Back/cancel/error/empty/late result.
- Search All/results, saved-TV/Progress Shows/Next Episodes/Continue Watching, representative provider transition and normal playback **preservation smoke checks** only, with existing independent provider/network paths untouched. Do not require a provider to be online for UI frame pass.
- Verify frame rate and screen refresh independently, correct 24/30/60 video pacing, foreground/background/thermal behavior and reduced-motion preference, no unintended Cobra impact in protected member/source diffs.
- Repeat affected interactions for leaks/thread/FD creep and real cancellation. Record actual source, APK, run and all pass/fail/not-run cases. Host and emulator PASS is not physical Galaxy Fold acceptance.
- **No shutdown/Normal Close/Essential-First test or shutdown source mutation** without a new explicit owner selection; this is a permanent separate gate. Do not slip shutdown suites into setup or teardown.
- **One consolidated on-Fold test requested by owner**, after scoped engineering evidence. Avoid a sequence of half-finished APK tests.

## Stage 4 — release only if integrity/scope gates pass
- Reconstruct from **exact original-signed2103477** source+payload and validate 80/80 authenticated CC75 files, Skin270 and Cobra3445. If source identity mismatch, stop; do not substitute old77 metadata-only branch as APK.
- Reconcile currently issued **2103478/2103479** with canonical registry, reserve next genuinely unused versionCode(s) strictly higher (e.g. 2103480 only if proven free; never assume/reserve prematurely). Existing 78/79 must remain frozen and unaccepted.
- Complete selected ARM64/Android build/checks, protected file/DEX/native exports and original signer+package, persistent data install-over, exact hashes; prepare matching higher-numbered **forward recovery** restoring approved77 functionality without clearing user data.
- Deliver **one** signed combined owner QA APK, source/evidence/sha256 and matching recovery only when gates are complete; accurate NOT RUN and blocker reporting. No final lock without owner Fold acceptance.

## Requested Codex first report
Give a concise baseline-first decision: actual signed77 paths, current measured top bottlenecks (or NOT RUN), previously implemented/rejected work not to redo, minimal proposed changes categorized by rendering/loading/UI/stability, exact selected tests, and any source areas that cannot be changed without affecting Cobra. Then implement only supported scoped corrections; no unrelated networking work or release claim.
