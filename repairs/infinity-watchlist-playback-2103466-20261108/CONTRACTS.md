# Phase B source contracts and exact remaining boundary

Independent Astra source investigation, 2026-11-08. This document records static
evidence, not a runtime acceptance result. No provider code was executed, no
application test/build/install ran in this investigation, and no production file
was edited by this investigator. The owner authorization applies; the additional
native source boundary identified below is outside its seven-file allowlist.

## Evidence binding

`contract-evidence/SOURCE-PINS.json` contains SHA-256 maps of the inspected code:

- Actual supplied POV 6.11.02 export: 110 Python/addon-manifest files, from the
  larger supplied export. This is evidence of exported bytes, not a new live
  inventory of the Fold.
- Umbrella 6.8.00 public source: 198 Python/addon-manifest files. All five supplied
  installed files match this public source byte-for-byte. The unexported episode,
  playback and metadata emitters are **not** thereby proven to match the Fold.
- TMDb Helper public source: 425 Python/addon-manifest files, version **6.20.6**.
  The directory name `tmdbhelper-6206-publisher` must not be interpreted as 6.2.06.
  Actual installed version and relevant dependency bytes remain runtime gates.
- Jurialmunkey common 0.2.35 request implementation and manifest, retrieved from
  immutable upstream commit `8f42fb5f4698f3e4552f38955964b2f3843dba69`. These are
  public dependency references, not claims about installed dependency bytes.

`contract-evidence/NATIVE-BOUNDARIES.json` records the native files below and
their equality to the retained ARM64 `three-native-evidence/NATIVE-SOURCE-MAP.json`.
All nine inspected native boundary files match that map. The protected signed
2103466 APK/source binding remains the task's existing `BASELINE.json`.

## Provider identity contract: source established, path coverage differs

POV `resources/lib/menus/episodes.py:50,69,100-103,159-166` obtains IDs from
`tvshow_meta`, puts the show TMDb ID and exact S/E in `mode=play_media`, and emits
the same show IDs on episode ListItems. `resources/lib/menus/seasons.py` is a
second episode-list producer and must be included in any producer source pin.
`resources/lib/modules/sources.py:283-290` parses these coordinates;
`get_meta:363-375` gets the show metadata and exact season episode before playback.
`resources/lib/modules/player.py:65-68,125-141` emits that metadata on the actual
playing item. These generic episode unique IDs are show IDs for this reviewed
producer; that fact must never be generalized to unknown providers.

Umbrella's public `resources/lib/menus/episodes.py:3085-3086,3232-3233,3374,3390`
puts show IDs and S/E on its `action=play_Item` route and ListItem.
`resources/lib/modules/player.py:241-249,299-307` preserves those IDs in the
resolved typed playback metadata through `control.set_info`; that function is at
`resources/lib/modules/control.py:662`. The router, episode/movie emitters,
sources, player, metadata normalization and control emission files require exact
runtime matching before this candidate contract admits the installed producer.
The full public source pin map is retained so a narrower reviewed import/emit
closure can be derived without guessing old-version semantics.

Admission must require the actual typed playing item, matching namespaces,
nonnegative exact S/E for TV, and a verified Watchlist-origin chain. Runtime hash
mismatch withholds enrichment and leaves baseline playback unchanged. It does
not trigger a provider replacement or global playback/Search contract expansion.

### Hard source-bound scope blocker: POV uses a different playback item

The normal supplied POV playback path is:

1. `resources/lib/modules/sources.py:254` calls `POVPlayer().run(...)`.
2. `resources/lib/modules/player.py:73` creates a **new** ListItem through
   `make_listitem`; line 81 calls `self.play(listitem.getPath(), listitem)` with
   the resolved media URL. It does not return the original item through
   `xbmcplugin.setResolvedUrl`.
3. Native `xbmc/interfaces/legacy/Player.cpp:89-105` (`Player::playStream`) copies
   only that supplied new ListItem into `TMSG_MEDIA_PLAY`. It does not inherit
   the initiating resolver's saved-origin properties or original provider route.
4. `xbmc/application/Application.cpp:2442` enters
   `CPluginDirectory::GetResolvedPluginResult` only for `URIUtils::HasPluginPath`.
   The fresh HTTP item therefore bypasses the approved PluginDirectory capture.

Matching its IDs to a pending selection at `PlayerOperations::GetItem` would prove
identity only, not that the selected provider invocation created that item.
Membership, elapsed time, current focus or a shared stream URL cannot repair this
missing connection. The current four allowed native files cannot honestly claim
the required actual-item origin for normal POV playback.

