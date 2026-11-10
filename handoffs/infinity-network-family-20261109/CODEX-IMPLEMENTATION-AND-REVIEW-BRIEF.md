# Infinity-only Network Connections — Codex implementation and 6.1 / Astra review
Date: 2026-11-09
Status: **AUTHORIZED FEATURE SCOPE; NOT IMPLEMENTED / NOT TESTED / NOT SIGNED**
Repository: `mahfouzhassine8-ops/project-infinity`
Isolated work branch: `work/infinity-network-family-from-2103477-20261109`
**BASELINE CORRECTION (owner, 2026-11-09): Infinity versionCode 2103477 is the approved protected baseline.** Previous 2103474 was rejected in testing, even though its functional behavior worked as intended; 2103477 carries the preserved working behavior. Work forward from 2103477 and use a **strictly greater, currently unused versionCode** (2103478 is only a provisional candidate, not a committed release number). The starting source checkpoint for this branch is `80f9c78e5c133ef63abe95af359c3e4e7366153f` on `work/infinity-exact74-retest-2103477-20261109`; its metadata-only `REQUEST.json` states `from_version=2103474`, `to_version=2103477`, `tracking_changes=false`, `dns_changes=false`, `user_data_reset=false`, and `owner_delivery_requires_fold_test=true`. This metadata and branch name **are not proof of a signed installed 2103477 APK**; before implementation, Codex must verify the exact accepted 2103477 APK's signed source receipts, unchanged functionality, and approved combined module versions, and stop if the source is not a faithful reconstruction. Historical 2103466/2103469 checkpoints and rejected 2103474 **must not be substituted as the new baseline**.

## Team and authority
- **Codex: sole implementation/integration/build owner.** Trace production paths, write the scoped Infinity changes, run only selected feature checks, preserve the original combined signer/package/locked component receipts, produce one engineering signed APK and evidence when gates pass.
- **GPT-6.1: design and networking review**. Independently review dual-stack resolution/connect behavior, fallback bounds, TLS/SNI/Host, redirects, proxies, native Kodi/Python integration and failure diagnostics. Findings only; no conflicting source edits.
- **Astra: preservation and stability review**. Independently review actual Infinity System Hub placement, front/inner-screen behavior, regression boundaries, evidence, package signing/recovery and strict Cobra protection. Findings only; no parallel incompatible edits.
- Codex consolidates review feedback; no branch merge or release is assumed without real evidence. The reviewer roles are proposed coordination roles; creating this brief does not start external agent executions.

## User-authorized feature
Add **NETWORK CONNECTIONS** as a single item to the *existing Infinity System Hub*, immediately **after KODI SETTINGS and before UPDATE**. Use the approved hub's black/cyan style, icon sizing, padding, selectable rows, touch/back semantics, accessibility, and light/dark compatibility. Do not redesign or move any existing hub entry. Dedicated page presents:
- **Automatic (default)** — ordinary compatible dual-stack operation with a bounded Happy-Eyeballs-style family fallback where Infinity owns the transport. Prefer IPv6 when available, but promptly try IPv4 for connection-family failures, without causing unnecessary delays. A fallback may race connections; successful transport takes precedence. Do not retry provider rejection/HTTP auth/content errors as if they were IP-family failures.
- **IPv4 Only** — require IPv4 for Infinity-owned supported connections. No silent IPv6 escape.
- **IPv6 Only** — require IPv6 for Infinity-owned supported connections. If no usable AAAA/IPv6 path, report an actionable failure; no silent IPv4 fallback.

The setting must persist under Infinity-only ownership, default safely on absent/corrupt settings, apply to new connection/session attempts without killing ongoing playback, survive app restart, and never change Android Wi-Fi/cellular/private DNS/VPN configuration, JVM-wide IP-family preference, the OS network stack, or Cobra preferences.

## Required implementation investigation (before code)
1. Trace current Infinity System Hub implementation and existing settings persistence, native Kodi HTTP/VFS/player/libcurl network entry points, Python embedded networking used by search/provider add-ons, artwork/metadata requests and playback fetches; inventory the *actual* connection clients and their owners.
2. Identify feasible per-Infinity control boundaries that do not change Cobra's shared behavior. **Stop and report** if family enforcement would require unsafe changes to Cobra-owned or common components without provable isolation; do not silently enlarge scope.
3. Inspect Cobra's historical `repairs/cobra-network-family-control-2103183/` as **read-only behavior reference**, never reuse its Cobra Java code/settings as the Infinity implementation.
4. Distinguish Infinity-owned networking versus third-party clients that independently manage sockets. Do not claim full coverage where it cannot be demonstrated; mark each path enforced / unsupported / unaffected with evidence. Do not rewrite The Crew, WatchNixtoons2, Otaku, Seren, Umbrella or other provider search engines.
5. Confirm signed 2103477 baseline/source provenance, already approved Infinity search/navigation/watchlist behavior, original package and permanent signer, combined feature ownership and recovery chain.

