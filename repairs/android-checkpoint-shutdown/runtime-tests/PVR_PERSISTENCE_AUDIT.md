# Native PVR persistence checkpoint audit

Audit date: 2026-10-08. Source: the preserved 2103334 transformed native lineage, inspected in `runtime-native/xbmc/pvr`; the PVR files were not modified for this audit. References below are relative to `xbmc/`. This is an owner inventory and integration proposal, not a successful PVR checkpoint implementation or device acceptance result.

## Current disposition

The Android coordinator must keep reporting `pvr / active_pvr_owner_has_no_persistence_participant` for a running native PVR manager. The present source does not justify replacing that refusal with success, `CPVRChannelGroups::PersistAll()`, a zero SQL transaction count, or `CPVRClient::Stop()`. No preservation-parent file was edited.

Native Kodi PVR is not synonymous with all live media. Plugin-provided live streams played by native VideoPlayer, and playback in a distinct Cobra process, require their own observed player/owner inventory. This audit neither rejects nor proves those routes. Physical testing must establish which route the installed configuration actually uses.

## Required persistent owners

| Owner and state | Current save path | Checkpoint implication |
| --- | --- | --- |
| Channels: user names/icons/hidden/parental lock, EPG preferences, last watched channel/group | `pvr/channels/PVRChannel.cpp:234` `Persist`; `pvr/PVRDatabase.cpp:1143` persists dirty channel fields; `PVRChannel.cpp:394` performs immediate last-watched SQL | Fence mutation before dirty snapshot; save dirty channels only; retain dirty state until checked commit. Last-watched must acquire checked dirty recovery. |
| Groups and channel membership: names, visibility, position/order, numbering, last watched/opened | `pvr/channels/PVRChannelGroups.cpp:457` `PersistAll`; `PVRChannelGroup.cpp:827`; `pvr/PVRDatabase.cpp:1013,1086` | Existing flags are not reliable success evidence. All TV and radio owner groups must be fully loaded and stable. |
| Provider user changes and client priority/identity | `pvr/providers/PVRProviders.cpp:292,330`; `PVRProvider.cpp:288`; `pvr/PVRDatabase.cpp:403,568` | Persist immediate accepted user changes with truthful errors; add owner dirty generation for failed saves. Provider metadata cannot all be dismissed as cache because user changes are supported. |
| Local reminders and local timer rules/children | `pvr/timers/PVRTimers.cpp:494,1031,1083,1127,1141`; `PVRTimerInfoTag.cpp:598`; `pvr/PVRDatabase.cpp:1300` | Local CRUD is primarily synchronous. Drain accepted semantic operations, freeze rule generation/expiry, and retain failed updates/deletions; do not blindly re-save backend-owned timers. |
| Saved EPG search definitions and execution history | `pvr/epg/EpgContainer.cpp:980` and following update/delete methods; `EpgDatabase.cpp:1383` and following | These are user data in the EPG database, not disposable program-guide cache. Commit accepted operations; preserve dirty filters until successful return. Unsaved dialog edits are not automatically committed user intent. |
| Live-channel playback history | `pvr/PVRPlaybackState.cpp:148,229,654`; `pvr/PVRManager.cpp:840` | Snapshot the final channel/group history and honor the configured minimum-watch delay. A paused/frozen player alone does not execute `OnPlaybackStopped` and therefore does not prove final history was saved. |
| Recording watched/resume and backend timer/control changes | `pvr/recordings/PVRRecording.cpp:313,325,338,351`; `pvr/addons/PVRClient.cpp:875,887,973,985,997` | Depending on backend capabilities, required writes occur through client ABI calls, not only local Video DB. Their result must participate in the barrier. A local bookmark readback does not prove remote state persisted. |
| Kodi-managed PVR add-on settings | `CPVRClient` holds the instantiated `CAddon`; common add-on settings save APIs | Include the real loaded add-on settings owner, including instance settings; successful generic settings save says nothing about private binary data. |

## Existing return/dirty-state defects that block an acknowledgement

* `pvr/PVRDatabase.cpp:964` `PersistChannels` calls `channel->Persisted()` before `CommitInsertQueries()`. An individual `Persist(..., false)` failure does not reliably set the aggregate false. A failed commit can leave channels apparently clean.
* `pvr/channels/PVRChannelGroup.cpp:827` clears `m_bChanged` even when `database->Persist` fails. It also returns true without saving an existing group that is not fully loaded.
* `pvr/PVRDatabase.cpp:1013` `PersistGroupMembers` skips invalid channel IDs, ignores `QueueInsertQuery` returns, and marks all members saved following only the final batch result.
* `pvr/channels/PVRChannel.cpp:394` changes last-watched fields before SQL, without setting its general dirty flag. Group `SetLastWatched` and `SetLastOpened` (`PVRChannelGroup.cpp:1068,1088`) ignore DB return values and do not preserve retry dirtiness. `CPVRPlaybackState::UpdateLastWatched` ignores the channel return.
* `pvr/providers/PVRProviders.cpp:292` ignores provider persistence returns after changing the in-memory owner. `PersistUserChanges` at 330 always returns true.
* `pvr/timers/PVRTimers.cpp:494` has local rule/expiry branches ignoring `Persist` and `DeleteFromDatabase`; `DeleteLocalTimer` at 1083 removes the in-memory entry before the database deletion result. `UpdateLocalTimer` at 1127 is delete-and-recreate. A dropped dirty owner cannot be recovered merely by scanning current live objects.
* `pvr/epg/EpgContainer.cpp:239` `PersistAll` ignores both in-loop and final `CommitDeleteQueries`/`CommitInsertQueries` results. Its bool is insufficient proof even for cache writes.

