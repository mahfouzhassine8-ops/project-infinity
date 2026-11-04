**Checkpoint-aware Pause/Stop ANR — isolated source candidate, 2026-11-04**

The reproduced checkpoint queue deadlock has a one-file source correction candidate. Three before-case witnesses reproduce the wait; all 15 selected after-candidate host checks pass. This is not an Android or physical Fold acceptance result. No native engine, APK, signing, release, promotion or lock was performed.

Development branch: `work/infinity-kodi-checkpoint-pause-stop-source-20261104`, based directly on `cdbaa5abc86675094229171746a8c627a7f367e8`. The settings-owner retirement decision remains **BLOCKED**. No retirement implementation, prototype, tests, mutation tracking or owner references were changed. Scudo exhaustion, Continue Playing completion and Home loading remain independent unresolved scopes.

**Confirmed mechanism and exact correction**

The preserved native source already routes an active checkpoint through `CApplication::Process` → `ProcessCheckpointDisplayMessages` → checkpoint `Pump`, then returns. The selective message pump admits display setup/destruction but leaves `TMSG_GUI_ACTION` queued. `Pump` returns in `CHECKPOINT_FAILED`, and the checkpoint active flag does not reset in this process. Android's synchronous Pause/Stop/focus callbacks can therefore remain waiting for a message that never reaches its receiver.

The existing receiver already provides the required safe refusal: `CGUIWindowManager::OnApplicationMessage` sends an application-targeted action to `CApplication::OnAction`; its first Android guard returns immediately while a checkpoint is active, before any player or write work. The original receiver then deletes the action. Acknowledging that completed refusal releases the waiting caller without executing a playback command or claiming any write was saved.

The source overlay changes only `xbmc/messaging/ApplicationMessenger.cpp`:

1. Include the existing action/window declarations inside `TARGET_ANDROID`.
2. Add `IsCheckpointPlaybackControl`. Admit only `TMSG_GUI_ACTION`, application target `WINDOW_INVALID`, `param2 == -1`, `param3 == 0`, a non-null action, and empty string/vector parameters. The only action IDs are `ACTION_PAUSE`, `ACTION_STOP`, and `ACTION_PLAYER_PLAY`. Play is necessary for the unchanged synchronous request in Android `onResume`; leaving it queued would move the same failure to foreground return.
3. Extend the existing selective queue predicate with this exact allowlist. Keep the current queue lock, process-thread check, initial-population bound, real receiver call, payload lifetime, and wait-event acknowledgement order.

`SendMsg`, normal dispatch, native Android callbacks, `OnAction`, GUI receiver, display handlers and the checkpoint coordinator are unchanged. No synchronization primitive or timeout changes are needed: the missing admission is corrected, and existing synchronization is retained. The historical selective-pump method name is retained to avoid unrelated call-site/header edits.

Exact patch: [CANDIDATE.patch](CANDIDATE.patch). Full candidate file: [ApplicationMessenger.cpp](candidate/xbmc/messaging/ApplicationMessenger.cpp). Preimage SHA-256: `c565bf9dad1f5dcbdca3d81a6d3dc5a42c4d8fd8151dac2f20766caaeb4ef0c8`; candidate SHA-256: `f53c09ca57fe3b4e8e575b4f51e2f3108dc77836b35c4498dbb859f61c866f8b`.

**Safety argument and limits**

During a checkpoint these controls remain refused; the candidate does not force Pause, Stop or Play through the playback freeze. Sender acknowledgement means the message receiver completed, not that playback changed or a database write became durable. The original `SendMsg` result remains `-1` on this GUI-action path, identical to the existing same-thread refusal path.

The predicate reads only the action ID and message envelope while the queue is locked. It cannot create work, write settings, resolve an owner, change a receipt, unseal admission or authorize termination. The queue lock is released before the receiver runs. The sender's event is set only after the unchanged receiver and action destructor return. The application checkpoint guard precedes all player work and the checkpoint's active flag has no reset assignment in the bound native source. This prevents a control admitted for refusal from crossing into ordinary playback execution during a failed checkpoint.

