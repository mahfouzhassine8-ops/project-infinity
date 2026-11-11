# Functional initialization investigation — November 11 evidence

Status: the owner's intermittent functional failure remains unattributed. Since
93d025b6, native instrumentation is implemented in be06e127 and a separately
reproduced CPython NULL-return cleanup deadlock is corrected in 679807f7.
Authenticated Actions artifact access is resolved. Exact results and limits are
in `INSTRUMENTATION.md`, `CPYTHON-INITIALIZATION-RESULTS.json` and
`SIGNED82-VERIFICATION.json`. No new owner-device capture or test is requested.

## What the supplied files establish

Both files explicitly identify themselves as FILTERED logcat extracts, not complete bugreports. Their original `dumpstate.txt` members were 334,781,714 and 278,438,392 bytes. The supplied files are 37,980 and 855,308 bytes. Headers explicitly omit non-logcat sections. Their SHA-256 values, counts, safe event timestamps and original line references are in `EXISTING-EVIDENCE-RESULTS.json`. Raw reports remain outside Git.

The earlier extract contains 229 distinct Core load attempts and 229 namespace-denied failures; the later contains four more. Counting uses direct service messages keyed by timestamp/process/thread; split linker/debug echoes are not extra attempts. The earlier median interval is about 1.015 seconds, with substantial gaps, so this is not an uninterrupted retry-rate measurement. Each displayed failure says the Android loader namespace cannot access the staged library. It does not prove native Core execution or a permanent shared Python lock.

The same engine process and worker thread appear across the attempts in both reports. Command Center also executed widget policy changes at 05:02:54.327 and 05:02:55.378. Thus the observations do not support a claim that all Python execution, or the Command Center resident loop, was continuously stopped throughout the selected interval.

At 05:28:53.707 Android ActivityManager ordered the engine killed for excessive background CPU: 10,040 ms over a 300,072 ms accounting interval, reported limit 2 and adjustment 920. Input-channel removal at 05:28:53.911 and window cleanup through `binderDied` at 05:28:53.925 corroborate termination aftermath. This is an OS termination, not a captured ANR, a native crash, or verified Essential-First completion. The excerpts do not attribute that CPU to Core or prove that this later kill caused an earlier UI failure. Android freeze/unfreeze records must be considered when interpreting elapsed gaps.

No identifiable failed Health Center invocation, relevant invocation return code or interpreter-initialization progression is present in the supplied selection. Neither a fresh engine launch nor the successful-after-reopen comparison is established by it. `22031.mp4` remains unavailable here. The weather header is not used as job-state evidence. Absence from a filtered extract cannot establish absence from the original report.

The owner subsequently examined the complete original dumpstate and supplied its lines 812047–812050: at 05:10:12.835467836-0500 Android explicitly skipped the live Kodi PID 26041 backtrace because the process was cached. This replaces the earlier assumption that the live backtrace might merely have been filtered out. There is no captured current stack to recover from that section, and historical stacks must not substitute. `OWNER-ORIGINAL-EXCERPTS.json` distinguishes these owner-supplied references from independently read attachments.

## Shared execution paths and competing explanations

1. `CScriptInvocationManager::GetLanguageInvokerForAdmission()` and both `ExecuteAsync()` overloads (approximately 832–913) enforce the shutdown/startup-admission flags. `BeginCheckpointStartupAdmission()`/`BeginShutdown()` set those flags; the reviewed implementation does not reopen them in the same manager instance. A retained failed Close can therefore refuse new scripts. `AddonBuiltins.cpp::RunScript()` ignores the negative invocation result and returns zero, which can produce no visible Python dialog while native UI works. This is a confirmed mechanism, but these extracts do not show the relevant checkpoint transition. Existing service execution does not by itself prove new invocation admission is open.
2. Admitted work goes through `XBPython::OnScriptInitialized()` (about 498), its initialization lock, `CPythonInvoker::execute()` main-thread state/GIL/subinterpreter setup (about 263–329), Kodi module initialization and `InfinityPythonPersistence::Start()` (about 1036) before add-on bytecode. Existing services can progress while a different newly admitted invocation waits on an initialization/import/resource boundary. The precise waiting stage is unknown. Continuous service logging is counterevidence to a continuous process-wide GIL deadlock during those observations.
3. The Core staging/load/retry loop is a demonstrated separate malfunction and a possible resource contributor. There is no thread CPU or wait-chain evidence tying it to failed Health Center or provider execution. Installing its prototype or exempting it from native safety is not justified as this startup repair.

Native skin/input/rendering and Python invocations are separate execution paths. `CScriptRunner::WaitOnScriptResult()` also retains the GUI/busy-dialog event route while awaiting results. Consequently a responsive skin cannot certify add-on readiness. A new process would clear manager flags, interpreter state and process-local resources; the supplied same-process observations do not identify which state a successful restart actually corrected.

