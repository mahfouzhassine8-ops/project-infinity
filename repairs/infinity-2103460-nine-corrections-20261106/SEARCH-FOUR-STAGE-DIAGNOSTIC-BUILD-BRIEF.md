# Infinity Search — Complete Four-Stage Installable Diagnostic Specification
**Engineering handoff to GPT-6.1 / Codex — 2026-11-06.** Specification only; not an installer, not an implemented fix.

## Goal and already established identities
Create **one user-facing, on-demand, installable Kodi Search Diagnostic ZIP**, or the smallest authenticated matched add-on package required by the existing trust architecture, that collects enough correlated, privacy-safe evidence to diagnose and verify:

1. Search requests and genuine provider result return.
2. Provider-heading selection, Kodi GUI navigation/dispatch and actual destination activation.
3. False and legitimate `state_changed` causes, including settings/history and concurrency.
4. Before/after repair verification with preservation/security negatives and truthful physical-run evidence.

The user's confirmed install is **APK 2103462, skin 1.0.5.262, Command Center 0.3.5.61**. The 266/267 package is an **unaccepted partial test candidate**, not assumed installed. Investigate the *actual active signed module generation* if needed through automated, read-only self-identification; do not ask user for versions again. The 266 candidate restores direct-provider handoff; Search All heading activation and the two settings false-positive cases remain open.

**User physical PASS / immutable preservation:** #1 Power last, #2 Infinity Movies main menu, #3 Infinity TV Shows main menu, #5 Downloads Add videos and user-added folder persistence. Also preserve working Cast, browsing artwork/layout, provider settings, profiles, playback, skin and Kodi ownership. Cobra/Preview/shutdown completely off-limits. No broad Search rewrite, no lowering original-key protection, no uninstall, data clear, source deletion or hidden background telemetry.

## 0. Installer, lifecycle, and guardrails
- Prefer a **single complete Kodi add-on ZIP** with a unique, non-conflicting diagnostic ID, its own `addon.xml`, UI and private profile folder; verify Kodi's installation path and compatibility with the authenticated first-party system. If truly necessary to observe *private* first-party decisions, use narrowly gated diagnostic events added by a **separately original-key-authenticated Command Center update**. State transparently if that means more than one install action; **never pretend a standalone observer can read private native/CC variables**.
- No original signing keys in ZIPs, logs or code. Reuse the existing sole signer/authority if modifying authenticated modules. Verify current package identity, ZIP hashes, exact source member allowlists, update/recovery generation and original public-key signatures. An ad hoc ZIP is NOT a substitute for a CC manifest signature.
- On-demand, disabled by default. Only active after user chooses **Start Search Trace**. Provide **Stop and Export**, clear indicators of session armed/recorded and a simple "No failure observed / Evidence captured / Native event inaccessible" result. No constant background process, network calls, root, ADB, accessibility service, screen recording or telemetry upload. No auto launch to manipulate providers.
- Scope diagnostics to The Crew and WatchNixtoons2/Nixtoons by their **verified installed add-on IDs**; support Search All vs explicit provider vs heading click vs history as **different paths**. Do not conflate equivalent-looking provider names with exact IDs.
- Do not change provider implementation, query encoding, Search behavior, caching, cancellation, timeouts, settings or user media during collection. Do not execute additional searches or synthetic taps while user is testing, and never "fix" errors by changing labels.
- Session-bound controls: **one trace session**, at most one natural failure per provider, timeout/size limit, safe stop on abort/exit; bounded event ring buffer, local-only, minimal CPU/RAM/I/O, batched atomic finalization, deterministic cleanup. Disabled diagnostics are provably behavior-neutral.

