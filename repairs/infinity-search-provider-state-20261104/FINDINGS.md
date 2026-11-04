# Infinity Search provider-state diagnosis — 2026-11-04

Read-only production investigation. No Search implementation, add-on, settings, native, Preview, Cobra or APK changes. The separately authorized UI454/recovery455 work contains no Search correction.

Continuation: [provider-specific source findings and seven additional diagnostic cases](PROVIDER-CONTINUATION.md) identify normal WatchNixtoons2 settings writes and distinguish Crew's conditional paths. The initial 15-case evidence below is retained; current device attribution remains pending.

The [standalone read-only diagnostic script](infinity_search_state_probe.py) is delivered with [instructions and ten passing safety checks](STATE-PROBE-README.md). It has not been deployed; no connected authorized Kodi script-launch route is currently exposed. The initial source findings below remain the historical first-phase record; use the continuation for the newly verified provider-side writes.

## Confirmed source and executable evidence

Examined the actual original-key signed 2103453 APK, SHA256 `08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8`. Its `assets/addons/script.infinity.commandcenter/infinity_search.py` is SHA256 `cbbf36ee20974ada8be7a8630e0f0b621b0fb646004842508901b727ddad47b5`. The UI packaging allowlist freezes this member.

`_provider_result` (lines 277–303) computes `_query_signature` before the provider call and again afterwards. When unequal, line 293 returns `state_changed` and discards the answer. `_publish_result` (lines 329–337) converts that status to **State changed; search again**. The literal is Infinity-owned, not a message returned by The Crew or WatchNixtoons2.

The fingerprint contains the route, profile identity, Command Center version/profile, provider root and contract, provider/dependency addon.xml and settings.xml filesystem stamps, Continue Playing file stamp, and seven global revision properties. A stamp includes device, inode, size, mtime and ctime; it does not compare settings values. Global revisions include widget refreshes, Continue Watching, Resume Hub presentation and any Addons notification published by the inventory monitor.

The 15 focused host cases in `test_shipped_state.py` execute the unchanged functions extracted directly from that APK with synthetic platform/provider boundaries. All passed. They establish:

- A **byte-identical** settings file with a new timestamp rejects an otherwise completed fresh result.
- Each of the seven revision properties independently causes rejection without changing the source, route or returned answer. An unrelated Continue Playing file timestamp has the same effect.
- A dependency settings-file timestamp also rejects a result while dependency source hashes remain unchanged.
- The same check can replace a native timeout status with `state_changed`, obscuring the original failure. Cancellation detected by the foreground cancel object still takes precedence.
- Stable results work, cache hits avoid additional requests, completed-empty is distinct, and source changes/disablement are rejected as `unavailable`.
- The shipped TV route contracts retain their existing category and query encoding.

These are reproducible overbroad validation and status-classification mechanisms. They do **not** establish which fingerprint component changed on the user's phone, whether a real provider request completed, or whether a real credential/filter/source change occurred. No Android/provider-network test was run.

## Provider-specific paths

| Integration | Shipped TV adapter | Relevant state exposure |
|---|---|---|
| The Crew | `provider_capabilities.recognize` verifies its entrypoint, declared `script.module.thecrew`, static lazy action map and `TVShows.search_term/get` receiver shapes. Action/query parameter names are read from the verified installed router, not guessed. | Fingerprint includes both plugin and declared dependency settings. A dependency write can invalidate the outer result. |
| WatchNixtoons2 | `action=actionSearchMenu`, `path=/search`, `searchType=series`, query in `query`; scope is mixed anime/cartoon series. | Own settings plus shared global revisions. No evidence yet identifies a particular settings write. |
| Umbrella | `action=tvSearchterm`, query in `name`. | Uses the same validation, ownership and cache mechanism. Successful searches do not prove it cannot encounter the race. |
| Seren | `action=showsSearch`, query uses the existing JSON/URL `action_args` codec. | Same guard. No special exemption. |
| Otaku | `search_tv_show/<encoded query>`; anime TV series only. | A completed empty response is shown as zero results. That is not the `state_changed` condition and does not by itself establish a defect. |

These provider add-ons are installed separately and are not present as source in signed453. No current device-installed version, source hash, search term, response or state-delta trace was supplied. Historical October 26 Crew evidence documents an earlier version only; it is not proof of the current installation. Do not attribute this incident to a guessed search-history write, particular add-on update or missing account.

## Tokens, cancellation, concurrency and ownership

Python uses a per-Kodi-process abstract Unix socket for one active foreground plugin RPC, a unique UUID request token bound to the route SHA, and separate request/cancel/result properties. The original RPC worker owns admission until it exits. Exceptional consumer exit requests cancellation and joins that worker before clearing token properties. `_bounded_results` invokes providers sequentially, preserves the progress cancellation object and stops when admission reports busy.

The preserved native integration source (`interfaces/generic/ScriptRunner.cpp`) separately validates token format, exact protocol option, route proof, original owner authentication, installed skin, checkpoint/shutdown admission and plugin identity. Protocol metadata is stripped before provider execution. Native leases keep real invocations registered; timeout/cancellation does not manufacture script or persistence completion. No change to these protections is proposed.

The before/after fingerprint is **not the search token**. A background widget or Resume Hub update can change it while request ownership and source pins remain valid. Conversely, a real source/profile/settings change must remain protected. `route()` is rechecked before and after results/cache hits; failed source pins, disablement and dependency changes raise `unavailable` rather than the displayed state-change label.

## Smallest next step

Collect one bounded diagnostic session covering the failing Crew and WatchNixtoons2 TV searches and a working provider. Reuse the already-read signature components to record only: provider ID/version, validated adapter family, elapsed time, native result status, cache-hit flag, cancellation state and a **changed-component reason mask**. Correlate with an ephemeral diagnostic sequence, not a raw request token. Do not log query strings, paths, URLs, result titles, credentials or settings values. Do not execute a provider twice or add workers, retries, persistence owners or settings serialization.

This diagnostic hook is a proposal only; none was installed or activated. It should retain the current rejection decision while observing which component changed. If a settings write is implicated, distinguish unchanged bytes from changed content privately; do not infer that every write is harmless.

A minimal correction can then separate cache invalidation from fresh-response validity in the existing universal Search path, while preserving real source/profile/dependency/settings changes, token ownership, cancellation, error status and cache age/size limits. Native failure status should not be overwritten by an unrelated freshness change. Do not simply remove the check, accept stale cached answers, retry providers automatically or create provider-specific replacement searches.

Remaining verification: actual installed adapter/source identity; exact changed component and native outcome during the two failures; stable/changed settings, cache hits, provider update/disablement, cancellation and overlapping sessions on Android. Otaku needs a known compatible anime-TV query and its actual completion/error result before classification. Physical Fold behavior remains unverified.

## Preservation

Only this diagnostic directory is changed on `work/infinity-search-provider-state-readonly-20261104`, based on signed453 source `cb7c6214807b79661e397cccb0740fc91fab3e24`. No production files or recovery locks changed. No Search APK was built, signed or installed. Settings values and user data were neither read nor logged. Existing UI454/455 packaging is a separate branch and authorization.
