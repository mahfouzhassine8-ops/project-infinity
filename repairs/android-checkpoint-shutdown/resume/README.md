# Command Center persistence participant foundation

Status: implemented and tested in isolation. **Not installed in an APK, not wired
into Command Center, and not a complete shutdown barrier.** No Python teardown,
Kodi Quit, process termination, or global SAFE_TO_TERMINATE is performed here.

## Source provenance and audit

The eight files in APK 2103335's `assets/infinity/resume-hub-controller.zip`
byte-match `repairs/resume-hub-2103292/src/controller/`. The archive SHA-256 is
`cb6a2de4ecf9a47b3953d06ab8eccdf8cfbbcb4fb3a209b87f2ccc41f71c6688`.
The full Command Center 0.3.5.19 distribution was also inspected, including the
parent `common.py`, `default.py` and `view_mode.py` omitted from the APK overlay.

Findings in the existing distribution:

- `common.atomic_json` uses a unique temporary file, flush, file fsync, then
  `os.replace`. Errors propagate, but the containing directory is not fsynced.
  Its helper protects temporary filenames, not concurrent read-modify-write.
- `common.read_json` silently substitutes defaults on any exception. The new
  participant uses strict reads so corrupt/unreadable history cannot be replaced
  with an empty object and then declared saved.
- `service.PROGRESS_LOCK` is interpreter-local. `plugin.mutate` runs independent
  load/mutate/save logic without that lock. Both must enter the same OS gate.
- `InfinityPlayer.persist_continue(force=True)` can run after the player clock
  disappears, return without a final save, and fall back to the eight-second
  periodic snapshot. Checkpoint capture must run before stopping playback.
- `resume_hub.sync_kodi_playcount` is best-effort today. It returns failure for
  failed JSON-RPC as well as provider-only entries without a Kodi database ID.
  Integration must distinguish not-applicable from failure and require success
  for applicable Kodi library entries.
- The service's final flush currently follows `Monitor.abortRequested`, calling
  `persist_continue`, `persist`, `experience.shutdown`, and `stability.clean_stop`.
  A persistence request must be handled independently while the service lives.
- `default.py` changes add-on settings directly. `common.py` restore/snapshot/UI
  repair paths copy configuration files. These and skin settings are additional
  admission owners; this JSON participant does not attest their persistence.

## Implemented contract

`PersistenceParticipant` manages only these existing JSON files:

- `continue-watching.json`: resume, watched, watchlist, collection, ratings,
  lists and source memory.
- `playback-memory.json`: audio/subtitle/speed preferences.
- `session.json`: last eligible browsing session.
- `boot-history.json` and `boot-marker.json`: clean-stop bookkeeping.

`EngineOwner(pid, token)` identifies the live engine. `bind_engine()` establishes
existing-file proofs with checked fsync calls. An explicit compare-and-swap
previous-owner argument is required to replace an owner. The Android coordinator
must separately prove old-process death; the participant cannot prove it.
Same-owner rebind never clears a failed or fenced transaction.

`update(name, default, pure_mutator)` obtains an OS `flock` before reading and
holds it through the mutation and durable commit. Independent interpreters and
threads must each construct/use the same profile gate. `remove()` follows the
same protocol for marker removal. Unchanged content does not increment the
generation or rewrite the target. Mutators must not call Kodi, block on UI,
or re-enter this participant. Gather dialog input first, then load and apply it
inside the gate; never save an object loaded before a user dialog.

The journal records an uncommitted generation before changing the target.
Commits require file fsync, atomic rename, directory fsync and a checked journal
commit. Failed or interrupted writes remain uncommitted and prevent checkpoint
success. A file changed outside the gate is rejected. Unsupported directory
fsync, storage errors and malformed JSON fail closed.

Every journal read, write and same-owner rebind validates the complete schema:
exact required file-proof set, digest formats, owner identity, phase/session,
nonnegative integer generations (booleans rejected), pending-write consistency
and an ordered stage prefix. Completed state requires every stage and no pending
generation. A live participant also rejects a generation below one it previously
observed. This is corruption detection, not protection against coordinated
rollback of all files across a fresh process; engine identity remains native-owned.

`checkpoint(session, hooks)` establishes a write fence and executes:

1. `capture_final_playback() -> (OperationResult, snapshot)`.
2. `persist_final_playback(snapshot, checkpoint_writer) -> OperationResult`.
3. `stop_playback() -> OperationResult`.
4. `drain_required_events(checkpoint_writer) -> OperationResult`.
5. `persist_session(checkpoint_writer) -> OperationResult`.

Hooks run without holding the OS lock. Required callbacks use the session-scoped
writer; normal maintenance and user mutations are rejected once fenced. Every
hook must explicitly confirm checked success, including an explicit no-op when
there is no active playback or dirty state. Truthy strings/objects are rejected.
Failure leaves admission closed for explicit coordinator recovery.
`fail_checkpoint` poisons its live participant's session before lock acquisition
or disk I/O, so a failed FAILED-marker write cannot revive that local transaction.
Cancellation across independent interpreters must also revoke the session at the
authoritative Android/native coordinator. An unwritable file cannot reliably
communicate cancellation to another interpreter; a receipt alone is never
authority to terminate, and the coordinator must reject a revoked transaction's
receipt even if another participant still produces one.

The resulting receipt is **PARTICIPANT_COMPLETE**, carries PID/owner/session and
committed generation/proofs, and explicitly sets `global_safe_to_terminate` to
false. It does not attest native settings, SQLite, providers, skin writes,
Python services, or legacy `common.py` writers. An unintegrated or partial
participant must never enable normal process termination.

## Remaining production integration

- Route every managed-file writer, including service, plugin, source memory and
  required playback callbacks, through the shared transaction. Split hub data
  normalization from its disk write so normalization runs inside the gate.
- Enlist the already-running service; do not launch a new script whose lifetime
  or completion would be mistaken for the resident service's persistence.
- Read the final native/player clock before stop; do not convert a clock failure
  to zero. Define how already-queued ended/watched events are drained without
  duplicate watched/playcount increments or a late resume entry resurrection.
- Stop admission of recovery retries, session timers, refresh setters, restores
  and maintenance before requesting these stages. Keep necessary persistence
  owners alive. Native must account for existing provider/library writers.
- Await verified Kodi-library watched/resume updates and native database commits
  after applicable CC RPCs. Never acknowledge an arbitrary sleep or discarded
  queue as a persistence drain.
- Keep native GUI pumping/callback delivery available while asynchronous hooks
  are pending. Timeouts report failure; they never authorize thread/process kill.
- Persist skin/add-on/settings and critical configuration through their native
  owners. Coordinate all remaining participants before native can emit global
  SAFE_TO_TERMINATE. Verify actual Android storage fsync behavior on device.

## Verification

Run `python -m unittest -v test_persistence_participant.py` from this directory.
The tests cover cross-process RMW contention, precise final-position-before-stop
ordering, required watched-event persistence, stale owner/session rejection,
dirty-only updates, gate timeout, malformed JSON, ungated writes, and injected
directory-fsync failure. They validate the isolated participant only; they are
not device acceptance or full application shutdown tests.
Additional regressions cover omission of a required proof, thirty parseable
journal corruptions, generation rollback, and a concurrent failure whose durable
failure-marker write itself fails.
