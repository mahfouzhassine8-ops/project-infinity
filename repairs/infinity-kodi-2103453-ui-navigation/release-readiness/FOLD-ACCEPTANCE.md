# Planned Galaxy Fold acceptance — Kodi UI only

**Not executed.** This checklist becomes executable only after separate
packaging and installation approval, verified candidate/recovery downloads, and
the gates in [READINESS.md](READINESS.md). Physical installation is not release
acceptance. Keep results as PASS, FAIL, BLOCKED or NOT RUN with actual evidence.

Use the Galaxy Fold Android 17 cover and inner displays, each in portrait and
landscape. Record actual window bounds/orientation, APK version/hash, module/skin
generation and selected view ID. Do not collect private URLs, media paths,
credentials or arbitrary setting values. Optional existing bounded view probing
is not included in the production overlay and needs an authorized supported
invocation; do not install a new service to gather it.

## Entry and global preference

1. Open Infinity through the preserved chooser; enter Kodi's Videos first from
   Files and then from Red Light → In Theaters. The first movie directory must
   show the detailed media List when List is the saved default, not the generic
   folder rows or an empty container. Record actual container view ID and content
   type, not just the selector label.
2. Explicitly choose List (50). Visit Next, Back, Refresh, another category and a
   second installed movie provider, then TV-show browsing in another provider.
   Verify the same global choice and correct content, artwork and selection.
   Red Light is a real-provider example, not the full scope.
3. Repeat explicit choice and the cross-page/provider transitions for Posters,
   InfoWall, TriPanel and other registered modes offered by that directory.
   Confirm a new explicit choice replaces the old global default immediately.
4. Visit a directory that does not support the chosen view, including an episode
   or file folder where applicable. It must use a registered fallback; return to
   supported movies/TV and confirm the global preference was not overwritten.
   Non-media windows and settings must retain their existing behavior.
5. Repeat rapid Next/Back/Refresh and leaving/re-entering Videos. After work
   settles, actual view and global choice must agree with no repeated provider
   execution caused by changing the view. A processed dispatch acknowledgement
   alone is not a successful-view assertion.
6. After ordinary safe close/reopen, verify the global choice still applies
   across providers. Do not force termination or simulate a failed shutdown as
   part of this UI test. Persistent native skin-setting storage is under test;
   unrelated shutdown durability is not.

If a provider omits usable movie/TV content classification, record its actual
window/content/view IDs and result as a compatibility limit. Do not silently
classify unrelated directories or claim that unsupported route passed.

## Details, artwork and responsive rendering

- Check List regular/slim/compact variants, Posters, Icons, ShowCase, TriPanel,
  InfoWall, Wall/Gallery and every other applicable offered mode. Preserve each
  design rather than expecting identical geometry across views.
- Where provider metadata exists, verify title, proportional poster/fanart,
  synopsis, year, duration, genre and rating remain available without clipped
  controls or unreadable overlapping text. Distinguish absent provider metadata
  from missing UI rendering.
- Fold/unfold and rotate while browsing, with and without View Options open.
  Confirm layout reflows, saved view survives, focus/selection and browsing
  position remain coherent, and no oversized half-screen art or near-empty List
  returns. Capture real bounds and a screenshot of each affected presentation.
- Repeat affected menus in the existing light and dark appearances. No skin
  theme change or general geometry adjustment is part of this plan.

## View Options input

- Open main View Options and the nested selector/settings/disabled-view panels.
  Confirm full labels, spacing, readable selection and finger-friendly close
  targets, with no duplicate stray X controls.
- Tap each panel's X once. It must close the intended layer, restore the expected
  parent/focus and preserve browser scroll/selection; it must not exit Videos.
- Repeat Back gestures, outside/dismiss behavior where supported, mouse click,
  keyboard and remote navigation if those inputs are available. Mark unavailable
  input hardware NOT RUN, not PASS.

## Navigation and Library

- Verify drawer Home, Movies, TV Shows, Sports and Favorites in order. Retain
  existing styling, destinations, Back history and focus. Sports must reuse the
  configured existing Home/playlist route. With no verified route configured,
  the explanatory message is expected; no substitute provider is permitted.
  Verify existing Favorites data/actions rather than a new collection.
- Open Infinity Movies and Infinity TV Shows from Library. Confirm native
  indexed movie/TV collections, seasons/episodes, watched markers and available
  resume positions; these must not redirect to provider-browsing pages.
- Browse Files: navigate an already Android-authorized folder, enter/leave
  subfolders, cancel the picker and return normally. Media Sources must show
  existing configured local/network sources with credentials preserved.
- Downloads: verify accessible populated and empty folders. For denied access,
  confirm clear recovery guidance and an authorized Browse Files alternative;
  cancel must be harmless. No new permission, unrestricted access or silent
  denial is permitted. Android 17 restrictions may make particular sources
  BLOCKED; report the exact restriction without bypassing it.
- Play an accessible downloaded video using **existing Kodi VideoPlayer**,
  exercise supported audio/subtitle/seek/resume controls, Stop and return to the
  same folder/selection. Open a second video. No file may be scanned, imported,
  moved, renamed or deleted automatically. Verify Preview was not launched.
- Confirm Add-ons, Settings, UI Theme, System Hub and Power remain present with
  their existing destinations. Do not invoke Power/shutdown as a new regression
  suite or investigate unrelated system interfaces.

## Acceptance record and stop conditions

Keep a concise scenario table with display/orientation, provider/content class,
requested/actual view, input, observed result and sanitized evidence reference.
Report Android integration separately from physical Fold acceptance. Reuse
unchanged component hashes for Preview/Cobra preservation; do not expand into
unrequested experience-wide behavioral sweeps.

Stop installation or testing on unexpected source/generation mismatch,
authentication failure, data/persistence warning or a new severe regression.
Use only the preverified higher-version recovery after safe normal closure.
Record a blocked recovery rather than forcing shutdown, deleting data or
downgrading. The user alone accepts the candidate; no automatic lock.
