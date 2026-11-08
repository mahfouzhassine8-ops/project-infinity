# Owner scope extension — execution continuation, 2026-11-08

The owner explicitly authorized the two previously identified native observation
files in the current conversation:

- `xbmc/interfaces/generic/ScriptInvocationManager.cpp`
- `xbmc/interfaces/legacy/Player.cpp`

They may change only as necessary to carry verified Watchlist origin to POV's
actual playing item. The earlier seven-file scope and at most one authenticated
Command Center helper remain otherwise unchanged. Implementation stays on
`work/infinity-watchlist-phase-b-20261108`, based on protected2103466/5ee1c7ae.
No further routine approvals or duplicate architecture investigations are needed.

The owner also clarified episode ordering: reuse supported existing infrastructure;
if complete next-episode evidence is unavailable, retain accurate progress and
withhold the successor. Do not invent ordering or add a replacement tracker.
Accordingly the implementation reuses the existing checked local-library
`verified_next` path; nonlibrary episodes without that evidence remain correctly
tracked without an invented successor. No new metadata client/service/database.

Preserve Search and provider code, Cobra, ordinary Movies/TV, Trakt
saving/authentication, UI/navigation, all user data and existing recovery guards.
Reuse the seventeen passing host checks. Run only necessary focused new source,
ARM64 and Android checks, then original-key successor/recovery preparation when
its required gates pass. Physical Fold acceptance remains one owner test.

This records the owner's chat authorization; it is not a new blanket source,
shared-lifecycle, signature or testing exception.
