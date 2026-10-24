# Infinity 2103401 — focused physical Fold acceptance

Device: Samsung Galaxy Fold 8 Ultra, Android 17 / API 37.
Status: NOT RUN for this corrective source. No newly built or signed candidate exists yet. Do not install these source overlays as component ZIPs: CC32 requires the matching compiled owner/installer and native recovery protocol.

Before physical testing, the deliverable must identify its GitHub build, exact commit, APK SHA-256, permanent signer, package/version identity, and matching component ZIP hashes. Package identity must remain com.projectinfinity.kodi / 2103401, and the permanent certificate must match the installed signed reference (SHA-256 d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7). Signing and package integrity are required; shutdown acceptance is independent and is not a prerequisite in this cycle.

Preserve an existing verified backup/export of profiles, settings, favourites and local tracking outside Infinity's app directory. Do not uninstall, clear data, reset databases, remove providers or change existing settings. Do not replace live database files with a raw backup while Infinity is writing them.

Install-over order after a verified signed build is delivered: APK first. Confirm that Command Center 0.3.5.32, Watched Bridge 1.0.13, UI Repair 0.1.15 and skin 1.0.5.239 are active. If user-installed copies shadow bundled components, apply only the exact matching ZIPs: Command Center → Watched Bridge → UI Repair → skin. Finish the complete matching set before testing tracking actions.

| Case | Physical steps | Required observation | Result |
| --- | --- | --- | --- |
| 1 | Open previously working saved movies and shows from their existing lists. | Same destination/provider and behavior; no unnecessary chooser. | NOT RUN |
| 2 | Open Love After Lockup: Relationship Rehab, TMDb330430, from the failing Watchlist route. Explicitly choose Umbrella. Open again from Watchlist and Save for Later. | Correct seasons/episodes; choice remembered; subsequent openings go directly to Umbrella without retrying POV. Kodi Favorites remains unchanged. | NOT RUN |
| 3 | Exercise an unavailable or failed saved route, explicitly choosing Seren or another verified compatible provider. | Correct media identity, selection required, preference changes only after verified success; failed last choice retained until a successful replacement. Record POV/Umbrella/Seren results individually. | NOT RUN |
| 4 | From an actual search result, long-press → Infinity Trakt. Add/remove Watchlist and Save for Later; mark Watched/Unwatched. Open the saved movie/show. | Actions apply to the exact item, without compatibility warnings or unrelated data changes. Local tracking works independently; external Trakt is not claimed. | NOT RUN |
| 5 | View actual Home → TV → Continue Watching with multiple unfinished episodes of one verified series. Open its resume menu. | One card per verified series, most recently updated episode and correct resume position; all episode progress and completion history retained. Movies remain separately tracked. | NOT RUN |
| 6 | Time Trakt menu opening, saved-list navigation, provider selection, remembered reopening and Home card interaction during ordinary use. | Record actual seconds and any freeze, including where it occurs. No claim that the previously reported Home freeze is resolved without this evidence. | NOT RUN |
| 7 | Display Play/Pause while playing and paused, including light and dark appearance. | White symbol on the existing neutral dark disc, no cyan fill/glow; same size, position and action. Other controls, timestamps, rotation and rendering unchanged. | NOT RUN |

Choice persistence must also be observed on a later ordinary session. Do not run a Close/reopen or Essential-First acceptance suite for this feature cycle. Record any not-yet-observed cross-session behavior as NOT RUN.

For a failure, record the exact case, provider, verified media ID, observed destination, active component versions and elapsed time; retain the existing diagnostics export. Installation alone is not acceptance or final lock. Existing independent shutdown failures remain documented and runtime protections remain enabled.