Window-targeted actions, other action IDs, nonstandard envelope parameters, ordinary callbacks, GUI messages, `TMSG_SHUTDOWN`, and `TMSG_QUIT` remain queued. Retained messages keep their relative FIFO order. The separate window-message queue is untouched. The current display handler is still invoked and acknowledged after completion; there is no early acknowledgement of surface destruction.

The source contains no new persistence or teardown path. Pending/unknown owners, generations, dirty flags, failed obligations, write counts and termination authorization are unchanged by the admitted control refusals. The actual native write-guard bodies still deny commands throughout an active checkpoint and deny ordinary writes after failure, even with a stale persistence permission scope. Authorized coordinator-owned persistence in `PERSISTING` remains admitted and tracked; it is not falsely marked complete.

This argument establishes safety of the narrow queue admission under the existing checkpoint contract. It does **not** prove that native EGL destruction, a codec destructor, a worker callback, Android activity destruction or the full checkpoint coordinator cannot independently block. The application process thread and real receiver must still run. The existing stopped-messenger contract continues to rely on ordinary `Cleanup` to release queued senders; the candidate neither invokes Cleanup prematurely nor grants shutdown permission. There is no global no-ANR guarantee and no claim that the historical Scudo crash is repaired.

**Focused evidence**

Tests were selected before execution in [SELECTED-TESTS.json](SELECTED-TESTS.json). Evidence and exact source-body hashes are in [HOST-RESULTS.json](evidence/HOST-RESULTS.json), with [console output](evidence/TEST-OUTPUT.txt). Before/after C++ harness sources are retained. These are host executables only, not compiled Kodi engines.

| Selected observation | Result |
| --- | --- |
| Pause, Stop and resume-time Play before patch | All three remain waiting after four checkpoint frames; receiver calls remain zero. Baseline defect reproduced. |
| Same three controls after patch | Each completes through the existing refusal; zero player commands. |
| Actual native audio-focus callback, pauseable and cannot-pause branches | Both complete, dispatching the original Pause/Stop IDs. |
| Actual native onPause → onStop → onResume bodies | Complete; ordinary asynchronous RESUMEAPP remains queued. |
| 48 concurrent/repeated native callback interruptions | All complete; zero player commands; no remaining synthetic action/message ownership. |
| Acknowledgement during receiver payload destruction | Sender remains blocked until the receiver/destructor finishes. |
| Display acknowledgement and ordering | Completion follows the display-handler peer; setup/destroy order preserved alongside controls. |
| Unrelated-message and envelope negative controls | None dispatched; FIFO and window queue preserved. |
| Wrong-thread pump attempt | Does not dispatch; process-thread pump then completes the control. |
| Non-checkpoint normal dispatch | Normal queued and same-thread routes remain intact. Actual player behavior is a peer. |
| Reentrant display event | Existing bounded pass yields to the next frame; no new unbounded drain. |
| Checkpoint activation after enqueue | Control is refused safely when processed after activation. |
| QUIESCE, PERSISTING, CHECKPOINT_FAILED and SAFE_TO_TERMINATE; sealed/unsealed variants | Control refusal preserves host owner ledger and shutdown flags; exact write guards retain their admission rules. |
| Stopped messenger | Selective pump does not override Stop; existing Cleanup releases the waiter without dispatch. |

The three before tests deliberately assert the defective waiting condition; their successful exit means reproduction succeeded, not that the baseline behavior passed. Their synthetic waiters are rescued only after the defect assertions. Native Cleanup does not delete a queued CAction payload; the harness explicitly disposes of its own synthetic payloads for baseline/negative cases before Cleanup. That is test cleanup, not a production fix or a hidden candidate completion path.

