# Source and native mechanism findings — not a repaired Android result

## 1. Watched job: missing contract is the recorded checkpoint failure

The independently supplied receipt reports one unknown completed job with empty
owner/resource, matching the source-bound C++ reproduction. Its ordinary success
result does not retire an unclassified persistence obligation. Checking the
commit's bool alone would leave this failure unchanged.

The exact retained native member also confirms the class inherits these default
methods in its vtable at `0x5a9da98`:

| Vtable slot | Target | Symbol |
| --- | --- | --- |
| 2 | `0x1812224` | `CJob::GetCheckpointResponsibility` |
| 4 | `0x1812238` | `CJob::GetCheckpointPersistenceOwner` |
| 6 | `0x1812244` | `CJob::RequiresCheckpointCompletionReceipt` |

Those defaults are Unknown, empty owner, and false receipt requirement. The
actual admission/tracking methods plus actual class declarations and ledger
reproduce `completed_without_owner_receipt` after successful stubbed work and
destruction. No database write or data loss was simulated or asserted.

The unchecked commit result is an additional confirmed source defect in the
job's local write path. The supplied receipt does **not** show a commit failure.
A repair must provide a reviewed implementation/callback contract, checked
local operation results and persistence proof. Recursive, PVR and UPnP effects
must remain covered or explicitly unresolved; a type-name exemption or a global
essential-writes flag is insufficient.

## 2. Checkpoint failure leaves synchronous display dispatch unserviced

The failed state remains active and sealed. Coordinator Pump returns in that
state; Application Process returns before normal message dispatch. The
application-message handler independently rejects messages while active.

The engine's ARM64 call/branch inspection corroborates the same paths:

- `CApplication::Process`, base `0x1be163c`, calls IsActive at +36. TBZ at +40
  goes to normal processing at +56 when inactive. The active path calls Pump at
  +48 and branches at +52 to the return epilogue at +240 (RET at +272), skipping
  ProcessMessages at +176.
- `OnApplicationMessage`, base `0x1bdb20c`, calls IsActive at +56. TBNZ at +60
  goes to the return epilogue at +3616 (RET at +3664).
- `CApplication::Run`, base `0x1bdd47c`, has a direct BL at **+440** to
  `KODI::TIME::Sleep` (`0x161a360`), consistent with the supplied ANR's sleep
  frame. This is the normal no-render loop's sleep, not evidence of a destructor
  callback-drain wait.

Source-bound host probes reproduced both dispatch barriers under failed state,
with inactive negative controls proving dispatch is reachable normally. Android
surface destruction synchronously waits for display dispatch. Thus the current
source/engine contains a deterministic checkpoint-to-display starvation path.
The same-PID event chronology supports this mechanism, while historical producer
APK attribution and actual corrected Android execution remain unverified.

Do not clear active/sealed state to escape the failure. A narrowly isolated
correction must service required display lifecycle messages through their real
handler/acknowledgment while keeping unrelated actions and persistence admission
closed. Pumping every queued callback or merely changing the sleep/timeout is
unsafe. Fixing only the queue pump also leaves the application-message guard.

## Evidence and preservation limits

All three selected host cases reproduced baseline defects; they are not repaired
PASS results. The engine was copied read-only from an existing local 2103429
recovery APK and its SHA-256 matched the previously read 2103451 native member
exactly. That older APK is not this task's foundation or full 2103451 comparison.
No denied network transfer was bypassed and no diagnostic bytes were published.

ApplicationMessenger source has a preserved earlier late-admission-race repair.
Unmodified upstream bytes failed the expected hash check and were not accepted.
Replaying the checked-in producer for these two files reproduced their exact
native-manifest hashes. Preserve that existing repair; do not overwrite either
file with upstream originals.

Production source, Preview, Cobra, the lock and signing identity are unchanged.
Exact final source-map recovery, complete signed-451 APK access, safe operation
contracts and Android runtime evidence remain release gates.

## Staged corrections and current verification

The lifecycle staging producer changes only two checkpoint branches in
Application.cpp and adds one Android-only selective display-dispatch method in
ApplicationMessenger.cpp/.h. Seven host cases pass; existing normal-dispatch,
sender/cleanup and unrelated application methods compare unchanged.

The watched staging producer changes only VideoLibraryMarkWatchedJob.cpp/.h. It
accepts only the exact local nonrecursive/non-PVR/non-UPnP class and exact
VideoLibraryQueue callback for a native_databases receipt. It checks BEGIN
failure observations and COMMIT, reads watched/resume state through a separate
database object, includes open/close failures in the existing write observation,
and leaves final durability authorization to the existing native database fence.
No-op work receives VerifiedUnchanged only for that bounded scope. Unknown
paths and subclasses retain their obligations and original operation outcomes.

Fourteen final host cases passed with actual job/receipt code and real SQLite
3.46.1 files. These tests use controlled FileItem/profile/CVideoDatabase/queue
peers and do not claim real Kodi database, callback, final-fence or Android
execution. The original record's item route is still unknown, so coverage of
that particular historical job is not asserted. Five native source files are
staged in total; no APK, native engine build or lock has been produced.
