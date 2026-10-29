# GPT-6.1 CODEX — COBRA COMPLETE IMPLEMENTATION, OPTIMIZATION AND END-TO-END CORRECTIVE

**AUTHORIZATION: PROCEED — INVESTIGATE, IMPLEMENT, OPTIMIZE, INTEGRATE, VERIFY, SIGN AND DELIVER.**

**PRIORITY: CRITICAL. This is one comprehensive Cobra production assignment, NOT an audit-only request.**

**Repository:** `mahfouzhassine8-ops/project-infinity`  
**EXISTING engineering branch:** `work/cobra-only-from-2103427-20261028`  
**APPROVED, FROZEN combined baseline:** `lock/infinity-cobra-2103427-user-approved-20261028`  
**Exact signed-source commit:** `782242090483982c39a78f9c4da932a4751bdafc`  
**Signed baseline build:** GitHub Actions `40769526963`  
**Baseline APK:** `Infinity-2103427-Combined-Original-Signer.apk`  
**Baseline APK SHA256:** `cd0c8ab5c77067e508baea0ad7d5207b3d6c73775b86387d4099a67cfe4215ca`  
**Cobra component last updated:** `2103423`  
**Frozen Infinity component last updated:** `2103427`  
**Acceptance hardware:** Samsung Galaxy Fold 8 Ultra, Android 17 / API 37, cover/inner screen, portrait/landscape, relevant split/window layouts.  
**Recommended model:** GPT-6.1 Sol, High; selectively use higher effort for difficult player/video-surface and drag concurrency questions rather than automatically switching to Astra.

## 1. Start from the existing architecture, NEVER restart

Continue the current Cobra branch. Read `AGENTS.md`, `docs/INFINITY-FOCUSED-TESTING-POLICY.md`, `repairs/cobra-next-from-2103427/START-HERE.md`, the current signed Cobra owner inventory, and the owner/combined-release/signer contracts under `repairs/dual-experience-isolation-2103420/`.

Inspect the **actual signed 2103427 APK/component bundle**, not a rejected historical patch, before deciding what exists. Relevant history includes `repairs/cobra-all-layout-fold-reflow-20261027/`, `repairs/dual-experience-isolation-2103420/DELIVERY.md`, and `repairs/cobra-clean-restart/DELIVERY-2103372.md`. Prior tests may prove a historic candidate only; confirm presence in the current signed Cobra payload.

The user likes **Cobra's current Multi-View behavior**. Preserve and extend that system: its windows, channel picker, layout selector, streams, Fit/Fill, audio selection, fullscreen, PiP, focus, and Pro Sports functionality. Do not replace working players or impose one mode's visual identity on another.

## 2. Absolute preservation and owner boundaries

**INFINITY 2103427 IS FROZEN AND COMPLETELY OUT OF SCOPE.** It is user-approved. Do not change its code, sources, skin, Kodi behavior, Trakt/Infinity rail isolation, Search, watched/progress, Home/Resume, providers, caches, settings, playback, or user data. Prove exact source/member identity to the signed baseline.

**Cobra's already-working features and approved Pro UI must also be retained.** Cobra is the only feature owner being edited. Preserve Live TV, Guide/EPG, Channels, Favorites/Recents/Groups, Mobile/Compact/Cards/TV Grid/Pro mode boundaries, Pro Sports, audio, source/channel IDs, timeshift, buffer, player sessions, mini-player, fullscreen, supported Android PiP, existing in-app overlays, all theme/ambient settings and Fit/Fill. No retired Cobra Sports dashboard and no Sports tab leaking into Mobile.

**Choose Your Experience:** frozen design and behavior, except the single explicitly authorized wording change in §10 and necessary authenticated release-version metadata. Do not modify the chooser's background, cards, branding, sizing, positioning, selection/launch preferences, Ask Every Time or navigation.

**Shared/native/shutdown protections:** no changes to the shared Android contract, app identity, signing certificate, protected lifecycle/persistence/Essential-First Close, global background services, native libraries, or other owners without a *separate* user authorization after a precise ownership blocker is demonstrated. Do not add shutdown tests or make shutdown a feature/build dependency. Never uninstall, clear app data, reset databases/caches, alter the user profile, downgrade, or disable authenticity checks.

One installed app, one icon, one chooser, one original-key combined APK. Keep the 2103427 lock and signed rollback artifact untouched. Implement on the Cobra work branch only; new release versionCode must exceed 2103427.

## 3. Mandatory workstream A — Performance, loading and ultra-smooth responsiveness

