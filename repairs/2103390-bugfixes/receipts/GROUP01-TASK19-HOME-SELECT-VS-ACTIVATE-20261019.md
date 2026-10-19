# Group #1 / Task 19 — Movies↔TV category navigation and provider ownership audit (read-only)

**Date:** 2026-10-19. **Status:** REAL 2103390 signed APK inspected, **5/5 host checks pass**, exact repeat/reload ROOT CAUSE still NOT PROVEN, **NO #19 implementation**, NO actual Fold validation. Group #1 remains in progress.

## Source findings that distinguish navigation and redraw triggers

- The original signed base 2103390 (SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`) has exactly 14 Home.xml variants. In all fourteen, the category selector is `<control type="wraplist" id="9000">`.
- **MOVIES and TV SHOWS selection** changes the current `Container(9000).ListItem.Property(section)`; four distinct Home widgets display when their respective category visibility conditions evaluate true. Moving selection within Home is different from **activating** a category, whose original click route is `ActivateWindow(Videos,...)` and intentionally opens an entirely separate Kodi window. Returning from that window may run Home init and cause a new provider fetch. The source alone does NOT show which exact path was used for each user-reported blanking event.
- Original normal latest-release panels 8101 (Movies) and 8102 (TV) use `plugin.video.umbrella`. Original Continue Watching panels 8830 and 8831 use `InfinityCompactContinueMoviesPath`/`InfinityCompactContinueTVPath`, which in the original shipped first-party include select `script.infinity.uirepair`/Command Center. The URL owners and refresh contracts differ.
- The original already uses `Infinity.ContinueWatchingRevision` in the first-party Continue Watching content URL, and `widgetreload-movies` / `widgetreload-episodes` in Umbrella's URL. Those refresh controls must remain live for real progress, provider or media changes. A global cache, blanked refresh gate, or new background data store is not justified.
- Related previous private built-in diagnostic capture shows 20 new Continue Watching requests over ~49.584 seconds under ONE stable saved-data revision, all 20 plugin snapshot reads had cache_hit=0; nine movie and eleven TV requests. This is evidence of repeated jobs, but not of who reset the native directory provider. The original user's video shows Umbrella and Continue Watching blank at the same category transition. No guessed runtime cause or third-party patch was implemented.

## Saved read-only reproducibility and tests

- Source `repairs/2103390-bugfixes/group1/home_category_contract.py`, commit **`6dcb0ce4d1003e4e7cda4352f8b9fcc72ee33f8c`**, exact Git blob `fd1f7bc2242be6e4ecf322be777953900f1820d7`.
- Tests `repairs/2103390-bugfixes/group1/test_home_category_contract.py`, commit **`52c1840810dee5e74419101c1fab499226f6cfbf`**, exact Git blob `e52179b433c6ee2bc69d5b0502c6a9fd454342ba`.
- **5/5 PASS**: original signed hash, all 14 Home variants, the four expected media/category panels, two category route types, refusal to accept altered APK and privacy-free summary. No raw user history, URLs, titles or plugin tokens committed.
- Native upstream Kodi code documents that hidden controls may skip provider updates, while provider state resets can be forced on resource deallocation and a changed provider result. Neither source proves which of those occurred on the user's Fold. No native/skin behavior modified for #19.

## Next #19 gate

Collect an **exact event-correlated** Fold trace of category-focus versus category-activation, Home window init, panel visibility, evaluated plugin URL + revision, native invalidation/reset reason, and timing for two categories (including umbrella and CC). Then restrict any actual fix to the proven Infinity Home lifecycle/visibility/URL issue. Preserve legitimate updates, Umbrella implementation, source playback history, memory/ANR behavior and all controls. Verify >=6 category switches with populated rails on both Fold screens, orientation changes and Close/reopen. **Do not mark #19 completed without physical proof.**