The chooser's Java `Splash.showInfinityHealthCenter()` differs from the Python Health Center add-on. The unavailable video and missing invocation trace prevent treating these as the same failing path.

## New selected host result: bookkeeping versus refusal

`test_failure_admission.py` compiled retained production manager/admission methods, the `RunScript` built-in and real persistence headers. Four input files were checked against the BASE77 native source map. Existing lifetime-fixture peers substitute add-on lookup, filesystem access, classification, invoker allocation/thread launch and logging. No CPython, Android loader, actual provider or GUI ran.

Three separate processes completed within the five-second per-case deadline:

- Four synthetic opaque-writer diagnostic rows repeated 233 times remained four aggregated rows. With admission open, an independent Program-script request was admitted. Its own writer had no inherited failure. The original failure remained recorded and durability remained unproved.
- Closing startup admission refused the independent dispatch, without stopping the existing owner. The actual `RunScript` built-in still returned zero.
- Hard-shutdown admission likewise refused dispatch while the actual built-in returned zero.

All selected assertions passed. This is a **native host admission result**, not a functional startup PASS. The synthetic records all use the same opaque-writer classification; they do not reproduce original metadata-event classification, actual audit hooks, library loading, CPU load or interpreter execution. The result excludes these ledger records alone as a sufficient explanation under the tested conditions. It does not exclude loader resource effects, an admitted initialization wait, or actual retained checkpoint refusal on the Fold. It confirms that a zero built-in result is not proof that a script started.

Results: `HOST-FAILURE-ADMISSION-RESULTS.json`; preselected scope: `SELECTED-HOST-CHECK.md`. The generated C++ source hash is explicitly labeled as source, not binary. Existing Android and shutdown results were not rerun.

## Separate Resume Hub warning: safe legacy exclusion

The owner reports original dumpstate line 206221, 05:02:53.507: `Unexpected Command Center parent 0.3.5.78; Resume Hub overlay skipped`.

The legacy `InfinityResumeHubInstaller.applyChecked()` supports only CC 0.3.5.17 / 0.3.5.19. Version 0.3.5.78 correctly reaches its warning-and-return branch. That branch does not open the old controller payload or overlay its eight files. The actual retained DEX closes its `InfinityJavaWriteBarrier.Scope` before returning. `Main.onResume()` then continues to the power-route and weather code; the return does not exit native/Python initialization. This is not evidence of an incorrect installed CC version or a shared execution failure. Widening the guard could overwrite modern CC files with the old 0.3.5.19 overlay and is rejected.

Signed80 member bindings inspected by the preservation reviewer:

- `classes3.dex`: `5634f2376e5d0bf6176ebef6fa1ac16bb22fdecc1d018ac078f266bb757fe9b8`.
- `assets/infinity/resume-hub-controller.zip`: `cb6a2de4ecf9a47b3953d06ab8eccdf8cfbbcb4fb3a209b87f2ccc41f71c6688`.

Historical source: `repairs/resume-hub-2103292/InfinityResumeHubInstaller.java.in`, version constants 34–35 and exclusion 75–78. The retained disassembly, not the native-tree Java template, establishes the added write-barrier close and actual `Main.onResume()` call sequence. Authenticated Actions43034295742 now independently verifies signed82 preserves these signed80 members byte-for-byte. The warning indicates Java reached its nonpending-exit branch at that instant, not that native invocation admission was open.

## Additional source finding, not attributed to this incident

`CPythonInvoker.cpp` acquires the GIL before `Py_NewInterpreter()`, then reacquires it in the NULL-return cleanup branch. The pinned dependency is CPython 3.11.7. Its early interpreter/thread-state allocation failures return NULL while retaining the original thread state/GIL; `PyEval_RestoreThread()` unconditionally takes the GIL. This branch can therefore deadlock on reacquisition. Later interpreter-initialization failures have different fatal behavior and must not be conflated with this narrow NULL contract.

Reviewed upstream blobs: `Python/pylifecycle.c` 9248e971d9c78fa10daf68652d558701184623b9; `Python/ceval.c` bb6bb35030d2128598794fed02a374a5615c92f9; `Python/pystate.c` db2ce878af64ec3321850d0e5b4666368e945689, tag v3.11.7.

The controlled pinned3.11.7 execution in run43036765104's host job now proves
this failure path. A host-only native audit hook denies the real interpreter
creation API, verifies its actual NULL result, retained current state and error,
then executes the original cleanup. That child self-deadlocks at the second GIL
acquisition. It is recorded as `EXPECTED_BASELINE_SELF_DEADLOCK`, never a
successful application start.

Corrective commit679807f7 removes only the redundant restore/acquisition and its
duplicate ownership assignment in that branch. Clear/DeleteCurrent, pointer
reset, failure return and persistence protections remain. The exact corrected
block returns safely, creates/runs/retires three real interpreters and permits
an independent Python thread to run. Both original and corrected success paths
also pass. Injection is absent from the Android payload. Both reviewers checked
the pinned contract and preservation.

