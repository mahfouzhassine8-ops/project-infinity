# Cobra 2103169 — Status-bar edge-to-edge repair

2103168 passed its automated color/surface tests but did **not** remove the black strip on the Fold, so it is not a lock and is not a source baseline.

The remaining defect is window-fit ownership. Locked 2103167 restored the real Android status bar, but Cobra's drawable window was not guaranteed to extend behind that visible system-bar region. On Samsung, that leaves the black system surface exposed even if Cobra asks for a transparent or theme-colored bar.

2103169 starts only from locked 2103167 (`2d72c733998d3c535a16d354058344007c5f7921`) and makes the window explicitly edge-to-edge while preserving the 2103166 safe-area listener. On API 30+ it calls `window.setDecorFitsSystemWindows(false)`; on legacy Android it retains the layout-through-bars flags. `FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS` is forced on and `FLAG_TRANSLUCENT_STATUS` is cleared. The visible browse status bar stays transparent over the theme-matched root band, while mRoot's existing system-bar/display-cutout padding keeps actual Cobra content below the icons.

Fullscreen player and Multi-View keep their existing hidden black status-bar ownership. No guide geometry, Settings layout, PiP routing, player chrome, playback/background behavior, provider/EPG logic, native engine, signer, assets or resources are changed.

Acceptance requires all inherited locked tests plus six new system-bar tests. Expected total: **113 Android tests**, along with source-scope, signer, native and protected-resource gates.

Physical acceptance is simple: on a normal Cobra screen the black top strip must be gone, Android status icons must remain visible, and Cobra content must remain safely below them.

## Gate hardening after run 35378865504

The first 2103169 gate proved the new edge-to-edge path itself and all six new tests passed, but two inherited 2103166 safe-area tests caught a lifecycle regression: repeatedly calling `setDecorFitsSystemWindows(false)` could trigger a zero-inset redispatch after a valid inset had already been delivered. That would erase the safe-area padding during fullscreen return or Fold reflow.

The window-fit switch is now **idempotent**: it is configured once per Activity window. Status-bar visibility/color can still be reconciled repeatedly, but the structural window-fit mode is not toggled or reasserted after valid insets arrive. This preserves both requirements at once: Cobra draws behind the system bar, and its content keeps the locked safe inset.

## Second gate correction

Run 35379876318 showed that making only `setDecorFitsSystemWindows(false)` idempotent was not enough: reissuing the associated window flag mutations during the posted confirmation could still trigger a zero-inset redispatch in the inherited 2103166 tests.

2103169 now treats the **entire modern edge-to-edge window setup** as one-time structural state: `FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS`, clearing `FLAG_TRANSLUCENT_STATUS`, and `setDecorFitsSystemWindows(false)` all execute only once per Activity window. Repeated status-bar reconciliation changes visibility/appearance only and does not touch window-fit structure after safe insets have been delivered.

## Third gate correction — preserve the last delivered inset

Runs 35378865504, 35379876318, and 35380715339 consistently showed the same two inherited failures while every new edge-to-edge test passed. That isolated the remaining test/lifecycle problem to the **posted confirmation pass**, not the edge-to-edge setup itself.

`cobraConfirmBrowseSystemBars()` was still calling `requestApplyInsets()` after a valid system-bar inset had already been delivered. Under the controlled Android test environment, that causes a later zero-inset redispatch and overwrites the correct 44/28dp top padding. It is also unnecessary in production: the primary system-bar policy and normal Android window lifecycle already request/deliver insets.

The posted confirmation now only reasserts status-bar visibility, icon appearance, colors, and layout. It **never requests a second inset dispatch**. A new regression test delivers a 44dp top / 24dp bottom inset, runs the confirmation and two frames, and requires those exact safe-area values to survive.