Investigate and optimize real Cobra:
- Launch into first usable Cobra screen; initial Guide, channel and EPG loading; categories, Favorites/Recents/Groups.
- Channel and mode switching; guide scrolling; mini-player/fullscreen/PiP handoff; Multi-View entry, layout switching and artwork/logos/metadata.
- Frame pacing, rapid taps, focus movement, animations, transitions, gestures and responsive UI under actual effective refresh rate and Power Saving.
- Duplicate network/EPG requests, redundant data scans, unnecessary screen reconstruction, unnecessary background refresh, inefficient image decoding and offscreen work.
- Memory allocations, video-surface retention, CPU load, battery/thermal overhead, stale observers and cleanup.

Use real bottleneck evidence. Prefer bounded reuse/incremental updates and cancellation of obsolete nonessential work, preserving playback, authentication, data freshness and protected job ownership. No unbounded caches, forced 120Hz, error-suppression, fake instant-loading claims or unnecessary new services.

Record comparable before/after measures (samples, p50/p95 if sufficient data, CPU/memory/frame timings and source/host/device distinction). Host-only benchmarks are not proof of actual Fold frame rate, latency, heat or battery improvements.

## 4. Mandatory workstream B — All ELEVEN Multi-View layouts across ALL FIVE modes

Maintain the existing player and layout engine; add missing presentation choices/bindings without rebuilding from scratch. Support current Cobra modes **Mobile, Compact, Cards, TV Grid and Pro**, with mode-appropriate visual presentation.

Supported simultaneous player capacity remains **one to four**. The eleven multi-player arrangement choices are:

**Two screens (5)**
1. `50/50` — two equally sized panes.
2. `Picture in Picture — Bottom Right`.
3. `Picture in Picture — Bottom Left`.
4. `Picture in Picture — Top Right`.
5. `Picture in Picture — Top Left`.

**Three screens (3)**
6. `Main + Two` — one primary and two small panes.
7. `Main + Two Overlays` — primary with two in-app floating overlays.
8. `Three Columns` — three side-by-side panes.

**Four screens (3)**
9. `2×2 Grid`.
10. `Main + Three`.
11. `Main + Three Overlays`.

Single-player behavior stays exactly as supported and is not counted as a twelfth Multi-View layout. Do not invent five-plus simultaneous players. The in-app PiP-like overlays are NOT Android system PiP and must not break system PiP.

Preserve existing per-layout player order, Fit/Fill, selected audio, controls, session identities, channel picker, captions, buffering/timeshift, independent paused states and navigation. Where sensible preserve preferred layout separately for each screen count using existing settings—no unsafe new migration. Confirm each of the eleven options is genuinely available and functional in every applicable mode, not merely listed in a picker.

## 5. Mandatory workstream C — Interactive drag-and-drop Multi-View

**New explicitly approved feature across all five Cobra modes, including Pro. Pro's existing controls and Sports behavior remain unaltered except for adding this shared capability.**

### C1. Press-hold and swap panes

Example: `1 | 2 | 3`; hold pane 3, drag it onto pane 1, release; resulting pane order `3 | 2 | 1`. Positions swap, while the underlying channel/player sessions keep running. The user can swap any valid pair of active panes, including from layouts with primary/secondary regions. Preserve audio focus/selection unless explicitly changed, stream IDs, playback position, timeshift, buffer, caption and paused state. Maintain correct controls, touch targets and focus with the moved session.

### C2. Drag to transform layouts

Example: from `Three Columns`, hold screen 3 and move into a highlighted main-screen target; on release use `Main + Two`, with screen 3 as main and 1/2 in the smaller positions. Map valid targets to appropriate transitions among the existing 2-, 3- and 4-screen arrangements. Do not offer mathematically impossible or unauthorized target placements. Keep the regular 11-layout picker as an equally valid alternative.

**Distinguish**: simple swap onto a pane; promote-to-main or placement-zone layout transformation; cancellation/invalid drop. The outcome must be predictable and not accidentally select a different channel or stop a stream.

### C3. Interaction design and safety

- Start only after deliberate long-press **and movement beyond a reasonable gesture threshold**. Stationary long-press keeps existing context-menu semantics; ordinary taps retain existing selection/playback interaction.
- Show valid targets and a live placement preview; release snaps to chosen layout, cancel/offscreen/gesture interruption restores prior arrangement.
- Support touch event cancellation, simultaneous pointers, rotation/fold during drag, missing/stopped stream, stale video generation, and tiny cover-screen touch areas.
- Avoid duplicate listeners and unbounded animation/layout loops; do not repeatedly recreate ExoPlayer or its existing session. Rebind a surface only where the existing supported implementation requires it, proving stable playback.
- In remote/non-touch modes, offer an accessible equivalent `Move Screen` / `Arrange Screen` action using existing focus/navigation rather than inventing unsupported touch input.
- Preserve Pro's existing layouts, other controls and Pro Sports context. Don't redesign the player UI.

## 6. Mandatory workstream D — Fold, rotation and window reflow

