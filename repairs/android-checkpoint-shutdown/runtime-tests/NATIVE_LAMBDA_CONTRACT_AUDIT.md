# Native lambda persistence contracts

This is a source audit of `runtime-native/xbmc`. A lambda's type, successful
return, queue name, or disappearance from the job registry is not persistence
proof. `Required` below means that the exact accepted job must complete and its
named persistence owner must independently acknowledge durability. It does not
mean that lambda completion alone grants SAFE. Unclassified calls remain
`Unknown`, including after completion.

## Direct JobManager submissions

| Exact source / enclosing operation | Effects inspected | Narrow contract |
| --- | --- | --- |
| `application/Application.cpp`, `CApplication::Initialize`, `databaseManager.Initialize()` | `DatabaseManager.cpp` updates add-on, view, texture, music, video, PVR and EPG databases; may create/copy databases and run schema transactions. | `Required: native_databases`; never memory-only. Database barrier must cover the resulting SQLite paths, transactions, errors and closed handles. |
| Same function, `guiFontManager.Initialize()` | `GUIFontManager::LoadUserFonts` reads existing user font files, updates in-memory metadata, and may rewrite `fontcache.xml`. It does not change the font files. | Candidate exact derived-cache exemption; **not** memory-only. A conservative required mapping needs an actual file checkpoint owner. Do not infer all XML files are covered merely because a guard is named `xml_files`. |
| Same function, repository check / `MigrateAddons()` | Repository requests, installation/update of add-on files, add-on disablement and related settings/database/event changes. | `Unknown` until installer/configuration participants cover all these writes. |
| `addons/AddonManager.cpp`, `CAddonMgr::UpdateLastUsed` | SQL `UPDATE installed SET lastUsed`, in-memory add-on metadata, then `MetadataChanged` event publication. `SetLastUsed` returns a boolean currently ignored by the caller. | SQL scope maps to `Required: native_databases`; the event fanout remains a separate obligation. A whole-lambda exemption is inappropriate. |
| `pvr/PVRManager.cpp`, `CPVRManager::Init` | `Clients()->Start()` reaches client discovery and potentially private binary construction. | Implemented `Required: pvr`, operation `pvr.initial_clients_start`. |
| `pvr/addons/PVRClients.cpp`, `CPVRClients::RequestRestart` | `UpdateClients(addonId, instanceId)` may construct/recreate/destroy private clients. | Implemented `Required: pvr`, operation `pvr.request_client_restart`. |
| Same file, `CPVRClients::OnAddonEvent` PVR branch | Same update operation, only for relevant add-on events and PVR add-on type. | Implemented `Required: pvr`, operation `pvr.addon_event_update_clients`. |
| `pvr/PVRManager.cpp`, `TriggerPlayChannelOnStartup` | Starts playback through PVR GUI playback actions. | Remains `Unknown`; a playback request is not a memory-only operation. |
| Same file, `ConnectionStateChange` | Formats a notification and schedules `CPVREventLogJob`; that job updates in-memory `CEventLog` entries and GUI toast state. | Candidate exact `NonPersistent` contract for this lambda **and** its specific null-callback event-log child. It is not a contract for other PVR jobs. |
| `cores/paplayer/PAPlayer.cpp`, `OpenFile` / `QueueNextFile` | Decoder and stream preparation, player callbacks, queue advancement; job callback is `PAPlayer` itself. | Remain `Unknown` until the audio-player and exact completion callback are audited. No null-callback exemption applies. |
| Same file, `CloseFileCB` | `OnPlayerCloseFile` reaches resume/playcount/file-state persistence. | Candidate `Required: playback` only with the checked playback/file-state owner and job result/failure propagation. |
| `cores/RetroPlayer/RetroPlayer.cpp`, `SetPlaybackSpeed` pause/resume lambdas | Native callback dispatches Python player callbacks and GUI messages. | Remain `Unknown`; Python callbacks may persist state. Not memory-only despite small lambda bodies. |

The three implemented PVR annotations change only submission metadata, retaining
their lambda bodies and captured arguments. They are safe mappings because the
PVR owner checks both in-flight startup leases and the historical
`m_androidCheckpointOwnerEncountered` latch. A binary client encountered earlier
still blocks the barrier even if it is subsequently destroyed or no longer
ready. No private binary implementation receives a persistence exemption.

Validation commands:

```sh
python repairs/android-checkpoint-shutdown/runtime-tests/test_pvr_lambda_contracts.py --source-root /absolute/runtime-native
python repairs/android-checkpoint-shutdown/runtime-tests/test_pvr_checkpoint_admission.py --source-root /absolute/runtime-native
```

Both passed. The first compiles the actual three production function bodies with
a contract-capturing job double and checks the exact owner/operation, deferred
execution, captured arguments, event filter and non-PVR filter. The second
compiles the production owner predicates and verifies retained/private owner
history plus the three complete startup admission scopes. Production JobManager
ledger and Android execution require their separate checks.

