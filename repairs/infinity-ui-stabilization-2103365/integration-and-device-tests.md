# Integration and physical acceptance gates

Candidate: **1.0.5.207 UI Stability RC1**, ID `skin.infinity.diggz`, direct approved `.204` baseline. This is an independent skin candidate, not an accepted combined application.

## Ownership and file coordination

No native, lifecycle, Command Center, Resume Hub, provider, health diagnostic or persistence code is changed. No branch merge is performed. Protected 2103365 commit: `faf41ee1d35fe55140bb1e193089643cc9ac06ee`. Backend source inspected read-only: `48dc19c221fc41f88f3d52614beef8a877e426d6` on `work/infinity-system-stability-2103366`.

The package keeps active `unified` and the existing adaptive logical-canvas reflow. Native `repairs/inplace-reflow-2103291/inplace_reflow.py` and `repairs/mobile-regressions-2103304/native_patch.py` were inspected, never edited. Prior partial-row touch and reflow repairs are preserved. Reconcile any backend skin overlay installer with the manifest before integration: `Includes.xml`, `Includes_InfinityLegacy.xml`, `View_50_List.xml` and the custom windows are potential shared-file conflicts. Apply the .207 XML deltas to the agreed full skin; do not install a reference .206 package or silently overwrite this candidate with an older backend overlay.

`unified/DialogButtonMenu.xml` is byte identical to .204 (SHA256 `149b614b9dd96094e64c7b7a837fbc911bfceda40e4ecef84716f7a3a6220d78`). Power, Close/Force Close, timing, acknowledgments and optional motion remain backend/native owned. No new shutdown popup exists.

## Health Center contract

The inspected backend overlay at `repairs/android-checkpoint-shutdown/system-stability-2103366/health/overlay/default.py`, `_publish_dashboard_state`, publishes only these legacy Home properties used by the UI:

| Property | Existing authority | Candidate presentation |
| --- | --- | --- |
| `KHC.Status` | Legacy scan result text; no complete eight-state/freshness taxonomy | Reported status verbatim; blank becomes Unknown / not verified; only explicit Needs attention gets danger colour |
| `KHC.StatusDetail` | Legacy detail text | Bounded readable text; no green inference |
| `KHC.LastScan` | Saved scan-file timestamp, not necessarily the current scan | Explicit Saved scan label |
| `KHC.Baseline` | Legacy saved baseline string, currently can include Fresh baseline | Explicit Saved baseline (reported); backend wording remains its own responsibility |
| `KHC.Version` | Existing tool version | Footer only |

The UI cannot safely classify historical, resolved, advisory, running, failed/incomplete or newly verified healthy states from these strings. The coordinating backend must expose and verify the following proposed interface before enabling richer visuals. These property names are a proposal, not an already published or activated contract:

| Proposed Home property | Required semantics |
| --- | --- |
| `KHC.UI.StatusClass` | One of healthy, active_issue, historical_issue, resolved_issue, advisory, unknown, running, incomplete; failed/incomplete detail explicitly distinguished |
| `KHC.UI.StatusVerified` | true only for a completed verified current classification; never for an old saved snapshot |
| `KHC.UI.ScanState` | idle, running, complete, failed or incomplete |
| `KHC.UI.CurrentScanTime` | Current completed scan time; empty while unknown/unavailable |
| `KHC.UI.SavedScanTime` | Previously stored scan time, independently labelled |
| `KHC.UI.BaselineTime` | Saved baseline capture time, not fresh verification |
| `KHC.UI.StatusDetail` | Backend-authored explanation with scope and failure/advisory reason |

Coordinate these names and publication semantics, then add/test their UI binding in a separate integration commit. Do not independently edit diagnostics in this branch.

## Resume Hub and provider contract

`InfinityUIVerifiedWatchedBadge` is a dormant include with `verified=false`, `completed=false`, using the existing small check texture and blue tint. No consumer or action is activated. A verified movie/episode identity and supported watched/completed property must be provided by the backend; titles are not identity. Keep current partial progress presentation. Enable Mark Watched/Unwatched, My List, Remove from Continue Playing, Resume and View in Resume Hub only after each supported backend route is verified.

Context styling retains native group996/background999/template1000. Official Kodi 21.3 `GUIDialogContextMenu.cpp` was inspected for the background `Size - list.Size + list.GetHeight` contract. A fixed 104-unit inset supplies native chrome across adaptive canvases. Existing options are unchanged; no watched mutation is added to source links. The installed Umbrella call site is not available here. Verify on the device that Additional Link Info / Save to AllDebrid Cloud use this native shared menu. A custom provider dialog needs its actual owner identified before a separate repair; provider scraping, sorting, authentication, cloud operations and playback routes remain untouched.

## Installation and rollback

