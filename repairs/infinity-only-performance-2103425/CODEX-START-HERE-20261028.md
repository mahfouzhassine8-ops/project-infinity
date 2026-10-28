# CODEX — Infinity-only stability, loading, responsiveness and performance corrective

**User authorization:** PROCEED — investigate, implement narrow verified fixes, instrument, compare before/after, and prepare ONE original-key signed install-over candidate. Do not stop at an audit or produce speculative optimizations. Do not promise performance before runtime evidence.

**Repository:** mahfouzhassine8-ops/project-infinity
**Engineering branch:** work/infinity-only-stability-speed-from-2103425-20261028
**Immutable, user-approved combined baseline ref:** lock/infinity-cobra-2103425-fold-approved-chooser-20261028
**Exact original-key signing source/locked starting commit:** db730100a3bfea7e06d2e6c3434e89aeb6fa8a15
**Signed gate success:** GitHub Actions 40606707330. Signed candidate and component artifacts available there.
**Historical Infinity-only rollback ref:** lock/infinity-2103420-user-approved-baseline-20261026 at 883c64a4de6f87077893921454de71bba850235b.
**Combined app version accepted for chooser:** 2103425; chooser displays Infinity last updated 2103421, Cobra last updated 2103423, app version 2103425. The chooser physical Fold visual/behavior test passed. That acceptance does NOT mean this performance corrective has passed.
**Physical acceptance device:** Samsung Galaxy Fold 8 Ultra / Android 17 / API 37. Preserve user data; install OVER existing APK only.

## Absolute ownership and preservation

1. **Only owner INFINITY may change.** Keep the exact Cobra component, Cobra runtime behavior, chooser shell, app/container/shared Android contract, certificate, package identity, launch mode, and existing version labels byte-identical. The combined 2103425 snapshot and old 2103420 snapshot must not be moved or edited. Do not edit the combined signing authority merely to force a green build. Use the existing owner-aware assembly and pre-sign gate when authorized implementation is ready.
2. No Cobra source, classes, resources, settings, background service, navigation, PiP, player, Multi-View, Sports, or cross-owner calls; no chooser redraw, popup redesign, UI theme redesign, new feature, manifest migration or experimental app icon. A proposed fix requiring a shared runtime, native library, unowned boundary or protected lifecycle edit **must stop that subchange** and identify the exact owner conflict for separate user approval.
3. Preserve ALL Infinity behavior: Kodi and skin IDs; Search first-tap provider selection/second deliberate search/hold; Search All; History repopulate; Favorites, Watchlist, Collection, Save for Later, Continue Playing/Watching; tracked/source identities, playback/Resume/PiP; per-profile databases/addons/settings; Light/Dark/OLED themes; Rotate and non-cyan player controls; Option B vertical text; clocks; every already-working provider including Umbrella, Seren, Otaku, WatchNixtoons2, POV and the existing handling of other installed providers. Never guess routes or show fictitious results. Do not overwrite newer watched/progress state with cached data.
4. Essential-First Power/Close, native/Java writer fences, protected persistence, shutdown owner accounting, and all receipt/termination behavior remain **frozen**. Do not run new shutdown tests, embed shutdown in feature setup/teardown, or make it a packaging prerequisite. Immutable-source/member comparison is permitted.
5. No uninstall, clean install, clear-data action, cache purge as a fake fix, database reset, download of untrusted binaries, certificate swap, downgrade, or repeated diagnostic APK installations. No global worker-limit change that could block legitimate playback, saving or another experience.

Read before coding: top-level AGENTS.md and docs/INFINITY-FOCUSED-TESTING-POLICY.md; repairs/dual-experience-isolation-2103420/DATA-AND-LIFECYCLE-CONTRACT.md, release-authority.json, release_gate.py, component_bundles.py, ownership-reviewed-roots.json and current owner inventories; repairs/infinity-final-closure-2103407/WORK-P0-FINISH-MISSING-IMPLEMENTATIONS-SHUTDOWN-FROZEN-20261026.md, SEARCH-CACHE-418-PLAN.json, PROVIDER-CACHE-DEPENDENCY-PLAN.json, RESUME-RENDER-HOST-MEASUREMENT.json, EXACT-SOURCE-HOST-MEASUREMENT.json, NATIVE-STARTUP-419-RESULT.json, and current signed-bundle actual member contents. Older historical documents are evidence, NOT authorization to mutate the protected current APK.