## Queue lambdas and event fanout

`cores/VideoPlayer/VideoPlayer.cpp` owns a private outbound queue constructed with
the playback owner. Its nine current submissions call `RequestVideoSettings`,
`OnAVStarted`, `StoreVideoSettings` (two sites), `OnPlayerCloseFile` (two sites),
the stopped/error/ended callback, `OnPlayBackStarted`, and `OnAVChange`.
These belong to the checked playback pipeline and its callback-drain ordering.
Some read native state, some save databases, and others dispatch Python and GUI
events. They must not become global `CLambdaJob` or `CJobQueue` exemptions.

`utils/EventStream.h`, `CEventSource::Publish`, copies arbitrary subscriptions
and runs each `HandleEvent`. Its source line alone cannot prove a persistence
contract. For example, add-on events can start Python services, update PVR
clients, schedule repository updates, load binary add-ons, and post GUI refresh
messages. The generic event-source lambda remains `Unknown`.

There are narrow memory-only candidates if both event type and exact registered
callback set are enforced:

- `PlayerShowInfoChangedEvent` to `CPVRGUIChannelNavigator::Notify` updates a
  boolean and publishes `PVRPreviewAndPlayerShowInfoChangedEvent`.
- That preview event to `CPVRGUIInfo::Notify` only stores its boolean under a
  lock. Both stages would need their own exact contracts.
- `CDirectoryProvider::OnFavouritesEvent` and its add-on/repository callbacks
  only invalidate in-memory directory state, but other subscribers on the same
  event source can do more. Do not exempt the entire source based on this one
  callback.

An empty captured subscriber list can avoid creating a no-op job. This is a
structural empty-work case, not permission to exempt nonempty fanout.

## Command Center client classification and RPC ordering

The inspected `plugin.py` has 358 lines. Listing, navigator, custom-list display,
command-palette listing and unavailable-source display do not perform user-state
mutations. They return list items/URLs; they do not execute provider playback or
palette commands. All directory results explicitly disable disk caching.
All manual mutations use the cross-interpreter participant gate and durable
managed `continue-watching.json`. Dialogs run before admission, then the operation
reloads current state. The client does not create private threads or writer
finalizers. Its `Container.Refresh` requests remain subject to native admission
and independently classified directory/provider owners.

The initial integration released the gate while running synchronous Kodi
JSON-RPC. This allowed a delayed client operation to overtake the resident's final
mirror operation and was a blocker to classifying the client.

Reproduction using the actual runtime modules and existing Kodi API doubles:

1. Client A snapshots a pending unwatched operation, then pauses before its RPC.
2. A newer watched operation B replaces A in the durable queue.
3. The resident establishes its checkpoint fence, commits B to Kodi, and empties
   the pending queue.
4. Client A resumes its old RPC and sets Kodi playcount to zero. Its subsequent
   JSON update is correctly rejected by `AdmissionClosed`.

Observed pre-fix final state: `hub_watched=true`, `kodi_playcount=0`,
`pending_kodi_sync={}`, delayed client error `AdmissionClosed`. Local JSON fencing
alone did not prove the external Kodi mirror stable.

The authorized fix in `resume_hub.py` now holds one admitted scope across each
queue snapshot, synchronous RPC, checked readback and operation acknowledgement.
It releases the scope between operations. Both ordinary and checkpoint mirroring
require an explicit `OK` response and verified playcount; failures retain the
durable queued operation. The checkpoint preserves an already nonzero native
playcount rather than resetting it to one.

The inspected native call chain is `ModuleXbmc::executeJSONRPC` to
`CJSONRPC::MethodCall` to `CVideoLibrary::SetMovieDetails/SetEpisodeDetails` and
their corresponding Get methods. Database work runs directly;
`CGUIWindowManager::SendThreadMessage` and `CAnnouncementManager::Announce`
enqueue their notifications and return. This exact chain does not synchronously
wait for a Python callback needing the held file gate. No interactive dialog is
inside the scope.

`test_runtime_rpc_admission.py --runtime /absolute/runtime-commandcenter` passed
using two actual host processes, the production file lock and production plugin/
Resume Hub code. A shared SQLite RPC double holds old operation A in flight,
proves newer B cannot acquire the gate until A finishes, then verifies B and the
checkpoint drain leave matching watched state with no queued operation. Separate
checks retain operations after failed readback or malformed acknowledgement.
The 13 actual-runtime tests and 14 inherited Resume Hub tests also pass.

The exact pinned `plugin.py` entry point can therefore use a separate
`command_center_client` contract sharing the complete source/dependency pins.
It must never count as the resident service, and the global native database
checkpoint remains responsible for SQLite durability after RPC completion.
`default.py` remains unresolved: restore/install/configuration paths have wider
file effects and are not covered by the Resume Hub receipt.

These are source and host-test findings, not physical device acceptance or a
claim that all installed add-ons have shutdown contracts.
