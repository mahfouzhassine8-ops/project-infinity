# Android-owned persistence checkpoint shutdown

This work starts from the delivered **2103335 Native Trace Bridge RC1** source
revision `515992ed6ac98a365bb75f42c117007ae94c2aed`. Its native engine is the
2103334 engine. Neither candidate is accepted as a shutdown repair.

**Status: runtime integration on the isolated work branch; build and device
acceptance remain open.** `runtime/` contains the actual Android, native and
Command Center and embedded add-on source overlays, each with a complete protected parent manifest
and enumerated postimages. These are not a locked candidate or a device-ready
APK. Unknown persistence owners explicitly prevent a safe acknowledgment.

## Contract

Normal Close succeeds when all required persistent state is committed and its
writers remain fenced. It does not depend on Kodi's complete destructor tree.
Android owns one transaction identified by a unique session, engine-instance
owner token, and PID. The default-process coordinator can authorize termination
only after a matching native persistence acknowledgment. The bound engine
endpoint validates its own safe state before terminating its own process.

The state sequence is IDLE, QUIESCE, CHECKPOINT_REQUESTED, PERSISTING,
SAFE_TO_TERMINATE, ENGINE_TERMINATING, COMPLETE. Failure or deadline expiration
leaves the engine running and explicitly exposes recovery. Force Close remains
a separate user action. A timer, lifecycle callback, missing PID, native teardown
receipt, or completed IPC send cannot substitute for a persistence acknowledgment.

The continuation of the brief authorizes publication to the separate shutdown
work branch only. It does not authorize merging to main, replacing the rollback
lineage, locking the architecture, or distributing a device-ready APK.

## Parent evidence

`PARENT.json` records the parent APK and native digests, signing certificate,
source commit and workflow runs. The downloaded APK digest was independently
verified. A recovered native review archive was transformed by the exact 3334
delta; all 4,479 recovered files match the compiled source manifest. This is a
verified local source subset. The work-branch CI subsequently reconstructed and
verified all 9,374 parent inputs before applying the runtime delta.

The delivered build records skin parent 1.0.5.204. The skin is installed content,
not a replacement skin bundled in the APK. The APK contains the 0.3.5.19 Resume
Hub overlay; its eight files match the repository source. The full 0.3.5.19
Command Center archive was recovered separately for inspection. Do not use an
older remembered skin version or replace `skin.infinity.diggz`.

## Existing routes and process ownership

The existing manifest already places Main, InfinityKodiEntryActivity,
InfinityPowerControlActivity, InfinityCloseNativeLease and the continuity
service in `:kodi`. Splash, Cobra and InfinityCloseGuardService remain in the
default process. A new process split is unnecessary.

The preserved parent close route was:

1. InfinityPowerControlActivity calls InfinityExitCompletion.requestNormal.
2. InfinityCloseNativeLease acquires a ticket and starts the default-process guard.
3. The guard binds the existing engine service with BIND_IMPORTANT, without
   BIND_AUTO_CREATE, then sends READY.
4. InfinityExitCompletion.guardedReady sends Application.Quit.
5. Native activity destruction enters the legacy shutdown chain.

The runtime overlay replaces the fourth step with asynchronous JNI request,
status and one-shot termination authorization. Main stays alive during the
checkpoint. The default-process guard writes the matched persistence receipt,
then authorizes the bound `:kodi` endpoint; that endpoint rechecks native safety
immediately before terminating itself. The old afterStop dispatch and
Activity-local Plan no longer certify Normal Close.

The parent InfinityKodiShutdown called completion only after an owner lease was
released and a matching `native.CXBMCApp.Destroy.complete` receipt existed. The
new route uses a distinct session-bound persistence receipt plus observed
engine death. It never forges a destructor receipt. Chooser and Health Center
identify checkpoint completion and the blocking persistence owner on failure.

## Runtime integration obligations

