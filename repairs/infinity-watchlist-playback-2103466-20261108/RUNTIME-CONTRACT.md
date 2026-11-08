# Authorized native/Python handoff contract

Latest owner scope now includes `ScriptInvocationManager.cpp` and legacy
`Player.cpp` exclusively for scoped origin observation. Native owner and Python
owner agreed the schema below before binding the corresponding integration.
There is no new metadata client, worker, service or database. Only the existing
local Kodi catalogue can supply `verified_next`; provider-only playback preserves
accurate progress/series/resume and safely withholds an unproven successor.

## Selection and fresh launch

Playable Watchlist row path: `plugin://script.infinity.commandcenter/?action=watchlist-play&key=KEY`.
The original selected provider target is `Infinity.Watchlist.Destination`; the
existing `Infinity.Selection.Snapshot` capsule remains the exact anchor row.
Native actual selection consumes this wrapper and posts its URL with
`&token=NATIVE_NONCE`. Home `Infinity.Watchlist.Selected` contains schema 1,
`token`, `key`, `profile`, `selection` (full existing capsule), `destination`, and
integer `epoch_ms`. Profile is normalized translated `special://profile`.

Python rechecks that native nonce/capsule, fresh current Watchlist row and exact
destination. It reselects current exact progress at dispatch and forwards the
original provider target. A fresh compact ASCII JSON descriptor is stored both
on Home and that exact playback item as `Infinity.Watchlist.Launch`: schema 1,
fresh UUID-hex `token`, `profile`, `key`, `selection`, `destination`, `epoch_ms`.
Direct wrapper dispatch additionally includes the consumed native
`selected_token`. Explicit popup/Information Play mints this descriptor only
after confirmed first-party Play and the existing fresh selected-row check.
Rendering alone never mints a nonce. Native consumes exact Home/item agreement
before resolving; mismatch leaves ordinary playback unchanged and grants no
origin. Requests expire and are one-use under the native contract.

Folder rows retain original navigation. Native observation carries their exact
selected anchor through generation-bound successful descendants, then the exact
provider invoker/new player item. It never uses membership/title/URL coincidence.

## Actual item

GetItem adds `infinity_watchlist_origin` only for the validated actual current
CFileItem. The schema is 1 with `token`, `key`, `profile`, anchor `selection`,
actual playing provider `destination`, and integer `epoch_ms`. Native controls
its lineage/invoker/consumption validity; Python independently rechecks current
profile/Infinity, anchor capsule against current Watchlist state, current exact
producer source/version pins, typed playing IDs and precise S/E.

Source-reviewed U 6.8.00 / POV 6.11.02 route IDs may establish parent series IDs
only for this admitted receipt. Ordinary same-title playback has no receipt and
uses the original service path. Existing global source/progress identity helpers
are unchanged. Progress-only opt-in identity matching preserves original keys,
raw saved identities/routes/manual proofs; existing record/writer/thresholds and
occurrences remain authoritative. No progress occurs at dispatch or resolution.

The only successor proof is existing `_continue_show_identity` local catalogue
evidence. No valid local proof means no invented successor, including season
transitions. Host evidence does not establish native/Android acceptance.
