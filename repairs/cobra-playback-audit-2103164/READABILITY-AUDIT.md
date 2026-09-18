# Final visual verification addendum

Rendering the unchanged HM Theme 2.0.3 ZIP against 2103164 exposed an inherited white-on-pale text issue in Light mode. The native video-sheet helper forced a dark-text policy flag regardless of the chosen appearance, while the visual theme correctly supplied Light surfaces.

The final correction uses the same resolved palette for sheet background, header, close icon, and rows. Hard-coded dark row callers are normalized only inside player/multiview sheets. This adds cobraSheetIsDark and cobraSheetRow to the explicit source-change allowlist: the final audit now preserves 434 of 456 original Activity methods unchanged, rather than the 436 in the initial audit stage.

The existing palette geometry test now asserts readable light/dark text polarity as well as geometry. All 62 preserved and 30 new automated Android cases pass locally. A separate supplemental test imported the exact unmodified HM 2.0.3 ZIP and rendered six portrait/landscape Light/Dark/OLED configurations against this final source. No theme ZIP, artwork, native engine, or playback behavior was changed by this readability correction. CI still requires all 92 tests and the signer/native/resources checks before publication.
