# Job973 / token976 attribution — evidence boundary

The user confirmed on2026-11-03 that the media item/source cannot be reliably
recalled. Do not assign this historical job to a local item, add-on, folder,
UPnP or PVR. The archive observations remain secondhand from the separate private
reader; original ZIP bytes are not available in this executor.

The actual signed451 native source/map is restored and verified by
run41726452356. The following is a source trace, not a recovered historical call
stack or confirmation that the historical producer was451:

- `xbmc/utils/JobManager.cpp:487` assigns `m_jobCounter++`, skipping zero.
  Job973 is a process-local admission identifier, with no item/source encoding.
- `xbmc/utils/JobCheckpoint.h:165` assigns `token = ++registry.next` in its own
  registry. Token976 identifies that ledger admission; it is not a media ID,
  provider ID or route discriminator. The numeric difference proves no route.
- `CJobManager::TrackCheckpointJob`, lines509–579, records responsibility,
  owner, operation, RTTI class, and the optional `GetCheckpointResource()`.
  The baseline watched class has no resource override; `utils/Job.h:127`
  defaults to an empty resource. The ledger has no `CFileItem`, item path,
  media type, recursive/PVR/UPnP flags, callback RTTI or originating UI field.
- The reviewed core source has one construction site for the exact class:
  `video/VideoLibraryQueue.cpp:159`, via `MarkAsWatched(item, watched)`.
  It admits the same class for the video-nav ToggleWatched action
  (`video/windows/GUIWindowVideoNav.cpp:88`), watched/unwatched context-menu
  actions (`video/ContextMenus.cpp:128,167`), and PVR recording actions
  (`pvr/windows/GUIWindowPVRRecordings.cpp:120`). Folder/UPnP/PVR branches
  remain inside the same job implementation, so its class name cannot choose
  among them. An add-on-provided item may reach a native menu; this does not
  identify any specific add-on in the reported incident.
- `CJobQueue::QueueNextJob` (`utils/JobManager.cpp:214`) submits with `this`
  as callback. `CVideoLibraryQueue::OnJobComplete` lines238–254 performs the
  normal refresh/queue cleanup, then calls its base callback. The historical
  record does not preserve that callback identity, so this is the matching
  source route, not proof of the historical object/callback pair.
- `CJobManager::OnJobComplete` lines752–793 invokes the real callback and frees
  the job. `JobCheckpoint::Complete` refuses Unknown records at line201;
  `GetSnapshot` lines270–271 labels a retained completed record
  `completed_without_owner_receipt`. No path is reconstructed at retirement.

The available corroborated receipt supplies the job ID, token, type and empty
owner/resource. The retained/truncated histories and source-side fields do not
establish the missing item route. A class label, a successful operation result,
or an empty resource is insufficient evidence of durability or route ownership.
No unavailable historical item is reconstructed or inferred from the user.

The staged correction classifies only the exact reviewed job/callback pair for
one nonrecursive, non-UPnP, non-PVR item and checks actual database outcomes.
Unknown callbacks/subclasses/recursive/remote work keep their obligations. It
does not resolve, erase, reclassify or fabricate a receipt for the old token976.
A verified current-run route with real native queue/database/callback execution
is still needed; matching it would not retroactively identify the old event.
