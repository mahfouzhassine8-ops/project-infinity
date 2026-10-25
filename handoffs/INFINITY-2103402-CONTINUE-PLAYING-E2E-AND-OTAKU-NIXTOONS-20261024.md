# Infinity 2103402 — Continue Playing end-to-end findings and pending context menu corrections

**Investigation only. No source repair or APK was built here.** Baseline 2103401, Cobra, databases and the five Fold-approved UI corrections remain off limits. Findings use exact signed 2103402 matching-version artifact from GitHub run **40153625864** and the previous signed 2103401 reference.

## Proven root blocker: UI Repair rejects revised Command Center

**UI Repair 0.1.18** routes Home Continue Playing for both TV and movies to its own plugin when enabled. The normal/compact TV rail is panel **8831**, with `InfinityCompactContinueTVPath` selecting `plugin://script.infinity.uirepair/?action=continue&media=tv` ahead of the direct Command Center route.

The actual `script.infinity.uirepair/plugin.py` executes `controller_access.load()` before reading the local saved `continue-watching.json`. That loader checks all 25 Command Center file SHA-256 hashes pinned in `CONTROLLER-PREIMAGES.json`. The latest matched `0.3.5.35` Command Center contains newer, Fold-approved files, while UI Repair still expects the old signed 2103401 hashes.

| Expected original file | Original hash prefix | Actual 2103402 hash prefix |
| --- | --- | --- |
| `information.py` | `c388b833` | `8cf3cfca` |
| `resources/skins/Default/1080i/InfinityInformation.xml` | `bcfae57f` | `b9059729` |
| `service.py` | `ca923350` | `51fc63f6` |

Original 2103401 had **0/25** mismatches. Latest signed matched 2103402 has **3/25** mismatches. The separately updated Watched Bridge `1.0.16-MATCHED-QA` has **0/25** mismatches: that earlier compatibility repair failed to update the independent UI Repair gate.

Actual released-code host reproduction: `controller_access.load()` deterministically raises `Command Center differs from the verified version. Your saved data was left unchanged.` before `hub.load_view`. The actual UI Repair `plugin.main()`, executed with mocked Kodi calls for both `media=tv` and `media=movie`, emits **zero items**, then `endOfDirectory(succeeded=False)`. Since the skin doesn't fall back when this route fails and hides the Continue heading if 8831 has no items, it produces a blank Home rail. These are source/package-level results, not a claim of physical Android 17 PASS.

In-memory dry-run: replacing only the three expected SHA constants with their exact signed-2103402 values makes the UI Repair table match **25/25** installed Command Center files. All other mandatory verifications and component code remain unchanged. **No changes have been installed or committed to a component yet.**

## End-to-end state pipeline and limits

- **Write:** Command Center's resident playback callbacks arm verified media/episode identity, record progress and save `continue-watching.json` through the existing essential persistence participant. The `resume_hub.py` and `plugin.py` bytes are unchanged from accepted 2103401; only a Home reflow revision path in `service.py` changed.
- **Read:** `hub.load_view` validates the saved state/participant, and `hub.entries(data, 'tv', 'items')` filters `media='tv'`, excludes explicit `resume_hidden` items, and groups proven series identities. These remain intact.
- **Display:** UI Repair's hash rejection happens *before* that read; therefore current stored record count is unobserved.
- **Evidence gap:** the supplied `Infinity-Diagnostics-20261024-202236.zip` contains native widget timing and version metadata but **does not contain the actual saved `continue-watching.json` or current post-.35 TV record counts**. It only identifies an earlier .36 installation with `command_center_applied=false`. Do **not** infer data deletion, successful restoration, or the latest on-device participant status.
- **Scope:** The failing UI Repair gate affects both TV and movies when both use that proxy. If movies are visible via a different rail/Trakt/direct path, verify that separate source before claiming this one gate explains a TV-only symptom.

**Corrective action required:** Update only the three revised CC hashes in UI Repair's `CONTROLLER-PREIMAGES.json`, keeping all 25 pins and module ownership checks mandatory. Verify all native and reciprocal component contracts after repackaging; do not change CC back to outdated code, bypass hashes, or alter Resume Hub data. Add positive/negative host tests for TV/movie and installation states, and confirm TV card count and saved-record presence on the Fold using **sanitized read-only counters** (stored `items`, `media='tv'`, `resume_hidden`, `hub.entries`, UIRepair output and panel 8831). Do not export raw watch history or reset state.

## Newly logged: unfinished original system-wide context menu

**Otaku and WatchNixtoons2:** User confirmed both providers return Re:ZERO search results (WatchNixtoons2 needs the punctuated query `re:zero`). Press-and-hold instead shows an Infinity Trakt *unsupported verified media identity* notification. The shared `context.title_popup` requires trusted identity **before** opening any title menu. The Search publisher merely forwards IDs supplied by each provider; neither the anime MAL identity nor missing unique IDs can be converted into TMDb/IMDb by guessing.

**Required behavior:** Preserve original provider routes and exact-item selection; open a useful context menu even without tracking identity (Open in Provider, Information and supported local/Favorites actions). Block only **identity-dependent mutations** (Mark Watched/Unwatched, Watchlist, Save for Later, etc.) until verified by a supported source. Reuse existing provider metadata proof; do not match by similar title, fabricate IDs, migrate or delete saved data. Test Otaku and WatchNixtoons2 separately.

**Other unfinished user observations:** Favorites long-press sometimes opens a tall/narrow black popup; Home posters still reload after playback (partially faster); provider chooser/focus, native Search SIGBUS, and unrelated shutdown issues remain open. Do not misrepresent these as fixed.

**Acceptance:** Preserve 5 user-passed visuals, exact provider/search/playback routes, Cobra, 2103401, all data, no clean install. No new APK should be promoted until **all** matching APK/add-on/native hash contracts pass and the Fold confirms the corrected behavior.

This is a preservation checkpoint and scope ledger. GitHub Issues is disabled in this repository, so the evidence is recorded as a separate handoff document on this investigation branch rather than editing shipping source.