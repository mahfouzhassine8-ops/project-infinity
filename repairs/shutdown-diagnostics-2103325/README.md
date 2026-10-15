# Infinity 2103325 — Shutdown diagnostic candidate

This is diagnostic instrumentation, not a proven shutdown-speed repair. No new lock is authorized here. The ARM64 build, signed APK verification and physical Fold acceptance are separate gates.

## Immutable parent

- APK 2103324, source `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`.
- APK SHA-256 `5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3`.
- Skin remains `skin.infinity.diggz 1.0.5.201`.
- Native parent is the exact 2103308 engine inherited by 2103324, packaged SHA-256 `b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6`.
- Do not substitute the older 2103291 engine or the separate 2103313 cooperative-shutdown candidate.

## Submitted implementation

Branch: `repair/infinity-shutdown-diagnostics-2103325`.
Corrected native source: `5f27da83c149dcb8232b537628637324422efba6`; native run `37603168381`.
APK source: `1d1dd742836bbf25f2f30fb26bf3a0e78864afd4`; packaging run `37603284023`.
The package workflow requires that exact native run and source identity to succeed. Older runs `37600529076` and `37602080292` are superseded and must not be delivered. These run references do not assert successful completion; check their actual status and receipts.

## Scope

Twelve existing C++ files and one new trace header instrument application stop/cleanup, player/audio/render/window cleanup, service stops, Python GIL waits and interpreter finalization, thread joins and database close/commit/rollback. The entire native preimage map is verified before instrumentation; protected source hashes are checked after compilation.

Four Android diagnostic source files change. Event time is captured before logging is queued. Three calls separate Java destruction from NativeActivity destruction. The existing Health Center exporter includes fixed diagnostic files. Native diagnostic identity is rebound to the actual packaged library instead of its stale inherited value. The normal-close, legacy-quit, force-close and plan bodies remain unchanged. The 250 other shell source files are protected.

Current-thread names use PR_GET_NAME rather than the API-26-only pthread getter. CI compiles and links the writer with the exact ARM64/API-21 NDK before the full engine. The application minimum SDK is not raised.

There are no new UI screens, addon replacements, Python services, timeout changes, skipped saves, automatic kills, data resets, provider changes or runtime permissions. Measurement has overhead; bounded regular-file writes are not hard real-time guarantees.

## Device procedure — only after verified APK delivery

Install 2103325 over the existing app without uninstalling or clearing data. Confirm the installed version. Open Infinity, let startup settle, and press normal Close Infinity once. Record the observed delay and whether playback was active. After reopening, use the experience-card gear, Infinity Health Center, then Export diagnostics ZIP. The clipboard text summary alone is insufficient. Do not use Start Fresh or clear logs.

Recording is automatic during shutdown. The Responsive/Fold Trace toggle is unrelated. Relaunch does not erase the native capture; one previous native capture is retained too. Export before repeated unrelated close cycles replace those captures. If manual Force Close becomes necessary, state that explicitly: the incomplete trace is useful but cannot prove a normal clean exit.

New ZIP entries are `shutdown/native.jsonl`, `shutdown/native.previous.jsonl` and `shutdown/java-close-history.txt`. Existing native cleanup, process-state, summary and available Android crash/ANR evidence remain included. `exit-manifest.json` records availability, truncation, engine tag and actual packaged native SHA-256.

The new collector reads only fixed app-private diagnostic files, not provider credentials or user databases. The pre-existing report and Android traces can contain private diagnostic data; review before sharing. Nothing uploads automatically.

## Evidence limits

A returned scope is not a success verdict. An exit-request marker is not proof of PID death. A missing end marker is not proof of deadlock; it may mean an operation is active, evidence was interrupted/truncated, or the process exited. Java NativeActivity destruction may not return because the existing native path exits after native destruction. Do not invent an error from that alone.

Correlate PID, boot-based session time, Java occurrence time and matching external Android exit evidence. Do not assign historical exit records to the installed build solely from PID equality. Nested timings overlap and must not be added as if independent. A slow container phase is not proof that every child service caused the delay.

This pass does not add arbitrary native stack unwinding, universal mutex-owner identification, provider-internal network tracing, or independently verified PID-death timestamps. Uninstrumented work is visible only within its containing phase. Use captured waits for targeted follow-up; do not promise a complete root cause from the presence of a log entry alone.

## Verification and acceptance

Host tests exercise concurrent trace writes, capture limits and retention, a real embedded CPython GIL wait, exact source transforms and preserved close-command bodies. These are not physical Android tests.

The APK pipeline also requires all 15 inherited Android regression suites plus 8 new exporter/clock tests, protected payload and DEX comparison, unchanged JNI/resource/manifest contracts, and the permanent signer. An APK is published only after those gates pass. Build success does not imply Fold acceptance.

No lock until repeated physical-device shutdown/relaunch and persistence checks pass. The next objective is a useful evidence ZIP, not a claim that shutdown is already faster.
