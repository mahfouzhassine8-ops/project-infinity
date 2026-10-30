# Cobra Cards — inner Fold density correction (user-requested proposal)

**User request:** On Galaxy Fold 8 Ultra, Cards currently looks appropriately compact on the narrow front display but enormous on the opened inner display. User asks to make **Cards smaller when unfolded so more channels fit**. This is a Cards-only responsive-density follow-up, NOT a request to switch to the separately named Compact view mode or redesign any other Cobra view mode.

## Grounding in supplied physical screenshots

- Front display screenshot `20687.jpg`: **689 × 1536** pixels. Existing Cards grid has **two** reasonably compact columns and several visible rows.
- Inner display screenshot `20685.jpg`: **1473 × 1536** pixels. Cards is still **two** columns despite ~2.14× horizontal pixels, so each card, its logo/text, the preview header and toolbar are much larger and fewer rows are visible.
- These are captures in this ChatGPT conversation, not presumed available in the GitHub workspace; to do pixel matching, obtain the actual user images. Dimensions are raster facts and not proof of Android dp, insets, fontScale or hinge posture.

## Source-grounded root cause to verify on device

Current signed433 Cards implementation owns `repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsLayout.java`.

- Layout column decision (around line 98) is `int columns=width<280?1:width>height && width>=1100?3:2;`. A portrait/square-ish unfolded inner display with width less than height remains **two columns**, even with ample horizontal space.
- `float unit=width/941f` in logical layout and `scale=width/941f` in `physicalLayout` (around line 300) enlarge the full header, preview, details and filter bar based on the much wider viewport. This causes the whole top region to grow instead of using extra width to show content.
- `CobraCardsTiles.java` uses `scale=width/448f` based on each GridView card width; with two massive columns, logos and text become correspondingly large. Tile height is then measured from scaled text, including the approved paired-row handling.

**Do not blindly patch numeric constants:** Android display density, actual usable content bounds, insets, fontScale, fold state and orientation need to be measured from the real accepted Cards display. Verify column source of truth and both logical/physical layout, so no 2→4 disagreement occurs between model, GridView, tile sizing and scroll/state restoration.

## Recommended responsive design

- FRONT/COVER display: preserve signed433 Cards appearance **exactly**, including **two columns**, top preview/Now Playing, toolbar, labels and card size.
- UNFOLDED INNER display: use a separate **Cards-only expanded-width density profile**, with **four columns as the preferred target** if usable width and minimum accessible card width permit. With screenshots 1473 px wide, four columns yield roughly the same pixel card width as the 689 px front display with two columns; adapt thresholds by real dp and fontScale, not hardcoded screenshot pixel count. Use three columns as a safe fallback if content, accessibility/font scaling or usable viewport width would be compromised.
- Keep the Cards video preview and EPG details side-by-side but **cap their height and typography** rather than scaling those panels and header in proportion to total inner-display width. Keep video aspect/presentation and PiP preview controls functional, no recoloring/cropping of video.
- Likewise cap the menu/header and Favorites/Channel Wall/Search toolbar height; keep touch targets accessible. Use extra usable width to show **more channels per row** and extra vertical space for more rows rather than making everything huge.
- Preserve exact current cyan borders, logo assets, program text, live dots/progress, selected state, real EPG and existing Cards design. Do not hard-code poster/video/EPG data or invent schedule content.
- Preserve actual selection, identity, focus, first visible channel and scroll offset when folding/unfolding or rotating. Retain existing measured peer-row synchronization when changing grid column counts. Recycle existing views; do not trigger full source reload, playback restart or unnecessary network fetch.
- Check toolbar fit, selection geometry, More/quick actions, long press, remote focus and native video/PiP interaction after a density switch.

## Boundaries and verification

This is **only the existing Cobra Cards mode**. **Never change** the appearance or logic of Mobile, Compact, TV Grid, Pro/Pro Sports, Multi-View, Fullscreen/PiP, other experiences, Infinity loading work, chooser, original signing identity, native libraries, data, or shutdown.

This improvement may be integrated with the user-approved Infinity seamless-loading feature through the previously discussed single coordinated combined-APK integration, **but the two owner changes must remain isolated and independently checked**. Preserve original signed 2103431, 2103432 and 2103433 APKs. No automatic release lock.

Selected testing: Cover display byte/geometry parity to accepted433, inner 2→4 density and readability, larger font safe fallback (3 cols), UI tap/long press/More/PiP and actual video aspect, fold↔unfold/portrait↔landscape, selected channel/focus/scroll preservation, no unnecessary grid/list recreation or EPG reload, Pro/other modes unchanged. Physical Galaxy Fold 8 Ultra Android 17 user acceptance required.

**STATUS:** A technical proposal grounded in user screenshots and inspected current Cards source. No production code or APK is changed by this document. Do not treat four-column preference as a released or physically verified result.
