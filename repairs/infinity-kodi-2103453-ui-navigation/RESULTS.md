# Global media view persistence — source-only candidate

Continues `4e4b662b` on
`work/infinity-kodi-2103453-ui-navigation-source-20261104`.
The latest user instruction explicitly replaces the earlier per-provider policy
with **one movie/TV media-view preference**. No APK or component ZIP was built,
installed, signed, released, promoted or locked.

## Implemented global preference

- Explicit selection in Infinity Videos' View Options stores
  `Infinity.MediaView.Default` through native `Skin.SetString`, before applying
  the existing view action. A new explicit selection replaces it.
- The existing Command Center foreground UI loop observes that preference in
  Videos window 10025, with the Infinity skin and declared movie/TV content.
  Its existing checkpoint and background gates remain before the observer.
  No new service, worker, timer, database, provider execution or refresh loop.
- Registered view IDs and availability predicates are generated directly from
  the signed skin. Missing/disabled/incompatible layouts fall back to registered
  List without writing the global setting. Returning to supported content restores
  the saved choice. Direct provider view overrides do not become user preferences.
- Unset preferences preserve legacy behavior. File folders, add-on roots, Music,
  Settings, specialized windows and other skins do not acquire a media preference.
  Selecting a local view in such a folder does not replace the movie/TV default.
- Commands are asynchronous and coalesced while awaiting an observable result.
  The helper does not change directory, selection, scrolling, playback or focus.
  Native Kodi's existing view switch transfers the selected item.

## Confirmed mechanisms and limits of attribution

1. `GUIViewState.cpp`/`ViewDatabase.cpp` save and restore by full directory path,
   window and skin. A provider's page/category URL can therefore have a different
   stored view. There was no shared movie/TV default in the signed skin.
   `Container.SetViewMode` can also replace the current native view after a
   directory finishes. The Linux fixture reproduced this with a synthetic
   provider: Posters 56 on page one became Icons 500 on page two.
   This establishes the mechanism and missing global policy, **not the exact
   installed Red Light override or its historical URL sequence**.
2. View 54 is explicitly excluded from Videos by the original selector. Movie
   ShowCase is 53. The initial registration lead was ruled out; no View 54
   registration, native calculation or provider code was changed.
3. The original nested selector used 20.833333% title/list widths and an off-panel
   64x48 close target. Videos now has scoped, wider panel variants with 128x128
   in-panel targets and explicit dismissal. Original shared Music/Pictures
   variants remain untouched. Selecting a view dismisses the selector and main
   options; pressing X in the nested selector preserves its legitimate parent.
4. Non-Cinema plugin List routing unconditionally selected generic plugin rows,
   even for movie content. The staged four-predicate correction permits the
   existing detailed movie List/SlimList instead; it rewrites no view's metadata
   or artwork implementation. **Its runtime sufficiency is not established.**
   The Linux first-entry capture still showed generic plugin List rows: include
   conditions are resolved during window loading, before the new directory's
   content necessarily exists. The static predicate tests are not proof that
   every first-entry/pagination layout is repaired. This remains an open rendering
   requirement; no forced skin reload, new view tree or native change was added
   to conceal it. Do not package this candidate as a completed layout repair.

## Other retained source corrections

The existing drawer retains its style and original actions. Navigation contains
Home, Movies, TV Shows, Sports and Favorites. Sports uses only the existing
configured playlist Sports route and reports unavailability rather than silently
substituting another provider. Favorites uses the native existing destination.

Library contains native Infinity Movies and TV collections, Browse Files,
Downloads and Media Sources. The helper uses the original Kodi folder picker,
video sources and JSON-RPC navigation. Downloads distinguishes accessible-empty
from access failure and offers an existing authorized folder. It grants no new
permissions, scans/imports/deletes nothing, and creates no playback engine or
library database. Actual Android 17 storage/provider access remains unverified.

## Focused evidence

| Evidence | Result | What it establishes |
|---|---:|---|
| Previously acknowledged navigation API fixtures | 11 passing, reused | Sports routing, local folder selection, safe parameters, empty/error/cancel handling; underlying helper unchanged |
| Updated skin/source contracts | 13 passing | Selector actions/guards/geometry model, old actions and metadata sources, declared registration and drawer structure; not rendered Fold layout |
| New global-view host tests | 15 passing | Multiple providers/pages/categories, TV, replacement, service recreation, fallback, late overrides, exclusions and untouched resident bytes |
| Optional diagnostic probe tests | 5 passing | Redaction, per-session fingerprints, bounded observation and read-only/no-wait database access |
| Native Linux baseline fixture | 7 assertions | Baseline provider override reproduces loss of the requested global view |
| Native Linux candidate navigation fixture | 74 assertions | List/Posters/InfoWall/TriPanel, real Next-page item selection, Back, other provider, refresh, TV, episode fallback and restoration |
| Linux process restart/focus fixture | 12 assertions | Native skin setting survives process restart; selected movie, title/plot and keyboard navigation remain available |
| Linux pointer fixture | 9 assertions | Main menu opens scoped selector; actual X11 mouse click closes nested X; native action closes parent without leaving Videos |
| Final native media-write guard | 13 assertions | Selecting List in Files leaves movie default intact; a different movie provider restores it |

The 44 distinct host cases include the 11 unchanged navigation cases reused from
the acknowledged run. Repeated source checks are not counted as additional cases.
The 108 candidate Linux assertions include setup/state assertions and two
pointer diagnostic checkpoints; they are not 108 independent user workflows.