At least the following additional observation boundary is required:
`xbmc/interfaces/legacy/Player.cpp::Player::playStream`, immediately before the
fresh-item clone/message. A narrowly scoped observer could carry an existing
Watchlist provider-invocation nonce only when the active Python invoker, provider
identity, exact media identity and current generation all agree. Existing
`PythonLanguageHook::GetAddonId` and `GetInvokerId` are available, but provider ID
alone is insufficient. The current `CScriptRunner::RunScriptInternal` retains the ID returned by
`ExecuteScript`/`CScriptInvocationManager::ExecuteAsync` internally; that ID is not
exposed to PluginDirectory. Binding
the expected invocation to the new player item therefore remains a design gate.
Thread/new-invoker propagation, concurrent same-provider invocations, one-use
consumption, cancellation and playlist behavior require source review and tests.
This is a proposed **additional file requiring owner scope authorization**, not
an implemented fix, a promise that one extra hook suffices, or a trivial pass.
No generic player callback change,
provider patch, title matching or global interception is authorized.

Umbrella normally uses `control.resolve` at `player.py:319`, so the existing
resolver-item seam is applicable there. Its direct-player/playlist branches at
312 and 317 similarly require explicit coverage or truthful unsupported status;
the normal branch is not proof of every provider launch mode.

## Directory cache and first-party popup contracts are closable in current scope

`GUIMediaWindow::GetDirectory:739-742` loads cached directory items without a new
PluginDirectory request. Requiring a new provider request receipt would therefore
reject legitimate cached navigation. However every `Update` invocation already
calls `PrepareNext` at 826 and `WindowResult` at 962, with the intervening body in
a lambda. The existing two hooks can assign and complete a thread-local invocation
generation even for cached results, without editing the GUI source file.

The contract needs a bounded LIFO invocation stack because failure recursively
calls `Update` at 858-859. Only a current generation associated with the actual
selected parent may tag returned descendants; a stale outer result cannot
restore discarded lineage. Unexpected/unbalanced calls expire fail-closed.
`MovieAttempt` also calls `PrepareNext`; its call must use the recovery-only
helper after refactoring within the allowed header, not push a GUI invocation.
Directory success proves returned selected descendants, not catalogue completeness.

Popup evidence is `GUIBaseContainer.cpp:929` passing the exact native item to
`context.title_popup:519`, then `selection_contract.read` and
`plugin.show_item_menu` comparing the selected saved snapshot, accepting explicit
Play and re-reading the same saved identity before dispatch. The selection hash
is deterministic integrity/freshness data, **not** a native-issued security nonce.

Within the existing authenticated first-party control-flow trust boundary, popup
and Information Play can mint a one-use handoff only after confirmed Play and the
fresh saved-row check. Bind key, identity, original destination, selection token,
profile/experience and generation in both the exact forwarded CFileItem and a
bounded pending descriptor. Native resolution consumes their agreement once.
Rendered properties alone cannot grant admission. Supersession, failure,
cancellation and recovery retry must invalidate/rebind the intent. This proves
resolution of first-party-dispatched intent, not a native observation of the
popup's GUI click or resistance to malicious arbitrary in-process forgery.
Ordinary same-title provider launches carry no such intent and retain baseline
behavior. This popup contract needs no additional GUI source file.

## Complete successor metadata: concrete API candidate, not runtime closure

The public TMDb Helper 6.20.6 implementation offers a suitable unfiltered raw data
boundary: `tmdbhelper.lib.api.tmdb.api.TMDbAPI.get_response_json`, lines 83-86.
Its parent `NoCacheRequestAPI` (`lib/api/request.py:20-21`) does not instantiate a
metadata cache database. Use public metadata GET requests only:

- `get_response_json('tv', show_tmdb)` for the root show and complete `seasons`
  descriptors, including season IDs and declared `episode_count`.
- `get_response_json('tv', show_tmdb, 'season', season_number)` for each exact
  descriptor's complete episode array. These detail endpoints are not paginated
  or subject to the helper's directory presentation filters.

No account/login/Trakt method, user credential inspection, direct API-key extraction
or independent replacement HTTP client is proposed. The installed dependency
owns its ordinary public metadata client. Its module imports read its own benign
language/endpoint/notification preferences; no preference is changed by this
adapter. Actual installed source, dependency identity, import ownership and API
shape must be checked before invocation; arbitrary import-path shadowing is not
acceptable. The request implementation's default is 15 seconds with connection
retry (`jurialmunkey reqapi.py:107,123,217-235`); a supposedly nonblocking call
cannot be inferred from that API. Any per-instance timeouts/retry/notification
configuration must avoid changing shared class/global behavior.