## 1. One cross-layer correlation protocol
- Generate one random opaque `session_id` and separate `attempt_id` / `request_id` / `navigation_id` / `provider_id` / `response_id` (only verified IDs, no raw query). Relate every event to the same attempt, including late completion and cancellation. Do not claim a cross-process link when no matching token is observable: mark `correlation=unproven`.
- Each event has: monotonically increasing sequence; UTC timestamp; monotonic elapsed time; phase; process role (first-party Python, provider directory, Kodi UI, native observer, diagnostic-only); observable source; status; duration; outcome; reason code; sanitized error category; confidence (observed / inferred / not observable). Clock jumps must not reorder events.
- Self-identify once: APK versionCode; safe public cert fingerprint; native `libkodi.so` hash or BuildId when available; *resolved active* skin ID/version and relevant XML digests; CC ID/version, full authenticated manifest digest and relevant `infinity_search.py`, context and plugin digests; selected profile ID as a **session-local opaque ID**, not path; installed/enabled provider IDs and source/dependency proof status. Flag mismatched installed vs loaded vs bundled generations, stale script invokers, or missing fields explicitly.
- Retain exact *counts, booleans, stage timings, reason categories and opaque attempt tokens*, not queries, filenames, paths, URLs with query parameters, media titles, provider credentials, XML contents, auth tokens or raw Kodi logs. Hashes of low-entropy secret settings are not safe to publish; if content equality is needed, use a fresh session-local keyed digest that is discarded after export or derived nonreversible equality tags.
- Every observed stage emits both entry and exit; incomplete stage after crash is visible as `started/no terminal event`. Bounded synchronous write only at safe checkpoints, never blocking the native Search lease or modifying request ordering.

## 2. Stage ONE — Search request and returned results
Instrument where technically authorized: `infinity_search.py` `_open_search`, `route`, `providers`, `_search_results`, `_provider_result`, `_leased_directory`, JSON-RPC `Files.GetDirectory` boundary, provider directories **only if events are exposed without patching providers**.

Capture:
- UI origin: Search All / explicit provider / provider heading / Search history; media category; accepted input presence/length bucket (never text); provider inventory count and IDs; provider chosen and whether enabled; contract/pins/dependency check outcome; whether constructed target route agrees across pre/post verification. Record sanitized route *shape* (first-party aggregate vs direct provider; plugin ID and action category), with ephemeral digest of canonical route; **never raw encoded query**.
- Search protocol readiness/probe; eligibility error; CC/provider dependency missing or disabled; route construction failures; forced refresh/inventory revision; history commit result and whether direct-provider path bypasses aggregate correctly (266 behavior).
- Native admission: `Infinity.Search.Protocol` readiness, active-consumer count, admission lock acquire/busy, request token created/published, job start/finish, cancellation request/ack, bounded join/retirement, token cleanup, native worker status. Record lease span and **actual request-vs-interpreter lifetime**, not speculative "cleanup completed" if only RPC finished.
- `Files.GetDirectory`: invoked vs not invoked; start/end time; JSON-RPC result vs error; native status `completed/busy/timeout/cancelled/unavailable`; files array valid/type and **original result count**, cap 40 and filtered-result count with filtering reasons; directory-vs-playable result types; API error code/class (sanitized), provider-enabled and pin checks after result.
- Distinguish: provider was never called; provider called but returned empty; provider returned nonempty but CC rejected; provider result completed but UI display failed; provider returned error; request still active/cancelled. Never report "provider broken" solely because aggregate returned `state_changed`.

## 3. Stage TWO — provider heading TAP and actual Kodi navigation
At the source: `_publish_result` and original direct-provider handoff. Observe native JSON-RPC / Kodi `GUI.ActivateWindow` **only where exposed**; observe Kodi window current state, directory opening and native error codes through existing logs. Use `xbmc.Monitor.onNotification` only for notifications the running version actually emits; it is **not a universal raw touch hook**.

Capture:
- Provider heading created; exact **sanitized route digest** and provider ID; folder flag, playable flag, status shown, visible item count, addDirectoryItem success/failure and Kodi plugin directory completion/EndOfDirectory if observable.
- Heading selected by UI vs synthetic automation: initial window ID, visible container/focused item ID, selection event if actually exposed, builtin/action/JSON-RPC dispatch attempted, return value, foreground window transition and selected directory identity via safe digest. Record return/history flag, stale retained child/root, focus loss, overlay/touch interception, wrong window/scope, source disabled, addon invocation exception and missing provider context **when observable**.
- Trace `heading_published → selected? → dispatch? → window_transition? → provider_invocation? → directory_started? → items_returned? → rendered?`, each as yes/no/not observable, with event time and reason. Kodi accepting a navigation request **does not prove it opened results**. Absence of an exposed tap event cannot prove the user did not tap.
- Read-only comparison: direct provider selection, Search All heading, and provider-owned direct search. Confirm whether their route digests and enabled/source contracts match; explicitly compare installed 2103462 with the 266 direct-provider correction in a disposable fixture, never silently change current user Search path.
- If no Python-level event exposes **the critical native touch/dispatch**, export `NATIVE_EVENT_NOT_EXPOSED` plus surrounding Kodi window/error evidence and exact missing native callback/offset needed. Do NOT invent a Python callback or modify Kodi core just to claim total visibility. Native instrumentation is a separate scoped escalation only with evidence.

