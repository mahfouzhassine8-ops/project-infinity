# INFINITY — APPROVED UNIVERSAL SEAMLESS LOADING

**User approved October 30, 2026:** the animated cyan frame belongs to the item the user pressed; the top-left Infinity drawer frame is a subtle fallback for background/global loading. No floating popup, giant loading panel, added movie artwork, invented percentages, or redesign of Home. This direction is approved, but NO IMPLEMENTATION OR APK IS CLAIMED BY THIS DOCUMENT.

## Source, independence and preservation

Repository: mahfouzhassine8-ops/project-infinity
Infinity-only branch: work/infinity-only-seamless-loading-from-2103433-20261030
Branch origin: original-key signed 2103433 source commit 6f6abe78fae65046e1ef475c558957eae873130f; this is a source starting point, NOT user acceptance of 2103433.
Protected physical-approved combined 2103431, signed 2103432 and 2103433 artifacts, and the frozen Infinity 2103427 component remain intact.
Cobra and all its modes (including Cards/Pro/Multi-View/PiP), chooser, original signing identity, shared/native player, providers, user data, persistence/shutdown and unrelated Infinity UI behaviors are NOT authorized to change.

The user's real current Infinity Home screenshot (Screenshot_20261030_072248_Infinity.jpg, shared in the conversation) is the look and geometry to preserve. The generated loading mockups illustrate ONLY a tiny moving cyan border on an EXISTING tile/drawer, never a new background/poster/banner. The screenshot is a conversation asset, not presumed to be accessible to Codex.

## Primary behavior — what you press shows loading

- Movies tap -> animate the EXISTING Movies tile cyan perimeter while the real Movies route loads. Same rule for TV Shows, Sports, Arcade, Search, Genres, Movie Providers, Movie Portal, View All and other supported action tiles.
- On suitable controls inside provider lists, Search, Favorites, Continue Playing, Watchlist, shows, seasons and episodes, animate exactly the chosen existing card/option, not every surrounding tile.
- Use a gentle traveling cyan highlight following the frame edge. Preserve existing selected border dimensions, icon, color palette, fonts, geometry, focus and tap/hold semantics. No large glowing rectangle, new textual overlay or fake progress indicator.
- Instant routes open normally with no flash and no artificial delay; a subtle short threshold may suppress animation on very fast routes, but the tap still receives immediate existing feedback.
- Do NOT show a fake percentage. Only a real provider progress signal could justify numerical progress.
- Once actual destination content is ready, end indicator and open cleanly, where doing so is safe and supported. Completed-empty results count as ready, not a loading deadlock.

## Secondary behavior — background/global loads

- If widget updates, artwork sync or refresh occur without a visible user-selected item, animate the CURRENT top-left Infinity drawer/menu cyan frame in a restrained way.
- Coalesce overlapping legitimate jobs into one global indicator; clear when the last tracked job completes or is canceled. Do not show idle or phantom loading.
- A selected item is PRIMARY; avoid redundant distracting drawer glow while it has a visible owning loading state.
- Keep Home and foreground responsive. Do not add polling services or blocking main-thread activity.

## Navigation and readiness: technical reality

1. Investigate the ACTUAL current signed Infinity skin, Command Center, Home routing, Kodi ActivateWindow/RunPlugin navigation and third-party provider launch behavior. Historical source overlays are evidence, not proof of installed component identity.
2. For routes with a reliable readiness/completed-empty/error signal and safe one-time deferred launch, keep the current screen intact until the destination content has finished preparation, then transition once.
3. For third-party Kodi/provider routes that cannot safely prefetch or delay navigation, KEEP their original operation and window transition. Provide the local loading cue until the action starts, or other safe supported feedback; DOCUMENT these fallbacks. Never preinvoke a plugin twice, suppress real errors, or hold the old screen indefinitely just to imitate deferred navigation.
4. Use per-action unique owner/target tokens (idle/pending/preparing/ready/failed/canceled), stale-result guards, and idempotent teardown. Back/Cancel, rapid taps, new selection, context menu, profile change, orientation/fold, experience switching, playback launch and backgrounding must clear stale loading safely.
5. Preserve user-approved provider behavior exactly: first tap SELECTS a provider, second tap starts the search; Search All remains available; history fills query for later provider choice; press-hold context menus; selected provider only searched; Seren does not open a spurious separate window. DO NOT indicate a search is loading merely from first-tap provider selection.
6. Preserve native playback, timeshift, Resume, subtitle/Audio, PiP, favorite and watched actions. Do not delay valid playback, change list data, clear caches, destroy active sessions or alter Essentials-first durable writes.
7. On real failure/timeouts, stop indicating progress and use existing UI Retry/Back flows. Use accessible status semantics and honor reduced motion/power-saving where feasible. No high-frequency layout invalidation, new unbounded timers, observer leaks or network/polling work.

## Selected feature-only verification (not shutdown)

- For Movies/TV/Search/Genres/Providers/Favorites/Continue and deeper selected routes, assert actual tapped-view -> animation state -> correct original action -> completion/error/cancel; test tap, remote focus and long-press where supported.
- Fast action, genuinely slow action, completed-empty, provider error, timeout, Back, repeated fast taps, superseded request, late callback, background overlaps and drawer fallback; no spinner leaks, double execution or false success.
- Ensure original Infinity Home geometry, rail artwork, current selected focus, Light/Dark/OLED rendering and physical Fold portraits remain unaffected outside the tiny animation.
- Verify one-shot navigation is safe for supported routes. Report actual routes unsupported for deferred readiness and retain their original transitions.
- Record actual measured overhead, before/after UI frame pacing, callback count and worker churn; do not claim speed or battery gains from a visual change or host-only estimates.
- Verify exact owner protection: Cobra ZIP/code unchanged, signed 2103431/2103432/2103433 recovery files immutable, chosen Infinity components only, original signer/package, native/chooser/persistence/shutdown unchanged. No unrelated or shutdown suites.
- Follow permanent focused-test policy in AGENTS.md. Run only approved targeted feature tests. Physical Galaxy Fold Android 17 user acceptance is mandatory for any claim of completion.

## Delivery / acceptance

Do not alter or automatically lock the already signed 2103431–2103433 APKs. Preserve the existing Cobra development branch separately.
Implement the new Infinity-only route loading state on THIS scoped branch; report any forbidden cross-owner/native change and do not proceed on that path without explicit permission.
After successful focused implementation, preservation gates and original-key signing, provide ONE next-version combined install-over APK, matching components, build run, commit, SHA256 and honest device-only limitations. No repeat diagnostic APKs.
The final behavior is selected-item cyan perimeter loading for user actions, drawer-frame cyan perimeter for global background work, and safe deferred reveal only for routes with authoritative readiness. No visually invasive loading dialog.

**STATUS: APPROVED SPECIFICATION ONLY, NOT YET IMPLEMENTED.**
