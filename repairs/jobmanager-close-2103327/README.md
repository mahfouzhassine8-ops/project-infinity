# Infinity 2103327 — JobManager shutdown repair candidate

Parent: GitHub-passed Infinity 2103326 Cooperative Close RC1. Locked rollback remains 2103324. Skin remains `skin.infinity.diggz 1.0.5.201`.

## Proven 2103326 device evidence

The Fold trace shows the shared Python shutdown repair working: service stop completed in about 5.25 seconds and the remaining script pass in about 0.05 seconds. Final native shutdown then entered `stop.cancel_jobs` and never returned. `android.kodi_thread_join` remained open, the Android close guard expired without a matching native completion receipt, and the current PID stayed in DESTROYING state. This proves the current blocker is `CJobManager::CancelJobs()` waiting for at least one `JobWorker`; it does not yet identify that worker's exact job type.

## Repair scope

1. Add a nonblocking `CJobManager::BeginShutdown()` phase. It rejects new jobs, frees queued jobs through the existing abort contract, marks active jobs cancelled through the existing `ShouldCancel()` path, and wakes idle workers.
2. Call that phase during the existing Android cooperative pre-destroy window, after settings and skin snapshots but before Python service/script shutdown. Active workers therefore receive the cancellation signal while the already-approved five-second Python grace is running.
3. Keep the original final `CancelJobs()` worker wait. No worker is detached, deleted while running, force-stopped, timed out, or reported complete without exiting.
4. Trace every active JobWorker with its job ID, job type, TID and elapsed execution. While final teardown waits, record the exact remaining active job once per second. Add `jobs.*` to the independent critical shutdown timeline.
5. Preserve the 2103326 Android guard, Python repair, Health Center export, native cleanup, database/settings persistence, chooser ownership rules, Force Close route, Cobra, providers, skin, data and all unrelated payload.

The early cancellation is the repair attempt. The detailed JobWorker records are the fail-safe: if a non-cooperative job still blocks, the next device export identifies the exact job rather than only the broad JobManager call.

## Prohibited shortcuts

No PID kill, force-stop substitution, detached worker, shortened final join, automatic data reset, add-on disablement, provider removal, fake completion receipt or progress animation workaround.

## Acceptance

The candidate is not locked until repeated Fold tests show clean Normal Close, immediate relaunch after actual PID exit, intact settings/resume/watch state, no provider/Cobra regression, and Health Center evidence matching the current PID. If it still stalls, export before Force Close; `jobs.waiting_active` must identify the exact remaining job.
