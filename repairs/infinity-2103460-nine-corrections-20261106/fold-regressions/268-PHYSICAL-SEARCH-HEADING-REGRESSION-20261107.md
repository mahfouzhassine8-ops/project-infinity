# P0 — Physical Fold video confirms 268 Search All heading regression (FAILED)

**Status:** **268 Search All heading handoff FAILED on the actual Galaxy Fold; do not lock or promote.** This finding is independently observable from the user's **61.6-second screen recording** (provided 2026-11-07). The original recording stays in the conversation and is **not** committed, copied to a public repository or transformed into an installer. The earlier 268 signed update was installed; APK2103462/skin268/CC61 were previously confirmed in Health Center.

## Timestamped original-video evidence (approximate playback seconds)

- **00–05 s:** User is viewing an Infinity Search All results page for TV Shows. **Seren — 1 result** and **Otaku — 5 results** show clickable poster/title results. **THE CREW — Open fresh provider search** and **WatchNixtoons2 — Open fresh provider search** display **NO provider results below their headings**. These "fresh" labels are the changed 268 UI, not provider counts.
- **02–05 s:** User selects **THE CREW — Open fresh provider search**. This is a confirmed physical heading click, not inferred from a log.
- **06–12 s:** Kodi changes to **VIDEOS → Infinity Command Center** with only an empty/parent `..` directory area; no Crew search results. Additional navigation shows **Files / Playlists / Video add-ons**. The clicked heading **does not produce the intended provider results**.
- **19–26 s:** User opens Infinity Search from the TV home, using Search All and a saved query/history. This is the normal shipped Search UI with keyboard and history; no independent provider add-on was opened for the first test.
- **30–39 s:** The original Search All request shows *Searching compatible providers* while in a blank Videos directory.
- **39–42 s:** Search All displays **Seren — 1 result, Otaku — 5 results**, plus Crew/Nixtoons **Open fresh provider search** headings again; Crew heading is selected a second time.
- **42–52 s:** The Crew fresh handoff again opens **VIDEOS → Infinity Command Center** blank/parent view, not Crew results. **Repeatable failure.**
- **54–59 s:** A Nixtoons handoff is attempted; Kodi briefly shows empty **Infinity Command Center**, then **WatchNixtoons2** parent directory with no matching search results. **Nixtoons's result display also fails.**
- **59–61.6 s:** User exits to Infinity home. **No native crash is visibly recorded in this 61.6s video**. This clip is strong heading/navigation regression proof, not a Search crash stack.

## Exact source failure boundary
The 268 changes are present in authenticated `script.infinity.commandcenter`:

1. `infinity_search.py` `_publish_result` (near line 487) identifies `state_changed` and builds **`plugin://script.infinity.commandcenter/?action=search-open-verified&…`** via `_verified_heading_target`; it publishes this URL with `isFolder=True` and labels the item **Open fresh provider search**, leaving previously completed Crew/Nixtoons rows rejected.
2. `plugin.py` `main` `search-open-verified` (near line 936) resolves a source-verified provider URL, **ends the current first-party directory listing with zero items**, then immediately requests an asynchronous **`ActivateWindow(Videos,"plugin://plugin.video.*",return)`** from inside that same directory invocation. Kodi's standard directory lifecycle expects `endOfDirectory` to commit a listing. `xbmc.executebuiltin` is asynchronous by default, and signaling it after completion of the empty parent directory does **not** prove that native Videos navigation has rendered or won against the parent directory state (Kodi official Python API). The video concretely shows the empty first-party directory and no results.
3. Existing 50 host tests only assert command order, safe route checks and "builtin requested/returned". They do **not** model Kodi's actual directory transition/render lifetime. Mark that integration contract **FAIL on Fold**, and prevent these tests from being misused as physical PASS.

**Causal confidence:** `search-open-verified` is confirmed the 268 newly introduced route and precisely matches the visible "Infinity Command Center" empty window. The intermediate empty-directory/async native builtin is the **leading source-level explanation**; exact event ordering (whether the native builtin started/returned, provider route response or Kodi replaced the listing) requires `INFINITY_SEARCH_NAV` events and/or native window lifecycle trace. Do **not** overclaim a fully proven scheduling race or blame provider failure.

## Regression relative to previous behavior
- Prior physical trace, *before 268*, proved **Nixtoons 31 / Crew 2 real results** returned from the provider but were rejected by Infinity's `state_changed` validator. New 268 did **not fix** that validator; it replaced the rejected provider heading with a new supposedly interactive path that now demonstrably opens empty views.
- The pre-268 heading also failed to open on the Fold, so the correct comparison is **added broken intermediate navigation and misleading "Open fresh provider search" UI, not the loss of previously functioning headings**. Working Seren/Otaku results shown in this clip do not indicate Crew/Nixtoons are disabled.

## Engineering release gate: fail closed and fix actual integration
- Immediately mark **268 physical Search acceptance FAIL**. **No 268 lock, no automatic 269 recovery installation**, no unrelated rollback/downgrade, no new "fixed" ZIP without at least a real native directory lifecycle/dispatch integration proof and one user-approved Fold test.
- **Do not add a second empty plugin directory hop.** Design a single native directory navigation where the selected provider's verified original search URL reaches Kodi as the actual folder, without a competing `endOfDirectory(empty)` + asynchronous `ActivateWindow` command. Verification must be current, source/enable/dependency/profile guarded, and must not republish invalidated stale rows. If fail-closed validation cannot be maintained with a direct Kodi item URL, revert misleading active headings to an honest error until there is a validated user path.
- Independently finish the original `state_changed` writer/ABA cause with no timestamp-only bypass; retain current native lease, cancellation, source pins, meaningful-setting protection.
- Host regression must simulate **plugin directory invocation/end, queued ActivateWindow, and actual selected folder/page identity**, not merely capture `xbmc.executebuiltin` text; assert that Crew and Nixtoons open **nonempty actual provider directories** with correct request origin. Keep negative changes/ABA guards and four physically accepted passes (Power, Movies, TV, Downloads) locked.
- **Separate P0:** Three Search-tap-triggered native crashes documented in `268-FOLD-DIAGNOSTIC-20261107-SANITIZED.md` also remain unfixed; this new clip shows neither a crash nor its repair. Do not force another crash reproduction now.
- **No user questions needed:** Video provides both actual heading clicks and native resulting screens. Do not ask for a new screenshot, re-entered query or version.

**Owner impact:** 268 accepted as installed source identity, **rejected as functioning Search result/navigation fix**. Cobra, Preview, native APK462 and four physical PASS features remain protected, and the owner should not repeatedly install speculative Search revisions.
