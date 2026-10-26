# INFINITY — GPT-6.1 FINAL END-TO-END CORRECTIVE, CONSOLIDATION & RELEASE HANDOFF

**PREPARED FOR GPT-6.1 — FINAL FROZEN SCOPE.**
**Current authorization:** The user authorized preserving known-good passing work and preparing this execution brief. Source implementation, builds, and any final lock must remain subject to the user's explicit execution and final physical-acceptance gates. Do not silently expand scope or claim a completed final APK because this document exists.
**Mission:** Complete exactly the previously approved Infinity corrections in ONE final integrated release, prove their real Android 17 behavior, deliver the actual permanently signed ARM64 install-over APK with its genuinely matching required components, and ask the user to verify on the physical Fold. After explicit acceptance, lock Infinity and leave its feature set closed.

## A. FIXED REPOSITORY, BASELINE, AND PROVEN WORK — DO NOT START OVER

Repository: mahfouzhassine8-ops/project-infinity.
Frozen signed working base: Infinity 2103407.
Exact production QA source commit: 0e8739d2d0e1be0ab8f127519b526556426fb160.
Passing-source checkpoint ref: lock/infinity-2103407-proven-passing-only-20261025 — identical to signed base commit, zero changed files. DO NOT MOVE this ref.
Signed build verification: GitHub Actions run 40230842944, success.
Signed release artifact: ID 12613590219; Infinity-2103407-SEARCH-SINGLE-FLIGHT-ORIGINAL-SIGNER-QA.
Signed 2103407 APK SHA256: 3616c4e69c976bd63b36170d4dbbd9b190a7ec2eace4bc0c34c3c72f7f9e8578.
Original certificate SHA256: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7.
Android package: com.projectinfinity.kodi; ABI arm64-v8a.
Matching 2103407 components and checksums:
- Command Center 0.3.5.39; 085626880963b4ae43870ff7fb57746d45dfa3ea7ce56ea2dd6be7fe53768fcf.
- Watched Bridge 1.0.20; 42a03a9c3c8452d8f1f8cffc651c2805902bf9376b18975e8828af023218f55a.
- UI Repair 0.1.22; f37749294e5f3f0a6f431fbbe06c728e7ea3e08f7f455bcde5cf080739a222a7.
- Skin 1.0.5.243; 0adfed89f1d5384a3fa3a023152c7c2a094ef2edb6dd60129f336fe3b7cb9ef9.
Protected earlier signed references: 2103406 (run 40191243446) for isolated Crash Recorder correction and 2103405 (run 40184543219) for WatchNixtoons2 native Infinity Tracked.
Owner/evidence receipt: locks/infinity-2103407-proven-passing-only-20261025/PASSING-CHECKPOINT.md on the handoff planning branch.

Acceptance device: Samsung Galaxy Fold 8 Ultra SM-F976U1, Android 17 / API 37; physical folded/unfolded and supported portrait/landscape, split/popup, Light/Dark/OLED cases. Android 15/11 or host simulators do NOT substitute for Android 17 physical acceptance.

**Actual passing evidence to preserve:**
1. The 2103407 Search fix prevented baseline cross-invoker overlapping native directory requests in seven deterministic source-based host tests; exact APK packaging, original signer and component/native source-pin checks all passed on run 40230842944.
2. The user stressed the installed 2103407 Search for about one minute on the Fold without a crash. PROVISIONAL DEVICE PASS for that scenario only, not a guarantee all SIGSEGVs disappeared.
3. The user previously confirmed the 2103405 WatchNixtoons2 native Infinity Tracked entry finally worked on device. That native context-registration behavior was preserved by 2103406/2103407 scoped APK-diff gates. This does NOT prove every provider and Infinity Movies/TV long-press works.
4. Earlier user-confirmed working Otaku, Favorites and Continue Playing must be preserved and retested, but do not falsely mark complete 2103407 integrated physical acceptance without current observations.
5. The 2103406 SIGABRT recorder source correction has verified source/build/signing; actual fatal SIGABRT Android stack handoff was NOT independently tested on the Fold. Preserve it; no instrumentation-only update masquerading as native root cause repair.

