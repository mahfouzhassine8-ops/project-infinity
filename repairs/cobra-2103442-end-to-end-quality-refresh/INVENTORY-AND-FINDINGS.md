# Signed 2103442 inventory and initial defect register

Read-only checkpoint before production edits. Source is the canonical DEX and
readable translation of the original-key signed 2103442 Cobra owner, not rejected441.
The accepted lock resolves to `2e88f85250ef2e46952192cf0fdb42ac5af7c9c8`.
Delivery and user-acceptance documentation were retained by documentation-only
cherry-picks; no accepted binary was rebuilt or replaced.

## Actual owners and routes

| Area | Installed owner and contract |
|---|---|
| Primary modes | `cobraPremiumViewMenu` enumerates `CobraModeLayout.MODES`: `mobile`, `grid`, `compact`, `cards`, `focus` (normal Pro). |
| Pro Sports | Separate Pro state/route, with its own hero/sports geometry; not a sixth replacement for normal Pro. |
| Multi-View | Existing `CobraLayoutCatalog`: equal2, four PiP corners, main2, overlay2, columns3, grid4, main3, overlay3 (11). |
| Guide navigation | Channels, categories/groups, All/Favorites/Recents, search, EPG/schedule, native row actions; Pro's six existing horizontal tabs. |
| Additional routes | Existing sports schedules/teams, VOD movies/shows/details/episodes, recordings/history, source/profile/settings dialogs remain native Cobra routes. No new backend or replacement route. |
| Presentation | CobraModeLayout, CobraPresentation, CobraVisualRenderer, CobraCardsLayout/Theme/Tiles, CobraProUi and CobraProExpandedLayout. Existing preferences drive light/dark/OLED and ambient effects. |
| Playback | InfinityLiveActivity is **Cobra-owned** despite its legacy name. Existing CobraPlayerBinding/vitals own preview/fullscreen/Multi-View state; native Media3 and shared bridges are frozen. |
| EPG | Source-identity/generation gates, full XMLTV plus stream-short-guide publication; native `cobraProgrammeAt`, `cobraNextProgram`, `cobraPrograms`; minute freshness and visible-guide fetches retained. |
| Refresh/cache | Existing ProfileDataReuse, channel projections, CardsReuse, bounded logo executor/cache and per-mode scroll/focus restoration are already accepted. Do not reimplement or claim their historic gains as new. |
| Lifecycle | Existing alive/session/generation checks, presentation tick, audio/preview/Pro observers and foreground/resize paths. Pro listener removal is present; no leak is presumed. |
| Protected | Infinity owner ZIP, second Cobra DEX when unchanged, all shared/native DEX/resources, chooser, icons, shutdown and all user stores. |

## Prioritized findings before implementation

| Finding | Reproduction/evidence | Owner / severity | Baseline metric | Minimal proposed correction |
|---|---|---|---|---|
| Repeated date-format construction | Signed `formatTime(long)` creates `SimpleDateFormat` and `Date` for every programme label; called by visible-row and header refreshes. | Cobra activity / performance | Host measurement selected, pending | Reuse only formatter machinery if measurement supports it; retain exact pattern, locale, timezone changes and thread safety. No text/result freshness cache. |
| Repeated full+short-guide merge | `cobraNextProgram` calls `cobraPrograms`, which copies, builds ranges/dedup keys and sorts when both lists exist. | Cobra EPG presentation / performance | Host measurement selected, pending | Investigate exact merge precedence and mutability first. No identity-only or stale cached programmes. |
| Mode/theme/resize/interaction consistency | Full accepted code is available; no new failure assumed. | Cobra UI / assessment | Matrix selected, pending | Repair only reproduced defects; preserve all already working layouts and callbacks. |
| Async/lifecycle stability | Generation guards and Pro cleanup already present. | Cobra lifecycle / assessment | Focused evidence selected, pending | No speculative crash patch, extra polling, retry or worker. |

Host measurements use actual owner DEX translated to JVM, Robolectric API35 native
graphics, synthetic channels/EPG and controlled player state. They are not Android
17/Fold decoder measurements. Android and physical-device results are recorded
separately. Selected tests are in SCOPE.json; no shutdown tests are selected.
