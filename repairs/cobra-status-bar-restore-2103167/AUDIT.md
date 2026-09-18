# Cobra 2103167 — Android status-bar restore micro-fix

## Protected baseline

2103167 starts **only** from the user-locked Cobra 2103166 end-to-end baseline:

- locked branch: `locked-cobra-2103166-end-to-end-ui-lifecycle-audit-passed`
- commit: `644160d0ca3baeebb6759638d3f40e2853eeed0b`
- successful Actions run: `35347847781`
- versionCode: `2103166`

The locked 2103166 branch is not modified.

## Physical-device finding

The 2103166 safe-area and layout work is correct on the Fold: TV Grid, preview, guide, cards and internal screens occupy the expected screen area. The remaining device-only defect is that Samsung SystemUI can keep the **real Android status bar hidden** even while Cobra is on an ordinary browsing surface.

The fix therefore does **not** add padding, move headers, resize the guide, change the player, or change the shared 2103166 safe-area owner.

## Root cause addressed

2103166 already cleared `FLAG_FULLSCREEN` and called `WindowInsetsController.show(statusBars())` on browse surfaces. On modern Samsung devices, stale legacy immersive/fullscreen system-UI state can survive a fullscreen/PiP transition and keep SystemUI hidden.

2103167 hardens that ownership in four compatible layers:

1. **Browse surfaces add `FLAG_FORCE_NOT_FULLSCREEN`** while clearing `FLAG_FULLSCREEN`.
2. **Legacy hide/immersive flags are explicitly scrubbed** before the modern WindowInsetsController call.
3. **WindowInsetsController behavior returns to `BEHAVIOR_DEFAULT`** and explicitly shows both status and navigation bars on browse surfaces.
4. **A one-frame confirmation pass** reasserts the browse policy after window traversal, which protects against OEM state being re-applied after the first request.

Fullscreen video and Multi-View clear `FLAG_FORCE_NOT_FULLSCREEN`, keep `FLAG_FULLSCREEN`, and continue hiding **only** the status bar. The navigation/gesture bar remains visible by contract.

## Protected contracts

The micro-fix is forbidden from changing the 2103166 layout/safe-area implementation, Settings, TV Grid/Guide, player chrome, player drawers, More/Display, track picker, lock controls, preview, PiP routing, background playback, provider/EPG loading, navigation or Health Center.

The patch hashes those owners before editing and requires them to remain byte-identical. Only:

- `cobraApplySystemBarsForSurface()`

may change, with one new helper:

- `cobraConfirmBrowseSystemBars()`

Kodi C/C++, native libraries, signer, APK resources/assets and the Candidate 14 protected payload remain untouched.

## Acceptance

CI reconstructs the exact source chain through locked 2103166, then applies only 2103167.

Required gates:

- exact locked 2103166 APK identity;
- permanent signer unchanged;
- native engine unchanged;
- protected `lib/`, `assets/`, `res/` and `resources.arsc` unchanged;
- all **102** previously passed Android tests rerun;
- **5** new status-bar ownership tests;
- total **107 Android tests**;
- protected method hashes unchanged;
- compiled DEX contains the 2103167 status-bar confirmation contract.

Physical Fold acceptance remains the final confirmation that the clock/battery/signal status bar is visibly restored on normal Cobra screens while fullscreen video still hides it.
