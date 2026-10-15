# Infinity 2103291 — In-Place Responsive Reflow RC1

## Scope

Targeted follow-up to the user-preserved 2103290 native-responsive APK and skin 1.0.5.181.

This candidate changes only Kodi GUI resize behavior after the Android/native geometry is already
correct. The active Kodi window and its controls are retained across Fold/rotation/window-size
changes. Their authored XML geometry is recomputed in place against the new logical viewport.

It deliberately does **not**:
- uninstall, clear or migrate Kodi userdata;
- change providers, accounts, playback ownership, PiP/background behavior or Cobra;
- change skin 1.0.5.181;
- re-add old rotation/responsive helper add-ons;
- redesign Home, drawer, Movies, Shows or Settings.

## Expected behavior

For an already-open Infinity screen:

1. Fold / unfold / rotate / split-screen / popup resize changes the Android window.
2. 2103290 geometry ownership commits the real new size.
3. 2103291 updates the Kodi logical viewport after the existing 90 ms settle period.
4. Existing controls recompute left/right/center/percent/fixed-size XML geometry in place.
5. The existing control objects remain alive. No responsive resize path calls window
   FreeResources/AllocResources, SaveControlStates/RestoreControlStates or window load/unload.
6. The control resize notification is delivered only after the new bounds are authoritative.

## Primary physical Fold acceptance

Use the matching Infinity skin 1.0.5.181.

A. Start on cover/front portrait Home. Open and close the drawer normally.
B. Open the drawer, unfold to the inner screen, then collapse and reopen the same drawer.
C. Verify the selected Home section, focus and scroll position survive without a Home reload.
D. Fold back to cover while the drawer is closed, then repeat with it open.
E. Rotate inner portrait/landscape in both directions.
F. Repeat on Movies, Shows, Settings and a dialog.
G. Resize into split-screen / popup if available.
H. Enter playback, rotate/fold and return to Home. Playback ownership must remain unchanged.

### Pass conditions

- no stuck/non-collapsible drawer;
- no old portrait frame stretched across the inner screen;
- no 16:9 fallback takeover;
- touch targets follow their rendered controls;
- no unexpected Home/window restart;
- focus/selection/scroll survive;
- no provider/account/settings reset;
- player/PiP/background behavior remains as 2103290.

Health Center Responsive/Fold Trace should contain:
- `Infinity geometry committed:`
- `Infinity responsive viewport:`
- `Infinity in-place responsive reflow:`

The final in-place reflow line must report:
`controls_reused=true window_reload=false`.

Physical device acceptance remains required before promotion beyond candidate.


## Default Kodi skin core check

This is now a required core-Kodi acceptance case, independent of the Infinity skin.

1. Switch to Kodi's bundled Estuary/default skin.
2. Start on the inner/main Fold screen and confirm normal proportions.
3. Fold to the tall cover/front screen without restarting Kodi.
4. The UI must not become horizontally squeezed or vertically stretched.
5. Text glyphs/icons must preserve their aspect ratio.
6. Touch targets must continue to match the rendered controls.
7. Fold back to the inner screen and verify the same window/focus remains usable.

The user reproduced the pre-fix failure with Estuary itself: the inner view was acceptable, while the
cover view showed the entire Kodi GUI compressed horizontally. That proves the remaining defect is
not Infinity-skin-only. 2103291 therefore includes an Android legacy-skin adaptive logical canvas in
addition to the Infinity marker-based responsive path.
