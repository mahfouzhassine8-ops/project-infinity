# Command Center runtime participation audit

Parent: complete `script.infinity.commandcenter` 0.3.5.19 distribution and the
byte-matching eight-file controller overlay in APK 2103335. `addon.xml` remains
unchanged (SHA-256
`c274318b59563e0febb07538e5abe7de0df02b61cadd0c4ab39f066261a5f191`).

Only these existing files change:

| File | Necessary participation change |
| --- | --- |
| `common.py` | Shared native-owner writer gate; strict checked reads/commits for managed JSON; full RMW entry scope; checked marker removal; admitted configuration/restore writers; managed JSON restores pass through journal; runtime ownership files excluded from backup/restore. |
| `default.py` | Existing ambient preference setter uses the admitted settings helper. |
| `experience.py` | Existing source-memory/progress RMW scope combines the existing callback lock and shared OS gate. |
| `plugin.py` | Manual watched/list/rating mutations hold the shared gate for their complete RMW; dialogs happen before locking and reload afterward; required Kodi watched updates are durably queued before RPC. |
| `resume_hub.py` | Durable pending Kodi watched-sync queue; each queue snapshot, checked synchronous RPC/readback and compare-by-operation removal holds one shared admission scope. Failures retain the operation. Existing schema, watched semantics, local lists and provider routes are preserved. |
| `service.py` | Resident checkpoint loop and Monitor marker; callback admission; final memory/persistence shared scope; watched-sync queue drain; clean-stop marker uses checked removal. Normal observers park during checkpoint while callback delivery remains active. |

Two new runtime modules:

- `persistence_participant.py`: checked file+directory commits, full RMW flock,
  journal generations/proofs, exact schema validation, ownership/session fence,
  nested scopes and resident-session authorization.
- `checkpoint_runtime.py`: native file-protocol participant, frozen-clock capture,
  two-phase preparation/finalization, actual ended-event bookkeeping, required
  Kodi watched-sync drain and scoped participant receipt.

The skin and every other original Command Center file are byte-identical,
including `addon.xml`, settings XML, icons, `view_mode.py`, and `skin_upgrade.py`.
No version bump or settings-default change was made. Test files and generated
Python caches are not part of the install overlay.

## Protocol and ordering

Native owns engine PID+token and writes `.android-checkpoint/engine.json`.
The resident service retries registration if that file is not present yet.
Registration requires the exact known add-on version and durable baseline file
proofs. A new engine must present verified `previous_owner` to replace persistent
owner state; the service never infers process death.

The native player owner freezes playback before requesting PREPARE. Command
Center captures the still-available final clock and selections, persists resume,
and reports PLAYBACK_CHECKPOINTED. After native callback queues are drained,
native sends `Other.InfinityCheckpointDrain` from sender `Infinity` and writes
FINALIZE with `player_freeze_complete: true`. The resident Monitor receives that
marker after earlier callbacks for the same interpreter, then seals watched,
memory/session and clean-stop data. It emits PARTICIPANT_COMPLETE only. Python
never grants global process-termination authority, aborts its interpreter, or
calls Kodi Quit/StopPlayer.

An actual ended callback queued after clock release still retains its known
title identity and marks watched. An ordinary stopped/error event without a
verified final clock fails the checkpoint instead of inventing a resume time.
Duplicate ended callbacks do not increment watched/playcount twice.
Checkpoint-only Kodi mirroring reads the native playcount first and leaves an
existing nonzero count untouched. A required zero-to-watched or unwatched update
requires an explicit successful RPC and checked readback. Nonseekable streams
with a verified zero duration do not invent a resume clock; seekable media with
an unavailable final clock still fails the checkpoint.

Manual plugin RPCs use the same admission gate as the checkpoint drain. A delayed
old RPC cannot execute after a newer checkpointed watched operation. The exact
native VideoLibrary Get/SetMovie/EpisodeDetails path performs database work
synchronously and queues notifications; it does not synchronously await Python
callbacks. No dialog runs while this gate is held. This covers the exact pinned
`plugin.py` entry point as a client participant; `default.py` restore/install
operations require wider contracts and remain unresolved.

## Verification

Thirteen actual-runtime tests and fourteen original Resume Hub behavior tests pass.
The two-process real-flock RPC ordering test and failed-readback/acknowledgement
retention checks also pass against the actual runtime source.
The fifteen persistence invariant tests also pass against the runtime helper
(adapting only the hook name from legacy `stop_playback` to `freeze_playback`),
including contention between three independent processes and injected fsync
failure. Native Player and Monitor callbacks both enter the same
`RetardedAsyncCallbackHandler::g_callQueue`, filtered by their shared
`PyThreadState`; `Monitor.waitForAbort` pumps `MakePendingCalls`. The marker is
therefore an ordering proof only after native freeze prevents later playback
callbacks. Android/device acceptance remains required.
