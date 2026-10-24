# Physical Fold acceptance — Infinity 2103401, coordinated component 35 candidate

Device: Samsung Galaxy Fold 8 Ultra, Android 17 / API 37. This checklist continues
all 20 original requirements, the shared-selection contract and the performance,
refresh and responsive addendum. Every physical check below is **NOT RUN** for
this candidate. Successful packaging and host checks are not physical acceptance
or a final release lock. The Search Enter/Home freeze and the native pure-virtual
and Scudo failures remain unresolved without their actual runtime evidence.

## Candidate and installation order

Record the delivered build number, exact source commit, APK SHA-256 and matching
component ZIP hashes before installation. Do not substitute signed checkpoint
build `40086558043` / commit `c0dba465e6b74af7bd82ea0c16755d5bf7508f1e`
for the new candidate's identity. That checkpoint contains component 34.

The delivered ARM64 APK must retain package `com.projectinfinity.kodi`, application
version code `2103401`, install-over compatibility and the original certificate
SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Use the delivered source/artifact preservation receipt to confirm the Cobra
boundary; source-only or host checks do not prove a signed artifact is preserved.

Preserve existing backups/exports, profiles, settings, installed add-ons, watched
history, Resume Hub, Continue Playing, Watchlist, Favorites, Collection, Save for
Later, Search History and provider memory. **No uninstall, app-data clearing,
database reset, provider purge or replacement of live databases is permitted.**
Do not change Cobra source, resources, settings, player, navigation or data.

1. Install the verified, permanently signed candidate APK **over the existing
   installation**. Do not uninstall first.
2. Confirm active component versions. If installed copies shadow bundled
   components or the matching updates have not already applied, install only the
   delivered matching ZIPs, in this exact order:
   **Command Center 0.3.5.35 → Watched Bridge 1.0.16 → UI Repair 0.1.18 →
   Infinity skin 1.0.5.242**.
3. Complete the whole matching set before tracking or selection acceptance.
   Confirm real initialization and the applied participant/source receipts, not
   just the installer report or displayed ZIP filenames. Retain unchanged
   components, including Rails 0.2.7. Never replace matching active components
   with older ZIPs.

## Original targeted acceptance

| # | Targeted check | Required observation and evidence | Status |
|---|---|---|---|
| 1 | Install or enable a verified compatible add-on | It becomes available in appropriate Infinity operations without another APK or unnecessary app restart. Record installed version, adapter and capabilities. | NOT RUN |
| 2 | Update, disable and remove a designated QA add-on | Inventory and capability state update; disabled/removed providers leave Search All. Preserve existing user providers and their saved data. | NOT RUN |
| 3 | Movie, TV, anime and cartoon filtering | Each advertised operation has a verified route. Metadata, playable content and specialty capabilities remain distinct. | NOT RUN |
| 4 | Unknown or unsupported provider | May be identified as installed but is never advertised or dispatched as functional without a verified adapter. | NOT RUN |
| 5 | Search All | Every currently eligible provider is included, results retain provider attribution and original navigation, cancellation works, and one stalled provider does not freeze Home. | NOT RUN |
| 6 | Single-provider Search | Only the selected provider dispatches; focusing or first-tapping its tile does not launch it. | NOT RUN |
| 7 | Enter and Search-button submission, separately | Both yield usable results; results navigation, Back and Home remain responsive. Retain keyboard/dispatch/Directory/native lock evidence if the known freeze recurs. | NOT RUN — known freeze unresolved |
| 8 | Search History | Stored query is restored without automatic launch; provider selection and explicit submission remain available. History is retained. | NOT RUN |
| 9 | Common quick actions across all supported sections | First tap selects, second opens the exact title, hold opens Title Options. Applicable watched, Watchlist, Favorites, Collection, Custom List, Later and Continue actions reflect authoritative state. Dismissal retains focus and scroll. | NOT RUN |
| 10 | Information | Hold → Title Options → Information opens dedicated premium Option B for that exact selected title. The quick-action popup remains available. | NOT RUN |
| 11 | Complete original synopsis | Compare the available original metadata word for word, including whitespace-sensitive paragraphs and final sentence. Long text wraps and scrolls completely below title/runtime, without overlap or ellipsis. Poster and actual runtime remain readable. | NOT RUN |
| 12 | Play, Resume and Trailer | Original verified routes execute; Resume uses the latest valid position. Missing/unsupported trailers are not invented. Optional cast appears only from reliable available metadata and does not delay primary content. | NOT RUN |
| 13 | Continue Playing uniqueness | Same verified movie has one card across providers; same verified series has one card with latest episode/position. Rewind/restart work, unrelated similar titles stay separate, and episode history remains. | NOT RUN |
| 14 | Cross-section tracking | Removing Continue through another section suppresses the correct movie/series card without an older duplicate reappearing. Other lists/history/provider memory survive; later valid playback may restore it. | NOT RUN |
| 15 | TrackIt remembered provider | A failed saved route offers compatible alternatives; explicit successful choice opens the correct identity, is remembered and is reused on later opening. Discovery alone never replaces a working remembered route. | NOT RUN |
| 16 | Install-from-ZIP header | The demonstrated narrow blue artifact is absent; intentional divider, buttons, navigation and styling remain intact. | NOT RUN |
| 17 | Responsive application surfaces | Home/rails, Infinity Movies/TV, Search, add-ons, saved views, dialogs, settings and player return remain usable when folded, unfolded, rotated, in landscape, split screen and supported popup windows. No overlaps, missing controls or clipped action labels. | NOT RUN |
| 18 | Loading and smooth interaction | Comparable cold/warm screen-readiness, touch/menu latency, scrolling/frame-pacing, CPU and memory observations show actual behavior. Preserve 120Hz UI support where available; never force video to 120fps. Host timings do not establish device gains. | NOT RUN |
| 19 | Android component integration | Command Center initializes real participants and applies the exact 35/16/18/242 source set. Installer reporting, Watched Bridge, UI Repair, skin and verified POV 6.10.22 routes work together without bypassing source verification. | NOT RUN |
| 20 | Native stability | Investigate the actual pure-virtual and Scudo failure reproductions separately; retain original fault stacks before re-raise, allocation/map/RSS evidence and relevant GUI/Directory lock traces. Missing stacks cannot become a successful crash-fix claim. | NOT RUN — causes unresolved |

