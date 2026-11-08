# Phase B Python contract — Watchlist playback

This contract is written before corresponding production edits. The owner
authorization in `OWNER-PHASE-B-AUTHORIZATION.md` supersedes Phase A's read-only
restriction. Native field names and handoff are pending agreement with Codex;
producer/catalogue evidence is being closed independently by Astra. This file
does not claim those gates have passed.

Implementation outcome: only the independent exact-progress/projection portion
below is implemented and host-tested. Native origin, fresh direct-click dispatch,
current-emitter enrichment and catalogue integration remain UNIMPLEMENTED after
the source-proven fresh-`Player.play` item bypass exposed a required source seam
outside the seven authorized files. `IMPLEMENTATION-STATUS.md` is authoritative
for completion; the remaining protocol sections below are proposals, not code.

## Exact resume projection

Add an opt-in `resume_hub.watchlist_progress(data, saved)` selector. Existing
ordinary callers, `same_identity`, `_resume_identity`, series grouping, keys and
writer admission retain their baseline path.

The selector accepts a verified playable movie or episode only. It evaluates raw
`items`, rather than `entries()` (which collapses TV series). An episode's exact
season and episode are mandatory. Existing producer side-table proof can supply
a temporary progress-only canonical identity after its exact raw identity,
provider and reviewed scope match. Verified parent fields on an actual playback
row may supply the equivalent temporary view. No stored identity, key, provider
route or membership is rewritten.

Use conflict-aware ID components to reject a connected set that contradicts any
namespace, including conflicts visible only through a second alias. No titles,
labels, route similarity, untyped IDs or guessed series IDs participate. Choose
the newest agreeing item by its existing persisted revision/time ordering.
Hidden state and completed occurrence state suppress stale matching aliases;
a genuinely newer playback occurrence may resume under existing semantics.
Reject nonfinite/negative offsets and invalid duration, and require an offset
strictly below duration. Completion/replay returns zero rather than the old end.
The selector is read-only and never creates an item or advances history.

`plugin._list_item` uses this selector only for Watchlist playable rows. It
overlays effective position/duration/percentage on presentation/launch metadata,
while retaining the original saved key, identity, bucket and destination.
Show/season rows retain directory behavior. Collection, Save for Later, custom
lists, Continue Playing and ordinary external ingress retain existing behavior.

## Fresh direct launch and selected origin

A playable first-party Watchlist row dispatches to a Command Center resolver
action before entering the original provider. Its original provider destination
is retained independently on the item for native saved-navigation observation.
The action is a selector, not authority to start progress.

The native actual row-selection hook must issue a fresh nonce bound to this
selected item/generation, key, Watchlist bucket, saved identity and exact original
destination. A stale Home property, copied row property, membership match or
invoked URL alone cannot authorize a Watchlist-origin receipt. The concrete
native nonce transport/consume API must be agreed before binding this action.

At dispatch, re-read the existing store, verify the selected saved row is still
the same identity and original route, and select its exact current progress.
Resolve using the original provider route and this fresh offset. Do not replace
the saved route with a remembered progress row's provider. Preserve the existing
recovery route/token/bucket semantics when the original route needs recovery.
Failed selection validation must not create progress or authorize provenance.

Popup Play and Information Play use the same fresh offset selector, with a new
native selected-action handoff. The rendered offset is never the final authority.
Folders carry exact native lineage through selected successful descendants;
neither folder navigation nor stream resolution records history.

## Actual playback and persistence

The native active-item export supplies the exact origin receipt alongside the
existing `infinity_original_route`. `service._arm_continue` validates that receipt
against the current profile/experience, saved snapshot, source-bound producer
contract and exact typed playing item before applying Watchlist-only parent and
catalogue proof. Native API names/schema remain pending Codex agreement.

No catalogue request, network call or new worker occurs in AV callbacks. Astra's
approved complete snapshot is obtained at the explicit launch/navigation seam
and validated for exact series/current-episode membership and availability.
Missing proof withholds a successor and does not block baseline playback.

The existing player occurrence, writer, `continue-watching.json` schema 2,
periodic eight-second sampling, seek/stop/error handling and publication remain.
The duration>=120s, position>=30s and >=1% rules gate new partial progress only.
Natural playback-ended completion and >=95% completion retain baseline behavior
independently of the partial-duration gate. No saving/browsing/failed launch write.

Any progress-key/canonical comparison extension must be explicit and opt-in for
the admitted saved-origin playback. Ordinary playback of the very same saved
title must execute the baseline path. Preserve WatchedBridge/manual actions,
hidden markers, raw saved records, pending sync and unknown store extensions.

## Selected host evidence, before execution

The focused cases will exercise actual overlay functions with controlled Kodi
boundaries: exact movie/episode matching; S1E1 vs newer S1E5; duplicate/conflicting
alias chains; hidden/manual watched/completed state; fresh rewind/replay offset;
store reload; nonfinite offset rejection; fresh dispatch vs stale rendered row;
invalid/stale receipt; ordinary same-title negative control; AV-start-only writes;
partial and natural-ended thresholds; repeated completion and released clocks.
No test execution has occurred under this contract yet. Exact test names will be
recorded in a task test-selection receipt before the first focused run.
