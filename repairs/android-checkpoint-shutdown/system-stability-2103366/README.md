# Infinity 2103366 — implementation candidate, not Fold accepted

Protected source is `faf41ee1d35fe55140bb1e193089643cc9ac06ee` (2103365),
Android run 38100173431, inherited engine source `15e3cdb7c0c6a107599d1bab65cb369cd286214e`.
`GREEN-2103365.json` records the original signed APK, signer, exact script
postimages and the physical reference: 17/17, 9492 ms, consumed authorization,
confirmed native death. Those original artifacts and source branch are retained.

## Implemented, coordinated repairs

* Resume: synthetic next-episode records copy only show identity; their resolver
  never consumes the previous episode's route/source/database ID. Existing
  unfinished resume and original-episode replay retain their own provider route.
  Season zero is a real season. Missing resolver metadata remains unavailable.
* Series identity: Kodi item unique IDs can describe the episode. Only a checked
  GetEpisodeDetails → GetTVShowDetails relationship supplies series IDs for a
  synthetic resolver route. This read occurs during playback arming; listings add
  no RPC/network work. Ambiguous legacy next cards remain unavailable, without
  rewriting saved state or altering original resume/replay routes. Verified series
  IDs also group library episodes correctly across different episode IDs.
* Timing: bounded numeric/PID/request observations cover service publication,
  verified snapshot loading, filtering, list construction, native queue/fetch,
  artwork metadata and skin binding. Read-only visibility observation recognizes
  the existing reference skin controls 8830/8831. It does not prove texture decode
  or a presented frame; other installed layouts remain unmeasured.
* List items are constructed offscreen through Kodi's existing supported API,
  avoiding needless GUI locks for private, not-yet-published items. No persistence
  gate, digest validation, snapshot revision or provider lookup is bypassed.
* Installer: reviewed install/uninstall jobs supply resource-specific receipts
  after synchronous/nested work, filesystem fsync/namespace checks, checked SQL
  results and the actual callback. Cancellation before DoWork acknowledges no
  writes; active cancellation, missing callback and SQL/fsync failures remain
  blockers. A fully verified reinstall can retire an earlier failed installation
  of the same add-on only when no competing writer remains. History is retained.
* Command Center 0.3.5.19 fallback and installed 0.3.5.20 source pins, reviewed
  manifests and transactional Android installers change together. The exact
  2103365 preimages and interrupted legacy journal are recognized. This requires
  one coordinated native compilation; a standalone modified CC ZIP is unsafe.
* Diagnostics exports code identities and bounded timing rows without reading
  account settings. Stored completion is explicitly previous-close evidence;
  native trace attribution requires matching engine/PID/clock interval.
* Conditional Health reference fixes require ordered authorization/death evidence
  and reject failure wording as a successful authorization. They are not included
  in the APK: the device's installed Health identity remains unknown.

## Preserved limits

The Android Close authority, 17-owner registry, termination gates, PVR/client
refusal, Python retirement/probes/ctypes/SQLite improvements, compat 0.8.2,
approved skin/UI, providers and all user-state formats remain protected. No reset,
new controller, shutdown popup or forced termination is introduced.

Active native PVR durability is **not repaired or accepted**: the audit identifies
an explicit refusal and no complete third-party client persistence handshake.
Changing that path would threaten the protected contract. Full PVR/client design
and hardware evidence are required before a later change.

The reported 30-second TV delay has not been assigned to a measured stage. The
candidate supplies timing and removes a proven avoidable GUI lock, but no faster
Fold measurement is claimed. Installed skin version/Health bytes, authorization,
all themes/views, PiP/rotation/multitasking and long-session memory need hardware
coverage. Historical ANRs are not attributed to 2103365.

## Targeted checks and CI

Tests execute shipped Python methods, complete production JobManager/coordinator,
installer filesystem methods on real files, actual SQLite wrappers and actual Java
installer recovery. They cover stale routes, season zero, restart/offline state,
watched counts, pending/cancelled/failed receipts, missing callbacks, scoped repair,
symlink/FIFO rejection, busy/failed SQLite commits, hash pinning, transactional
code upgrade, hard process death, corrupt backups and unknown edits.

`infinity-2103366-system-stability.yml` compiles Android and one native batch, reuses
only matching dependency/compiler caches, verifies source inputs and signs with
the permanent certificate. `verify_2103365.py` compares all protected APK payloads,
script identities/preimages and JNI declarations with the exact original APK.

## Fold acceptance, before locking anything

1. Record existing nonsecret resume positions, watched counts/checkmarks, selected
   settings, profile/favorites/source memory and functioning authorizations.
2. Install the exact signed candidate over existing data; do not uninstall/reset.
   Export identities to establish the actual skin/Health/provider bytes.
3. Compare five cold and five warm movie/TV trials, first/repeated TV selection,
   background return and online/offline operation. Record selection-to-first-card
   alongside per-stage timing. Separate uncached artwork from local list latency.
4. Complete an episode, resume an unfinished episode, replay watched content,
   switch provider, exercise season transitions/missing next episode and restart.
   Verify the playback target, progress, play counts and blue checks, not only cards.
5. Test benign add-on install/update/cancel/failure/retry; do not update providers
   merely to test. Verify actual files/DB/callback receipts. Exercise PVR/live TV
   and active recording separately; an unsupported operation must remain refused.
6. Cover Fold cover/inner, portrait/landscape, rotation while playing, PiP,
   split-screen/pop-up resize, screen lock and background/foreground recovery.
7. Perform ten normal close/reopen cycles with mixed playback/settings activity.
   Every accepted close requires all 17 owners, no required blockers, consumed
   authorization and identity-matched native death. Compare restored state after
   each reopen. Missing evidence or green CI is not a successful device test.
8. Keep original 2103365 and the coordinated same-certificate code/native rollback
   candidate available. A rollback must restore matching script pins before Kodi
   starts and preserve userdata. Never use uninstall as a rollback.

Health companion installation is withheld until exact installed code matches its
reviewed preimages; a clean/quiet log never establishes recovery. Keep original
diagnostic exports and failed operation history.
