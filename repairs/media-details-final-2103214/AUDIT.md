# Infinity/Cobra 2103214 — Media Details Final

Protected parent: locked and device-working 2103213 Live Blue Ambient + Settings Return.

This is the final scoped Movies/TV Shows refinement. It does not add another permanent landing-page rail and does not redesign the approved Movies/TV Shows home structure.

## Movies and TV Shows

- Recent Releases now prioritizes current/recent release-year metadata first while keeping the visible row name simply **Recent Releases**.
- See All and Genre collection pages gain Sort and Filter:
  - Newest
  - A–Z
  - Rating
  - Recently Added
  - Provider
  - Watched / Unwatched
  - My List
  - Genre refinement
- Empty filtered collections show a clean **Clear filters** recovery action.
- Deeper collection/genre pages retain the existing ambient-aware Cobra trim.

## TV Shows

- Provider series metadata is rendered as a real season/episode browser rather than a generic episode dialog.
- Season chips.
- Episode thumbnails when supplied by the provider.
- Season/episode number and title.
- Air date when supplied.
- Watched, unwatched and partial-progress state.
- Resume Episode.
- Play Next Episode.
- My List state on the show.
- Existing automatic next-episode playback remains authoritative and unchanged. Completion UI is shown only when that automatic next episode does not own the transition.

## Details

- Richer metadata presentation.
- Dynamic + My List / ✓ In My List state.
- More Like This from the already-enabled local provider catalogue.
- Cast & Crew only when provider metadata supplies it; selecting a person performs a bounded explicit lookup against available provider titles.
- Collection / franchise browsing only when provider metadata supplies a collection name; no collection is invented.

## Completion

- Movie completion: Back to Movies and More Like This when available.
- Final TV episode completion: Back to Show / Back to Shows.
- Existing auto-next behavior is preserved.

## Hard preservation

Unchanged from locked 2103213:
- Live TV fixed-blue Ambient Mode.
- Player/Night Cinema ambient coverage.
- Settings return-to-previous behavior.
- Infinity-native Health Center and crash/export behavior.
- Live TV playback, providers, guide, Quick Peek, timeshift/rewind, Multi-View, PiP/background, networking.
- 2103209 Python 3.11 GIL-stability native engine.
- APK assets/resources and permanent signer.
- Video pixels are never recolored.

2103213 remains protected until 2103214 passes device acceptance and the user explicitly locks it.