The first harness compile failed before any test ran because of a missing helper brace and an unused peer parameter under `-Werror`. Only those harness defects were corrected. The original compile error is preserved in [INITIAL-HARNESS-COMPILE-ERROR.txt](evidence/INITIAL-HARNESS-COMPILE-ERROR.txt). No unchanged failed application test was repeated. The previously passing watched/display, memory measurement and retirement evidence was retained rather than rerun.

The harness executes exact extracted sender/queue/dispatcher bodies, the GUI_ACTION receiver case, application checkpoint prefixes, selected Android callback bodies and native write-admission bodies. ThreadMessage/event/critical-section storage, graphics lock, Android services, actual player/EGL work and checkpoint Pump are explicit host peers. Consequently these tests prove the selected source interactions, not real decoding, native display teardown, disk persistence or physical Fold responsiveness. Millisecond host process timings in the machine report are not device performance measurements.

**Preservation**

[PRESERVATION.json](PRESERVATION.json) verifies all 9,411 mapped files in the restored native tree remain identical to the retained 452 source map. The staged overlay consists of one file only. Existing source work for the watched-job and display-lifecycle repairs is retained; 452 remains unapproved, and 451 remains the protected recovery baseline.

The prior 452-versus-451 native differences are still exactly the existing five paths: `Application.cpp`, `ApplicationMessenger.cpp`, `ApplicationMessenger.h`, `VideoLibraryMarkWatchedJob.cpp`, and `.h`. This task adds only the selective-message correction to an isolated copy of `ApplicationMessenger.cpp`; it does not reapprove those historical changes or overwrite the signed baseline.

Signed 451 APK remains `d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399`. Signed testing 452 APK remains `efc24cc53e25675360bb70a2c8c0122cfc107f99035d04c957265d08206f6729`. Whole-file equality also preserves their Preview, Cobra and unrelated members. No new APK exists, so a successor APK-member comparison is **not performed**, not reported as passed.

The main repository's preexisting status is unchanged. Checkpoints `7ea3f0b9`, `8c54e2cf` and `cdbaa5ab` remain clean and unchanged. No settings owner, add-on, provider, layout, database, profile, watched history, Resume Hub, signer, release workflow or recovery lock was modified. No application/user data was accessed or cleared by these tests.

**Required next verification, before any release**

1. Separately authorized native integration must verify the exact parent source/map, this one-file overlay, real headers and original ARM64 toolchain. Reuse existing watched/display results only with source binding. Stop on any unexpected native delta. No full native build was done under this source-only task.
2. On an authorized ARM64 Android test device, capture the actual path from lifecycle/focus callback through enqueue, checkpoint guard refusal, receiver completion and sender wake-up. Exercise Pause, Stop and foreground Play during a failed checkpoint and repeated interruptions. Prove no new player commands or writes occur through the admission exception.
3. Verify actual surface create/destroy with failure still latched, screen-off/on, background/foreground and simultaneous focus interruptions. Confirm real EGL/codec completion precedes acknowledgement and no UI/event-loop ANR occurs. The host display peer cannot establish this.
4. In a disposable controlled test profile, retain pending/failed/unknown persistence obligations. Verify a failed checkpoint remains failed and cannot authorize termination; separately verify ordinary successful shutdown/restart with durable watched/settings data. Do not inject failure into the user's real databases, force-kill, clear data or fabricate a receipt.
5. On the physical Fold, check cover/inner displays, fold/unfold and rotation during those lifecycle cases, plus ordinary Pause/Stop/resume with no checkpoint. Record exact APK/native identity, private thread traces and checkpoint state if a wait occurs. Preview and Cobra remain preservation controls, not modification targets.
6. Only after separate APK authorization, compare actual package members, preserve the original signer and user data, and deliver an install-over candidate. No current claim of Android or Fold acceptance, signing readiness, or automatic lock is made.

The source-level decision is to retain this minimal candidate for native/Android verification. Settings retirement stays blocked. Any independently blocking native receiver or teardown path discovered during that verification must be reported with evidence rather than bypassed.
