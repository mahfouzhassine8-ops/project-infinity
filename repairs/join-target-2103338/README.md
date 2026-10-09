# Infinity 2103338 — join-target diagnostic candidate

User authorized integration and native build on 2026-10-08. This candidate adds
the prepared invoker/add-on to Linux OS TID and worker-stage observations. Its
source recipe is pinned to 83bb461c1523f7e648ea4b32148e9e9eb7998598, which packaged
2103337 successfully from the Android/native jobs of run 37771220035. The existing
accepted and rollback refs are not updated.

The native delta is the two exact-hash LanguageInvokerThread files, the new
InfinityInvokerTarget header, and the diagnostic engine tag. The original trace
tag changes to `infinity-shutdown-2103338-diagnostic-v1`. Production shutdown
admission, cancellation, joins, timeouts, finalizers and save behavior are retained.
The diagnostics require an ARM64 native rebuild; the old engine cannot activate them.

Host tests use mocks at Kodi/runtime boundaries. The workflow also reconstructs
the whole protected parent source and runs its required gates before applying the
diagnostic delta, cross-compiles native ARM64, compiles the complete Android shell,
and runs the inherited Health exporter regression. Packaging checks the source,
native SHA-256, permanent signer, JNI/class coverage, stable resource IDs and all
protected non-DEX/non-manifest/non-engine entries against the actual 2103337 APK.

An APK built by this workflow is an unaccepted diagnostic Fold candidate. It does
not establish the cause of historical PID 32099 or constitute a shutdown fix.
During a stuck close, collect the native/critical traces and a contemporaneous
thread dump before another Kodi session rotates the trace. Match `os_tid` to
`sysTid` in the same PID/session. A stage label is not the worker's complete stack.
No physical Fold capture or acceptance is implied by successful CI.