**Unfinished defects are NOT accepted:** universal long-press (specifically Infinity Movies/Infinity TV), unified Command Center, Essential-First Shutdown, full loading/refresh measurements, UI/player regressions, long-term native crash stability, end-to-end whole-app physical proof.

## B. ABSOLUTE NON-NEGOTIABLE NO-TOUCH RULES

**COBRA IS COMPLETELY OFF LIMITS. ZERO COBRA MODIFICATIONS.** No Cobra source, resources, classes, native binaries or native playback logic, player, PiP, Sports, Multi-View, navigation, UI, settings, callbacks, shared behavioral changes, registration, or data. Do not touch Cobra even to improve shared input, activity, display, video, or lifecycle behavior. If a necessary Infinity-only fix uses a shared native subsystem, isolate it to verified Infinity-only ownership and prove Cobra behavior unchanged with source, APK-member and runtime negative checks. Otherwise do not apply that native edit.

No clean install, uninstall, data wipe, profiles reset, unrequested database migration/deletion, user cache wipe as a fake fix, changing Kodi package, changing original signing certificate or downgrading version code. Preserve Resume Hub, watched/ratings/playcount, Watchlist, Favorites, Collection, custom lists, Continue Playing/Watching, providers, source memory, data/Trakt optionality, skin ID skin.infinity.diggz, active playback, PiP, original Search semantics, and already accepted user-facing designs.

No additional features or new workstreams. This is already the FINAL feature scope. Do not invent a different UI family or replace providers. Never silently re-play a stale provider URL, guess a TMDb title by fuzzy name, make false save receipts, reduce source-integrity controls, or disable failed gates to force a green build.

Create an isolated new final corrective branch FROM EXACT frozen commit 0e8739d2... not from stale old experimental overlays or the handoff branch. Preserve the original source branch, signed artifact, prior passing components and rollback. Before changes, write a file/member change budget and ownership map. Do not churn working code just because it is adjacent to a defect.

## C. WORKSTREAM 1 — SEARCH: PERMANENT OVERLOAD HARDENING AND RECURRING-BUG PREVENTION

**Not just review. Tighten and strengthen 2103407 against future recurrence.** Preserve its working single-flight behavior as the starting point and prove any extension actually improves a demonstrated fault.

1. Inspect the exact signed 2103407 Command Center Search source, native lease and worker lifecycle, Android keyboard/IME submission, provider inventory, Kodi JSON-RPC dispatcher and each subinterpreter. Document where concurrency is admitted or canceled and who owns each worker, result token, callback and window.
2. Guarantee a bounded maximum native provider directory RPC concurrency **across independent Search invokers**. The existing Linux abstract-UNIX-socket process-wide admission must not be accidentally narrowed to per-invocation/per-provider capacity, lost during cancel, or duplicated after rapid dismiss/reopen. Preserve safe process lifetime and accurately report busy/retry. A running non-Search provider or legitimate original Kodi operation must not be indiscriminately killed.
3. Make request identity/generation explicit: canceled or older provider results, thumbnails, or History selections must never overwrite the current query/provider/title or trigger unexpected navigation. No duplicate submit on Enter/IME/button; preserving first-tap selection vs deliberate Search.
4. Bound active worker count, repeated request attempts, queue depth, CPU/RSS/memory growth and callback lifetime during rapid repeat submit/cancel/Back/provider switching. Ensure repeated cancel signals are idempotent, and a stalled provider cannot strand forever-owned resources or block the UI. Preserve existing native 20-second lease semantics where legitimate; if changed, prove no new orphan invokers or interpreter use-after-free.
5. Preserve Search All, single-provider Search, provider order/filter selection, Search History repopulate-without-run, provider inventory updates and error/unsupported capability messages. A bad provider cannot bring down Home or corrupt unrelated saved titles.
6. Prevent regression structurally: source-level concurrency contract, deterministic interleaving tests, race stress, cancelled worker still returning, duplicate old result, Python subprocess/late callback, startup/reopen, missing plugin, provider reinstall/disable, native shutdown boundary, process restart. Assert one active provider RPC globally under the scoped controller and cleanup/reuse without leaks. Embed release-blocking tests in CI.
7. On physical Fold, perform at least 50 repeat Search History/single provider/Search All/rapid submit/cancel/back cycles plus sustained pressure. No SIGSEGV, SIGABRT, ANR, bad provider substitution, hung keyboard, wrong selection or runaway threads. Report real outcomes, not guessed causes or fake frame rates. The previously observed 2103406 SIGSEGV and older destroyed-mutex aborts may be separate faults; do not claim one repair fixes everything without proof.

