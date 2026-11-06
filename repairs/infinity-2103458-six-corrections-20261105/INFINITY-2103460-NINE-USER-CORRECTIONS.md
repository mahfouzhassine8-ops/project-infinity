# Infinity 2103460 — Nine User-Authorized Corrections (Saved Reference)

**Status:** SAVED FOR FUTURE IMPLEMENTATION — NOT IMPLEMENTED OR TESTED BY THIS DOCUMENT.
**Source foundation:** The installed **signed 2103460** is the protected working foundation. Preserve the improvements and functional behavior already present in 2103460; do not revert to 2103458. Keep the previously signed releases as historical/recovery references only.
**Authority:** These nine issues were specified or accepted by the user during physical Fold testing of 2103460. They form the exhaustive currently authorized correction scope. This document is documentation only: no APK, source, skin, provider, Android permission or native engine changes are authorized merely by saving it.

## Nine Corrections

1. **Power must be last in the entire Infinity drawer.** Power is the absolute final visible drawer entry, not just the last entry under System. The Explore section currently appears beneath Power. Preserve unrelated features and navigation, including Explore functionality; move/reorder rather than delete unrelated features without further approval.

2. **Infinity Movies drawer shortcut opens the existing Infinity Movies menu.** Use the *same action/destination already used from Infinity's main interface* to open the real Infinity Movies menu, including its existing Continue Playing, Watchlist, Save For Later, Collections, and other entries as present. It must be a direct shortcut, with no extra intermediate screen, and **not** a new/empty Kodi `videodb://movies/titles/` titles library. Preserve original content and actions.

3. **Infinity TV Shows drawer shortcut opens the existing Infinity TV Shows menu.** Use the *same action/destination already used from Infinity's main interface* to open the actual Infinity TV Shows menu, including existing Next Episodes, Progress Shows, Continue Playing and other entries as present. Direct shortcut, no intermediary, **not** the empty Kodi `videodb://tvshows/titles/` titles library. Preserve original content and actions.

4. **Remove unwanted visual footer elements universally across Infinity.** Eliminate the white curved graphic/line identified in the user's screenshots, the entire bottom touch-instruction bar (including “Tap = Select | Tap Again = Open | Press & Hold = Menu”), and their associated purely decorative borders/dividers **end-to-end in every applicable Infinity view**: movies, TV, Kodi/browser lists, providers, seasons, episodes, library views, both themes, front/inner Fold displays and orientations. Preserve actual tap, double-tap, long-press, Back, playback, focus and context-menu behavior. Do not indiscriminately remove functional controls or unrelated elements.

5. **Downloads: direct Kodi Files root, initially only “Add videos...” visible.** Both the drawer Downloads and any browser Downloads entry must stop automatically opening the phone Download folder / showing the current access warning. Instead open the existing Kodi Videos → Files screen with **only its genuine native “Add videos...” action visible initially**. The user will select/configure their own folder(s). Hide existing unrelated provider-source rows only in this Downloads context; do **not** delete/change the underlying source registry or interfere with ordinary Kodi Files/provider functionality elsewhere. Preserve Kodi's real Add videos workflow and user-configured folder access after they add it. No fabricated substitute button or new permission workaround.

6. **Fix Search crashes after repeated searches.** Search currently can crash the Infinity process after several queries; investigate actual cause (including native/Python worker, script-invoker lifetimes, cancellation, memory and thread cleanup) using existing evidence. Apply a narrowly proven fix, not a Search rewrite. Preserve user working Search results. Historical signal-11 summaries have no native failing stack, so crash ownership is **not yet established**. Host-simulated 30 operations are not physical Android proof.

7. **Fix misleading Search `state_changed` warnings while preserving working results.** The Crew and Nixtoons may report `state_changed`, but tapping the provider does show valid results. Preserve the currently working provider searches and safeguards; distinguish harmless self-writes/history updates from genuine configuration changes, and fix only verified false-result rejection or warning presentation. Do not classify providers as broken and do not bypass legitimate invalidation/security rules.

8. **Complete original universal browser and Info/Details visual polish.** Finish the previously approved visual corrections for movies, TV shows, all supported providers, genres/seasons/episodes, browser/list/detail views, both themes, both Fold displays and orientations. Fix overlapping/truncated text, art and synopsis placement, empty wasteful space, Cast presentation and button layout where applicable. Preserve metadata, playback, providers, selection, loading and all working improvements **already included in 2103460**. Verify on the actual Fold; static/host checks are not visual acceptance.

9. **Make Info/Details controls reliably functional.** Existing **Play, Trailer, Cast and More** buttons must perform their intended original actions, with correct touch, directional focus, navigation and Back. Play selects existing playback; Trailer uses existing working trailer route when available; Cast shows/navigates cast when metadata exists; More opens its existing intended options. Fix clipped labels, inaccessible focus, excessive whitespace or missing Cast display where real data exists, without fabricating metadata. Apply consistently across relevant Infinity Info/Details views; preserve original behavior outside requested repairs.

## Nonnegotiable Preservation / Release Boundaries

- **Protected working baseline: 2103460.** Preserve what 2103460 already improved. Do not reset working implementation to 2103458 or reinterpret the list as permission to start over.
- **Cobra: completely untouched.** All Infinity functionality outside the nine corrections stays untouched: providers, Search behavior that works, playback, favorites, other navigation, context menus, UI, sources, settings, saved data, signing and recovery.
- Touch only the proven minimum files/dependencies necessary to implement these nine. If a change genuinely requires additional scope, seek the user's authorization first.
- User does **not** want serial single-fix APK loops. Consolidate fixes into one forward install-over candidate, signed with the original identity, retaining user data. No uninstall, reset or source deletions.
- Do not mark “PASS” merely because a host harness, XML check, Linux fixture, APK compilation or signature check passed. Physical Samsung Fold acceptance for all nine is required.
- **This saved checklist is not implementation approval.** No source patch, APK build or baseline promotion is implied. The user will decide when to proceed.

## Evidence / Current Outcome

- During actual 2103460 testing, user screenshots showed Power followed by Explore; empty VIDEOS → Titles for both library drawer shortcuts; instruction/footer clutter; Downloads access warning and a Kodi Files root containing unwanted preconfigured provider sources.
- Search provider results still appear after the `state_changed` warning, so search is **working despite the misleading report**. Repeated-search crash remains separately unresolved and not proven causal by historical signal-11 summaries.
- Browser and Info/Details visual code exists in 2103460, but completed cross-view physical acceptance and control functionality remain open.
