# 2103163 behavioral refinement — Candidate 14 remains locked

Baseline: 1465eabb045badad56142642c48292df94caaa12, run 35324889607, version 2103162.
This is an isolated Android-shell delta; no native Kodi build, renderer patch, signer change, resource-ID change or skin merge.

## Findings and repairs

The prior run-5 green build proved compilation and inherited tests, not the five new behaviors. Its media session hard-coded PLAYING and had no player-connected transport callbacks; onStop could request a foreground service after the app was backgrounded; the chooser workaround discarded the custom scene below 700dp; category work omitted the fullscreen drawer; and the published artifact used the old 2103162 name.

The refinement leases the already-playing preview to the foreground service, with generation-scoped callbacks, truthful native playback state, Play/Pause/Stop, focus loss handling, bounded paused-session cleanup and ExoPlayer's local wake mode. It never allocates, prepares or replaces a stream. Return cancels pending promotion and reattaches the same texture. Fullscreen PiP remains owned by the existing route. Task dismissal/explicit stop ends audio. Extended session continuity remains an independent preference. The added WAKE_LOCK normal permission is used only by ExoPlayer while the leased stream requires it.

Main and fullscreen category directories share normalized allowed provider groups and retain source/hidden/parental filtering. The old 12,000-channel cut-off becomes a bounded 50,000 limit with explicit overflow failure, not silent truncation. A provider refresh must succeed to replace previously cached limited data; Arabic is not hard-coded or invented.

Player settings are measured within the actual window/inset bounds, centered above the player controls. The custom chooser scene fits the available height without replacing its artwork or native launch/settings actions. Scrolling remains an accessibility fallback when fitting would make native controls smaller than 44dp.

Files app selection uses a package-neutral GET_CONTENT chooser, including compatible MiXplorer installations. System selection retains OPEN_DOCUMENT. Persistent access is requested only when the returned URI actually grants it. Third-party provider/OEM behavior requires device validation.

## Gates

Reconstruct all 17 baseline source-receipt entries and verify the exact signed baseline APK before editing. Preserve pre-change source and APK rollback artifacts. Exact preimages and locally compiled postimages gate the refinement; 442 other Activity methods remain byte-identical to run 5. Compare native source patches and all protected APK lib/assets/res/resources.arsc entries; require the permanent signer and unchanged JNI inventory. Permit exactly the scoped foreground permissions/types in the structural manifest guard; negative mutation tests remain mandatory.

Local Android/Media3 compilation passed; 62 unchanged inherited Android tests and 29 new behavioral tests passed. The new suite is also mandatory in CI before delivery, alongside 13 compiled-manifest guard cases. Nothing skipped or failed is accepted as a passing suite.

## Remaining device acceptance

These are Robolectric/controlled-player tests, not physical playback or decoder tests. Robolectric's native MediaSession binder is a no-op, so tests execute the exact callback registered by production and verify actual player commands and notification state. Real Android media-controller delivery, long-duration streaming, Fold visual appearance, system indicator placement, and the user's installed MiXplorer remain device checks. Do not mark this candidate locked or physically verified automatically.

Rollback keeps the original Candidate 14 APK and source unchanged. It does not back up device userdata; Android may reject version-code downgrades. Do not uninstall or clear app data merely to force rollback.