The final selector change adds only the movie/TV condition to the preference
write. Earlier candidate runtime evidence is retained for unchanged code and
media actions; `media-write-guard` rechecks that exact final XML change. The
restart and final guard use the resident's existing 0.5-second observation cadence.
No performance improvement or physical Android acceptance is claimed.

### Failed observations retained

- The first candidate Back assertion failed because the harness used direct
  `ActivateWindow` for page two. Native Back correctly returned to the provider
  root. The corrected fixture selected the real Next-page item; the full flow
  then passed. Original result remains `results/linux/candidate/RESULT.json`.
- The first pointer run exited with SIGSEGV before it produced a result. Holding
  the Python Window reference throughout control inspection, with bounded signal
  diagnostics, allowed the selected mouse scenario to pass without production
  changes. The original exit/log is retained; without its native stack, its exact
  crash site is not claimed proven or attributed to the Android engine.
- An initial probe assertion matched the word `token` in the intentional
  `path_token` field name. It now checks actual private query material; no private
  value was emitted. Original failed output is retained.
- The source allowlist caught local host-test `__pycache__` output in the overlay.
  Only that generated file was removed; the test disables bytecode output.
  The allowlist was not widened. Final source preservation passes.

## Exact proposed payload changes

All paths below are under `assets/addons/` in the reviewable overlay.

| File | Authorized change |
|---|---|
| `script.infinity.commandcenter/service.py` | Three additive lines: import, observer instance, foreground tick. Removing them restores every original byte. |
| `script.infinity.commandcenter/media_view.py` | New narrow global media-view observer, signed-skin-derived registration predicates. |
| `skin.infinity.diggz/unified/MyVideoNav.xml` | Scoped Videos menus and staged movie List include predicates; List first-entry limitation above. |
| `skin.infinity.diggz/unified/Includes.xml` | One added include declaration; all original bytes retained. |
| `skin.infinity.diggz/unified/Includes_InfinityVideoOptions.xml` | Videos-only clones of existing menu/row/settings definitions. |
| `skin.infinity.diggz/unified/custom_1136_InfinityVideoViews.xml` | Scoped selector, persistent explicit media choice, close/Back behavior. |
| `skin.infinity.diggz/unified/custom_1137_InfinityVideoViewSettings.xml` | Scoped existing view-settings panel. |
| `skin.infinity.diggz/unified/custom_1138_InfinityVideoDisableViews.xml` | Scoped existing enabled-view panel; original settings actions retained. |
| `skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml` | Requested Navigation/Library destinations with retained existing row styling/actions. |
| `skin.infinity.diggz/resources/lib/infinity_library_navigation.py` | On-demand, non-mutating native folder/Sports/Downloads routing. |

Four existing members and six new source members. Exact preimages, candidate
hashes and diffs are in `SOURCE-PLAN.json`, `results/SOURCE-PRESERVATION.json`
and `results/*.diff`. Test source/artifact hashes are in
`results/EVIDENCE-BINDING.json`. The optional `view_probe.py` is **outside** the
production overlay, is never started automatically and was not run on the Fold.

Signed 2103453 APK SHA-256 remains:
`08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8`.
Protected ARM64 engine remains:
`d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98`.
All 5 DEX members, all 47 native members and 7,613 other baseline payload members
are excluded from the proposed changes. No Preview, Cobra, provider, native,
manifest/permission, release-control, signing or shutdown edits were made.
This is source-preservation evidence, not a comparison against a nonexistent
candidate APK.

## Remaining verification and completion requirements

- Original user screenshots/recording are still inaccessible to this executor.
  No original visual inspection or recording playback is claimed.
- Linux renders at 1080x2520 and 2160x2250 were inspected. They visibly mis-handle
  percentage item layouts and aspect geometry. Signed Infinity's preserved
  `GUIListItemLayout` has percentage/auto/aspect handling absent from upstream
  Linux. These renders validate neither Fold sizing nor visual acceptance.
  Native first-entry movie List ownership, poster proportions and details/spacing
  across all existing layouts remain open. No speculative geometry rewrite was
  made to compensate for the different Linux engine.
- Real Red Light/other installed providers, rapid queued navigation, screen
  transitions, rotation/folding, touch/remote accessibility and genuine Android
  process restart must be checked on the preserved native engine. Provider routes
  that omit usable movie/TV content retain native behavior rather than receiving
  guessed classification. Direct provider `SetViewMode` is an override, not an
  explicit Infinity View Options choice.
- The optional 180-sample probe can capture provider ID, keyed route fingerprints,
  numeric page/view IDs, content, busy state and matching native view preferences
  during a later authorized real session. It records no raw URL, titles, media
  identifiers, credentials or arbitrary settings values, and modifies no DB.
- Android Downloads permissions, local movie playback/return and configured
  Sports require real accessible sources/device evidence; only API fixtures ran.
- The actual authenticated Command Center service was not started in Linux; its
  checkpoint/background gates are byte-preserved and source-tested. Later
  authorized packaging must regenerate the existing trusted source manifests
  and prove full application integration. No authentication guard was bypassed.

Do not sign or describe the entire movie-layout repair as complete on this
evidence. Global preference behavior is implemented and exercised as above;
remaining layout/device gates stay explicit. Recovery baselines and locks remain
untouched.