The current 2103427 Cobra owner includes the previous 2103423 measured-window resize correction for 1–4 players. **Preserve it; fix only identified gaps.** Verify cover→inner, inner→cover, portrait↔landscape, split/multiwindow/popup resize, fullscreen↔Multi-View, supported PiP return, adding/removing/enlarging panes, drag transforms, mode switching and background return.

Use current measured bounds, insets/density, proper parent/video/overlay/control hit rectangles; don't use stale cover pixel dimensions or rely only on `onConfigurationChanged`. Fit may letterbox correctly, Fill may crop per existing policy, but neither may distort video. No left-strip stale-size canvas, clipped controls, unused black parent region due to incorrect layout, wrong input mapping, unwanted audio change or stream restart. Preserve channel order/selection, focus, all player sessions, buffer/timeshift and paused state. Compare actual geometry and session identities before/after.

## 7. Mandatory workstream E — Playback, PiP and audio reliability

Inspect and correct **demonstrated Cobra-owned defects** in channel tuning, background/PiP return, mini/fullscreen, channel-picker mute retention, audio focus, paused panes, buffering/timeshift, Fit/Fill, caption state, session lifecycle and inappropriate fullscreen/player restoration. Explicit mute retention applies only to the previously approved fullscreen `Channels` tuning path; do not globally propagate mute across unrelated channel operations. Maintain platform PiP and existing in-app overlay separation.

Prevent repeated player construction where re-layout is sufficient. Avoid speculatively patching shared codecs, native allocators, system player lifecycle or protected services.

## 8. Mandatory workstream F — More (⋮) is LAST in non-Pro fullscreen controls

The user's screenshot shows the vertical More menu incorrectly before Fullscreen and PiP in a non-Pro player.

Make **More the last / far-end control** in each applicable non-Pro fullscreen strip: Mobile, Compact, Cards, TV Grid and any other supported non-Pro mode containing it. Preserve existing controls, icons, callbacks, and their established relative order; reorder only the More item. Ensure correct widths, scrolling, insets, focus and touch hitboxes. No duplicate More or menu behavior changes.

**Pro already has correct More-last order. Preserve Pro's entire existing horizontal strip exactly, including its non-Sports controls and Pro Sports order.**

## 9. Mandatory workstream G — Pro and Pro Sports functional preservation and correction

Inspect actual signed Cobra and historically authorized features, not a rejected patch. Preserve full Pro mode identity, horizontal controls (no unsolicited arrows/instruction captions), Live Sports Stats with freshness/spoiler/source validation, original leaders/team/stat content, correct header/theme contrast, broadcast/channel chooser with four visible rows where available plus scrolling for additional choices, focus/Back/menu consistency, mini/fullscreen PiP and channel selection.

Required existing Pro Sports fullscreen menu order:
**Channels → Display → Multi-View → PiP → Stats → More.**

Keep non-Sports Pro's pre-existing control set/order (with More at end); no Sports-only Stats/actions in non-Sports Pro or other modes. Preserve all legitimately shown channel/sports facts; never fabricate stats or live availability. Check and restore demonstrably missing *approved* features, not automatically cherry-pick old experimental fixes.

## 10. Mandatory workstream H — Narrow Choose Your Experience VERSION wording exception

The user explicitly authorizes replacing `Last updated in` underneath BOTH experience cards with the label `Version` and the respective actual release number. On the frozen 2103427 baseline the intended wording is:
- Infinity: `Version 2103427`
- Cobra: `Version 2103423`
- Footer: `App version 2103427`

For the eventual Cobra update, Infinity stays `Version 2103427`, Cobra displays its **actual newly published component update version**, and the footer displays the **actual new combined versionCode**. Use authenticated packaged offline metadata; do not hardcode incorrect future values.

**Everything else in the chooser is unchanged byte-for-byte if possible:** galaxy background, card/logo art, layout, sizing, fonts, colors, controls, focus, Ask Every Time, Just This Time, preferences and navigation. Changes to chooser-owned text/layout/metadata require an explicitly scoped original owner-aware gate; do not weaken it or silently cross protected shell boundaries.

## 11. Mandatory workstream I — Independent end-to-end Cobra defect discovery and correction

**In addition to the user-named requirements, Codex must independently inspect the entire Cobra system for actual mistakes and fix demonstrated Cobra-owned problems.** Audit actual shipped production entry points and UI flows across all supported modes, not only test helpers.

Look for:
- Dead/incorrect buttons, menu actions, settings, channel/EPG destinations, lost saved state, stale callbacks and invalid navigation/popup context.
- Pro/Sports cross-mode leakage, retired panels/tabs, incorrect active-mode versus stored-preference ownership, invalid theme/ambient transitions.
- Stale layout bounds, incorrect overlays, clipping, overlapping controls, invisible focus, wrong hit targets, unmatched fullscreen/mini panels.
- Player/PiP/session leaks, unintended retuning, wrong selected audio, lost independently paused state, stale stream owners, unnecessary reinitialization, bad lifecycle return.
- Excessive jobs, repeated EPG/provider work, UI jank, memory growth, resource leaks, unnecessary background polling, unhandled errors.

