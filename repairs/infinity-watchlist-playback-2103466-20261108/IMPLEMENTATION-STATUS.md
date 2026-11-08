# Phase B bounded Python implementation — feature incomplete

The accepted independent Watchlist resume projection is implemented in the task
overlay. The full playback-continuity feature is **not complete or install-ready**.
No application, Android, native integration, build, signing or installation ran.

## Implemented exact source scope

`overlay/script.infinity.commandcenter/` starts from the exact retained signed
APK 2103466 extraction. `PYTHON-PRESERVATION.json` binds baseline and overlay
hashes and function-level AST differences; `PYTHON-PROJECTION.diff` is the full
reviewable production diff.

- `resume_hub.py`: adds `_watchlist_progress_identity` and `watchlist_progress`.
  Existing functions are unchanged. The opt-in selector inspects raw items,
  matches exact playable movie/episode identities, quarantines conflicting alias
  components and uses current revision/time ordering. Existing exact producer
  proof or verified parent fields can supply a temporary comparison view; raw
  keys/identities/routes are preserved. Hidden/latest completed state suppresses
  old aliases; genuine newer replay may resume. Invalid/nonfinite/end offsets
  are rejected. Selection returns a private copy and performs no write.
- `plugin.py`: changes only `_menu_rows`, `show_item_menu`, and `_list_item`.
  Playable Watchlist movie/episode rows read effective progress for presentation,
  popup/Information resume indication and existing recovery offset dispatch.
  They retain the selected saved key, original route, identity and membership.
  Show/season rows and other list buckets keep their existing path. No new
  wrapper/nonce/receipt dispatch is bound.
- `service.py`: copied as a baseline reference and **byte-identical**. No player,
  provenance, threshold, identity, occurrence or persistence logic changed.

There is no optional helper module, new database, schema migration, global
identity relaxation, provider proof expansion or native modification by this
implementation. Existing Watchlist saved data remains immutable during resume
projection. Ordinary Movies/TV recording and all existing service functions are
unchanged.

## Focused host evidence

`HOST-TEST-SELECTION.md` records selected cases before execution.
`HOST-PROJECTION-RESULT.json` records all runs and current source hashes. The
final selected run passed **17 cases**, using actual overlay hub/list-item/menu
and existing service-writer functions with controlled Kodi boundaries.

Evidence covers exact movie/current offset; exact episode vs newer other episode
and season; duplicate agreeing IDs; transitive secondary-ID conflict quarantine;
similar titles and namespace separation; hidden aliases; manual watched and
completed occurrence vs replay; nonfinite/invalid/end offsets; disposable store
save/reload and unknown fields; proof mismatch; original saved route/key;
non-Watchlist rendering; exact baseline folder popup comparison; natural-ended
completion with zero/short duration; 95% completion below partial-duration gate;
duplicate completion; partial minima and released-clock preservation.

One intermediate 16-case run had a fixture key expectation error: the test used
an arbitrary row key where the actual writer derives its identity key. The
fixture alone was corrected, and that failed run is retained in the receipt.
The final 17-case run followed a narrow preservation correction restricting the
new projection to playable rows. No passed case was rerun without a recorded
new case, fixture correction or source correction.

These are host checks, not evidence of actual Android item lineage, playback,
fresh click dispatch, installed-provider admission or complete Next Episodes.

## Unimplemented contracts and precise blocker

The reviewed POV 6.11.02 player creates a fresh ListItem and calls native Python
`Player.play` directly. That path can bypass `PluginDirectory`'s final resolver
item and discard a saved-origin observation carried on the original item.
Umbrella also contains exceptional direct-play/playlist paths. Neither a pending
global receipt nor matching title/IDs/stream URL proves causality for the fresh
active item. Ordinary playback of the same saved title must remain unchanged.

Closing that handoff requires the actual native Python Player caller boundary
(the additional `xbmc/interfaces/legacy/Player.cpp` source scope identified by
Codex/Astra), unless a source-proven equivalent is found. It is outside the
seven authorized production files. Owner authorization explicitly requires new
scope approval before such expansion. No provenance guessing or unused handoff
code was added.

Consequently these remain NOT IMPLEMENTED / NOT VERIFIED:

- Native selected-row/descendant/actual-item origin receipt.
- Fresh direct-click offset recheck after rendering. The current patch refreshes
  Watchlist row rendering and existing explicit Python dispatch only; direct
  provider URL activation can still carry its render-time offset.
- Current Umbrella/POV scoped runtime emitter admission and parent enrichment.
- Complete supported catalogue acquisition and completed-to-next advancement.
- Real AV-start/order, Android persistence/restart and ordinary same-title
  negative-control acceptance; native ARM64 compile/link; candidate packaging,
  permanent signing, install-over and forward recovery.

The safe bounded patch is retained for review. It must not be labeled completion
of the requested feature, a release candidate, or a passed owner Fold journey.
