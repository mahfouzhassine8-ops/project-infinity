# INFINITY 2103408 — PHYSICAL FOLD CREW + RED LIGHT SEARCH-ROUTE PROBE HANDOFF

**2026-10-26 — narrow parallel evidence handoff for the ongoing final seven-workstream Work session.** Do not restart, re-scope, supersede the authoritative brief, stop an in-flight ARM64 build, or defer shutdown/performance/Option B/UI/stability work. This supports the ALREADY APPROVED automatic provider search-verification correction. No runtime files changed by this handoff.

## Source of evidence and handling

- **User ran the read-only Infinity Crew + Red Light Route Probe v1.0.0 inside installed Infinity on physical Samsung Galaxy Fold 8 Ultra / Android 17.**
- Private user-provided `Infinity-Crew-RedLight-Routes-20261026-080440.zip` has exactly `manifest.json`, `ROUTE-EVIDENCE.txt` and `README.txt` (collected UTC 2026-10-26T08:04:39Z). This is installed-source evidence rather than a speculative online version match. The ZIP and any user diagnostic content are PRIVATE: do not commit the raw ZIP, user filesystem dump, provider settings, user data, API keys or private diagnostic logs to the public repository.
- Separate private `Infinity-Diagnostics-20261026-040513.zip` is also available to the user and can be attached by the user to the active Work conversation. Treat as independent shutdown state evidence, not proof of provider compatibility.
- Probe is **read-only**: reads installed `addon.xml` and bounded `.py` sources, computes file hashes and redacted search-related excerpts. Does not invoke a provider, follow network routes, read `userdata`/`addon_data`, or prove successful live Search.
- This note reports strictly what the probe actually extracted; Work can use it to avoid repeating broad repository discovery, and then verify only the missing links.

## 1. RED LIGHT — actual installed source has plausible MOVIE + TV search implementation

**Installed on physical Fold**:
- ID `plugin.video.redlight`; displayed name `Red Light`; version **2.9.1**; Kodi JSON-RPC `enabled=true`.
- Plugin entrypoint `resources/lib/redlight.py`; `xbmc.python.pluginsource`, `provides=video`; additional module extension `resources/lib/`.
- `addon.xml` SHA256 `a2ccceb1e503d3ab06242df149d6d7b87210c48d88177523a8c008e8e25b3f09`.
- **152 Python files inspected, 0 skipped, no probe warnings/errors**. The probe does NOT carry full source files; it includes hashes and selective redacted snippets.

**Actual identified code chain and SHA256**:
- `resources/lib/redlight.py` `eff3258041bb8daec747c8d437a9bde415d135c9cb97492e91f4d404608b4d10`: imports `routing` from `modules.router`; calls `routing(sys)`, then extracts incoming URL parameters with `parse_qsl(sys.argv[2][1:], keep_blank_values=True)`; reads `mode`, default `navigator.main`.
- `resources/lib/modules/router.py` `d0f6241ac206db952fa... [FULL HASH MUST BE READ FROM PRIVATE manifest.json — DO NOT TREAT THIS ABBREVIATED STRING AS A PIN]`: needs **focused examination of dispatcher mapping** from external plugin URL `mode` to movie/TV indexer; the probe's relevance selection did not include dispatcher source lines.
- `resources/lib/indexers/movies.py` SHA256 `7608fc1f0667a8223ef48715d4f03a67dc474761b5a4496ec09f1ab7d80b7177`: its special-action list includes `tmdb_movies_search`; when handling a special action it reads `self.params_get('key_id') or self.params_get('query')` (around lines 12, 64–67, 516–519). The code calls the chosen function with the search term and `page_no`.
- `resources/lib/indexers/tvshows.py` SHA256 `5824b9f9b95c0de362629b570928f21447157c06d4c13b8fc7d1f3bf74f41e37`: special-action list includes `tmdb_tv_search` (and `tmdb_anime_search`); reads `key_id` or `query` (around lines 13–14, 78–81, 521–524).
- `resources/lib/apis/tmdb_api.py` SHA256 `2670f6e42f42747e...` (read FULL hash from private manifest): defines `tmdb_movies_search(query, page_no)` at line ~348 and `tmdb_tv_search(query, page_no)` at ~489. These are real named search implementation functions but are **not themselves proof of externally invocable plugin routing**.
- `resources/lib/indexers/navigator.py` and `resources/lib/modules/kodi_utils.py` were inspected; use their hashes/source only if a gap in mode/action propagation requires them.

**What this DOES prove**: the installed and enabled Red Light 2.9.1 source has a Kodi plugin entrypoint and distinct real query-driven TMDb movie and TV search code, with observed `query` / `key_id` intake.

