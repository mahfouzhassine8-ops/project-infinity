# CODEX — COBRA P0: UNIVERSAL FOLD / WINDOW RESIZE FOR EVERY SUPPORTED PLAYER LAYOUT

**AUTHORIZATION: INVESTIGATE, CORRECT, INTEGRATE, VERIFY AND PREPARE A COBRA-ONLY SIGNED COMBINED RELEASE, SUBJECT TO ACCEPTED BASELINE AND ORIGINAL OWNER GATES.**

**Sole engineering owner:** Codex.  
**Repository:** `mahfouzhassine8-ops/project-infinity`  
**Cobra work branch:** `work/cobra-all-layout-fold-reflow-from-2103421-20261027`  
**Source starting point:** `4cc1560bb06b6aca4f5617b2ad0633273114a1c3`, signed 2103421 distribution checkpoint.  
**Current user-approved Infinity:** 2103420, immutable lock `lock/infinity-2103420-user-approved-baseline-20261026`.  
**2103421 combined isolation APK:** signed run `40447183241`, `Infinity-2103421-Combined-Original-Signer.apk`, original cert, **physical Fold acceptance not yet reported**. The video-recorded Cobra APK version was not independently confirmed; do not assume it was 2103421. The 2103421 registry is still candidate, not accepted. Do not silently advance either accepted pointer.

## The bug the user actually demonstrated

User's Galaxy Fold screen recording `20425.mp4` (chat attachment, private; do not upload video/raw diagnostics to a public repo) shows three Cobra live videos displayed on the **outer/cover screen**. The user physically unfolds to the **inner display**. All three streams remain running, but **the entire video layout remains sized to the narrow outer display**, collapsed on the left with the rest of the inner screen black. This is not a deliberate tile aspect-ratio letterbox and is not evidence of a lost video stream. The user confirmed the transition caused the layout shrink; **the three panes were only a reproduction example**.

**CRITICAL SCOPE CORRECTION — NOT A THREE-TILE PATCH:** The requirement applies to **every actually supported Cobra player/presentation arrangement** and tile count. Confirm the supported counts in the shipped Cobra runtime, including **one single player, two tiles, three tiles, four tiles, and any other count legitimately implemented**. All must adapt to display changes in unison. Do not invent an additional count, remove a count or hardcode a fix for count=3.

## Required runtime behavior

1. **Cover → inner:** Recalculate actual current usable window/client bounds on unfold and expand the root presentation, tile layout, all video surfaces and associated controls to fit the inner screen (respecting real cutouts/nav/gesture/status insets). No left strip of stale cover-width layout or unused black parent canvas.
2. **Inner → cover:** Recalculate all root/tile/surface/control bounds to the smaller display. No clipped controls, stretched video or video off-screen.
3. **For every supported count/layout:** Preserve the existing design policy (single full player; 2 splits; 3 large+2 small; 4 grid; actual supported Pro/Mobile/Full Screen/Enlarge/Restore arrangement); remeasure with fresh window bounds rather than cached cover dimensions. Preserve tile order, selection and focus.
4. **Fit versus Fill:** Both layouts use the correct **new-sized tile rectangles**. Fit is allowed to letterbox inside a valid full-sized tile; Fill may center-crop if previously approved; no video aspect distortion or false claim that deliberate source letterbox is a viewport bug.
5. **Preserve playback:** Do not recreate/retune all players to resize. Maintain stream/channel IDs, ExoPlayer identities, timeshift/buffer and playback positions, independently paused tiles, background state, audio focus/selection, PiP controls and fullscreen return. If a player genuinely requires surface rebinding, prove no destructive session reset.
6. **Player chrome / hit targets:** Reflow controls, focus, labels, overlays, action sheets and pointer hitboxes—not just TextureView pixels. Avoid stale touch-coordinate translation, wrong tile selection, black unused canvas and orientation-dependent popup clipping.
7. **All resize events:** Real fold/unfold in both directions, rotation, supported multiwindow/split/popup resizing, Full Screen↔Multi-View, PiP↔player where supported, resume from background, add/remove/enlarge tile, and any presentation/window change that alters bounds. Handle posture and window-metrics changes even if Android does not recreate the Activity; **do not assume `onConfigurationChanged` alone always fires**.
8. **No Infinity regression:** All changes must be Cobra-owned and pass the existing combined owner/anti-rollback gate. Infinity's locked 2103420 PiP, player, Home/Continue, Search, startup and Essential-First shutdown stay protected. Original one APK, one icon, same chooser/preference and original signing identity remain.