## 4. Stage THREE — explain `state_changed` without weakening integrity
Use the original `_query_signature`, `_query_file_stamp`, `_state_rejection_trace`, `_provider_result` checks as the authority. Record separate pre/post **response signature** and **cache/UI signature**, matched/mismatched/unknown; `cache_hit`, known UI-property revisions, current provider-enabled/dependency/source pin check, cancellation, active profile change and origin of the rejection.

For provider/dependency settings fingerprints capture **only comparisons** of `st_dev/inode/size/mtime_ns/ctime_ns` (which dimensions changed), and a safe in-memory equality test of content if necessary. Classify:
- no change;
- same-content rewrite / metadata-only stamp;
- provider history/requestTimes update;
- confirmed meaningful settings change;
- change → restore (ABA) within request;
- provider addon/source hash or dependency change;
- addon disable/update/profile change;
- UI cache/progress-only change;
- unreadable/linked/racing file;
- cancelled/timeout;
- **unknown writer / cannot prove no meaningful intermediate change**.

**Critical:** A before/after content comparison does not prove absence of an intervening meaningful write. A watcher polling a file, Kodi `UpdateSetting` notifications, or wrapping only first-party writers does NOT cover arbitrary provider direct-file writes. Mark `ABA_NOT_OBSERVABLE` if such coverage is absent. Do not bypass existing timestamp/ABA/revision/signed-source checks or erase `state_changed` to make tests pass. Positively attribute benign writer only when an instrumented writer event is correlated to the attempt and all relevant writes are covered.
- Capture first-party history writer `shared_history` (success, wait, revision) without saved data; provider-owned history writes only if provider event is genuinely observable; note Crew and Nixtoons may have **different writers**.
- Print for EACH rejection a safe reason vector, previous/current component flags, original result count, cache hit, whether direct provider route still valid, and `confidence`. Show "valid provider output rejected by aggregate" when proven. Preserve original error and original destination, no forged results.

## 5. Stage FOUR — reliable before/after proof
The collector must have two session modes: **Before repair** and **After repair**. No modification in Before. After mode only observes newly installed *authenticated* candidate. Verify exact candidate source/manifest/skin signatures and a proper versioned recovery path.

Test matrix (automated host fixtures PLUS at most one natural physical demonstration of each issue):
- Direct Crew results open; direct Nixtoons results open.
- Search All heading publishes and opens provider's original route; no empty page, wrong Videos root or click swallowed by overlay; Compare historical and new attempt timelines with the *same media/provider category*, not raw queries.
- Nixtoons benign history-only update and byte-identical rewrite no longer false-reject (only if safely proven). Crew's writer independently attributed. Genuine settings/dependency/disable/source/profile changes still reject. ABA changes-and-restores must reject; direct-file writer outside coverage must not be declared benign.
- Verified zero-result responses remain genuinely zero; provider errors remain visible; no result transplant, fabricated title/result or new provider request side effect.
- Overlapping searches/busy, cancellation, timeouts, history, source update, user Back, widget-refresh/cache race, repeated invocation and background/resume paths preserve original admission and cleanup.
- Post-fix repeated Search stability target of 30 natural completed requests **only after** functional fixes and in a safe test session; stop on first failure. A missing native crash stack is "NOT PROVEN," never a PASS.
- Include four **negative preservation assertions** protecting Power last, Infinity Movies, Infinity TV Shows and Downloads/Add videos + added-folder persistence, and preserve Cobra, Cast and existing browser visuals. Do not run unrelated shutdown suites.
- Provide a per-stage verdict: `PASS`, `FAIL`, `NOT_OBSERVABLE`, `NOT_RUN`, `PARTIAL`, each with evidence IDs. A "PASS" requires actual observed request/response/navigation or physical device evidence, not mere XML tests.