**What is STILL missing**: exact external `plugin://` dispatcher `mode`/`action` contract, the branch selecting indexer class/method, endDirectory/directory item return semantics, title IDs, route encoding, and one controlled live safe movie/TV search result. **Do not guess** an invocation URL or admit it into Search All until actual router proof is complete. Never blindly assume it's Umbrella's route solely from related conventions.

**Shortest productive Work path**: start with the exact installed `resources/lib/modules/router.py` dispatch, `redlight.py` entrypoint, `indexers/movies.py` and `indexers/tvshows.py` special-action branches, plus version/hash matching against a legitimately accessible source copy. Where version-matching full source cannot be retrieved, use the already captured source evidence to narrow a second **read-only scoped** source inspection and ask for that one gap only. Do not reattempt a previously approval-rejected Red Light download via an unauthorized route.

## 2. THE CREW — installed identity confirmed, but full router was NOT collected

**Installed on physical Fold**:
- ID `plugin.video.thecrew`; displayed name `THE CREW`; version **3.2.2**; Kodi JSON-RPC `enabled=true`.
- Plugin entrypoint `thecrew.py` under `xbmc.python.pluginsource`, `provides=video`.
- `addon.xml` SHA256 `17b833c8752fd7c2171939294c6a05f958e82b1e50537721189868e468ae1b91`.
- Probe found **only 2 .py files in this installed add-on folder**, no skips/errors: `thecrew.py` SHA256 `9ee54c130080be01f1fe209384e7cba04add0d09bb8edf72...` (read full private manifest), 2,625 bytes; `service.py` SHA256 `dd19417bfef7c5918efa59e671e6b17812dd019970ae6a21fcd8ad5185b7a238`, 1,704 bytes.
- **Zero extracted search-related excerpts** in this installed folder. This does NOT prove The Crew has no movie/TV search; it means this probe did not capture a search handler. The installed entrypoint may import functionality from another installed module/add-on or a packaged form not enumerated as local .py; this is a hypothesis to investigate, not a finding.

**Shortest productive Work path**:
1. Read the exact **2,625-byte installed `thecrew.py`** entrypoint or find an exact matching SHA/version through already fetched public Crew plugin module sources; discover import/dependency/dispatcher chain.
2. Read the addon.xml `requires` entries (not included in probe summary) to find any separate Kodi `script.module.*` dependency that actually owns router/indexers; only scan the identified dependency's installed **code**, never userdata.
3. Resolve external movie and TV search action/query receiver and output semantics with full source/hash evidence, then run a bounded safe Search test. Do not conclude incompatible from zero excerpts or adapt using guessed old The Crew URLs.
4. If a genuinely missing piece remains after examining existing GitHub source that Work has already fetched, request only that **narrow** read-only module-source probe rather than another broad archive or manual user verification step.

## 3. Integration contracts / expected outcomes

- Current signed Infinity 2103408 Search scans installed providers but enables only recognized reviewed source contracts (seven static reviewed contracts). Crew and Red Light are therefore listed but report "Search interface not verified for this category."
- Implement auto-recognition of demonstrably equivalent **reviewed** plugin search interface patterns per **movie / TV** capability, with exact installed version + entrypoint + source fingerprint proof; invalidate on update/disable/remove, preserve negative/ambiguous fail-closed behavior, no arbitrary imports/eval at verification time.
- On supported categories, one query routed only to the correct provider; Search All includes only verified operations. Preserve source attribution, user-selected item, result identity, Search single-flight concurrency/cancel/old-generation defenses.
- Normalize Kodi `[COLOR ...]` in displayed provider labels only, not IDs/source; clearly distinguish installed/enabled from Search-verified.
- Favor authenticated Command Center update path for provider-family compatibility so adding a safely compatible provider does **not** require reinstalling the whole native APK each time; never replace native source integrity with global allow-all.
- Report *separately* for each provider and media category: installed → actual source inspected → dispatch proof → result proof → version/hash-bound compatibility → regression → physical Fold acceptance. Red Light current status **actual query handlers identified; external dispatch unverified**. Crew current status **entrypoint/identity verified; search handler not yet located**.
- **DO NOT PAUSE or RESTART** the other original seven-workstream work: safe multi-image shutdown, Option B, Command Center, memory/CPU efficiency, cold/warm Home/poster loading, content/provider refresh, display refresh/frame pacing, touch/hold, UI/player polish and original-key ARM64 build/delivery remain active, independent priorities.
- Cobra completely off limits. User data preserved. No premature final-lock/physical-pass claim.

**HANDOFF INSTRUCTION TO WORK:** Read this file and the existing authoritative scope. The user can attach the private `Infinity-Crew-RedLight-Routes-20261026-080440.zip` to the Work conversation for complete device hashes/excerpts. Continue engineering on other approved defects concurrently; use this as an installed-device shortcut, not a new audit-only assignment.
