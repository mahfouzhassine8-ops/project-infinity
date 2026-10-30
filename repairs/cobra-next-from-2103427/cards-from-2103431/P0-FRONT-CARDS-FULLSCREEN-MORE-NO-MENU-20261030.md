# P0 — Cobra Cards: Fullscreen “More” button receives focus but does not open menu on FRONT Fold display

**User-reported physical Fold issue (October 30, 2026).** This is the user's **second new Cobra issue**, in addition to the separately documented **inner-display oversized Cards density**. Fix the *existing fullscreen player More action*, not the card tile menu, and do not redesign or alter the existing FRONT Cards appearance.

## Confirmed visual evidence and boundaries

- User supplied native screen-recording `20689.mp4` (private conversation upload, 1080×2520 pixels, duration approx. 13.925 seconds, SHA256 `e9756c47a19ab2610d75560c78dbdff12ddabbd3a1973273d4ed4aeaff0c6f58`). Do not claim this video exists in a Codex workspace/repository unless explicitly transferred.
- The recording starts **already inside Cobra Cards → fullscreen playback**, on the Fold **FRONT/cover display**, showing USA: Nicktoons with a playing video and bottom control strip.
- The bottom player strip displays **Channels | Display | Multi-View | PiP | More (⋮)**. The far-right More control is visible, has normal hit area and gains a cyan-highlighted border around the middle/latter part of the recording (notably around 7.5–10s). **No More/overflow action sheet appears**; playback/video and other controls remain on the fullscreen page. At the end of the recording, the user exits fullscreen to the Cards channel wall.
- The user's direct report is: **“Fullscreen cards front display pressing on the more button does not work as you can see it.”** The video demonstrates a highlighted More control without a visible menu, but it does NOT by itself establish whether the root cause is pointer dispatch, a focus-only event, click guard, action-sheet ownership, modal/window visibility or rendering. Do not invent a root cause or say it opened PiP: that was a different historical report.
- The active install context in conversation is the newly signed **2103433 test candidate**, but the video contains no on-screen package version. Treat 2103433 as the probable baseline, and verify actual installed version/source when testing.
- **Distinguish the separate per-channel three-dot MoreView** in `cards-from-2103431/runtime/CobraCardsTiles.java` (which calls `showCobraChannelActions`) from the **fullscreen player's bottom-right More**. The latter is the actual broken button. Do NOT “repair” the wrong control.

## Scope and absolute preservation

1. **Target only Cards-mode fullscreen playback on FRONT display**, plus narrowly necessary shared dispatch fixes if proven behavior-preserving. The video is not evidence that Pro, Pro Sports, Mobile, Compact or TV Grid More buttons are broken. They are negative-control/regression targets, NOT redesign targets.
2. **Front Cards visual layout is user-approved and FROZEN**: preserve exactly the signed 2103433 cover-screen two-column card geometry, video/Now Playing preview, toolbar, logos, typography, card borders, progress, selected state, same fullscreen control order, colors, icon sizes and hit-target appearance. A functional click/action correction is permitted, no visible redesign.
3. Separate pending issue `INNER-FOLD-CARDS-DENSITY-PROPOSAL-20261030.md` concerns ONLY inner-display responsive compactness (four columns when accessible, fallback as needed); **never let that change spill into cover geometry or this fullscreen player's controls**.
4. Preserve signed 2103431, 2103432 and 2103433 APKs/owner ZIPs and original key, native libs, package identity, existing user data/settings, PiP, timeshift, media session, subtitles, pause/play, channel selection, More menu contents/actions, Android Back, Pro and Sports, Multi-View, chooser, Infinity and shutdown. No cross-owner/native patch without separately approved gate.
5. The user also approved a **different Infinity-only universal loading animation** on `work/infinity-only-seamless-loading-from-2103433-20261030`. Coordinate one combined next-version signed release only when both owners independently pass, instead of multiple diagnostic installs; do not develop Infinity features in this Cobra correction.

## Required investigation

- Inspect the exact signed 2103433 Cards fullscreen builder/controls, not only the original home/player preview or per-card MoreView. Identify native `mPlayerOverlay` / fullscreen control root, displayed More view identity/tag, its OnClickListener, touch handler, possible parent intercept/overlay, existing click guards and action sheet open/close paths.
- Reproduce **real screen-coordinate touch/tap** on the visible More control. Record click recipient and whether the expected action-sheet method is invoked. Distinguish clickable→focused only from true activation; verify accessibility/D-pad action if applicable.
- Trace click→handler→menu creation→attachment/z-order→visibility→dismissal. A menu could open then immediately close, attach behind fullscreen, or be blocked by stale fullscreen state; investigate evidence before changing code.
- Reproduce after reopening fullscreen, after player chrome auto-hide/reveal, while video plays, after PiP return and after mode/fold transitions. Preserve all current player/control functions.
- The historical `CobraPresentation.java` `moreLast` logic and earlier 2103429 Pro/non-Pro positional issues are **not proof of this root cause**. Do not blindly swap callbacks, reorder icons, or alter Pro.

## Focused verification, no unnecessary suites

- **Before**: signed 2103433 actual fullscreen Cards FRONT tap on visible More with playback active: record focused/tapped view, expected/actual callback and UI outcome.
- **After**: the same touch creates the **existing original More menu** exactly once and is visible/usable. Its menu actions execute correctly, can close and re-open, and do not change channel/session, playback audio/decoder, PiP, menu order, or video presentation.
- Verify More on/off-screen or a live control reveal (including no stale/dead hit box), back/cancel, touch and remote activation. Guard against parent control hide before click executes.
- Verify front Cards visual geometry is unchanged pixel/structurally from signed433 aside from the moment a legitimate menu is open; other front controls Channels/Display/Multi-View/PiP remain correct.
- Negative controls: Cards **inline/tile** More and channel Quick Actions still work; ordinary Pro, Pro Sports, Mobile, Compact, TV Grid fullscreen controls remain unchanged; inner-display density change does not affect current fullscreen functionality.
- Focused source/DEX checks and packaging preservation only, **NO shutdown tests**, no data clear or repeated experimental APKs. Physical Galaxy Fold acceptance by user, host-only PASS does not prove Android action.
- Document the real source/method change and hard evidence for the cause. If cannot reproduce in host/emulator, preserve the user's physical report as a blocker rather than “fixing” unrelated Pro controls.

## Integration/delivery

Add this **second Cobra issue** to the existing coordinated Cobra + Infinity work plan:
- Cobra: inner-screen Cards compact density, plus **front Cards fullscreen More action**.
- Infinity: previously approved selected-item cyan perimeter loading with drawer fallback, separate owner.
- Keep the **front Cards design exactly unchanged** and preserve signed 433 as recovery.
- Use one controlled integration/owner gate, only necessary tests and **one next-version originally signed combined install-over APK**, when the verified changes are ready. Do not auto-lock/promote; await user Fold acceptance.

**Status at this documentation commit:** Video inspected, observed failure documented; root cause, production repair and physical post-fix verification are NOT claimed.
