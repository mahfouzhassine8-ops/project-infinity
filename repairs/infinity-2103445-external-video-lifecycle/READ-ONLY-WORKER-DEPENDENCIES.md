# Read-only dependency continuation — four occupied workers and playback drain

This continues e4eb93c9. The request-order correction and nine passing tests remain unchanged and were not rerun. No application/native/shared/Cobra/chooser/shutdown code or signing infrastructure was changed. No successor was built or signed.

## Evidence provenance and version limit

The user supplied independently verified ANR observations: PID7723 Android main waits in SendMsg→XBMC_DestroyDisplay→surfaceDestroyed (lines27–48); Kodi thread7779 is in CVideoPlayer destructor+192→ClosePlayer→StopPlaying (lines509–524). The actual ANR is SCREEN_OFF broadcast timeout10s. Additional source-tagged private review reports four occupied CJobWorkers, Python import-lock waiters and an announcement event wait. These are attributed supplied observations; this executor has not materialized or read the original archive bytes.

The export's currently installed445 does not identify historical exit producers: `producer_apk_version:null` and truncated histories remain decisive limits. A shared install-directory token or a preservation-parent SHA is not producer binding. Neither the old ANR nor tombstone is automatically assigned to445. The signed445 ELF is used below only as an independently inspectable reference.

## Independently verified admission rule

The signed445 library SHA256 remains `151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e`. ELF symbol/ARM64 instruction inspection resolves GetMaxWorkers at0x1981b1c to:

    add  w8, w0, #2
    cmp  w0, #4
    mov  w9, #10000
    csel w0, w9, w8, eq
    ret

The available Job.h priority enum is LOW_PAUSABLE0, LOW1, NORMAL2, HIGH3, DEDICATED4. Thus the reference limits are **NORMAL4, HIGH5, DEDICATED10000**. This is not an unconditional four-thread pool. Both StartWorkers and PopJob compare the **global active processing count**, not merely the count of jobs with the requested priority, against that priority's limit.

The available VideoPlayer constructor sets its outbound queue to FIFO, one callback at once, **NORMAL** priority. CJobQueue immediately places an accepted global job ID in its local processing list; that job can still be waiting for a shared worker. Therefore `m_outboundEvents->IsProcessing()` does not prove a playback callback is currently executing. It can also describe locally pending or globally submitted but not-yet-started work.

## What the reported worker snapshot supports

The private reader reports these four captured workers:

| Worker TID | ANR lines | Reported operation |
|---|---|---|
|7901|728–745|CWeatherJob::DoWork+380, sleeping|
|7956|749–781|CDirectoryJob→plugin directory→WaitOnScriptResult|
|8124|3494–3523|CDirectoryJob→plugin directory→WaitOnScriptResult|
|12318|4221–4250|CDirectoryJob→plugin directory→WaitOnScriptResult|

None is reported executing a playback/bookmark/settings callback. The supplied PCs map exactly into the corresponding signed445 reference symbols: Weather+380, Directory+276, ScriptRunner+188 and JobWorker+244. That is **symbol/offset compatibility**, not cryptographic historical-version binding.

**Conditional conclusion:** if these four jobs occupied the same manager's active processing set while a NORMAL playback callback was queued, the admission rule would prevent that callback from starting until a slot became available. Kodi's application thread could then wait for its playback queue to drain, preventing display-destruction message handling and leaving Android main waiting. This supports **shared-worker starvation as a concrete lead**, not a proven root cause or a demonstrated deadlock. It does not require assuming the running directory jobs' priorities; the rule uses the total active count. It does require evidence that the playback work was queued and the reported jobs occupied that shared manager consistently at the relevant time.

Queue contents, IDs, actual priorities, manager identity/state and a time-consistent processing count were not present in the supplied archive review. A single multi-thread snapshot does not establish a permanent cycle or distinguish a long operation from a deadlock. The separate Directory.cpp HIGH-priority CGetJob is a different class from the captured CDirectoryJob; its priority must not be assigned to that trace by analogy.

## Queue completion and callback dependencies

Read-only source inspection establishes:

- The playback queue may contain earlier RequestVideoSettings/AV-start/AV-change/file-switch work, not just final close work. The sleeper cannot identify which callback is outstanding.
- Close-time FIFO submissions include settings persistence, file-close/bookmark persistence, then stopped/ended/error notification. A stalled earlier item can delay every later one.
- Settings persistence takes the existing save mutex and performs video-database work. File-close state also takes the stack-helper critical section and performs bookmark/play-count/cache-update work. These are dependency locations, not identified lock owners in the ANR.
- The native OnPlayBackStopped callback sends a GUI thread message; its body does not directly synchronously run the Python stopped callback. A Python stopped-handler blockage must not be inferred solely from this destructor stack.
- CJobWorker catches ordinary job-work exceptions and still enters completion handling. CJobManager releases its own lock before invoking queue completion; CJobQueue::OnJobNotify removes the completed entry and attempts the next item. The source does not justify assuming that any ordinary exception abandons a queue forever or that the manager lock is necessarily held across this callback.

The private review additionally reports28 global-import-lock waiters, e.g. TIDs7955/7950; TID7968 is in an import-initialization lock path. This is compatible with Python work failing to make progress, but neither module name nor lock owner nor a cycle is identified. A TryExecute frame is an execution wrapper, not proof that its frame owns the contested import lock. The announcement thread's CEvent wait is compatible with an idle consumer; pending announcement state was not captured. None of these waits can be promoted to a root cause without ownership evidence.

## Independent unresolved Loading and external-intent path

The separate reader reports that all textual archive entries lack MiXplorer, ACTION_VIEW, content:// and video/mp4; Loading matches only class-loading statistics. The existing export therefore cannot establish the actual external MIME/URI or UI Loading ownership. The absence of metadata is not proof that an intent or dialog never occurred. Repeating that same export or asking for nonexistent footage will not resolve these missing fields.

The Java correction remains limited to local file/content ACTION_VIEW with a supplied video MIME. Its actual MiXplorer applicability remains unverified. The overlay still needs an actual window/dialog/operation identity. Player A already playing must never be treated as completion of request B, and native Busy/Progress must not be globally dismissed. The screen-off ANR is not evidence that screen-off caused the external-video freeze, and the separate SIGSEGV remains unresolved.

## Exact evidence and permission boundary

To resolve the starvation lead, the missing evidence is the pending playback job's identity/priority and queue phase, a contemporaneous shared-manager processing snapshot, and ownership of the Python import/module lock or other dependency preventing the occupying jobs from finishing. Actual MiXplorer intent action/MIME/URI scheme/grant handling and dialog/readiness timing require a distinct focused observation; those fields are not recoverable from the supplied export. Raw diagnostic/URI data must remain private. A supported read-only native runtime/observer is required; no new diagnostic APK, permission escalation or signal-based crash test is selected here.

Changing playback priority/reserved workers, global worker admission, native callback draining, Python import locking, persistence guards or display destruction would cross the protected native/shared/durability boundary and needs separate explicit authorization **after** the causal dependency is established. Do not increase pools, cancel provider/weather work, bypass saves, remove waits, add timeouts, suppress dialogs or skip display cleanup based on this hypothesis. An Infinity-owned correction could only be considered if an actual offending Infinity-owned operation is identified within the approved scope.

Signing remains blocked. Locked2103445 and the verified source correction are retained. See [machine-readable evidence/provenance](evidence/READ-ONLY-WORKER-DEPENDENCIES.json); the new inspection script reads reference ELF bytes only and executes no native/application code.
