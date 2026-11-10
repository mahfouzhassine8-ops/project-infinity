# DNS deadline blocker — targeted Codex repair handoff
Date: 2026-11-09
**Status: INVESTIGATION AND FOCUSED CORRECTION ONLY — NO SIGNED APK**
Repository: `mahfouzhassine8-ops/project-infinity`
Work branch: `work/infinity-network-family-from-2103477-20261109`
Frozen implementation/evidence checkpoint: `ddf6b078fdf0cb402ffe51fefd4bca8675dd1f99`
Protected installed/approved signed baseline: **2103477**.

## Verified current result
- New Infinity System Hub NETWORK CONNECTIONS, Automatic/IPv4/IPv6 persistence, per-request libcurl IP-family enforcement, correct forced-family behavior, eligible automatic fallback, and pool/cookie-preserving reuse are **implemented in source**.
- Four real ARM64 translation units and full engine link **PASS**, with original 71,213 exports, dependencies and Cobra resources preserved.
- 12 host transport cases PASS, 7 settings checks PASS, and 5 focused DNS cache/policy checks PASS.
- Mandatory DNS deadline case **FAIL** on exact curl 8.10.0 threaded resolver: connect timeout 2000ms, total timeout 3500ms, 5.01987s observed, CURLcode 28. Confirmed call path: `Curl_resolver_kill -> thread_wait_resolv -> Curl_thread_join` after blocking system `getaddrinfo`. No actual Android resolver reproduction yet; do not overgeneralize host results.
- Actual Android network/UI/playback verification, real Fold acceptance, registry reconciliation/version reservation, signed APK and recovery **NOT RUN / NOT PREPARED**.

## Specific additional test-contract finding
`test_network_family.py::test_dns_failure_is_bounded` requires `elapsed < 3.0s`, while `curl_probe.cpp` explicitly configures `CURLOPT_TIMEOUT_MS=3500ms`. These are inconsistent acceptance bounds even for a correctly terminated transfer near 3.5s. Reconcile the test threshold against the explicit policy and a documented small scheduling tolerance, **without weakening the real wall-clock requirement or converting the 5s overrun into PASS**. Keep the blocker as FAIL until actual behavior is demonstrated. Record curl operation time separately from resolver cleanup/return/cancellation time and ensure the timer covers what a Kodi caller experiences.

## Next focused engineering actions — Codex sole owner
1. **Freeze/protect** `ddf6b078` and the verified signed 2103477 payload. No new broad implementation, source migration, Cobra edit or signing while the DNS blocker exists.
2. **Identify the actual production Android resolver** (threaded libc `getaddrinfo`, c-ares, another backend) in the exact Android-bound libcurl binary. Confirm the host 8.10.0 reproduction is representative of the Android deployment; inspect resolver ownership, cancellation and `curl_easy_perform`/multi-return cleanup paths. Keep the host FAIL if unresolved; disclose Android as NOT RUN until verified.
3. **Investigate genuinely cancellable, bounded DNS** under Android's own network/Private DNS/VPN rules. Potential feasibility paths only, not preselected fixes: native Android async DNS (`android_res_nquery` / `android_res_cancel` on supported API levels) or a scoped Java `DnsResolver` bridge, feeding verified per-request A/AAAA responses to libcurl while preserving the original hostname/TLS/SNI/Host and proxy semantics. Engineer and prove correct network selection, redirects, DNS cache staleness, concurrency and socket ownership before adopting. A curl c-ares build is an alternative *only* if Android DNS and routing semantics can be shown equivalent and all dependencies/security/ABI are validated. Neither route is a blanket authorization to alter global networking or core dependencies.
4. **Do not use `CURLOPT_QUICK_EXIT`, detach unbounded resolver threads, skip joins by leaking resources, use global socket monkeypatches, disable TLS verification, add synthetic success, or change Android/OS/private DNS settings.** Official curl documentation warns that QUICK_EXIT is intended for a program about to exit; it may leak resources.
5. **Keep the family policy**: Automatic must not hang indefinitely or misrepresent fallback before DNS completes; forced IPv4/IPv6 must not escape policy; independent Python, FFmpeg, and external inputstream transport paths remain NOT ENFORCED/NOT PROVEN unless separately verified. Preserve first-class proxy behavior, no new global DNS caches, and all current cookie-pool and user-data behavior.

## Narrow verification gates
- Record exact build/backend versions and controlled resolver stall simulation. Observe wall-clock DNS deadline, failure classifications, abort latency and cleanup completion under repeated requests and Wi-Fi/mobile network changes.
- Verify no accumulating threads, sockets, file descriptors, retained curl handles, callbacks after destruction, or persistent memory growth across repeated failures; preserve cookies and connection pool isolation.
- Re-run the corrected DNS deadline test **plus directly affected host transport/cancel/cache-policy checks only**. Do not silently rerun other suites. If native source changes, redo exact ARM64 compilation/link and original-export/dependency preservation check for changed units.
- After DNS gate has an evidence-backed PASS on the relevant target, perform separately selected actual Android feature checks. Physical Fold acceptance remains owner-only and separate.
- **Do not sign or publish** until the mandatory DNS gate, relevant Android checks, Cobra isolation, original signer/source receipt, version registry reconciliation and greater unused version reservation are all addressed. 2103478 remains provisional.

## Reviewer roles
- GPT-6.1: evaluate exact resolver backend, safe cancellation/fallback semantics, test deadline contract, family security and TLS/proxy compatibility.
- Astra: audit resource lifetime and leak proof, source boundary/Cobra isolation, accepted signed baseline and issuance registry. Both give findings to Codex; Codex remains sole implementation/build owner.
- All other Infinity performance/stability work is **deferred** until network feature acceptance, not silently bundled into this repair.

## Authoritative platform references
- curl QUICK_EXIT: https://curl.se/libcurl/c/CURLOPT_QUICK_EXIT.html
- curl CONNECTTIMEOUT_MS: https://curl.se/libcurl/c/CURLOPT_CONNECTTIMEOUT_MS.html
- Android NDK networking and async DNS APIs: https://developer.android.com/ndk/reference/group/networking
- Android DnsResolver (cancelable queries): https://developer.android.com/reference/android/net/DnsResolver
- Android DNS architecture: https://source.android.com/docs/core/ota/modular-system/dns-resolver