The following are the review obligations for the runtime integration. Source
and host-test results do not by themselves certify native ABI compilation,
packaging, installed-owner coverage or physical-device behavior.

1. Wire the Java transaction to the default-process guard, its existing Messenger
   binding, durable coordinator receipts, chooser snapshots and engine-death
   observation. Verify same UID and session/owner/PID on every IPC message.
2. Add asynchronous checkpoint request/status JNI methods to JNIMainActivity.
   Service checkpoint work in the live application loop. Do not call TMSG_QUIT,
   CApplication::Stop/Cleanup or NativeActivity finish on the successful path.
3. Enlist every required state owner from `PERSISTENCE-AUDIT.md`. Instrument the
   complete mutation interval, including work accepted before Close. Registering
   an owner name without wrapping its actual writes is not a barrier.
4. Add a dedicated quiesce mode for playback, jobs, scripts, refreshes and
   maintenance. Preserve already-accepted persistence jobs and the message loop.
   Existing JobManager::BeginShutdown deletes queued jobs and cannot be reused.
5. Capture the final player state before the player clock disappears; await
   checked video/audio settings and final resume/watched jobs, then the Resume
   Hub participant. Block auto-next and duplicate playcount updates.
6. Route actual Command Center service, plugin, common helpers and maintenance
   mutations through one OS-level read-modify-write fence. Park the service after
   its matching checkpoint result. An interpreter-local RLock is insufficient.
7. Propagate storage errors through every relevant save adapter. A low-level
   SQLite fix or durable-file helper alone does not fix callers that discard
   results. Preserve dirty generations on partial failure and retry idempotently.
8. Classify every admitted third-party Python/binary add-on writer, including
   invocations that completed before Close. Direct Python
   sqlite3/file IO bypasses native database wrappers. Require an acknowledged
   participant, a justified noncritical classification, or fail closed.
9. Prove no required writer can resume between SAFE and termination. Validate
   identity again at the bound engine endpoint; do not trust a reused numeric PID.
10. Preserve APK assets/resources, all unrelated native source changes, Cobra,
    JNI compatibility, permanent signer and install-over behavior. Build against
    the exact inherited engine recipe and validate the resulting packaged bytes.

The coordinator may not classify missing instrumentation as a clean owner.
There is no production adapter that returns SAFE unconditionally in this patch.

## Implemented runtime scope and remaining coverage

The integration includes the resident Android coordinator, authenticated Binder
consumption gate, explicit JNI operations, player-thread freeze and checked final
playback writes, real SQLite transaction/queued-write accounting, atomic checked
XML saves with metadata preservation, loaded add-on/skin settings participation,
favorites/peripheral save owners, and the actual resident Command Center service
and plugin write paths. Force Close remains a separate recovery action.

The checkpoint captures accepted pending rating, calibration, delayed settings
and game-default changes without window deinitialization. Checked write/readback
and serialization failures retain their obligations; unsupported pending actions
are reported instead of replaying UI commands. The GUI owner completes only
after the final settings/database barrier.

Job admission records the actual implementation and callback responsibility.
Audited in-memory jobs can remain alive; required jobs stay attached to their
checked persistence owner through callbacks and destruction. Unknown jobs remain
named lifetime obligations even after returning true. Neither a global job count
nor worker completion serves as a durability receipt.

Startup registers the actual held Android engine-owner lease before native
activity creation. Native publishes that identity before starting Python
services. Relaunch checks the previous engine and participant journal owners
independently through the existing Android lease mechanism. Missing lease
evidence is unknown, never proof of process death; numeric PID reuse is not an
ownership transfer. The participant journal uses exact previous-owner CAS.

The embedded compat service participates in the same checkpoint and parks its
writers after checked file and startup-marker persistence. Only three compat
code files change; its settings, resources and the other embedded add-ons remain
hash protected. This prevents successful normal checkpoint closes from being
miscounted as unclean service exits. Audio-policy file durability is a separate
native owner; an unaudited active/completed policy dialog is still unresolved.

