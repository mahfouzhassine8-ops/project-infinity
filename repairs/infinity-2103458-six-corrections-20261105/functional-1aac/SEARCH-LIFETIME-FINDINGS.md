# Search: consumer completion and interpreter retirement are different

Read-only source analysis bound by NATIVE-SOURCE-BINDING.json to the preserved451 source map and the documented signed458 engine chain. No native/provider/Search code changed. The existing two state_changed acceptance failures remain open.

## Confirmed source contract

1. `infinity_search.py::_leased_directory` serializes foreground plugin.video JSON-RPC workers through the existing abstract socket. The worker closes that socket when `Files.GetDirectory` returns, including exceptional return. This is a **RPC lifetime**, not a guarantee that the provider interpreter has exited.
2. `PluginDirectory.cpp::EndOfDirectory` marks the directory result done via SetDone. `ScriptRunner.cpp::WaitOnScriptResult` can return that result when m_scriptDone is set, before interpreter finalization. The timeout/cancel path deliberately returns the consumer while leaving the interpreter registered. It does not fake persistence completion or force-kill the provider.
3. Native `InfinitySearchLeases` separately tracks token->scriptId. It admits at most three retained tokens. A subsequent Reserve removes an old token only after ScriptInvocationManager::IsRunning(id) is false; that flag changes with manager execution completion, not EndOfDirectory.
4. Ordinary direct provider navigation omits the Search token and does not use this Search-specific lease guard. Other Kodi services and ordinary provider work are not bounded by the foreground RPC mutex. One RPC at a time therefore does not prove one live interpreter or bounded total process memory.
5. Provider setting `reuselanguageinvoker=true` permits a completed script body to wait for reuse in a still-live LanguageInvokerThread. The retained manager entry remains not-done until its exit callback. The lease map counts request tokens, not distinct script IDs. Under a same-live-invoker reuse sequence, three tokens can therefore occupy the capacity even if they reference one interpreter. Actual installed provider flags and request sequences are not available, so this is a conditional source finding, not a reproduced device failure.
6. Existing plugin handle lookup/removal and item callbacks use their shared scripts lock. This review found no evidence sufficient to declare a use-after-free or change handle ownership. No callback bypass or early retirement is proposed.

## Bounded accounting proof, not a crash test

The exact existing InfinitySearchLeases struct was extracted unchanged and compiled in a small host harness. Its manager supplies synthetic IsRunning values; no Kodi, Python interpreter, provider or Android engine ran. Six cases passed: duplicate refusal, failed-start cleanup, three-live-invoker capacity, conditional repeated tokens for one live invoker, retention while liveness remains true, and removal after observed completion. Source substring and full-file hashes, extracted code, compiler output and results are retained.

This establishes the algorithm's accounting, not an Android crash root cause or successful30-search stress run. It does not authorize releasing leases early: any correction would need proof of callback/persistence ownership and separate precise native approval. No lease limit, timeout, invoker reuse option or cleanup code was changed.

## Existing private November5 evidence

The capture remains historical2103456. The two supplied signal11 exit summaries have no stack/request/PID binding sufficient to establish their root cause. Current exported engine/source equality to458 preserves relevance of source analysis but does not cryptographically identify each historical crash producer.

A bounded read-only scan of critical history found The Crew invoker9 reaching `vfs.python.children_wait` / `python.child_thread_wait` in PID19492 (21:08:45–48 UTC capture) and PID13439 (15:55:57–59 UTC capture). These are checkpoint-session observations, not Search-token traces. No retirement event for that invoker appears within those short captures. Absence from this bounded interval does not prove a permanent hang, leak or relationship to either signal11 exit. The later provider process/child owner and actual triggering operation are unknown. Raw logs remain private; PRIVATE-EVIDENCE-SUMMARY.json contains selected phase/identity/time facts only. No shutdown test was run.

## Keep state_changed separate

`_provider_result` returns state_changed only after a completed, non-error response fails signature validation (or cache generation validation). Native busy/timeout/cancelled status is returned earlier. The conditional lease-capacity issue therefore does not explain these two state_changed labels.

Nixtoons history/settings writes remain a known self-invalidation path; the exact stamp includes inode/size/mtime/ctime, so a legitimate settings-file rewrite invalidates publication. Crew's actual changed component remains missing. The current source emits reason-only INFINITY_SEARCH_STATE records; none were retained in the supplied archive. The standalone existing diagnostic probe can classify sampled setting changes but explicitly cannot identify request ownership or observe every intermediate write. Endpoint semantic equality or that sampled probe is not a safe substitute for meaningful configuration-change detection.

Do not suppress state_changed, exempt all settings files, ignore source/dependency changes, accept stale results, change providers, or claim an interpreter-count observation fixes memory exhaustion.

## Smallest next evidence and release condition

Use a current supported Health Center incident export and existing Search rejection records during actual Search All/TV requests. Obtain current provider version/source identities and reuse flags without exporting settings values. Correlate request start/result/timeout with actual invoker/native exit evidence where the existing logs provide it. If existing telemetry cannot bind those events, request a separately reviewed bounded observation change; do not invent request attribution from checkpoint logs.

A connected authorized Android17 ARM64 device is still unavailable here. Real repeated Search operations, transient/native memory measurements, original fault stack and30-cycle physical stress remain NOT RUN. No simulated result closes this gate. Any future native repair must identify exact files and demonstrate necessity before implementation.
