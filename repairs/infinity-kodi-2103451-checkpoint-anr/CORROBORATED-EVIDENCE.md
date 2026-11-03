# November 3 evidence supplied by a separate private reader

Provenance: a coordinating reader reported direct retrieval and CRC verification
of the original archive. This executor has **not** accessed the archive. These
are independently supplied observations, not this executor's ZIP inspection.
No raw diagnostics are committed here.

Archive: 945,406 bytes; SHA-256
`bbb1932619b0e99619e20011ee2c8dc870b2336e86d7377a2c95d1c19e4e8ec4`.
Current installed build is reported as 2103451 on SM-F976U1, Android 17.
Historical event producer APK version is null; installed build is not a
cryptographic binding of the historical ANR to a producer APK.

## Checkpoint event

`coordinator-receipt.json`, PID 12745:

- Checkpoint began 11:24:00.018 UTC.
- `CHECKPOINT_FAILED` at 11:24:06.135 UTC, elapsed 6,173 ms.
- Sole blocking owner `background_jobs`, detail
  `unknown_native_job_persistence_contract`.
- Blocker type `CVideoLibraryMarkWatchedJob` (RTTI length prefix `27`), job 973,
  token 976, phase `completed_without_owner_receipt`; owner/resource empty.
- `essential_writes_durable=true`, `checkpoint_saved=false`,
  `authorization_consumed=false`, `terminate_requested=0`.

One retained job is reported, not 27 jobs. The missing contract establishes no
database mutation failure or data loss. Independent essential-write durability
does not authorize clearing this obligation or marking the checkpoint saved.

## ANR event

- Same PID 12745; dump at 11:24:40.167 UTC.
- Input dispatch timed out after 10,000 ms on `FocusEvent(hasFocus=false)`.
- Android main waits through `SendMsg -> XBMC_DestroyDisplay -> surfaceDestroyed`.
- Kodi thread 13047 sleeps in `CApplication::Run+440`.
- Java close history records the checkpoint failure and a 15-second bound,
  followed by before/after AndroidPause at 11:24:30.087 UTC.
- The ANR trace is untruncated. Two 8 MiB native histories are truncated.
- `native-cleanup.json` belongs to an older, different PID; it is not cleanup
  proof for PID 12745.

This differs from the November 1 VideoPlayer-destructor wait. Same process and
time ordering support investigating a shared checkpoint/message-dispatch
dependency, but do not by themselves establish causation or a blocked callback.

## Source control flow under examination

The checked-in source retains `active` when finalizing a failed checkpoint.
`CApplication::Process` calls the coordinator and returns before normal message
dispatch while active. The coordinator returns immediately in CHECKPOINT_FAILED.
`OnApplicationMessage` also rejects messages while active. Android's destroy
callback uses synchronous message delivery. These source paths require a focused
reproducer and exact binary/source binding before a production repair is claimed.

The private observations permit bounded source tracing and host reproduction.
Full archive access, exact source-map provenance, signed-451 package access,
Android verification and final package preservation remain independent gates.
