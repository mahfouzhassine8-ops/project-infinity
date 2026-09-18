# Cobra 2103168 — Status-bar surface match

## Why 2103167 was not enough

2103167 restored the **real Android status bar**, but physical Fold testing showed the original acceptance condition was still not met: the band behind the status icons stayed black while the Cobra screen itself was using a lighter visual surface.

The root cause is now isolated. On target-SDK 35 / modern edge-to-edge Android, the status bar is effectively transparent. Cobra's 2103166 safe-area padding lives on `mRoot`. The active Visual Theme paints `mStage` with the `screen` style, but the safe-area band behind the transparent status bar was still using Cobra's older base background. So we were fixing visibility while the black band came from the **underlying safe-area surface**.

## Exact protected base

- locked branch: `locked-cobra-2103167-status-bar-restore-passed`
- commit: `2d72c733998d3c535a16d354058344007c5f7921`
- successful run: `35371132749`
- versionCode: `2103167`

## 2103168 repair

Normal Cobra surfaces now resolve the status-bar band from the same Visual Theme source as the screen:

1. Read the **persisted active Visual Theme manifest** directly, so the status-bar surface does not depend on asynchronous renderer publication.
2. Resolve the same panel-style cascade used by the screen itself: `all.panel → screen.panel → screen`, with the same base → layout → appearance variant precedence.
3. Use `palette.background` when supplied.
4. Fall back to the already-published runtime theme for non-persisted themes, then Cobra's built-in appearance background.

The browse status bar is transparent so that matched safe-area surface is what Android displays behind the clock/battery/signal icons. `mRoot` receives that exact resolved color, eliminating the black edge-to-edge band without changing any inset dimensions.

Fullscreen player / Multi-View remain black and continue owning hidden-status-bar behavior exactly as before.

## Protected scope

No layout, padding, guide geometry, Settings geometry, player chrome, PiP routing, background playback, provider/EPG logic, navigation, native engine, signer, resources or assets may change.

Only these existing methods may change:

- `cobraApplySystemBarsForSurface()`
- `cobraConfirmBrowseSystemBars()`

One helper is added:

- `cobraBrowseSystemBarSurfaceColor()`

## Acceptance

CI must reconstruct through locked 2103167 and rerun every prior Android suite plus four new surface-color tests. Expected total: **111 Android tests**, plus the new source-scope audit and all signer/native/resource gates.

Physical Fold acceptance is the final confirmation that the former black band now visually blends with the active Cobra screen while the Android status icons remain visible.

CI trigger: execute the complete locked-chain reconstruction and 2103168 surface-match gates before accepting the candidate.

## Gate correction after the first 2103168 run

The first full gate deliberately failed three new surface tests. All inherited 2103166/2103167 tests passed; the failure exposed a real timing weakness in the new resolver: it depended on `CobraVisualRenderer.active` having already published the installed theme. That is not strong enough for startup/window restoration.

The resolver now reads the already-validated active theme manifest from its persistent pointer without decoding artwork/fonts. The regression tests intentionally hold the renderer on `builtin` after installing a custom theme and require the status-bar band to resolve the installed screen fill anyway. This strengthens the production path rather than weakening the gate.