## Historical observations — hypotheses to verify, NOT present-day performance claims

- Physical Fold with earlier 2103410: first Resume/Continue usable card samples about **0.55 s, 1.68 s, 10.23 s**; slow sample ~10.17 s native directory fetch while 41–42 jobs were queued; another queue reached ~114. Re-measure on unchanged 2103425; do not assume identical results.
- Earlier Home had a redundant absent PlaylistBrowser helper invocation costing 24.163 s. A conditional invocation fix was made in 2103419: retain and verify its integration rather than reintroduce or duplicate.
- Prior **host-only** per-render source memoization for eleven cards improved median 8.26 ms -> 4.27 ms; this did not establish fast physical Home or native request performance. Prior provider source-verification host performance similarly does not prove physical FPS/temperature.
- 2103418 Search added a bounded four-entry per-provider response cache within a strict 300000-byte property budget and 300-second original-answer TTL, preserving profile, source, route, lease and stale-result checks. Do not casually broaden invalidation or disable trusted-source checking.
- Earlier Android17 emulator runs experienced some Search keyboard timeout/native provider timeouts, rising PSS and native heap, and emulator early native constructor failures. Search SIGBUS was also reported on the actual Fold in earlier iterations. Treat failures as distinct; obtain a matching build/stack before assigning cause. Host memory growth is not automatically a leak or the Fold behavior.
- Strict 16-KiB-page emulator failures and many 4-KiB-aligned ELF libraries were documented earlier, but physical Fold page size was not established. Do not rebuild shared native/Cobra merely to satisfy an unsupported synthetic emulator; if actual target hardware needs it, disclose a separate owner-sensitive blocker.

## Engineering deliverables (complete in the following order)

### A. Establish an honest 2103425 baseline and first-usable performance trace
Trace separate monotonic intervals: icon tap -> chooser visible/selection -> Infinity engine ready -> Home first interactive frame -> verified first selectable local Continue movie/TV card -> artwork first decoded/drawn -> provider refresh completion; separately trace Stop/Back->Home with and without recent progress updates. Never include chooser dwell or screenshot/proof analysis time in a claimed render-time measurement.

Identify main/UI-thread blockers, native queue scheduling, duplicate directory requests, observer lifecycle, image decoding/cache misses, first-party module verification, profile and provider path validation, and precise invalidation triggers. Record before metrics (median/p95 and samples where possible), queue depth/age, request count, UI frame duration/jank, CPU and memory growth, load spikes and effective display refresh rate, with power-saving/thermal conditions recorded. A local cached card may appear first only if its identity, watch/progress and source state are confirmed safe.

### B. First-viewport/local-first Home + real Continue cards — priority 1
Ship a correct, actionable first viewport from verified per-profile local saved state without waiting on unrelated provider/network/metadata/poster work. Preserve movie/TV/season/episode identity, seek position, watched/complete rules and no autoplay. Defer non-visible enrichment and artwork, coalesce identical jobs, bound cache memory and enforce TTL/source/profile/revision checks. Invalid or unavailable provider routes must remain visibly honest. Incrementally update visible cards on native provider completion; stale asynchronous results must not replace fresher watched/progress updates. Correctly invalidate on Stop/Back, watched changes, saved actions, provider enable/disable or reinstall, profile changes and Latest Releases changes. Do NOT patch only a fixture/mock or return a placeholder as a successful card.