The Command Center update changes only eight code files. Its version, settings
schema, skin-upgrade code and UI resources remain unchanged. A pre-native
installer verifies all original or retry postimages before applying the pinned
payload; its journal permits rollback/recovery without touching user data.
Resume Hub's queued native-library RPC, checked readback and queue acknowledgement
share one admitted cross-interpreter scope. This prevents an older operation
from overwriting a newer checkpointed watched value. The plugin has a separate
exact-source client contract; restore/install commands remain unresolved.

Unaudited foreign Python/private binary add-on writers, unsupported player
backends and uncovered active PVR owners are explicit coverage gaps. Script exit,
thread disappearance and elapsed deadlines are not persistence acknowledgments.
An unresolved-script obligation is recorded at admission and survives invocation
completion, exceptions and registry removal for the process lifetime. Verified
code contracts bind actual entry and dependency hashes, not just add-on IDs.
The current work must not be declared accepted while required installed owners
lack a checked participant or an audited nonpersistent classification.

`native_ci.py` reconstructs the complete inherited Infinity engine recipe before
applying the reviewed overlay and protects all 9,374 parent source inputs.
`android_ci.py` compiles the complete current shell as a non-distributed donor.
The full Android shell compiled successfully at work commits
`d13881ad2f7ccfad8bdbed092847e69e3ef11c19` and
`8b56d1b7ddeacba43f87403b981239f4fe45a440`. The latter includes startup ownership
and embedded compat assets but predates the final GUI-owner/RPC-scope additions;
it must not certify the later source. Native ARM64 compilation remains a separate
required gate.
The work-branch workflow does not publish an APK or alter accepted refs. Build
success is separate from the Fold and dirty-state acceptance matrix below.

## Acceptance evidence required before an APK is called a fix

- A dirty-state/relaunch check for each required owner, including final resume,
  completed-item removal, watched badges, settings, favorites and session restore.
- Close raced with seek, completion, manual watched changes, database work and
  already-running Python writers; no last-write loss or duplicated playcount.
- Real SQL busy/write errors, disk-full and file/receipt failures; none authorizes
  normal termination. Failed or unknown saves remain visible.
- Duplicate Close, stale acknowledgments, chooser recreation, dropped IPC and
  process death at every phase; exactly one owner and a truthful completion state.
- A deliberately stalled legacy teardown owner while persistence succeeds; the
  new route must terminate after the barrier without entering that teardown.
- The correct engine process dies, shell/Cobra remain usable and reopening starts
  exactly one fresh engine instance with preserved state.

Host tests are prerequisites. They do not substitute for the integrated Android
build, installed add-on coverage, physical Fold testing or measured close time.

## Staged code and reproducible checks

- `src/` contains the Java transaction and strict endpoint protocol.
  `ANDROID_TRANSACTION.md` defines the still-required authenticated IPC adapter.
- `native/InfinityPersistenceBarrier.h` owns required-owner generation tracking,
  mutation/commit leases, retries, revocation and the continuing writer fence.
- `native/InfinityCheckpointFile.h` implements checked local-file checkpoint IO.
- `native/checked_sqlite.py` produces an exact-preimage, two-file transaction-error
  overlay outside the preserved native source. It does not activate close.
- `resume/persistence_participant.py` provides shared read-modify-write admission
  and durable JSON participant receipts. All real add-on writers still need to
  use it; it never returns global SAFE_TO_TERMINATE.

Run the components with an independently recovered exact 3334 source tree:

```bash
python3 repairs/android-checkpoint-shutdown/run_checks.py \
  --native-source /absolute/path/to/recovered-3334-source \
  --report /absolute/path/to/verification.json
```

The Java runner uses a JDK compiler targeting Java 8. C++ tests use C++17 and a
real host SQLite library for transaction failure cases. The report explicitly
records that APK integration and physical-device verification are incomplete.
