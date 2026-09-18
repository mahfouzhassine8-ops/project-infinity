# Cobra 2103169 — Status-bar edge-to-edge repair

2103168 passed its automated color/surface tests but did **not** remove the black strip on the Fold, so it is not a lock and is not a source baseline.

The remaining defect is window-fit ownership. Locked 2103167 restored the real Android status bar, but Cobra's drawable window was not guaranteed to extend behind that visible system-bar region. On Samsung, that leaves the black system surface exposed even if Cobra asks for a transparent or theme-colored bar.

2103169 starts only from locked 2103167 (`2d72c733998d3c535a16d354058344007c5f7921`) and makes the window explicitly edge-to-edge while preserving the 2103166 safe-area listener. On API 30+ it calls `window.setDecorFitsSystemWindows(false)`; on legacy Android it retains the layout-through-bars flags. `FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS` is forced on and `FLAG_TRANSLUCENT_STATUS` is cleared. The visible browse status bar stays transparent over the theme-matched root band, while mRoot's existing system-bar/display-cutout padding keeps actual Cobra content below the icons.

Fullscreen player and Multi-View keep their existing hidden black status-bar ownership. No guide geometry, Settings layout, PiP routing, player chrome, playback/background behavior, provider/EPG logic, native engine, signer, assets or resources are changed.

Acceptance requires all inherited locked tests plus six new system-bar tests. Expected total: **113 Android tests**, along with source-scope, signer, native and protected-resource gates.

Physical acceptance is simple: on a normal Cobra screen the black top strip must be gone, Android status icons must remain visible, and Cobra content must remain safely below them.