## Connection, safety and diagnostics contracts
- Preserve HTTPS hostname, SNI, certificate chain verification, ALPN, host headers, URL routing, redirects, per-request credentials, cookies, headers, proxies and authentication. Never disable TLS validation; no IPv4/IPv6 IP-literal substitution that breaks virtual-host or certificate checks.
- Enforce family per request/socket/resolver at a proven Infinity-only boundary. Do not monkeypatch process-global sockets, edit system hosts/DNS, set `java.net.preferIPv4Stack`/`preferIPv6Addresses`, or change the existing Cobra codepath.
- Use short bounded fallback delay, explicit total timeout, correct cancellation, retry ceilings, same-family address rotation when applicable, no infinite loading spinner or retry storm. No fallback for logical/provider/HTTP failure. Respect connectivity change (Wi-Fi to cellular) for new requests.
- Diagnostics: saved mode, requested host (redacted if sensitive), whether IPv4/IPv6 A/AAAA were available, attempted and successful family (when measurable), connect timeout/failure category, and actual support scope. No tokens, secrets, private DNS values or credentials in logs. Surface honest user-facing errors.
- Honor IPv4/IPv6 literals, dual-stack hosts, IPv4-only hosts, IPv6-only hosts, DNS timeouts, broken IPv6 paths, IPv4 fallback, redirect chains, HTTPS/TLS, streaming sessions and cancellation.

## Explicitly authorized focused checks (feature only)
1. Source diff/protected component check: no Cobra Java/resources/settings, no cross-owner changes; no unrelated Infinity source/files, search logic, touch, skins or playback semantics.
2. Settings UI placement, focus/back navigation, persistence and update-on-next-connection on both Fold front and unfolded screens.
3. Resolver/socket unit and integration tests: AUTO fast working IPv6, failing/stalled IPv6 with timely IPv4 fallback, v4-only and v6-only host, IPv4 Only no v6, IPv6 Only no v4, redirects, SNI/TLS, proxy compatibility where supported, network transition, cancellation/timeouts/retries and truthful diagnostics.
4. Selected end-to-end Infinity connections: search/provider reachability, artwork/metadata, source discovery and actual stream playback startup, using existing `Blade Queen` example when available. Verify representative provider paths **without modifying their searches** and preserve unaffected providers.
5. Packaging checks only after implementation and focused evidence: full real ARM64 compilation, source receipt, original signer/certificate, original package ID, forward versionCode, in-place update and matching recovery. Test/QA limitations must be explicitly disclosed. Android emulator evidence is not physical Fold acceptance.
6. No shutdown tests, uninstall, data reset, cache/provider purge, broad regression suite or unrelated refactor. Existing permanent `AGENTS.md` / `docs/INFINITY-FOCUSED-TESTING-POLICY.md` remain binding.

## Protected scope / deferred next phase
**Cobra remains entirely untouched**: its native source, networking, settings, UI, timeshift, player, data, tests, build ingredients and behavior, including indirect shared-runtime effects. Preserve Search All, providers, Trakt, watchlists, Resume Hub, playback, Next Episodes, Continue Playing, layout/drawer/touch, Health Center/Command Center and combined chooser as already approved.

The user also authorized a **subsequent** full Infinity performance/stability refresh: cold/warm launch, loading responsiveness, search latency, artwork/media fetch, buffering, cancellation, recovery, responsive Fold UI, leaks and memory, provider isolation, and other genuine bottlenecks. **Do not mix those broad repairs into this network feature branch before feature verification.** Inventory and measure later, repair only confirmed Infinity issues, consolidate into one reviewed signed combined APK, Cobra still untouchable.

## Delivery definition
- Scoped source, independent 6.1 and Astra review notes (or explicit not-run), real test/evidence, per-path support matrix, documented risks, signed combined APK and matching recovery if all gates permit, and a short on-Fold one-pass QA checklist.
- No release/acceptance claims until the user actually tests the installed APK. No silent downgrade or unapproved changing of baseline, signer, provider logic, protected data or Cobra.
