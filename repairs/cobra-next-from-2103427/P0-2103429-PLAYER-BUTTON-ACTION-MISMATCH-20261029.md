# P0 — Cobra 2103429 physical Fold: Fullscreen/PiP/More touch-action mismatch

**USER AUTHORIZATION:** Correct this documented 2103429 defect within the EXISTING Cobra task/branch. Implement, verify and preserve; do not stop at an audit. This is a scoped repair added to the existing Cobra work, not a new project or a replacement for already approved requirements.

**Repo:** `mahfouzhassine8-ops/project-infinity`
**Working branch:** `work/cobra-only-from-2103427-20261028`
**Actual installed test version reported by user:** combined APK 2103429.
**Signed candidate:** `Infinity-2103429-Combined-Original-Signer.apk`, source `f2b76fb76ad4edd87197f9521347295b4e612f26`, original-key run `40818697397`.
**Protected user-approved recovery:** `lock/infinity-cobra-2103427-user-approved-20261028` at `782242090483982c39a78f9c4da932a4751bdafc`.
**Evidence:** User's physical Galaxy Fold 8 Ultra / Android 17 video `20608.mp4` and explicit verbal reproduction on Oct 29. The video is a private conversation attachment, not assumed to be directly available in the GitHub repo or Codex workspace; don't claim to have watched it if you have not. The user's exact observed effects below are authoritative input.

## Actual, confirmed user-reported behavior

On the Cobra player control strip (user demonstrates the Pro-style horizontally scrollable buttons):

| Actual button tapped | ACTUAL result in installed 2103429 | REQUIRED result |
| --- | --- | --- |
| **Fullscreen** (expand/corners icon) | Opens **PiP** — WRONG | Open **Fullscreen** |
| **PiP** (small-window icon) | Opens **PiP** — CORRECT | Open **PiP**; leave working behavior unchanged |
| **More (three vertical dots)** | Opens **Fullscreen** — WRONG | Open **More/overflow** menu |

**Important:** This is a button-to-action *interaction mapping* defect, NOT a request to rearrange the buttons, make them smaller, redesign Pro, or reorder the More icon. Earlier assistant guesses about More being absent, about fullscreen's control list lacking buttons, and about button size were INCORRECT. Do not convert those guesses into engineering requirements.

## Corrective instructions

1. Inspect the **actual signed 2103429 production Cobra control-strip code and generated/DEX behavior**, with special attention to horizontal scroll offsets, overlapping or stale touch rectangles, drawing order, event interception, icon-to-view mapping, indexed action arrays, player-mode transitions, focus and button callbacks. **Do not assume the callbacks themselves are incorrectly wired.** Determine whether taps are landing on the wrong view/hitbox or are dispatched incorrectly; reproduce before deciding the change.
2. Make the **smallest Cobra-owned production correction** so each tap/click/remote activation invokes the action visually identified by its button, for all button states and when the horizontal strip is initially visible, partly clipped or scrolled to the end.
3. Fullscreen button must exclusively enter the appropriate fullscreen presentation; PiP button must continue invoking the existing working PiP handoff; More button must exclusively open the original More menu. Preserve all existing menu contents, submenu behavior, playback session, current channel/audio, paused states, focus and return navigation.
4. Preserve the existing **Pro More-last order**, existing Pro Sports control order `Channels → Display → Multi-View → PiP → Stats → More`, and the approved non-Pro More-last change. Do not move or remove icons. Inspect the active mode (Pro Sports vs non-Sports, Mobile, Compact, Cards, TV Grid) so a fix does not leak actions or mis-map other player controls.
5. If button mapping depends on layout/panel creation or scroll state, verify initial render, scrolling in both directions, reopening More, entering/leaving fullscreen, PiP enter/return, orientation/fold, and mode switches. Only those relevant focused paths; no broad unrelated stress, shutdown suite, or repeated full device APKs.

## Selected, required focused verification

- Execute **real coordinate/touch or equivalent production view-dispatch tests**, *not only direct calls to button action methods*. Verify icon center and actual hit rectangle agree; pointer dispatch target and action are correct across relevant scroll offsets / clipped edge. Include remote/focus click on current visible control where supported.
- Demonstrate exact 3×3 action separation (Fullscreen→fullscreen, PiP→PiP, More→More) with original working PiP continuity and no accidental double dispatch, and verify More menu contents remain unchanged.
- Recheck Pro Sports/non-Sports and applicable non-Pro modes, active versus saved mode, and backdrop/navigation state. Check no overlay intercepts, hitbox overlaps, offscreen targets, or duplicate views.
- Compare actual new APK member identities with 2103429 and locked 2103427 where meaningful; retain unchanged non-target Cobra code, 2103427 Infinity exact, original chooser except previously authorized `Version` wording/metadata, and shared/native/persistence/shutdown contract.
- Record before/after reproduction, touched files/methods, and selected test PASS/FAIL. Physical Fold validation remains user-owned; host/emulator PASS must not be presented as a verified Fold fix.

## Delivery and preservation

**Cobra-only correction.** No Infinity changes; 2103427 remains frozen. Do not touch Cobra features outside this bug, rewrite Pro, change original PiP behavior, or alter the protected shutdown. No shutdown tests, uninstall/data clear, source authentication bypass, certificate swap, stale-component combination, or automatic baseline lock advancement.

Integrate this fix into the **existing Cobra release work**, keeping 2103429 as an unaccepted test candidate and 2103427 as the accepted rollback. Build one subsequent properly versioned, original-key signed install-over combined APK with matching owner components **when other approved Cobra work is ready**; do not issue additional experimental APKs merely to test this repair unless the user asks. If actual code is inaccessible or a shared-owner change is required, document the precise blocker instead of claiming a fix.

**Exit condition:** verified Fullscreen→Fullscreen, PiP→PiP, More→More for the actual visual controls, and no regression of original Pro menus/playback, with honest status of device acceptance.
