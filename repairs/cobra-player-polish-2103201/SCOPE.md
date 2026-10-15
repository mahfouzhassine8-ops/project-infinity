# Cobra 2103201 player interaction and polish scope

Parent: exact verified 2103200 at 3a74876701abfd9e1382e466c07a5f3388abaef4. Complete rollback was archived, hash/CRC verified and saved before runtime changes. It includes the exact signed APK, all generated Android inputs, recipe snapshot, receipts, evidence and restore instructions.

## User observations and clarified intent

- Holding the visible scrubber opens the Live TV drawer.
- A saved English subtitle preference appears to conflict with the current-track sheet, which lists only an Off action and undetermined-language audio.
- Repeated functions and confusing presentation should be cleaned up; existing functions must still work.
- Fold Adaptive should automatically fit the actual usable display across screen sizes and orientations.
- Subtle player and application animations are welcome where they improve the existing presentation.

## Evidence and boundaries

The local buffer can be READY while the real seek control is hidden. The visible progress line then passes touch through to the background long-click that opens Live TV. Repair gesture ownership and reuse existing local-rewind activation when the user commits a seek. Buffer creation, ingest, playlists and native engine stay unchanged.

The screenshot does not establish a supplied subtitle track. The saved preference picker offers common languages unconditionally, whereas the active picker enumerates actual supported tracks. Clarify these different functions, display subtitle availability even when audio is present, and repair proven runtime-state/cue/discovery issues. Selecting a preference cannot manufacture captions. No extractor flags or decoder changes are justified by this screenshot alone.

Fold Adaptive currently adds a small crop for near-matching viewport ratios. The clarified contract is proportional whole-frame fit in the measured usable viewport. Expected bars caused by different screen/video ratios are allowed; stale viewport dimensions and arbitrary crop are not. Modes 0–11 remain unchanged.

Remove only demonstrated duplicate routes, beginning with the Options Aspect row already served by the dedicated Aspect button. Keep all unique functions and saved preferences. Retain the original four player toolbar actions and existing menus.

Motion changes normalize cancelled/replaced animations, honor disabled system animations, and add restrained feedback to existing controls. Video surfaces, playback, seek positions and transport are never animated.

## Evidence classification

Source and host checks, Android/Robolectric input/layout tests, package/signature verification, and physical device observations are separate. New regressions must exercise actual event dispatch, selected state, cancellation and rendered geometry instead of merely checking stored mode values. Intentional changes to old test expectations will be explicit; inherited case identities and assertions unrelated to the changed user contract remain protected.
