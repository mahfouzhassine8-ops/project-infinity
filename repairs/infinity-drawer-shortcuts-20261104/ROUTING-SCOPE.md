# Infinity drawer: restore four direct shortcut destinations — 2026-11-04

**Status:** User-confirmed desired destinations / source investigation only. Not repaired, signed, installed, promoted, locked or physically tested. This branch is documentation-only. Base: `work/infinity-kodi-ui-2103454-2103455-packaging-20261104` (the 454 UI and 455 forward-recovery record). Actual installed Galaxy Fold build has not been independently identified for this report.

## User-provided intended destinations

User's screen recording and four screenshots establish that the **top-level Infinity drawer** should open the existing native provider/destination screens directly:

| Main drawer label | Direct destination | Preservation requirement |
| --- | --- | --- |
| Movies | Installed **Umbrella** Movies destination, as previously configured/working | Do not open the Command Center intermediate `Infinity Movies` menu or replace installed provider |
| TV Shows | Installed **Umbrella** TV Shows destination, as previously configured/working | Do not open the Command Center intermediate `Infinity TV Shows` menu |
| Sports | Installed **SportHD** root/menu displaying `LIVE EVENTS` and normal SportHD options | Do not silently substitute playlistbrowser or another provider |
| Favourites | Existing Infinity/Kodi native **FAVOURITES** browser (`Saved destinations • Infinity`) | Preserve all user favourites/saved data; a `..`-only screenshot is not proof of data loss |

Both supplied Umbrella screenshots show an Umbrella listing. Verify the actual installed/movie vs TV route identities; the visual similarity is not proof that both should hardcode one URL. Neither installed provider ID, installed revision, nor historical target URL was verified from the screenshots. Infer no plugin action/query syntax without source or runtime proof.

## Read-only source finding

The UI454 candidate XML file
`repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml`
currently sets:

- Top-level Movies: `ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=movies,return)`.
- Top-level TV Shows: `ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=tv,return)`.
- Sports: `RunScript(special://skin/resources/lib/infinity_library_navigation.py,sports)`.
- Favourites: `ActivateWindow(favouritesbrowser)`.

Its on-demand navigation helper `repairs/infinity-kodi-2103453-ui-navigation/navigation.py` accepts a configured `plugin.video.playlistbrowser` Sports path; this is **not** the demonstrated SportHD menu. Favourites' target matches the screenshot and should not be changed unless a separate route defect is proven.

The Library section's separately labeled Infinity Movies and Infinity TV Shows entries are independent and must **remain unchanged**. The Search `state_changed` investigation is separate.

## Boundaries / exact next checks

1. Confirm the user's actual installed APK version, approved module hashes, and last working destinations if evidence exists; locate the exact *installed* Umbrella and SportHD browse entrypoints from source/verified addon metadata instead of guessing plugin URLs.
2. Compare current routes with last working navigation and restore **only** the main drawer shortcut targets. Do not remove/replace Command Center, mutate addon identities, or disturb the separate Infinity Library buttons.
3. Preserve loader ownership and route-bound loading indications when changing any destination. Retain close, focus, Back/return, cover/inner behavior, menu styling and permissions.
4. Verify native Favourites reads the intended saved-destinations backend; an empty list alone is not grounds for clearing, migrating, or overwriting favourites.
5. Select narrowly scoped contract/host checks and, when authorized, physical Fold QA for four paths, disabled-provider handling, Back/return, and preserved saved items. No unrelated test suites; no shutdown verification.
6. No Cobra, Preview, search, player, installed providers, Kodi native, data, databases, settings, logging, security, signing policy, recovery or accepted/locked branches may be changed. No uninstall/data clearing/provider reset.
7. Stop with a named blocker if exact target verification or original-key signing/forward-recovery gate is unavailable. No unsupported fallback destination, speculative patch, or APK claim.

**Deliverable of this checkpoint:** exact user-intent routing specification plus source mismatch identification; no production modification, tests, APK or user-data access.