Also execute **Play → Rotate → Stop → Home** and record whether the upper-right
clock remains visible in folded/unfolded portrait and landscape. Verify existing
Light/Dark/OLED appearance, player controls and the 120Hz interface setting.
Clock and appearance verification: **NOT RUN**.

## Shared selection and refresh addendum

Exercise supported title cards on Home and Latest Releases, Infinity Movies,
Infinity TV, content rails, Search results, Continue Playing, Watchlist, Save for
Later, Collection, Custom Lists, watched/history and relevant library views.
Record exact typed media IDs, original provider route, selected row, focus and
scroll offset for each tested surface; screen coordinates alone are not identity.

For each surface, verify first-tap selection, second-tap exact-title opening,
hold without accidental activation, Information for the same title, and popup/
Information dismissal without selection or scroll loss. Check supported removal
labels when already saved and absence of Continue removal for a title that is
not actually in Continue. Native regular Movies/TV context menus, folders,
add-on tiles and Cobra behavior must remain unchanged. Synthetic next-up or
identity-unverified rows must not gain unsafe persistence actions.

Change membership in one section and revisit its corresponding other section.
Verify the expected update without a full-screen reset, duplicate card or stale
overlay. Refresh a provider or reorder a list between interactions; the selected
title must never switch to its neighbor. New provider discovery must not alter
progress, saved preferences or remembered routes. Observe persistence during a
later ordinary session without making a Close/reopen suite a prerequisite.
Selection, cross-view refresh and later-session observations: **NOT RUN**.

## Performance and responsive measurements

Use comparable content, profile size, network condition, display mode and device
temperature for the reference and candidate. Keep raw observations and failures.
Record first visit and repeated warm visits separately; do not label a warm OS
cache as a cold start. Capture actual screen readiness and touch-to-feedback/
menu-open intervals rather than substituting test duration for latency.

Cover Home/widgets, saved-library loading, provider inventory/Search submission,
Search results, add-on browsing, Title Options, Option B, scrolling, navigation
and playback-to-Home. Observe fold/rotation reflow while a popup or long synopsis
is open. Its selected item, focus and scroll must survive. Check the shortest
supported split/popup viewport: all actions and Continue card artwork/title
remain reachable without covering neighboring controls.

Record frame intervals and stalls from the actual Kodi/OpenGL surface separately
from Android HWUI samples. Record elapsed loading/menu intervals alongside CPU,
RSS, thread/map counts and sustained idle behavior where available. Preserve
battery efficiency, playback quality, full metadata and persistence integrity.
The read-only metrics helper does not itself navigate or measure touch latency.
The existing host timing and operation-count reports remain separate evidence.
No phone frame, touch, memory-pressure or full-application smoothness result is
claimed by those reports. All physical performance measurements: **NOT RUN**.

## Result recording and independent shutdown scope

For each executed case record build/APK hash, active component versions, device
orientation/window mode, exact media IDs, provider/version, expected and observed
destination/state, elapsed measurements and relevant screenshots/diagnostics.
Retain genuine failures; leave unexecuted checks **NOT RUN**. Installation alone
does not accept the release. Final physical acceptance belongs to the user.

Normal Close, Essential-First, shutdown durability, service-retirement and a
Close/reopen acceptance suite are **NOT SELECTED / NOT RUN** here. Do not run them
as feature, measurement, packaging or installation prerequisites. Existing
durability protections and independently recorded shutdown failures remain intact.