Proposed complete-snapshot validation, before supplying existing `verified_next`:

1. Root ID equals the independently verified show TMDb ID. Require a bounded list
   of unique nonnegative season coordinates, unique valid season IDs, and declared
   nonnegative counts. Do not invent missing season numbers from a total count.
2. Fetch every declared season in the ordering domain. Each response must match
   its requested season and the root descriptor's season ID. Its episodes list
   length must equal that descriptor's count; errors/partial responses reject the
   snapshot. Empty seasons require an explicit zero-count descriptor.
3. Every episode has the correct season, an unambiguous episode coordinate and
   unique valid episode ID; reject conflicting duplicate coordinates/IDs. The
   observed playing S/E must be present exactly once. A second root read may
   verify the season/count signature has not changed during acquisition.
4. Order by actual numeric S/E from the complete arrays, preserving the existing
   separate season-0 versus regular-season domains. Derive the following member
   from this catalogue, not arithmetic. Do not advance from specials into S1.
5. Select the immediate following catalogue member before considering availability.
   A missing/invalid/future air date withholds that successor; never skip it and
   present a later member as the immediate next. A complete terminal ordering has
   no successor. A date-only source cannot prove intraday stream availability;
   use an explicitly documented conservative date rule in implementation/tests.
6. Bind snapshot generation, source contract hashes, show ID, capture epoch,
   complete ordered digest, selected current S/E and successor S/E. Keep it
   transient until actual playback qualifies for existing persistence; retain
   only relevant evidence in existing `verified_next`/progress records. No second
   tracking database and no provider saved-state mutation.

Numerical request, payload, episode/season, memory and lifetime bounds still need
to be selected in the concrete implementation contract. An exceeded bound yields
unavailable metadata, never a truncated catalogue presented as complete.

### Rejected metadata shortcuts

- Bundled TV scraper `getepisodelist` is a real supported plugin route: native
  `addons/Scraper.cpp:1265-1290` uses it. But its `libs/tmdb.py:178-200` silently
  replaces a failed season response with `{}` and can emit a partial episode list;
  the public list lacks an independent expected-count receipt. Its urllib helper
  has no explicit timeout. It cannot alone certify complete ordering.
- TMDb Helper's displayed seasons/episodes depend on user filters and aired-only
  counts. `ListFlatSeasons` uses a truthiness test that skips loading season 0 in
  `baseview_factories/concrete_classes/flatseasons.py:42-46`. Those directory rows
  are not the complete raw API contract above.
- Public Umbrella `episodes.py:2375` assigns a hardcoded `next_episode_to_air`
  value in one path. Advertising such a field is not successor proof.

### Acquisition timing remains an integration gate

A full network catalogue cannot be acquired synchronously at a fresh direct Play
and also guarantee that network failure does not delay baseline playback. No
network/import-heavy metadata work belongs in the AV callback. A candidate is a
bounded transient invocation through existing Kodi script dispatch, initiated at
explicit Watchlist show/folder navigation, while original provider navigation
continues. It is not a persistent service or timer. Its snapshot must be tied to
current lineage; an obsolete completion is discarded.

If playback starts before that snapshot is ready, AV start must preserve baseline
playback and withhold the successor. Direct saved-episode launch with no earlier
snapshot has the same timing issue. No late-completion consumption protocol is
implemented or approved by this document. Source-bound API feasibility does not
establish installed availability, scheduling, real playback coverage or completed-
to-next acceptance. Those remain explicit engineering gates.

## Current preservation review

The current Python overlay changes only the opt-in Watchlist selector in
`resume_hub.py` and Watchlist presentation/menu/Information/recovery-offset uses
in `plugin.py`. `service.py` is byte-identical to the extracted baseline. The
ordinary identity, progress-key, record-progress and writer functions retain
their original implementation. No producer, native, callback, lifecycle, Search,
Cobra or signing implementation is changed by this partial overlay.

The stored `HOST-PROJECTION-RESULT.json` reports 17 selected host tests passed and
retains the earlier fixture failure. This investigator read that receipt and the
actual source diffs without rerunning tests. That evidence covers only the
stated host projection scope: it does not prove fresh direct-click dispatch,
native lineage, provider AV-start, catalogue acquisition, Android, signing or
delivery. The additional POV seam and metadata timing remain blockers to a
complete feature claim.

The later source-only `INVOCATION-SCOPE-ADDENDUM.md` identifies a concrete
two-file observation proposal to bind that ID before dispatch and transfer it to
the fresh player item. Both additional files require scope authorization; the
proposal has not been implemented or runtime verified.
