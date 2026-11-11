# Functional initialization investigation — November 11 evidence

Status: investigation active; the owner's intermittent functional failure is not yet reproduced or causally attributed. Production changes: none. This checkpoint consumes the two newly supplied private extracts and reuses existing source/build evidence. It does not request another device capture.

## What the supplied files establish

Both files explicitly identify themselves as FILTERED logcat extracts, not complete bugreports. Their original `dumpstate.txt` members were 334,781,714 and 278,438,392 bytes. The supplied files are 37,980 and 855,308 bytes. Headers explicitly omit non-logcat sections. Their SHA-256 values, counts, safe event timestamps and original line references are in `EXISTING-EVIDENCE-RESULTS.json`. Raw reports remain outside Git.

The earlier extract contains 229 distinct Core load attempts and 229 namespace-denied failures; the later contains four more. Counting uses direct service messages keyed by timestamp/process/thread; split linker/debug echoes are not extra attempts. The earlier median interval is about 1.015 seconds, with substantial gaps, so this is not an uninterrupted retry-rate measurement. Each displayed failure says the Android loader namespace cannot access the staged library. It does not prove native Core execution or a permanent shared Python lock.

The same engine process and worker thread appear across the attempts in both reports. Command Center also executed widget policy changes at 05:02:54.327 and 05:02:55.378. Thus the observations do not support a claim that all Python execution, or the Command Center resident loop, was continuously stopped throughout the selected interval.

At 05:28:53.707 Android ActivityManager ordered the engine killed for excessive background CPU: 10,040 ms over a 300,072 ms accounting interval, reported limit 2 and adjustment 920. Input-channel removal at 05:28:53.911 and window cleanup through `binderDied` at 05:28:53.925 corroborate termination aftermath. This is an OS termination, not a captured ANR, a native crash, or verified Essential-First completion. The excerpts do not attribute that CPU to Core or prove that this later kill caused an earlier UI failure. Android freeze/unfreeze records must be considered when interpreting elapsed gaps.

No identifiable failed Health Center invocation, relevant invocation return code, interpreter-initialization progression or native wait-owner stack is present in the supplied selection. Neither a fresh engine launch nor the successful-after-reopen comparison is established by it. `22031.mp4` remains unavailable here. The weather header is not used as job-state evidence. Absence from a filtered extract cannot establish absence from the original report.

## Shared execution paths and competing explanations

1. `CScriptInvocationManager::GetLanguageInvokerForAdmission()` and both `ExecuteAsync()` overloads (approximately 832–913) enforce the shutdown/startup-admission flags. `BeginCheckpointStartupAdmission()`/`BeginShutdown()` set those flags; the reviewed implementation does not reopen them in the same manager instance. A retained failed Close can therefore refuse new scripts. `AddonBuiltins.cpp::RunScript()` ignores the negative invocation result and returns zero, which can produce no visible Python dialog while native UI works. This is a confirmed mechanism, but these extracts do not show the relevant checkpoint transition. Existing service execution does not by itself prove new invocation admission is open.
2. Admitted work goes through `XBPython::OnScriptInitialized()` (about 498), its initialization lock, `CPythonInvoker::execute()` main-thread state/GIL/subinterpreter setup (about 263–329), Kodi module initialization and `InfinityPythonPersistence::Start()` (about 1036) before add-on bytecode. Existing services can progress while a different newly admitted invocation waits on an initialization/import/resource boundary. The precise waiting stage is unknown. Continuous service logging is counterevidence to a continuous process-wide GIL deadlock during those observations.
3. The Core staging/load/retry loop is a demonstrated separate malfunction and a possible resource contributor. There is no thread CPU or wait-chain evidence tying it to failed Health Center or provider execution. Installing its prototype or exempting it from native safety is not justified as this startup repair.