Keep the original .204 ZIP. Install the .207 skin with Kodi's Install from zip file on the existing installation. Confirm the displayed skin ID/version and active layout; preserve all userdata and settings. Existing Kodi dependencies are unchanged. Restart/reload only the skin as needed; no native engine rebuild or device reinstall is required. Installation itself still needs device verification.

Rollback to **1.0.5.204 Closing Status Polish RC1**, SHA256 `4238c9eaf341d921b319fd421bae5c47e3ed51925bed63033a558ae898787b47`. If Kodi blocks a downgrade, use Add-on Information → Versions or an explicit skin-folder restore of the preserved .204 files while Kodi is closed; do not uninstall/delete skin settings. Keep `.201` as the locked parent, SHA256 `c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5`; do not automatically revert to it.

## Device test record (all runtime results pending)

Record device model, Android/native build, installed .207 hash, skin settings, usable pixel bounds/insets, font setting, theme and backend source/hash for every run. Screenshots must show the actual running screen, with timestamps; projections are not acceptance evidence.

For each major screen, test cover portrait/landscape, inner portrait/landscape, rotation, fold/unfold, split-screen, floating/pop-up, live resize, narrow/short windows, foreground return and re-entry after long idle. Record clipping, legibility, aspect ratio, touch bounds, scroll, focus and selection restoration. Insets and live measurements must come from the running Android/Kodi surface.

| Screen | Required touch/remote/Back checks |
| --- | --- |
| Add-on Information | Installed, disabled, outdated, missing and configurable add-ons; Install/Update/Enable/Disable/Configure/Dependencies/Versions/Run/Auto-update; long title/description/disclaimer/broken reason; scroll action pane; close and return focus |
| Shared context menu | 1, 2, 10, 30 actions; first/middle/last option; internal scroll; long labels; disabled option; top/right/near-bottom invocation; close; rapid Back; resize while open |
| Provider source menu | Actual Umbrella owner; Additional Link Info and Save to AllDebrid Cloud still selectable; source order/playback unchanged; no movie watched actions on links |
| Resume prompt | Existing saved 01:04:58 position; Resume/Play From Beginning; close and Android Back; restored selection; no duplicate prompt or newly inferred title |
| Health Center | Scroll to all 13 cards plus header Scan; each original action binding; warnings/unknown/empty; backend status taxonomy after coordination; no false fresh/healthy display |
| Main drawer | Approved primary order; Power last in SYSTEM; scroll extras retained; Live TV still accessible through existing destinations; selection memory; close, touch, remote focus |
| System Hub | All six remaining tools, no duplicate Power, no empty focus target; settings and authorization routes unchanged |
| Settings/select/text/keyboard | Nested settings values persist; buttons/templates fit; categories, manual/cancel; text paging; keyboard character, shift/caps, symbols, IP, cursor, backspace, space, Done/Cancel; both text and graphical keyboard modes |
| Home/experience selector | Existing artwork, greeting, time/weather, widgets and experience layout unchanged; loading/empty/error truthfulness; returning from playback/background preserves focus |
| Movies/TV/player | Grids, long titles, metadata, episodes, progress, detail, context, restored scroll; audio/subtitle/seek overlays and time labels; no playback or watched identity regression |
| Themes | Dark/OLED, true black, light/pearl, cinema, glass, subtle/immersive; selected/disabled/loading/warning readability and transitions |

Repeat open/dismiss/Back 30 times per main modal; mix rapid touch and remote selection. Capture native logs for blank windows, dead targets or exceptions. Do not repeatedly invoke destructive Health tools merely to test layout; their controls can be verified up to their normal confirmation boundary with existing authorization.

## Representative 90-minute stability/performance scenario

| Minutes | Activity |
| --- | --- |
| 0–15 | Home/experience, Movies, TV, grids/detail/long titles; record baseline memory and 20 drawer/dialog open times |
| 15–30 | Provider directories/source menus; 1/2/10/30 native menu cases; add-on info and settings |
| 30–45 | Playback start/resume, seek/audio/subtitle overlays, return to browsing; no saved-state mutation tests until backend contract is ready |
| 45–60 | Health Center and System Hub scrolling, harmless tools/confirmation boundaries, theme switching |
| 60–75 | Rotation, fold/unfold, split/pop-up/live resize, repeated Back, foreground/background transitions |
| 75–90 | Idle/re-entry, repeat initial route and timings; record end memory, logs, screenshots and focus restoration |

Compare the same .204/.207 route and device conditions for median/p95 menu appearance and frame stalls. Record memory at 0/30/60/90 minutes and after modal dismissal. No performance improvement or native leak repair is claimed without these measurements. Backend worker timing, native directory processing, shutdown/PVR/playback and health publication defects are handed to their owning workstream, not masked by this skin.

Combined acceptance requires both branch verifications, exact shared-file reconciliation and physical Fold evidence. Do not lock or promote based solely on these automated source checks.