### C. Native queue, Search/IME and worker lifetime — priority 2
Reproduce measurable queue contention without amplifying background jobs. Classify and limit redundant nonessential provider/metadata/image work on the first-viewport critical path, but preserve user-initiated search, playing media, cancellation, protected writes and owner leases. Inspect actual process-wide Search admission/response identity and API37 Enter/IME routing. Prevent duplicate Enter, stale result publication, orphaned invokers, cancellation races, unsafe reuse after interpreter exit, main-thread blocking and cross-owner effects. Preserve truthful timeout/unavailable errors; don't hide failures by blanket timeouts or catch-all retry loops. Native SIGBUS/SIGSEGV/ANR fixes require a matching causal trace, not a guess or blind allocator patch.

### D. Playback-return caching, browsing, smoothness and thermal — priority 3
Avoid full Home/skin/rails reconstruction after a routine Stop/Back if the current screen remains valid. Apply targeted revisions for actual changed playback/watched/list state. Keep selection, scroll, focus, resume, artwork and rendered surfaces stable when appropriate through navigation/rotation/fold transitions. Bound image decode size/retention and offscreen metadata fetches; avoid unnecessary repeated verification or idle polling; eliminate repeated duplicate expensive native/Python work. Measure dropped frames and touch-to-visible response at the ACTUAL effective refresh rate (Power Saving may reduce it). No forced 120Hz, video recolor, timer abuse or invasive UX changes. Investigate resource/heat growth without undermining protected worker/persistence duties.

### E. Selected, non-shutdown verification only
Authorized focused checks:
- Source/APK owner diff and signed preservation: exact Cobra, chooser shell and shared-contract hashes unchanged; no protected close/receipt code mutated; no original signer/package/data migration weakening.
- Home first-viewport and Continue movie+TV: real local selectable card, exact ID/source/progress/watched, first artwork and no autoplay, cold vs warm, source absent/slow/disabled and profile changes.
- Playback -> Home: repeated Stop/Back without full reset, refreshed watched/progress, no stale card and no destroyed focus/scroll.
- Search: actual Enter/IME, Search All and selected provider, rapid cancel/Back and old-result return, valid source and timeout classification, bounded native queue/worker cleanup.
- Render/memory: finite representative scroll/card and fold/rotation view checks, frame-time/memory/queue comparison with power-saving state documented.
- Existing focused release-gate, source signature/inventory and install-over checks for the modified INFINITY component only.

**EXPLICITLY NOT SELECTED:** any shutdown tests, synthetic full 50/30/20 stress matrix, repetitive installer APKs, destructive data operations, unrelated Cobra/chooser testing or schema migrations. Do not relabel an unexecuted test PASS.

### F. Delivery contract
1. Produce the minimum actual production edits required, with each touched file/member mapped to owner INFINITY, before/after reproduction, reason, selected test and regressions checked. Preserve unmodified members byte-for-byte. If the only feasible fix crosses the shared owner boundary, stop that fix and report exact conflict; finish independent Infinity changes if possible.
2. Attach a concise report: before vs after on the same code/device/conditions, p50/p95 cold/warm Home/Continue/poster and playback-return where measured, queue/redundant job counts, memory/frame measurements, remaining failures, Android emulator vs physical Fold distinction, expected versus actual improvement. Do not invent a measured FPS/speedup.
3. Route final approved owner changes through the existing signed combined build gate, increment Infinity component version/app version properly without replacing unchanged Cobra/chooser versions, and generate ONE original-key-signed install-over APK plus truly matching component ZIPs, SHA256, source commit and release workflow URL. Do not promote 2103425 acceptance or the immutable rollback pointers during engineering.
4. Deliver exactly one final physical-Fold candidate after focused implementation and signing checks. Physical acceptance remains the user's decision; no claimed Fold PASS merely from CI. If signing cannot be legitimately completed, state the blocker and do not provide a dummy APK.

## Execution discipline

**Not a research-only or instruction-only assignment.** Begin with source/APK evidence and instrumentation, implement proven Infinity-only bottlenecks, use only the selected checks, and prepare the final candidate. Keep all changes on the new engineering branch until reviewed; never auto-merge into an accepted lock. Cite concrete GitHub commits/runs/artifacts. Do not request repeated user uploads or experimental installations to compensate for host setup problems. 