No matching NULL failure or stack exists in the Fold evidence. This repairs a
proven failure path, not a proven cause of that incident. Continued Core Python
logs contradict a continuous GIL deadlock throughout their observed interval.

## 2103482 provenance and preservation

Protected baseline remains 2103477; currently tested QA input is 2103482. Seven inspected manager/Python/runner sources match the retained BASE77 source map (`RETAINED-SOURCE-CHECK.json`). Existing signed80 used the same engine. The 82 build/assembly records require 9,410 of 9,411 native files unchanged, with only `InfinityAndroidCheckpoint.cpp::Pump()` stage-6 receipt ordering changed to source hash `2273becee60a25e81b2c5844f052fe32eaa8d03335311672cd67b66bc3738648`.

- ARM64 native run 42959455792, source 5e26af40222bc521638bd184a2bfb0d5dce337f1: existing SUCCESS; recorded engine SHA-256 `503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437`.
- Original-owner preparation run 42970204230, source a7a5ca31a8353c6f6d42b9cc521146f811f5c8c9: existing SUCCESS. Exact allowed member changes are native engine, Android versionCode and experience version label. Python/provider payloads and DEX are preserved.
- Original-key signing run 42979187229, source 4ed6e8a8bdc19f7bca50429e5bbb286f70eaf143: existing SUCCESS; artifact 13836509327. Certificate pinned by that route: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Core-loader prototype host run 42934459571: existing SUCCESS, but the prototype is explicitly excluded from the 82 APK. Its host PASS is not startup acceptance.

The former local Azure CONNECT403 is no longer an artifact-access blocker:
authenticated Actions43034295742 downloaded artifact13836509327 and verified
its APK original certificate, v1/v2/v3, package/version, native hash and exact
signed80 member preservation. APK82 SHA-256:
`78b2a5dd878ea847f425f8bbf5b9c71e810d19e134fe4480588db55a7ea52a32`.
Exactly7,758 payload members are unchanged; only engine, versionCode and
experience label differ. This is evidence reuse, not a new issuance. The live
registry's candidate82/last-issued81 discrepancy remains to reconcile before
any successor; no version is reserved.

## Remaining evidence and release gates

The precise causal gap is a failed invocation matched to its native admission result or initialization stage and checkpoint generation. The original report explicitly skipped the current live backtrace. The supplied evidence does not contain the matching native receipt; another symptom screenshot or repetition of the same phone test would not resolve that gap.

The existing native ledger records invoker/thread/interpreter identities and
initialization progress. The new bounded native recorder adds explicit refusal
reasons, lifecycle flags, manager lock waits, runtime readiness, GIL waits,
interpreter/module/observer/bytecode boundaries, and the actual RunScript
admission result. RunScript's public return remains zero for compatibility.
The host checks demonstrate both admitted execution and refusal despite that
zero result. No admission policy or essential-save gate is relaxed.

Native instrumentation is internal QA only, compile-time off by default and
runtime gated to the exact Infinity engine process. It excludes script paths,
arguments, credentials and exception text. Buffers, capture duration and drain
work are bounded. The existing native source tree remains untouched; overlays
are applied only to a source-bound Actions build.

ARM run43036765104 passed source preparation, but both attempts stopped before
compilation because Ubuntu mirror DNS failed on the runner. Run43040415571 reused
the successful exact-source host proof and tried Ubuntu's official HTTPS
repositories with normal signature verification. Those hosts also failed DNS
resolution. ARM compilation/linkage are NOT_RUN, not a native compile failure
or PASS. ENGINEERING-STATUS.json retains exact errors and run bindings.

Manual feature run43039363818 selected unchanged signed82 startup, actual local
Python invocations, a nonce-bound real exception, another independent invocation,
and unchanged Health Center execution. It requires an absent-to-visible11188
transition and the source-bound1188101 control, actual installed source hashes,
and exact process/start/nonce identity. No RPC acknowledgement or stale window
can substitute for execution. Scope and helper bindings are committed in
`ANDROID-STARTUP-SELECTION.json`; reviewer corrections were verified before
dispatch. During emulator setup its libpulse0 acquisition hit the same package
mirror DNS failure. It was cancelled before application execution when source
inspection caught that HC publishes khc_contracts.VERSION2.5.26 despite
addon.xml2.5.27. Commitf2dc77b3 corrects the probe and verifies both installed
source hashes. The prepared case has not run; it is not a Fold reproduction.
No further identical attempt is launched against the confirmed runner blocker.

The new source touches four native call-site files and one diagnostic header;
the only intended runtime behavior correction is the two-line NULL cleanup.
Cobra, DEX, skin, Search/providers, Trakt/tracking/resume, settings/data,
networking and existing shutdown policy remain protected. No signed successor
or installer is available yet. Repeated functional Android starts, instrumented
Android execution, clean shutdown/relaunch and final Fold acceptance remain
unverified. The Core prototype and legacy overlay expansion are not included.
