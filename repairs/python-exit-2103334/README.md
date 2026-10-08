# Infinity 2103334 — script exit message admission repair

Candidate only. Current Android parent is exact 2103333, commit bbfbe8817cd65056dbbacf592dcb3e0de4c209ef, run 37720581322. Its native parent is exact 2103330 source/run 16cb5ccebb2b85107132ca0a04a5e639208476e0 / 37709784725. Retain the user's 2103327 rollback and skin.infinity.diggz 1.0.5.201 artifact. No new lock, UI/skin work, provider edit, reset, timeout shortening or hidden process kill.

## Observed limit of the phone evidence

The latest 2103333 export gets past directory cancellation and reaches scripts.join_remaining on invoker 0. That owner has no matching execution_done or native completion in the capture. Another invoker completes interpreter cleanup later. Historical ANRs and an earlier owner's receipt do not identify the latest inner call. The export establishes the remaining join wait, not which Python statement/native backend owns it.

## Tested and rejected hypothesis

An initial experiment compared the inherited direct async_exc write with PyThreadState_SetAsyncExc. The former blocked in a local CPython 3.13 experiment but completed on matching CPython 3.11.7. Run 37723294704 correctly failed the initial assumption. Therefore the API-based abort helper is retained ONLY as an investigation fixture and is NOT installed in native source. The existing Python abort semantics, cooperative grace, interpreter finalizers, module/GC teardown and final joins stay unchanged.

## Actual behavior repair

CApplicationMessenger::SendMsg checked the stop flag before acquiring the queue lock. Stop+Cleanup could run between that check and enqueue. A late synchronous sender could then wait on an already drained queue with no future consumer. The repair uses an atomic stop flag on Android and repeats the existing stop check under the queue lock, serialized with Cleanup. Requests accepted before the drain retain existing signaling; late requests return the existing -1 rejection result rather than entering a dead queue. No callbacks are fabricated or executed after shutdown to fake success. Normal dispatch and both queue cleanup functions are unchanged.

The deterministic test executes the exact original and transformed SendMsg/Cleanup/dispatch bodies with real producer/drain threads. A move-constructor barrier arranges the race without adding a hook to production. The parent reproduces the stranded waiter; a test-only second cleanup rescues it. The repaired path returns without that rescue. Tests cover regular/window queues, synchronous/asynchronous requests, admitted-before-stop requests, normal dispatch/results and already-stopped calls. GUI dependencies are stubs, not a running Kodi renderer. This proves the code race and correction, not that it was the only cause of invoker 0 on the Fold.

## Targeted evidence

At the existing abort helper's already-acquired GIL, capture at most eight target thread states and four frames each. Record only add-on ID, numeric thread identity, filename basename, function name and line number in bounded existing trace fields. No source lines, locals, arguments, URLs, secrets or full paths. Preserve pending Python exceptions and references. Record bytecode return, child-thread waits and the previously uninstrumented std::thread::join fallback. Nothing is marked complete merely because a stop was requested.

The four-mode real CPython test, repeated three times on exact 3.11.7, validates capture on active subinterpreters and child threads, exception preservation, interpreter isolation, finally-block writes and real joins/Py_EndInterpreter/Py_FinalizeEx. These are test scripts, not proof that every third-party add-on saves correctly.

## Preservation and acceptance

Native changes are limited to ApplicationMessenger.cpp/.h, read-only additions in PythonInvoker.cpp, a new evidence header, a diagnostic scope in Thread.cpp and the trace tag/budget classification. All other complete source-map entries, including the 3330 directory fix, are protected. Android changes are restricted to diagnostic engine identities and installable version 2103334, paired to the exact successful new native artifact. All skin/assets/resources, chooser, Cobra, notification behavior, owner leases, normal close dispatch and signing identity must remain unchanged from 3333.

A native rebuild is required. Host tests are a prerequisite, not device acceptance. Test on the Fold with settled startup and active provider widgets, then after playback. Review clean native completion for the actual PID, prompt reopening and retained settings/resume state. If the join still blocks, the new frame/child/fallback evidence must identify the next target; do not certify it fixed, force-kill automatically or lock on CI alone.