## D. WORKSTREAM 2 — ONE UNIFIED COMMAND CENTER AS INFINITY'S BRAIN

User-approved design: Command Center should own coherent Infinity Search, Infinity Movies/Infinity TV routes, Resume Hub, tracking, Favorites, Watchlist, UI behavior, Rails and first-party persistence, with specialized internal modules instead of separate user-maintained addon updates. Keep native Kodi/Android and visual skin independently owned.

1. Inventory and retain all live Kodi addon registration semantics: startup service, plugins, scripts, native context menu and selection token paths, Home/skin panel calls, Watched Bridge, UI Repair, Rails plugin/context, first-party state stores, add-on dependencies, exact addon IDs and old data paths.
2. Integrate what can safely move into the single Command Center package: isolated Rails, UI Repair and Watched Bridge modules, menu/router, tracking and service coordination. Do NOT delete a required Kodi extension point or break previously registered routes. If tiny compatibility shims must persist for registered Kodi IDs, migrate them with one automated coherent version contract, not recurring manual three/four ZIP reinstallation.
3. One authoritative first-party data writer and shutdown participant per protected path. No dueling watched writes, repeated context registrations, independently versioned conflicting controllers, excess resident services, or stale callbacks after state sealing. Isolate a failed module so it does not cascade through unrelated app features.
4. Preserve every saved category exactly: watched/continue positions, Collection, Favorites, custom lists, Rails order, current Home/view selections, Watchlist, Sync queue, provider verified identity, addon settings and all users' stored data. Use lossless checked migration/versioned compatibility/rollback; do not reset or reinitialize user profiles.
5. **Source integrity is mandatory.** Present native libkodi.so embeds Command Center file SHA256 in immutable read-only slots and helpers compare 25 reviewed source preimages. Build a stable **authenticated module/capability manifest and compatibility handshake**, not a blanket wildcard acceptance. Require original signed bootstrap/trusted hashes and fail closed on unknown code. The native trust transition requires actual compiled/verified signed ARM64 integration if it changes native code. After it is established, Python-only Command Center fixes should generally ship as ONE Command Center ZIP, while actual native or skin changes still need their own native APK/skin artifact.
6. Split Command Center package version from native shutdown protocol version. An addon version increment must NOT silently disable checkpoint registration. The existing 2103407 addon.xml 0.3.5.39 versus checkpoint_runtime.py ADDON_VERSION 0.3.5.38 is CONFIRMED and must be repaired without weakening observer proof.
7. Verify all existing provider/Infinity Tracked context capabilities (including WatchNixtoons2), user stored state, plugin routes, normal/abnormal reload, disabled addons, code hash pins, and source-version upgrades end-to-end. No false assumption that Python consolidation alone improves native FPS.

## E. WORKSTREAM 3 — OFFICIAL SYSTEM-WIDE TOUCH AND CONTEXT ACTIONS

Treat this as one shared officially approved interaction contract across supported Infinity surfaces, not piecemeal fixes.

**CRITICAL TARGETS:** Actual **Infinity Movies** and **Infinity TV** custom Infinity-owned navigation/listing surfaces; user reports press-hold not working there. DO NOT substitute generic Kodi Movies or TV Shows and DO NOT confuse the separate 32-bit onn television app with these Infinity navigation routes.

Other applicable surfaces: Home rails, Continue Playing, Continue Watching, Favorites, Collection, Watchlist, Save for Later, Search results and provider tiles, Latest Releases, Video Sources/All Add-ons and supported provider listings including Otaku and WatchNixtoons2. Preserve provider-native Kodi menus where already valid.