## Source/binary investigation: no speculative workaround

Inspect **the actual shipped Cobra owner module in the signed combined APK**, the activity and display containers (including `InfinityLiveActivity`), DEX code references, runtime view hierarchy and the device callback paths. Determine why child and parent bounds remain at outer-screen size: cached metrics, stale surface/layout transforms, wrong root size or inset calculation, missed remeasure, display-ID change, incorrect configuration/state restoration, old Media/VideoTile layout parameters, inactive listener, or nested mode mismatch. Do not name one of these as a proven cause without evidence.

Prior repair source is available for context, but is **not a current-binary patch to replay blindly**:
- `repairs/device-live-fold-multiview-2103227/`
- `repairs/multiview-stability-fill-2103229/DEVICE-TEST.md`
- `repairs/fold-fit-fill-2103226/`
- `repairs/cobra-fold-adaptive-aspect-2103194/`

Verify that the old viewport/layout code is present or has changed in the signed owner module. Produce an exact before/after code/geometry contract. Avoid unnecessary new background services, overlapping resize workers or lifecycle coupling.

## Small but COMPLETE acceptance matrix

For **each supported tile count** (at least 1,2,3,4 where present, and more only if present), check:
- `COVER -> INNER`, `INNER -> COVER`
- portrait and landscape where permitted by the selected mode
- existing Fit/Fill and enlarged/fullscreen options that apply
- correct measured window/root/tile/surface/control widths and heights
- stable active video/paused state, stream identity, audio and timeshift
- no unused layout-created black area, incorrect scaling, wrong hit targets, unintended stream restart.

For applicable player modes, also check PiP/fullscreen return and split/window resize once. Log actual screen/client/window metrics and video/player object identities before/after. Use practical, focused tests, not synthetic 50/30/20 repetition quotas; physically confirm on the user's Fold after delivering the one integrated APK. Report environmental limits honestly.

## Release sequencing and irreversible protections

- Engineering can investigate and implement on the isolated Cobra branch now. **The accepted 2103420 source lock is immutable.**
- **Do not treat signed 2103421 as an accepted release until the user physically approves it**; the combined acceptance pointer stays 2103420. If release sequencing needs a newer accepted combined base, wait for user acceptance or report the exact block rather than building a contradictory signed APK with stale Infinity.
- A Cobra-only updated APK must include the **latest accepted Infinity** component unchanged and the newest approved Cobra component (with the genuinely owned display fix). Reject any stale Infinity/Cobra combination or unowned modification BEFORE original-key signing.
- Original signer, one installed Android package, one icon and one chooser. No uninstall, data wipe, downgrade, public leak of the private recording, shutdown rewrite, or new repetitive shutdown tests.
- If a necessary fix affects shared shell/Infinity lifecycle, stop that specific edit and request scoped approval; do not bypass the release gate or claim shutdown unchanged without member-level evidence.

## Completion required from Codex

**One real Cobra-only correction** that fixes window reflow for all supported counts and modes, a concise actual matrix/results, protected Infinity owner/certificate/member audit, and a correctly integrated permanently signed one-APK update **after** release-authority conditions are satisfied. The user's real Fold acceptance determines final status.

**No three-pane-only patch, no forced reboot/retune, no premature PASS, no paperwork-only result.**
