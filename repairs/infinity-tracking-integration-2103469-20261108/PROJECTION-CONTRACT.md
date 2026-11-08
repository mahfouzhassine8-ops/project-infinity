# Common signed69 tracker projection correction

Owner-assigned source scope: exact signed69 `resume_hub.py` and `plugin.py` only,
copied into this task's overlay. No service, AV seek, native origin protocol,
provider allowlist, old68 helper activation or replacement tracker is introduced.

Signed69 already records typed actual playback through the existing service and
schema2 store. All Movies/TV families share `_values_for`/`_list_item`. The common
missing read connection is current exact playable progress, while Progress Shows
and Next Episodes inconsistently use namespace-preferred `_show_key` rather than
the existing conflict-aware ID grouping already used by Continue.

`exact_progress(data, entry)` reads raw `items` plus relevant watched state and
uses existing `_resume_groups(series=False)`. Movie kind/scope/namespaced IDs or
episode kind/scope/namespaced IDs/exact S/E remain mandatory; titles are irrelevant.
Conflicting connected aliases are quarantined. Newest persisted revision/time
wins; newest hidden/completed state blocks stale aliases; new playback occurrence
may resume normally. Finite positive offsets below the existing completion
boundary are read-only. An old untyped row may retain its own same-key offset
only when existing source/media/S/E agree and known IDs do not conflict; it never
joins another legacy key or receives a manufactured identity.

`_progress_rows` uses `_resume_groups(series=True)` over watched and unfinished
rows, with `_series_rows` selecting its TV subset. Continue, Progress Shows and Next therefore share verified
parent-ID alias/conflict semantics. Unknown parent IDs keep separate records.
Watched/items copies of the same original key and agreeing raw identity retain
one exact record when both lack parent evidence, so replay does not duplicate
that legacy record. Different legacy keys are never merged by name or raw ID
coincidence into an unproved series.
Contradictory typed-parent evidence cannot inherit a same-key fallback or
authorize a successor. Only existing verified successor proof can create Next;
no E+1 or catalogue work.

The plugin applies the exact selector at its common item renderer/menu/recovery
boundaries, covering Watchlist, Collection, Later, Ratings, custom lists, history,
Continue, Progress and Next. Original saved snapshots, routes, keys, identity and
membership remain unchanged. Folder navigation retains its existing menu path.
The external incoming popup's existing stored-progress route choice is retained,
with exact episode matching. Home Continue's explicit Play from beginning still
overrides the rendered offset in its unchanged caller. No second resume layer.

The writer, thresholds, persistence, occurrence logic, saved actions, source
selection/recovery, regular provider tracking relationship and all other files
remain original69. Raw identity/parent evidence for additional actual playback
families is root's separate investigation; these projections do not claim it.

The subsequently approved WNT extension reuses only the existing local identity:
valid local episode source plus exact `source_parent` reproduced through
watchnixtoons_source_identity(kind=tvshow). The local parent token groups episodes
without inventing canonical IDs or a season. `record_progress` copies the new
parent field only when valid and strips invalid incoming evidence before a new
row copy. Existing normal records compare exactly against original69 output.
An explicit show_ids_verified canonical link can join local and canonical series;
different WNT parent locators may alias the same proved canonical show, while
conflicting canonical IDs remain quarantined. Missing parent remains episode-only.

Series removal uses that same watched+items proof input with the selected query,
returning only canonical-key item aliases. Removing one displayed canonical
Continue card therefore hides all its agreeing unfinished aliases without
deleting stored items/history. A conflicting watched bridge cannot over-remove.
Exact-episode alias lookup and progress_key retain their original default path.