1. First touch/tap SELECTS/highlights exact card without navigating. Second deliberate tap activates that selected card's *existing* destination. Press and hold selects the exact touched item and opens exactly one intended context menu without opening playback.
2. Display ALL applicable supported Infinity context actions: Infinity Tracked, watched/unwatched, Watchlist, Collection, Save for Later, Favorites, custom lists and provider/Kodi-native options. Gate actions by verified media ID and provider capabilities, not by fuzzy title lookup; unverified metadata should not suppress otherwise safe generic actions or lead to a fake "verified" route.
3. Preserve exact title ID, source/provider identity, typed selection, list index, scroll position, filters, popup and originating window on cancel/dismiss/Back/rotate/fold. No accidental neighbor selection, orphaned tall narrow black popup, overlapping menu, double invocation or wrong item action.
4. Integrate Kodi native touch translation and window-specific container entrypoints with one Command Center capability/selection policy. Honor actual touch coordinate mapping after scroll/transform and the existing Kodi input system, but NEVER touch Cobra-specific input behavior.
5. Test first/second/long press with physical finger, scroll-before-hold, screen change, nested dialog, profile themes, mixed installed providers, source unavailable case and D-pad where supported. Source callback tests alone do not count. Preserve physically working WatchNixtoons2 Infinity Tracked exactly.

## F. WORKSTREAM 4 — LOADING, REFRESH, DISPLAY RESPONSIVENESS AND SMOOTHNESS

Both meanings of refresh are explicitly within the approved scope: content/provider refresh and display refresh/frame pacing.

1. Measure cold launch to first usable Home/search rail, actual poster-first-paint, metadata load, provider inventory, Python startup, UI routing and input-to-visible-response; classify expensive steps and remove demonstrated redundant work.
2. On play/Stop/Back → Home, reuse unchanged poster/rendered rails, view selection, scroll and session where valid. Avoid previously reported ~45-second warm poster redownload/blank Home. Target warm usable Home around 1–2 seconds where physically possible, but report actual Fold medians/p95 and do not fabricate a passing timing.
3. Refresh correctly on watched/continue/list changes, provider added/enabled/disabled/updated/removed, Search result and Latest Releases changes. Use bounded caches/invalidation rather than fake freshness or stale/unsupported provider URLs.
4. Control request storms, duplicate directory jobs, main-thread work, queue contention, blocking provider callbacks, unbounded memory/cache growth, startup reinitialization and unnecessary entire-window rebuilds. Preserve player continuity during supported fold/rotate/split/popup.
5. Measure real active display mode/Hz under OS constraints, thermal, power saving and Fold orientation; optimize input-to-frame latency, Choreographer or platform-equivalent frame times, jank/dropped frame rate, recycler/card presentation and scroll. Do NOT force 120Hz, override OS saving, stretch/recolor video or claim FPS that was not measured.
6. Mandatory Fold tests: representative cold/warm startups, 30 playback→Home cycles, 20 fold/rotate/supported window transitions, sustained scroll and popup dismiss, Light/Dark/OLED and real provider refresh. Log before/after p50/p95, worst outliers and actual CPU/RSS growth with comparable conditions.

## G. WORKSTREAM 5 — ESSENTIAL-FIRST SHUTDOWN 2.0: UNIVERSAL OWNERSHIP AND LIFE-PROOFING

The existing user-approved Essential-First Shutdown was temporarily deferred until other polish. It remains a REQUIRED final closure gate and must integrate seamlessly with the consolidated Command Center.