For every additional finding: provide the exact source/payload, reproducible or sufficiently strong evidence, cause, minimum safe correction, selected relevant test, and before/after observation. Do not invent defects or claim unexercised paths work. If the fix would change Infinity, chooser beyond §10, shared/native or shutdown ownership, **stop that subchange**, disclose why, and continue independent authorized Cobra-only work. No opportunistic redesign or unrelated new feature.

After implementation, independently review the *final integrated result* for regressions in all five modes and original controls. A green build is not a substitute for functional assurance.

## 12. Focused evidence, tests and quality gates

Record changes and correction-specific selected tests before implementation, consistent with existing scoped testing policy. Required focused checks for actual changed behavior:
1. Layout picker: eleven options × applicable view modes; 1–4 player capacity and invalid selections; identical active sessions across changes; visual geometry, Fit/Fill, controls and source mapping.
2. Drag swap/transform: drop targets, valid/invalid/canceled moves, stationary hold/context-menu parity, multi-touch, input focus, rotation/fold mid-drag, playback/audio state, no retune, remote equivalent.
3. Window: both fold directions, orientation, split/popup/fullscreen/PiP return, accurate parent/video/touch rectangles and live stream identity.
4. More-last: non-Pro order, overflow and keyboard/remote/touch; Pro unchanged; Pro Sports exact order and capabilities.
5. Pro: Stats, broadcast choices, versioned context, player behavior, Sports-only isolation, theme/header/ambient correctness.
6. Chooser: ONLY text `Version` replacement and version-field binding; no layout, branding, preferences or selection behavior changes.
7. Performance: source-grounded before/after work counts, host benchmarks and—when an accessible real runtime exists—actual loading, frame timings, resource and thermal observations. Distinguish host, emulator, and physical Fold; report blocked paths honestly.
8. Complete owner/member preservation and authenticated original-key combined-signing checks; **Infinity 2103427 exact**, unchanged Cobra segments, chooser exception narrowly bounded, shared runtime and shutdown exact.

Do NOT add or require shutdown tests, destructive installs, synthetic quota-driven stress matrices, or unrelated tests merely for a green status. Retain honest failures and exact evidence. Never mask failures by increasing timeouts, disabling checks, fake screenshots or changing a test to fit broken runtime. If emulator/native ARM cannot execute the app, report that, complete independent compile/host/integration checks and do not claim physical success.

## 13. Engineering order and delivery contract

1. Read this brief and `START-HERE.md`, the source owner/signer contracts and actual immutable signed 2103427 Cobra payload. Build a touched-file/member budget, exact source inventory, capability/requirement mapping and baseline evidence.
2. Reuse all already correct Cobra functions (including 2103423 window reflow), implement only absent/new features and demonstrated defects. Focus on real production logic rather than documentation-only patches.
3. Integrate and prove the new all-mode layout selector, drag swaps/transforms, session continuity, More-last non-Pro order, Pro preservation, narrow chooser wording and evidence-grounded end-to-end corrections.
4. Conduct the independent final regression review and before/after measurement. Every original workstream and newly found defect receives an honest status: `IMPLEMENTED AND VERIFIED`, `IMPLEMENTED — DEVICE ACCEPTANCE PENDING`, `BLOCKED — EXACT TECHNICAL REASON`, or `NOT YET IMPLEMENTED`.
5. Prepare **ONE** consolidated next-version **original-key permanently signed, install-over combined APK** with preserved Infinity 2103427, updated Cobra, only authorized chooser wording/metadata, original package/certificate, matching owner ZIPs, APK/component SHA256s, exact source commit and GitHub Actions run. Never bypass the existing fail-closed owner, manifest, anti-rollback, source-authentication or signature gates.
6. Deliver one candidate for user's real Fold acceptance, not repeated diagnostic APKs. No installation/uninstallation or migration on the user's device by Codex; no silent lock/promotion of an unaccepted new release. Keep 2103427 source and artifact rollback available.

### End conditions

**NOT audit-only**; implement all safely authorized Cobra improvements plus evidence-supported discovered defects. If a particular change is blocked by shared-native/owner/signer/runtime constraints, document its precise reason and do not invent an unsafe workaround. Finish the other independent work. If signing is legitimately blocked, report that honestly rather than supplying a fake APK.

**Do not reinterpret this as permission to revise Infinity or restart the entire project.**

**The user alone determines physical-Fold PASS and authorizes the next release lock.**

**Proceed on the EXISTING Cobra branch.**
