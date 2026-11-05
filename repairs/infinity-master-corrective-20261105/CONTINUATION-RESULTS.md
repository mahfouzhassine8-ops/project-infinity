# Continuation from62028085

**Not release-ready. No native patch applied, APK/component build, signing, installation, promotion or lock.** Completed navigation, Browse Files, thumbnail, global-view and portrait/landscape drawer corrections remain preserved. Protected components and user data are untouched.

## Search All versus direct-provider evidence

The user's new physical report establishes successful Crew and Nixtoons direct-provider searches. They are not treated as incapable of search. Recording bytes are not exposed here, so no recording playback or original aggregate status is claimed.

[Exact source comparison](SEARCH-ALL-COMPARISON.md) traces aggregate request → state comparison → answer discard → provider heading publication. The rejected heading retains the original query URI and opens the normal provider interface. Selecting a provider in the Search form instead still reaches the common guarded results handler; the two paths must not be confused.

The source now records one bounded `INFINITY_SEARCH_STATE` event per rejected aggregate response using the existing Kodi logger. It captures original status/count, cache flag and changed-component reason names, reusing the same reads as validation. No query, route, title, settings value/key, path, hash or token is logged. Logging failure cannot change the decision or replay the provider. No change to source verification, native lease/cancellation, concurrency, cache validity or meaningful/intervening settings-change rejection.

This is diagnostic completion, **not the Nixtoons settings repair**. The timestamp and Nixtoons acceptance assertions still FAIL. Final semantic XML snapshots alone would accept the existing temporary-configuration/restore counterexample. Native settings notifications are both caller-ID restricted and incomplete for direct-file writes/failures; Crew's repair path demonstrates why callback-only exemptions are unsafe. No provider patch, identity spoofing, field exemption, blind retry or settings-retirement change is made. Crew's actual phone state delta remains unknown.

## Favorites read-only diagnostic

The existing standalone state probe now has an explicit `favorites` mode. [Script and usage](diagnostics/README.md) compare active-profile/system file structure with native directory/API counts and the active Favorites container, skipping modal/unknown UI state. Counts/status only; no titles, actions, URLs, paths, credentials, settings writes, collection reload, other-profile scan or Favorites mutation. Its original Search sampler/readers and exclusive report writer remain unchanged.

The first-party Add to Favorites path already uses the same `Favourites.GetFavourites`/`AddFavourite` backend as native browsing. There is no evidence for a disconnected collection or a need to migrate data. Native load/lock/filter state still requires device observation. The probe is delivered, not deployed; no authorized device/script-launch route is exposed. Missing-items attribution remains **UNCONFIRMED**.

## Touch authorization boundary

[Exact request and unapplied patch](TOUCH-AUTHORIZATION-REQUEST.md) restrict proposed native changes to:

- `xbmc/input/InputManager.cpp`: existing Infinity Android touch admission.
- `xbmc/guilib/GUIBaseContainer.cpp`: existing media/Home-Favorites touch handling, legacy Option B/Resume hold-pair suppression and clearing an existing pair on actual focus loss/rebind.

The proposal reuses `InfinityTouchPress`; it preserves source/title ownership, transformed hit testing, original context/playback action dispatch, one-tap parent/Back navigation and direct buttons. No header/class layout, playback, settings, shutdown or other native source is changed. Before applying to verified native inputs, the user's requested separate narrow authorization is required. The source proposal has not been applied even to the native reference workspace.

## Focused verification

| Check | Result |
|---|---|
| Affected Search safeguards and prior corrections |15 PASS against final diagnostic source. [Output](results/SEARCH-CONTINUATION-FINAL-GUARDS.txt). No unrelated suites.|
| Aggregate publication/rejection diagnostics |10 distinct cases PASS cumulatively: exact provider URI retained, original completed/count recorded, Nixtoons category, fresh/cache isolation, no private data, logger failure, source/cancel priority and same metadata/file reads and exact guard-hash equality to62028085. [8 cases](results/SEARCH-PUBLICATION.txt), [read-reuse check](results/SEARCH-TRACE-READ-REUSE.txt), [checkpoint guard equality](results/SEARCH-CHECKPOINT-GUARD-EQUIVALENCE.txt).|
| Required settings/Nixtoons behavior |**2 FAIL** on current source. [Visible failures](results/SEARCH-REQUIRED-STILL-FAIL.txt). No waiver.|
| Favorites diagnostic |11 distinct host cases PASS cumulatively. [10 cases](results/FAVORITES-PROBE.txt), [final real-reader/modal case](results/FAVORITES-UI-READER-FINAL.txt). Synthetic inputs only.|
| Touch proposal scope/immutability |5 PASS on the final proposal, including exact legacy context preservation. [Output](results/TOUCH-LEGACY-HOLD-REGRESSION.txt). Native files remain unchanged; SetFocus is preserved.|
| Controller/framing helper and proposed focus/hold snippets |Host compilation and16 cases PASS; together with5 scope checks this is6 test methods. [Final output](results/TOUCH-LEGACY-HOLD-REGRESSION.txt). Full proposed GUI methods and ARM64 engine NOT COMPILED. Earlier14-case focus evidence is retained.|
| Initial touch harness |Failed extraction retained: enclosing native `#endif` was mistakenly included. Extraction-only correction passes; this was not an engine compilation failure.|
| Refocus review |Initial unconditional SetFocus clearing was rejected before application; the final OnMessage target-ID condition preserves a valid same-control second tap. Native GUIWindow focus ordering was inspected; mocked-message regression passes.|
| Frozen native input binding |Both proposed files match restored451 source-map hashes; [final read-only apply check](results/TOUCH-PATCH-CHECK-FROZEN451-FINAL.json) passes without changing either file. Unaccepted453 engine changes are excluded.|
| Source/member plan |Only the approved Search overlay and diagnostic/test/documentation files change in this continuation.12 planned source-overlay members; no native/DEX replacement or actual candidate APK.|
| Exact approved PNG SHA/visual inspection |NOT RUN; user will provide PNG separately. No substitute reference or independent browser generated.|
| Phone Favorites data, actual provider delta, Android/Fold/gesture/runtime and install/recovery |NOT RUN; no connected authorized target.|

No unrelated shutdown suite was run. Previous passing evidence and failures are retained. A current source inventory is in [PLANNED-MEMBERS.json](PLANNED-MEMBERS.json); it is not an APK preservation comparison. Final installed version/base, complete browser/touch/Search behavior, module authentication, exact APK preservation, original signer and forward recovery remain mandatory release gates.
