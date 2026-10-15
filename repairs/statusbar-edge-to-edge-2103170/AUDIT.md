# Cobra 2103170 — concrete status-bar black-band audit

## Physical failure
On the Fold, the Android status icons are visible but the entire status-bar band is black. Restarting the device is not an acceptance condition; only Infinity shows the defect.

## Historical comparison

The exact reconstructed Activity sources show the regression path:

- **2103164** — Cobra was globally fullscreen. No browse status bar existed.
- **2103165** — browse mode first stopped owning fullscreen. It simply cleared `FLAG_FULLSCREEN` and showed the real status bar. It did **not** force a separate non-fullscreen band.
- **2103166** — added the shared root safe-area listener and appearance handling. The root owns top status/cutout padding.
- **2103167** — attempted to harden status-bar recovery after PiP. It introduced
  `FLAG_FORCE_NOT_FULLSCREEN` and explicitly removed `SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN` on browse.
  That is the first change that fights the target-SDK-35 edge-to-edge model.
- **2103169 surface repair** — correctly resolved the active Visual Theme screen color and painted `mRoot`, but physical testing still showed black because the window policy still blocked/covered that underlay.

The final missing piece is window ownership, not another color assignment.

## Root cause

Infinity targets SDK 35. Android 15+ makes the status bar transparent and expects app content/background to draw behind it while insets protect interactive content.

The current browse policy had two independent black-band risks:

1. **Forced non-fullscreen ownership** — 2103167 added `FLAG_FORCE_NOT_FULLSCREEN` and stripped layout-fullscreen. That can leave the system/decor band visually separate from the Cobra root.
2. **Status-bar contrast protection remained enabled** — with a transparent status bar, Android/OEM SystemUI may add a dark contrast scrim. The code never disabled that scrim.

This explains why changing `setStatusBarColor()` and painting `mRoot` could pass unit tests while the physical Fold still showed black.

## 2103170 repair

Browse/PiP-return now:

- explicitly keeps the window edge-to-edge with `WindowCompat.setDecorFitsSystemWindows(window,false)`;
- clears stale `FLAG_FULLSCREEN` **and** `FLAG_FORCE_NOT_FULLSCREEN`;
- keeps `LAYOUT_STABLE | LAYOUT_FULLSCREEN` so the Cobra root paints behind the transparent status bar;
- disables status-bar contrast enforcement on API 29+;
- keeps the status bar transparent;
- preserves the 2103166 root safe-area padding, so controls remain below status/cutout insets;
- preserves the persisted Visual Theme surface resolver from the previous audit.

Fullscreen player/Multi-View still hide the status bar and remain black.

## Protected scope

The repair may change only:

- `cobraApplySystemBarsForSurface()`
- `cobraConfirmBrowseSystemBars()`

It may **not** change:

- locked 2103168 PythonInvoker/native crash repair;
- Candidate 14 contracts;
- player chrome;
- PiP routing/lifecycle;
- safe-area geometry;
- guide/view geometry;
- provider/EPG/playback ownership;
- themes/assets/resources;
- signer.

## Acceptance gates

The candidate must pass:

- all inherited theme/health/navigation tests;
- Candidate 14 rotation/theme tests;
- 2103164 playback stability tests;
- 2103165 PiP/inset tests;
- 2103166 lifecycle/safe-area tests;
- 2103167 status visibility tests;
- 2103168 surface-color tests;
- six new window-level black-band tests;
- source-scope audit;
- exact locked native `libkodi.so` identity and PythonInvoker guard checks;
- signer/resource/native inventory gates.

Physical Fold confirmation remains the final visual acceptance step.