## 6. Native crash evidence and escalation boundary
- If a crash occurs, retain **the first incident only**: UTC time, package PID/process, tested APK version and native `libkodi.so` hash/BuildId, last completed diagnostic sequence, active request/lease/cancel states and reason categories.
- Include a Health Center-export pointer to the *same incident*. The Python add-on cannot fabricate Android tombstones or access inaccessible native faulting-thread stacks. If no stack is accessible, write `FAULTING_THREAD_NOT_AVAILABLE` and request only a legitimate same-event Android bug report when actually needed. No root, no unsolicited Android permissions, no background screenshot capture and no repetitive forced crashes.
- A compiler/source reproduction in CI is not a physical Fold pass.

## 7. Single privacy-safe output ZIP
Implement **Stop & Export** as one locally generated ZIP:
- `README.md`: one-paragraph instructions + timestamp + scope/limitations.
- `summary.md`: top-level cause candidate, first failing stage, exact unknowns, next actionable development step, preserved features, four-stage verdict.
- `identity.json`: actual package/native/active skin/CC authenticated source hashes and capability coverage (never private paths).
- `events.ndjson`: ordered bounded sanitized event records with correlation IDs, latencies and observed status.
- `attempts.json`: one row per attempt including counts and accepted/rejected outcomes.
- `settings-diff.json`: only metadata *change flags*, safe semantic categories, known/unknown writer and ABA coverage; never settings values.
- `navigation.json`: heading construction, dispatch, window/directory result and missing native event markers.
- `crash-index.json`: same-event trace availability, not raw sensitive tombstone.
- `coverage.json`: every expected hook/status and whether it was instrumented, observed, unavailable or untested.
- `regression-matrix.json`: before/after positive and negative tests; source/build identifier.
- `redaction-report.json`: automatic allowlist verification; count of suppressed fields, no values.
- `SHA256SUMS` for exported report members; bounded package size, zero raw private dump attachments by default.

Default export is **offline only**, saved in user-accessible location using supported Kodi APIs; show precise file location. No auto upload, external URL, credential extraction, private provider query, account log, media path or full `kodi.log`. If exact failure cannot be proven, say so with the *single smallest missing event*, not 20 further questions.

## 8. Implementation tests and release obligations
1. Unit/source tests on all event hooks: event correlation, UTF-8 handling, bounded memory/size, atomic recovery on failure, monotonic clock, deduplication, schema validation, exporter redaction, no auto-start or network.
2. Host integration with **real signed existing module ABI** and provider dummy fixtures: not-called, no-results, results-before-rejection, correct heading but no native click, bad dispatch, success, cache-only update, benign history write, byte-identical rewrite, meaningful change, ABA, unknown writer, cancellation, timeout, stale invoker, provider disabled. Confirm existing Search lease and guards unchanged when diagnostic disabled.
3. Verify genuine original-key authorization where first-party modules are modified: package/addon identity, manifest member hashes, existing release pipeline, original certificate, install/upgrade/recovery protocol, no native/DEX/Cobra changes. No source-only ZIP falsely called installer.
4. On physical Fold, one authorized user trace session for Crew and Nixtoons and one export. Collector overhead must not modify the failing behavior. After remedy, one matching verification session. No repeated request for known phone version or screenshots, no data reset/uninstall.
5. Deliver actual **installable** ZIP(s) and forward recovery instructions only after matching signatures and installer validation. Distinguish "observer-only" coverage from private authenticated hooks and native-only gaps honestly.

## Required final engineering answer
Provide a compact root-cause matrix:

| Failure location | Observable evidence | Fix owner | Confidence |
|---|---|---|---|
| Provider not called | No request/provider invocation after selection | Search dispatcher/route | observed / unknown |
| Provider gave results but aggregate discarded | Nonzero original count, `state_changed` reason flags | CC response state validation | observed / unknown |
| Heading published, tap missing or swallowed | Heading exists; UI callback or native event missing | Skin/native UI only if proved | observed / not observable |
| Navigation accepted, directory never opened | Kodi request acknowledgment without directory-start | Kodi native/window dispatch | observed / unknown |
| Opened but empty/failed provider | Directory opened; zero items or provider error | Provider route/contract; avoid provider edits | observed / unknown |
| Repeated Search crash | Current matched faulting thread, or explicit no-stack limitation | Native if identified | confirmed / unproven |

**Release gate:** Stage 1 through 4 may collect evidence even when no code fix is ready. Never label the full four-stage repair verified solely because the diagnostic ZIP installed. No speculative native patch, unverifiable P0 claims, or changes to physically accepted functionality. Continue engineering where independent of missing device evidence. The next deliverable for the user is an authenticated diagnostic they can install and export—not another source-only investigation.