The integrated native SQL barrier makes actual wrapper SQL failures sticky during a checkpoint and tracks outstanding transactions/queues, but it does not reconstruct previously forgotten dirty semantic objects or prove opaque client writes. Those defects need truthful owner tracking in addition to SQL checks.

## Reconstructible EPG work

`pvr/epg/EpgContainer.cpp:306` processes backend guide refreshes, manual update requests, tag-change queues and expiry; it periodically persists guide data and does a final full `PersistAll` at thread exit (444). Backend-derived program-guide events can be classified as reconstructible cache once actual client behavior is verified. New refresh/generation may be rejected, and unstarted reconstructible requests may remain unexecuted. Already accepted SQL operations must finish or fail explicitly. The same database's `savedsearches` rows must never be discarded under a cache exemption.

Neither EPG `Stop()` nor PVR manager `Stop()` is the desired barrier. `pvr/PVRManager.cpp:483` leaves its main loop through client/timer/EPG/GUI stop and component unload; timer `Stop` (`PVRTimers.cpp:146`) and EPG `Stop` join threads. These are teardown dependencies, not proof that required state is durable.

## Safe integration shape

1. Add a session-bound PVR participant with `BeginQuiesce`, nonblocking `PollQuiesced`, checked `PersistRequired`, and `Seal`. It must share the authoritative coordinator session, never own process termination, and never call manager/EPG teardown for success.
2. At PREPARE, atomically close admission and count accepted semantic mutations. Cover user CRUD and setters, manager update scheduling and execution, local timer worker updates, EPG refresh/tag callback work, recording mutations and playback-history timer callbacks. Existing accepted operations retain permission until completion; no lock holder is killed.
3. Park PVR manager/timer/EPG work at non-destructive loop boundaries. `CPVRManagerJobQueue::AppendJob/ExecutePendingJobs` (`PVRManager.cpp:142,158`) needs classification: provider refresh/cache work can stop admission, but accepted user persistence cannot be deleted. Its `Stop()` alone does not prevent `AppendJob` and is not a queue-drained acknowledgement.
4. Replace check-then-increment client admission with a single mutex-protected lease covering outgoing calls and incoming callbacks. Allow exact final persistence calls while rejecting new optional work. Do not block backend calls required for recording resume before that final save completes.
5. After accepted operations settle, capture final playback history, flush only dirty channel/group/member/provider state, and verify required local timer/search operations completed. Fix the listed return/dirty defects and retain deleted-owner tombstones until their SQL commits. Use the existing checked DB participant to prove queues and transactions empty; never blanket-COMMIT another owner's transaction.
6. Seal all PVR mutation admission after successful local and client acknowledgements. A late mutation, unsupported client or failed operation yields `CHECKPOINT_FAILED` with the specific owner; it does not authorize termination.

## Binary client contract gap

`pvr/addons/PVRClient.cpp:1345` checks `m_bBlockAddonCalls` before incrementing `m_iAddonCalls`, leaving a race if used as a barrier. `Stop()` at 217 sets a flag but does not atomically settle calls. `HandleAddonCallback` at 1656 does not count callbacks; forced callbacks may bypass the block. Fixing those races still provides call completion only.

The generic PVR ABI inspected here has no `SAVE_COMPLETE` contract for private binary client files, raw SQLite connections, background workers, or delayed remote requests. The source snapshot contains the Kodi-facing wrapper/API, not a verified source/version/state inventory of the user's installed PVR binary clients. Before an active client can pass, audit its exact installed version and identify all required private state; either establish and test synchronous durable behavior with no surviving dirty owner, or implement a real client persistence acknowledgement. Absence of a known write is not proof of absence. Until then active native PVR remains a named unsupported participant, and Live TV acceptance remains unproven for that route.

## Required evidence before relaxing the refusal

Production-function tests should inject channel/group/member/provider failures, confirm failed owners remain dirty, exercise local timer deletion failure and saved-search rollback, and prove late client calls/callbacks cannot enter after the same atomic gate. Device tests must cover TV and radio group settings/history, local reminder rules, saved searches, recording resume/playcount for each installed backend capability, and restart after checkpoint termination. Success must not depend on PVR/EPG thread destruction.
