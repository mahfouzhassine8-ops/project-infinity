# First-entry List continuation from ca5153cb

Scope remains source-only Kodi media browsing. No native/DEX, Preview, Cobra,
provider, shutdown, permission, signing or release changes. No APK/component build.

## Confirmed load-order mechanism

`CGUIMediaWindow::Load` resolves skin includes and registers one container per
declared view ID before `GetDirectory` finishes. Content-based include conditions
therefore capture the previous/empty content. `UpdateButtons` later calls
`CGUIViewControl::SetCurrentView`, which reevaluates container visibility but does
not reconstruct omitted includes. The ca5153cb condition-only change could leave
generic folder rows bound to view 50 for typed movies.

## Selected minimal skin correction and tests, before execution

Register the existing detailed List/SlimList as canonical ID 50 independent of
directory content; retain the existing Cinema branch. Give the three existing
folder List variants distinct internal IDs (65050/65051/65052) and scrollbars
(65150/65151/65152). Runtime container predicates select exactly one List family.
No new user-facing view is introduced. The original view implementations remain
unchanged; scoped copies preserve their layout, artwork, text and action bodies.
Original IDs/settings for all movie view choices and the global preference stay
unchanged. Legacy saved List ID 50 falls back through Kodi's existing List-type
resolution in non-media folders; explicit folder List choices use their actual
internal ID without changing the saved movie/TV default.

Keep canonical List semantics for header/background/settings/loading/focus by
scoping compatibility includes to Videos. Other windows retain the original
shared includes. No skin reload, directory refresh or second provider dispatch
is introduced. Test exclusion of unused internal IDs and all existing saved
user-facing view IDs. Reject ID collisions against the complete signed skin.

Selected host checks: `tests/test_list_registration.py` models initial empty
content followed by movie/TV/files content; verifies one List family, preserved
original subtree semantics, all original view IDs, runtime predicates, legacy
List fallback ordering, folder actions, loading bindings, and unchanged global
observer/library/native inputs. Update only the affected routing assertions in
`test_skin_contract.py`; reuse unchanged global-preference/navigation evidence.

Selected native Linux check: cold window entry from non-media context, select
List with movie results, next page/Back/refresh, movies-to-files-to-TV transitions,
global List/InfoWall restoration, current item/focus, original folder layout
bindings, and no extra provider invocation caused by a view selection. Test the
regular and existing Slim/Compact/Cinema variants where directly affected. Use
the existing disposable renderer; no shutdown or playback suite. Linux geometry
still lacks the protected Android percentage engine and is not Fold acceptance.

## Newly recovered reference observations

A separate reader reports private CRC/SHA verification of the original
`Infinity-Kodi-UI-Original-Evidence.zip`, SHA-256
`eecf9f10f1c2a0c6356b9f28f6dffaa7df7d50d2133cf784ae19e1ffa08c7701`.
This executor has not received the original bytes and claims no direct viewing.
Attributed observations: narrow/clipped selector and duplicate small close icons;
List highlighted over nearly blank/play-triangle content; compact rows around
25 seconds followed by oversized left-side artwork and unused right space around
29–37 seconds; missing Sports/Favorites and the old Library entry around 44–45
seconds. The recording does not itself identify the exact pagination/Back cause.
These observations guide the existing scope; they do not constitute candidate
Android rendering verification or authorize any native change.

## Refresh counterexample found during the selected Linux run

`list-registration-regular` passes initial List registration, metadata, Next and
Back, but fails after Refresh: native view 500 remains despite global choice 50.
Preserve that failure. One bounded QA-only observer trace (at the existing tick,
at most 256 changed states, synthetic fixture paths only) will distinguish an
unacknowledged asynchronous request from an unavailable container or native
dispatch failure. No production diagnostic logging or extra worker is added.
If the observer contract itself is implicated, add a failing host case for that
exact ordering before the smallest correction; do not loosen the refresh check.

The trace remained `pending` for the same directory/current Icons 500 after
dispatch. A host counterexample independently proves that a processed command
followed by a provider override between observer samples never clears that state.
Use a unique, nonpersistent Home-window acknowledgement after SetViewMode on the
same FIFO GUI builtin queue. It acknowledges processing, not successful layout;
the observer still verifies the actual visible view. A mismatched view can then
be reapplied at the existing foreground tick, with only one unacknowledged pair
per context. No timeout, synchronous GUI wait, worker or provider reload.
Native ModuleXbmc::executebuiltin posts both calls to the messenger FIFO;
Container.SetViewMode handles its GUI message synchronously before the following
SetProperty builtin executes. Checkpoint/background guards remain unchanged.
Selected additional checks: missed observation/provider override, stale
acknowledgement versus a newer context, and existing queue-coalescing/exclusion/
fallback tests; repeat only the failed List transition fixture on the correction.

Final compatibility review also checks the raw MyVideoNav List visibility
conditions, beyond its scoped includes. Those existing predicates must recognize
the internal folder IDs as the same logical List; otherwise a folder's existing
collection/detail decoration can disappear. Select one source equivalence case
for all original predicates and a folder-transition Linux check if that check
finds missing aliases. Media ID 50/Cinema conditions remain logically unchanged;
reuse their existing runtime evidence with the pre-change byte bindings.