1. Correct real 2103407 Command Center version mismatch and prove native checkpoint participant startup, PREPARE, FINALIZE, durable receipt and protocol agreement. Separate semantic shutdown-protocol version from UI addon version; do not ever again ship a binary-and-addon set that cannot agree on this API.
2. **Save verified essentials FIRST**: final Resume Hub watched/progress/history, Favorites, Collection, Watchlist, custom lists, playback selections, profile/Kodi/skin/addon settings, sources, required native SQLite/WAL and critical XML files. The actual save operation needs a durable fsync/commit/readback/ledger generation, not just a returned Python function or window close event.
3. Separate **actual protected-write obligations** from **the mere lifetime of third-party service threads**. Retiring the last idle Python add-on must NOT remain upstream of Command Center/native essential saves. Optionally signal cooperative stop; use safe whole-process termination only after genuine essential/shared writes are fenced and proven.
4. Universal, future-add-on-independent classification via instrumentation: required/shared data write, optional private user state, disposable cache/network/thumbnail work, and genuinely unclassified/unobserved writer. Do not assume "The Crew" or any new provider is an essential first-party save owner just for running. Also do NOT misclassify a third-party write to the shared Kodi protected database as optional. Unknown shared writes must fail closed until observed or resolved.
5. Keep native authoritative session/PID/owner/generation, protected late-write fences, SQLite transaction and dirty job tracking, authenticated one-shot Android termination and actual native process-death proof. No timeout extension used as fake fix, no abandoned user transactions, forged SAFE/COMMITTED, partial native teardown underneath live Python services, unsafe blind script kills or silent private add-on data-loss guarantees.
6. When appropriate, report a truthful state such as ESSENTIALS_DURABLE_OPTIONAL_WORK_UNFINISHED separately from fully graceful all-retired shutdown; be explicit that unknown private third-party data could be interrupted by whole-process exit, whereas the protected first-party essential state is verified. If the essential barrier cannot be established, preserve fail-closed behavior, exact blocker, and user data.
7. One Command Center native checkpoint participant after helper consolidation; no orphan/duplicate writer service and no version-skew registration. Native shutdown authority, not Python UI, remains final authority.
8. Gate on real Fold: >=3 normal Close/reopen cycles under different workloads, including changed watched progress/Favorites/settings, concurrent Search, multiple active providers, stalled optional service, genuine shared database write, cold/warm restart. Inject failed essential fsync/SQLite/writer in controlled tests without corrupting actual user records. Verify matching receipts, sealed admission, consumed one-shot authorization and actual previous PID death. No forced success when worker proof missing.

## H. WORKSTREAM 6 — REMAINING APPROVED VISUAL AND PLAYER STABILITY POLISH

No general visual redesign; preserve the existing Light/Dark/OLED liquid-glass aesthetic and skin.infinity.diggz identity.

- Infinity Home logo: remove legacy extra numbers, small Infinity logo on right; theme parity without Home reflow regression.
- Home clock/time truncation after playback/rotation, date/weather and status indicators, screen sizes and fold modes.
- Option B Information: full synopsis/details, actual vertical scroll, correct overflow/scrollbar, compact appropriate spacing for short and long media, exact selected-title return.
- Provider chooser: full labels and Cancel, no raw markup such as [/B], compact adaptive size, correct scroll/focus/tap; provider source remains verified.
- Context menu/popups: eliminate tall narrow black stray window, focus loss, overlapping Add-on Information/Health Center/ZIP-preview, wrong entry and wrong touch hitbox.
- Playback UI: restore user-approved clean/lightly translucent Play/Pause appearance (avoid disliked cyan/dark solid filled), keep Rotate button not Repeat substitution, remove rejected playback Display Mode entry, readable elapsed/duration seek labels in every orientation/theme, upper-right time after stopping. Preserve video pixels, aspect, cropping, audio, PiP, background playback and underlying player.
- Preserve Continue Playing/Watching, watched indicators, source memory, Universal Save for Later, Trakt optional behavior, all provider routes, add-on health and local-first data.
- Health Center: robust low-overhead export of crash/ANR/native Search/Essential-First evidence, durable omission status when tombstone unavailable, truthful session/PID and checkpoint status; no sensitive credential collection, fabricated stack frames or repeated instrumentation-only update.

If a listed visual defect is already fixed in signed 2103407 on physical device, VERIFY/PRESERVE it rather than editing. Restrict code to confirmed remaining regressions.

## I. WORKSTREAM 7 — END-TO-END STABILITY OF THE COMPLETE INFINITY APP

All workstreams must function together after final integration, not merely pass isolated host scripts. Run representative user journeys:

- Cold startup → Home usable → Infinity Movies / Infinity TV → first-select/second-activate/hold menu → specific title/Save for Later → Favorites/Watchlist/watched/Continue Playing/Watching → Home → provider search including Search All/History/single-provider → playback → return → refreshed Home → normal Essential-First Close → reopen with EXACT saved data.
- Installed third-party services (including unavailable/stalling providers) and future-style unknown provider fixtures must not crash, freeze UI, erase saved data, bypass persistence, or falsely declare a clean shutdown.
- Foreground/background transitions, rotation/fold, supported split/popup, input gestures, UI/Home clock, Light/Dark/OLED, session and audio preservation, health export and per-provider navigation.
- Memory/CPU/frame/jank and native signal errors during repeated operations, precise owner failures, race/leak/ANR testing. No claim that a missing Android tombstone equals no crash. No regressions to tested Search, WatchNixtoons2, Favorites or original signer.
- Any modified shared native component requires source-diff/ABI/symbol and functional negative regression showing Cobra is completely untouched. If not possible, block that change and report the incompatibility, rather than relaxing Cobra boundaries.

## J. BUILD, DELIVERY, ACCEPTANCE AND FINAL USER LOCK

**Execution order:** baseline pin → inspect exact signed source and data owner contracts → reproduce open defects/negative controls → harden Search and lock new regression tests → unify Command Center and its identity/shutdown protocol → fix universal touch → targeted measured loading/refresh/visual polish → complete essential-first native shutdown integration → full Android 17 build/tests → one signed final candidate → physical Fold acceptance → final freeze.

Deliver ONLY a true installable permanently signed ARM64 final corrective APK with precisely corresponding necessary components, original package/signing certificate, checksum manifest, source commit, successful GitHub run, component mapping/install order, rollback protections and before/after numbers. If full native code changes are required, rebuild the verified matching ARM64 engine with no hidden old binary substitution. Central Command Center should become the single normal Python module update once integrated; Skin stays independent only when actual XML/assets changed. No separate manual multi-component ZIP dance after migration.

**Release-blocking acceptance gates:**
1. Exact signed 2103407 source and passing reference preserved; no unowned APK file/member or Cobra difference.
2. Native/API/Command Center source-integrity and original signing/certificate checks green without global bypasses.
3. Search >=50 substantial Fold cycles and genuine sustained overload, worker counts bounded, old results isolated, no crash/ANR/hang or legacy behavior regression.
4. System-wide tap/hold actions all correct across specifically named Infinity Movies and Infinity TV, provider contexts, retained selection and focus; working WatchNixtoons2 preserved.
5. Actual performance baseline vs candidate measured on device: cold/warm loading, posters, provider inventory, scroll responsiveness and real effective-Hz frame pacing. 30 playback/Home cycles and 20 fold/rotation scenarios.
6. Essential-First durable owner/protocol compatibility, >=3 authenticated and physically confirmed close/reopen cycles, known safe/unsafe writer outcomes, data preserved on reopening.
7. Full first-party unified update/migration integrity and lifecycle, no missing addon routes, saved content or dual writers; end-to-end journey succeeds.
8. Approved look/feel/OSD/Option B/provider chooser/Health Center remains correct; no new unrelated design or player change.
9. Final user physical Fold PASS is explicitly recorded before promotion to LOCKED final production Infinity. No invented pass, no acceptance solely from GitHub host tests. If blockers remain, mark candidate NOT FINAL, keep working signed 2103407 intact and repair the exact failing causal defect, not another speculative diagnostic-only APK.

**Reporting discipline:** Maintain for each workstream a live status ladder: evidence → exact cause → implemented → targeted tests → integrated Android 17 → physical Fold pass. Report only actual checked stages. Do not repeatedly ask for the same diagnostics, fabricate user test results or relabel host-only tests as device acceptance.

**Freeze after acceptance:** Archive final signed APK, exact component ZIPs, SHA256 and source lock, device acceptance and rollback, then STOP Infinity feature updates and proceed to Cobra only under a separately issued user directive. Cobra is mentioned solely as an absolute no-modification boundary; its behavior is not a workstream in this Infinity handoff.

**AUTHORITATIVE FINAL SCOPE FENCE:** The user declared the Infinity feature list complete. No new features, adjacent redesign, undocumented provider-specific hacks or unrelated refactors. Everything herein is previously approved corrective/consolidation/performance/stability work. This file is a prepared, comprehensive engineering handoff, not a finished build and not approval to touch the current working reference.
