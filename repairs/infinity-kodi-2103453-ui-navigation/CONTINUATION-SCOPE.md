# Source-only continuation from 4e4b662b

The latest user instruction authorizes independently reproducible corrections
while the original images/recording remain inaccessible. This supersedes the
earlier pause recorded in INVESTIGATION.md. No visual or physical acceptance is
claimed. Local attachment directories are empty; connected Pages still contain
only the older Cobra references. No new upload is requested.

## Corrections selected before implementation/tests

1. Correct non-Cinema movie-result List routing: plugin directories declaring
   `movies` currently bypass the existing detailed VideoList/SlimVideoList and
   use a generic icon/label directory with no synopsis. Reuse those existing
   detailed layouts; preserve nonmovie folders, other content and Cinema.
2. Make Videos' View Options and nested selectors use the existing Infinity
   panel surfaces at usable widths, with in-panel close buttons, explicit Back
   behavior and one dismissal after choosing a view. Isolate Videos-specific
   variants so Music/Pictures/other shared menu consumers remain unchanged.
   Preserve every existing view/action/visibility rule and settings action.
3. Reorganize the existing drawer without changing its styling. Reuse the
   existing Home/Movies/TV/Favorites/Sports routes and Kodi library/source APIs.
   Downloads access must be truthful and recoverable. No new permissions,
   scanning, storage writes, providers, engines or background services.

**View 54 is not a movie defect:** its selector item explicitly excludes Videos;
it is the square/music/add-on ShowCase implementation. Do not add it to Videos
or change its current registration. The initial cross-file mismatch was a lead,
not an established defect; the content/window guard resolves it.

Red Light's real pagination URL sequence, installed provider source, and view
database records remain unavailable. Do not guess a URL-normalization rule,
overwrite provider settings or change the native View database. The subsequent
explicit GLOBAL preference instruction supersedes the earlier per-directory
policy; implementation and tests are selected below before execution.

## Exact selected tests

- `tests/test_skin_contract.py`: baseline/candidate XML include selection for
  native and plugin movie directories (regular/slim/compact/Cinema), preservation
  of other content; movie metadata ownership; per-view registration conditions;
  selector rows, close/Back/action order, focus and container state preservation;
  geometry checks for cover/inner/landscape reference dimensions; drawer order,
  exact old destinations, conditional Sports availability and library URLs.
- `tests/test_navigation.py`: Kodi API fixtures for configured/unconfigured
  Sports, safe route parameters, native folder picker cancellation, accessible
  and empty Downloads, permission failures, no navigation on cancellation,
  no file/library/player mutation or provider execution.
- `verify_source.py`: exact allowlisted member preimages against signed 2103453,
  generated source/diff hashes, untouched original shared menus, no native/DEX/
  Preview/Cobra/provider/permission/shutdown/release-control differences. Only
  the existing foreground UI observer receives the global-view hook below.
- If an existing or safely restorable Linux Kodi renderer is available, a
  disposable feature-only full-skin fixture will exercise view selection and
  modal dismissal on movie result pages; capture actual rendering and disclose
  upstream Linux versus Android differences. Record its exact selected actions
  before execution. No production provider or protected shutdown is executed.

Host tests and geometry calculations are not rendered touch or Android tests.
Physical Fold, original-media comparison and live Red Light persistence remain
pending unless actual evidence becomes available. No APK or component ZIP will
be assembled, signed, installed, released or locked.

## Additional user-authorized persistence tracing

The subsequent instruction explicitly retains Red Light persistence in scope and
authorizes preparation of bounded diagnostics for a real browsing session.
Selected additional checks before execution: `tests/test_view_probe.py` will
verify route redaction, pagination fingerprints, numeric view preferences,
read-only SQLite access, strict provider scoping, bounded output and the absence
of settings/database/provider mutation. The on-demand probe will not be included
in the production overlay or started automatically. A missing real-session
capture remains unavailable. The newer user instruction independently authorizes
a global media preference; tracing is not a prerequisite for that policy change.

## Latest explicit global media preference correction

The user now requires ONE preference across movie/TV providers and categories,
not independent provider preferences. Save only explicit Videos View Options
choices through Kodi's existing persistent Skin.SetString mechanism. An unset
preference leaves legacy choices intact. Use the existing Command Center
foreground observation loop, after its unchanged checkpoint/background gates;
no new service, worker, polling loop, persistence owner or database mutation.
Apply only in Videos (10025), the Infinity skin, and declared movie/TV content.
Reuse the exact registered selector predicates and require a real control.
Unsupported views fall back to registered List without replacing the saved
preference. Preserve native view-switch item/focus handling. Wait for completed
directory updates and closed modal panels; dispatch existing SetViewMode without
synchronous waits. Coalesce a pending action until an observable state change.

Selected additional tests: tests/test_media_view.py will exercise two providers,
multiple pages/categories, TV, Back, refresh, explicit replacement, service
recreation with the persisted choice, fallback/restoration, delayed provider
overrides, disabled/missing views, in-flight directory/modal transitions and
non-media/window/skin exclusions. Verify no new setting write during fallback,
no duplicate dispatch while waiting, and exact original service bytes after
removing only the declared initialization/tick additions. Recheck the affected
selector action order and source allowlist. Reuse the unaffected 24-test evidence.

The selected Linux fixture may additionally exercise this helper with native
Kodi APIs and synthetic provider directories, including a disposable-process
restart. This is not physical Fold or real Red Light acceptance. Original
module authentication remains mandatory; any later authorized packaging must
regenerate its source manifest through the existing trusted build, never bypass
the guard. This source overlay is not an installable component.

## Selected upstream Linux runtime fixture

A Debian Kodi 21.2/Xvfb test runtime has been restored by downloading and
extracting packages to `/tmp/kodi-ui-runtime-qa`; nothing was installed into the
application or operating-system package database. Use a disposable profile with
the signed skin plus the source overlay and synthetic movie metadata. No real
provider, protected service or application shutdown runs.

Selected actions: open a two-page synthetic movie directory; select List,
Posters, InfoWall and TriPanel using native window/control actions; next page,
Back, directory refresh and category reopen; open the Videos menu and nested
selector; dismiss with Back and its X action; capture actual skin rendering.
The fixture can test native Kodi input dispatch, not Android/Fold touch or the
actual Red Light contract. Its coordinate system is upstream Linux and may
differ from Infinity's preserved Android-responsive engine. Dispose only the
isolated QA process after the finite test; do not invoke shutdown actions.

Additional selected input check: use the available X11/XTest mouse to click the
rendered nested selector X, then activate the main Videos View Options button
and dismiss it through its original action. This is mouse input in the Linux
fixture, never proof of Galaxy Fold touchscreen sizing or native Android reflow.

Final global-write guard check, selected before execution: in native Linux Kodi,
select TriPanel for movies, then select List in a synthetic `files` directory.
The local files view may change, but the saved media default must remain TriPanel;
reopening a different movie provider must restore TriPanel. Recheck the affected
skin-action source assertion only; reuse the unchanged preference/helper tests.