Native skin/input/rendering and Python invocations are separate execution paths. `CScriptRunner::WaitOnScriptResult()` also retains the GUI/busy-dialog event route while awaiting results. Consequently a responsive skin cannot certify add-on readiness. A new process would clear manager flags, interpreter state and process-local resources; the supplied same-process observations do not identify which state a successful restart actually corrected.

The chooser's Java `Splash.showInfinityHealthCenter()` differs from the Python Health Center add-on. The unavailable video and missing invocation trace prevent treating these as the same failing path.

## Additional source finding, not attributed to this incident

`CPythonInvoker.cpp` acquires the GIL before `Py_NewInterpreter()`, then reacquires it in the NULL-return cleanup branch. The pinned dependency is CPython 3.11.7. Its early interpreter/thread-state allocation failures return NULL while retaining the original thread state/GIL; `PyEval_RestoreThread()` unconditionally takes the GIL. This branch can therefore deadlock on reacquisition. Later interpreter-initialization failures have different fatal behavior and must not be conflated with this narrow NULL contract.

Reviewed upstream blobs: `Python/pylifecycle.c` 9248e971d9c78fa10daf68652d558701184623b9; `Python/ceval.c` bb6bb35030d2128598794fed02a374a5615c92f9; `Python/pystate.c` db2ce878af64ec3321850d0e5b4666368e945689, tag v3.11.7. No allocation/NULL-branch observation or matching blocked stack is supplied. No production cleanup change is made on that hypothesis. A host injection would prove only the failure-path contract, not the Fold cause; no such test was run here.

## 2103482 provenance and preservation

Protected baseline remains 2103477; currently tested QA input is 2103482. Seven inspected manager/Python/runner sources match the retained BASE77 source map (`RETAINED-SOURCE-CHECK.json`). Existing signed80 used the same engine. The 82 build/assembly records require 9,410 of 9,411 native files unchanged, with only `InfinityAndroidCheckpoint.cpp::Pump()` stage-6 receipt ordering changed to source hash `2273becee60a25e81b2c5844f052fe32eaa8d03335311672cd67b66bc3738648`.

- ARM64 native run 42959455792, source 5e26af40222bc521638bd184a2bfb0d5dce337f1: existing SUCCESS; recorded engine SHA-256 `503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437`.
- Original-owner preparation run 42970204230, source a7a5ca31a8353c6f6d42b9cc521146f811f5c8c9: existing SUCCESS. Exact allowed member changes are native engine, Android versionCode and experience version label. Python/provider payloads and DEX are preserved.
- Original-key signing run 42979187229, source 4ed6e8a8bdc19f7bca50429e5bbb286f70eaf143: existing SUCCESS; artifact 13836509327. Certificate pinned by that route: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Core-loader prototype host run 42934459571: existing SUCCESS, but the prototype is explicitly excluded from the 82 APK. Its host PASS is not startup acceptance.

These are source/build/signing records, not a new independent byte verification of the signed82 artifact. The artifact's authorized redirect was obtained, but this executor's proxy denied the Azure download CONNECT with HTTP 403. No proxy bypass was attempted. The live registry at signing source still lists candidate82 / last-issued81 and accepted-pointer unchanged; future issuance must reconcile actual signing history rather than reuse82. No registry change is made here.

## Remaining evidence and release gates

The next discriminating evidence is the **existing original report's** engine-thread/CPU/wait-state sections and the timestamped failed invocation: admission rejection versus an admitted invoker's initialization stage. Those sections were omitted by the supplied filter. The original archives or their unfiltered `dumpstate.txt` are the required existing source; a new phone diagnostic or speculative APK is not needed for this step. If the original report never captured the relevant native stack, report that limit rather than invent one.

No new host/application tests, ARM64 build, Android cycles, signing, registry reservation or APK release occurred in this investigation. Actual repeated functional launch, local-offline Health Center/add-on execution, independent clean shutdown/relaunch, recovery and physical Fold acceptance remain pending a demonstrated repair. All production code, Cobra, skin, Search/providers, Trakt/tracking/resume, settings/data and networking remain unchanged.
