# Selected P0 checks — recorded before execution

Authorization: the user's November 3 Kodi-only P0 repair and continuation.
The independently verified observations in CORROBORATED-EVIDENCE.md supply the
current event details. Execution access is restored. Original archive access is
still unavailable; no Android or APK acceptance is implied by these selections.

## Baseline-only host reproduction

Command (after the bounded harness is written):

```
PYTHONDONTWRITEBYTECODE=1 python3 repairs/infinity-kodi-2103451-checkpoint-anr/reproduce_baseline.py --out /tmp/kodi451-p0-host
```

Only these cases are selected:

1. **Watched-job completion retains an unknown obligation.** Compile the actual
   JobManager admission/tracking methods and JobCheckpoint header with the
   hash-checked watched-job class declarations. Stub the work body only to return
   success; execute no database operations. Check actual RTTI classification,
   owner, receipt requirement and post-destruction blocker. This tests why an
   ordinary completion cannot clear the missing persistence contract, not whether
   a real watched write persisted.
2. **Failed-checkpoint message dispatch starvation.** Compile the exact source
   failure-finalization and checkpoint/Process early branches with controlled
   boundaries. Verify active remains set, the coordinator does not advance and
   normal message dispatch remains unreachable. This is source-bound host control
   flow, not an Android ANR reproduction.
3. **Active-checkpoint application-message rejection.** Compile the actual early
   guard of OnApplicationMessage and check that a display-destroy message cannot
   reach its normal handler under that guard. This guards against proposing a
   pump-only fix that still rejects the lifecycle message.

Each successful reproduction is labeled BASELINE_DEFECT_REPRODUCED, not repair
PASS. Save exact input hashes, compiler command, logs and limitations. Run no
historical eight-/fifteen-case suites or unrelated application/shutdown tests.

## Read-only native identity check

An existing local recovery APK may supply a native member only if its SHA-256
equals the previously read signed-451 native SHA
`151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e`.
Inspect symbols/function bounds with installed tools only. Do not substitute the
older APK as this task's foundation, bypass an artifact access denial or use
that member as full signed-451 package preservation proof. No code is installed
or executed by this read-only identity check.

## Not yet selected/run

No data-durability success tests, Android application runs, emulator launches,
shutdown/reopen tests, signing or installs are selected by this note. Select
their exact commands after accessible inputs and correction scope are established.

## Isolated lifecycle correction — selected after baseline reproduction

The exact-hash native member confirms the two dispatch gates and the Run+440
sleep call. A stage-only correction is authorized for that confirmed mechanism.
It services only display setup/destroy on Kodi's process thread during an active
checkpoint; the existing real handler and waiter acknowledgment remain in use.

Commands:

```
PYTHONDONTWRITEBYTECODE=1 python3 repairs/infinity-kodi-2103451-checkpoint-anr/stage_lifecycle_repair.py --source /tmp/kodi451-p0-inputs --out /tmp/kodi451-p0-lifecycle-candidate
PYTHONDONTWRITEBYTECODE=1 python3 repairs/infinity-kodi-2103451-checkpoint-anr/test_lifecycle_repair.py --source /tmp/kodi451-p0-lifecycle-candidate --baseline /tmp/kodi451-p0-inputs --out /tmp/kodi451-p0-lifecycle-host
```

Select only these source-bound host cases, using the actual SendMsg, queue drain,
new selective pump and application guard branches with controlled GUI boundaries:

1. Actual synchronous sender is released after display dispatch.
2. Acknowledgment waits for the handler to return.
3. Unrelated callback/action FIFO and GUI queue remain untouched by the helper.
4. Wrong-thread helper calls cannot perform display work.
5. Inactive helper leaves normal dispatch behavior unchanged.
6. Rapid setup/destroy order and bounded passes preserve newly queued work.
7. Existing stopped admission and Cleanup semantics remain unchanged.

Compare all existing messenger method bodies and all unrelated application
methods against their input bytes; only the new helper and the two exact
checkpoint branches may differ. No real EGL/native-window, database operation,
Android execution or physical Fold acceptance is represented by this harness.

## Bounded local watched receipt — selected before execution

Stage and test commands:

```
PYTHONDONTWRITEBYTECODE=1 python3 repairs/infinity-kodi-2103451-checkpoint-anr/stage_watched_repair.py --source /tmp/kodi451-p0-inputs --out /tmp/kodi451-p0-watched-candidate
PYTHONDONTWRITEBYTECODE=1 python3 repairs/infinity-kodi-2103451-checkpoint-anr/test_watched_repair.py --source /tmp/kodi451-p0-watched-candidate --inputs /tmp/kodi451-p0-inputs --out /tmp/kodi451-p0-watched-host
```

Compile the actual staged watched-job implementation and original library-job
wrapper with actual JobCheckpoint/JobManager tracking and database-observation
headers. FileItem/profile/queue peers and CVideoDatabase are controlled adapters;
the database adapter must execute real temporary-file SQLite transactions,
separate-connection readback and reopen verification. It is not the Kodi database
engine or the final native-database checkpoint fence.

Selected cases: mark watched; mark unwatched; verified unchanged/no-op; failed
BEGIN; failed COMMIT; failed resume readback; failed count readback; failed close;
unclassified UPnP work preserving its original call; recursive-folder refusal;
unreviewed callback subclass; unreviewed job subclass; failed completion callback.

Assert successful local outcomes produce the correct job receipt only after
checked work/close; failures and unreviewed paths remain blocking. Verify file
rows after the host process exits. Never mark a complete shutdown saved or waive
the authoritative native database fence in this fixture. Android verification
and the actual reported item's route remain outstanding.

The first watched host compile stopped before any case ran: the new header
needed an explicit JobCheckpoint include, and two adapter statements triggered
the strict compiler's indentation check. Correct these specific defects and run
the same selected cases on fresh `-v2` staged/output directories; preserve the
first compile log. No lifecycle tests are repeated for these unrelated edits.

The v2 run passed mark-watched, then exposed an inconsistent cached-tag input in
mark-unwatched. Preserve the passed result in WATCHED-FIRST-CASE.json. Set the
unwatched fixture's cached count to 2 to match its initial database row; the
original job deliberately skips a cached status already matching the request.
No candidate source changes are made for this fixture correction. Execute only
the remaining 12 cases on fresh output `/tmp/kodi451-p0-watched-host-v3` using
`--cases mark-unwatched unchanged begin-failure commit-failure resume-read-error
count-read-error close-failure unknown-upnp unknown-folder unknown-callback
unknown-job callback-failure`, with the same v2 candidate source.

After those 12 remaining cases passed, add exactly one PVR negative control:
`--cases unknown-pvr` with the same v2 candidate source and fresh output
`/tmp/kodi451-p0-watched-host-pvr`. Verify its original remote call and local
playcount update occur, its resume row remains as in the original PVR branch,
and its unreviewed persistence obligation remains Unknown. Do not rerun the
already-passing watched/lifecycle cases for this fixture addition.

Before integration, tighten the new CheckpointSucceeded override to preserve the
original operation result for unclassified remote/subclass work. Their Unknown
ledger entry must still block retirement; successful remote work must not gain a
new misleading generic job-failure label. This changes a tested production
method, so select all 14 watched cases once against fresh candidate `-v3` and
host output `-final`, adding an explicit unknown-operation-result assertion.
Prior v2 results remain historical. The lifecycle source/tests are unchanged and
are not repeated. No Android run is selected by this correction.
