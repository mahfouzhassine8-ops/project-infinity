# Runtime v3 structural UI audit

## Finding
The 1.3.0 package installed successfully but produced no structural change because Runtime v3 validates/stores `cobra-ui.json` yet its `UiContract` only consumes the previously implemented scalar presentation tokens. Unknown `views.mobile` / `views.tv_guide` objects are accepted by schema validation but ignored by rendering.

## Required runtime bridge
The runtime must consume the structural view contract and map it to presentation behavior without transferring ownership of playback/native contracts to the ZIP.

Required bridge capabilities:
1. `views.default` / `views.available`: choose Mobile or TV Guide presentation.
2. Mobile presentation: preview-first shell, category/filter surface, channel rows, long-press context action sheet.
3. TV Guide presentation: favorites/groups navigation, timeline/channel grid, now marker, preview selection state.
4. First activation of a guide item updates preview; second activation of the same item promotes through the existing `playChannel` fullscreen path.
5. Back from fullscreen restores guide state/selection.
6. Runtime reload/install must rebuild the current Cobra presentation immediately after `cobra-ui.json` changes.

## Protected ownership
ZIP remains declarative. Kodi native, renderer, provider/playback engine, rotation/Fold ownership, background/resume and Infinity handoff remain native. Runtime validates those protected contracts before activation.

## Release plan
One Android presentation-runtime bridge update above 2103141. No Kodi native rebuild. Once installed, Mobile/TV Guide visual revisions return to UI ZIP delivery.
