# Cobra 2103435 — Cards drawer reflow/resize on Fold inner display (read-only diagnosis)

**Current authority:** User-locked signed 2103435 (source `e0c6153588992001d84076d33fdf8f0d676c0d00`). Engineering branch `work/cobra-only-from-2103435-20261031`. **Infinity and all non-Cards Cobra modes are frozen.** This file records symptoms, not an implementation or user acceptance of a fix.

## Distinguish the two physical-device recordings

- `20728.mp4`: user opens the **Cobra navigation drawer from the front/cover display** and then **transitions to the unfolded inner display**. This tests drawer ownership **across a true Android window/fold configuration change**. The 1080×2520 recorded canvas can show black letterbox areas around inner-screen footage; do not attribute recorder letterboxing to app rendering without independent evidence.
- `20729.mp4`: the phone starts and stays **unfolded on the 2256×2504 inner display**; user opens/closes the **Cobra experience navigation drawer** there, without a fold transition. This isolates drawer lifecycle effects independently of Android posture change.
- These are private conversation video uploads; not claimed to be present in GitHub unless explicitly provided to engineering. Both should be used as actual observation sources if available to Codex.

## What 20729 actually shows (approximate timestamps)

1. **0.0s:** Cards uses the full inner display: upper Cobra header spans screen; left video preview/right Now Playing panels are full-size; four channel-card columns fill the available width.
2. **~1.4–1.9s:** Opening the left **COBRA / Search / Live TV / Movies / Shows / Recordings / My List / Settings** drawer reveals it on the left. Behind it, the Cards header/video/details/grid visibly **shrink/reflow horizontally and shift**, instead of remaining at their normal full-width geometry.
3. **~2.2s:** The drawer has closed or is out of view; the underlying Cards page is still visibly **narrower and offset**, with a prominent black unused region; four columns remain but become narrower, truncating channel text.
4. **~3.4s:** Another open-drawer state shows content displaced/cropped behind the side panel.
5. **~4.1s:** After closing, Cards is briefly confined to the **left portion** of the inner display, with an empty black region on the right.
6. **~5.0s:** The full-width layout is restored, including appropriately sized four-column Cards.
7. A later drawer cycle exhibits further transient reduced-width states around **~6.2s and ~8.7s**, with restoration by ~9.6s.

**Conclusion supported by video:** The drawer event alone makes the Cards page appear narrower/shifted while the phone remains unfolded. This cannot be explained solely as a cover→inner density switch or recorder black bars. The same four columns often persist while their widths and upper panel sizes change, consistent with a narrower **effective content viewport or view-root geometry** during the drawer transition. Video does not prove whether the exact root cause is Android layout remeasurement, window inset/size policy, a programmatic container-width animation, a transform, or an interaction among them.

## Source clues to verify, not assume

- Signed435 Cards helper `repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsLayout.java` recalculates physical layout from `shell.getWidth()/getHeight()` and uses `scale=width/941f`; geometry and columns are tied to the model's available width. This may amplify a **temporary narrow width reported during drawer animation**.
- Older `repairs/cobra-navigation-2103157/presentation.java.inc` uses translation to open a contextual panel in an older implementation, but is NOT proof of the actual signed435 experience drawer implementation.
- Investigate *actual* signed435 Cobra experience-drawer owner and physical content-root width/translation/scales at each lifecycle step; don't patch assumed code or confuse this drawer with Cards' **All channels / Channel Wall** selector, the per-card three-dot More action, or fullscreen More.

## Desired correction (requires separate user authorization)

1. On inner display, opening/closing **Cobra experience drawer** should animate the drawer while keeping the underlying Cards page at its **stable full-screen four-column geometry**; it may be dimmed/occluded behind the drawer, but should not be reflowed, squashed, or shifted through temporary narrow layouts. No flashes, giant black exposed areas, rebinds, preview restarts, or focus loss.
2. For **front→inner while drawer is open**, recompute genuine Fold geometry **once** from the actual new usable window dimensions. The drawer should remain coherently attached/positioned; Cards restores the correct four-column inner layout behind it. Avoid animation-driven fake resize events.
3. Do not regress the original front-display Cards **two-column appearance** or change front presentation without explicit authorization; existing front visuals stay frozen.
4. Preserve the same selected channel, focus/scroll position, video decoder/surface and playback, real EPG, Cards action handlers and visibility, responsive 4-column (accessible fallback) grid, original drawer navigation/actions, dark/light themes, and reduced-motion policy.
5. Make drawer opening **non-structural for Cards**: ideally only the overlay drawer's transform/opacity changes. If the current product intentionally reduces underlying canvas width as a drawer effect, restrict correction to authorized Cards/inner ownership, not shared/global drawer behavior for Pro/Mobile/Compact/TV Grid/Infinity.
6. Test both independent scenarios (20728 cover-drawer→unfold and 20729 inner→drawer), repeated open/close and rapid reversal, with real measured root bounds/model-width/translation/scale/insets and source/observer comparison. Confirm no extra content provider calls, grid/adapter recreation or decoder restart. Only focused tests.
7. The user's **2103435 lock** and original signed artifact remain protected; no automatic release/promote and no Cobra code change from this report.

**Current status:** Videos inspected; symptom confirmed. Underlying cause and code-level fix **not yet verified or implemented**.
