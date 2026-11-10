# Infinity Local Network Gateway — scoped feasibility handoff (NOT implementation approval)
Date: 2026-11-10
Repository: `mahfouzhassine8-ops/project-infinity`
Research branch: `research/infinity-local-gateway-feasibility-20261110`
Source/evidence parent: `7fd0364ce510d5fa3c941e107c7e2d7a0d95e39e`
Protected owner-approved installed baseline: original-signed **2103477**
Frozen/unaccepted engineering pair: original-signed **2103478/2103479**; do not rebuild, install, mutate, reissue or imply release approval.
Status: **FEASIBILITY / READ-ONLY REVIEW AND ISOLATED PROTOTYPE ONLY**. No production edits; no original signing keys; no installer; Cobra always off-limits.

## User's goal
One Infinity System Hub control: **Automatic / IPv4 Only / IPv6 Only**. For requests actually routed through an Infinity-owned gateway, the gateway chooses the outbound IP family, including provider discovery and video data where compatible, so the user does not have to configure each provider individually. A local loopback gateway runs on the phone; it does **not** require an external VPN/server, a subscription, or changes to the phone's router. Unsupported/unrouted connections must be disclosed, not advertised as restricted. Automatic should use bounded dual-stack fallback, but do not promise a DNS wall-clock deadline already known to be an inherited Kodi limitation.

## Why this is a distinct investigation
At `7fd0364c`, the read-only report `repairs/infinity-network-family-2103477-20261110/universal/TRANSPORT-BOUNDARIES.md` established:
- Kodi cURL has request-local family controls; independent provider `requests` / `urllib` clients have no **injected Session/opener factory** in the reviewed call paths.
- FFmpeg 6.0.1 has no **TCP address-family AVOption**; some HLS/HTTPS streams can bypass Kodi cURL.
- The above does **not** prove that existing **proxy configuration options** are unavailable. Proxy routing is a different integration hypothesis, **not yet shown to work** for installed providers or Kodi's FFmpeg input path.

Documented client capabilities to examine (verify on exact pinned code/source and actual installed provider revision; never assume publisher source matches Fold):
- Python Requests supports explicit per-request `proxies=` and Session proxy settings; environment settings can override Session defaults. Source: https://requests.readthedocs.io/en/latest/user/advanced/
- Python `urllib.request.ProxyHandler` can create an opener configured per caller; a global `install_opener()` is forbidden here. Source: https://docs.python.org/3/library/urllib.request.html
- FFmpeg HTTP protocol documents an `http_proxy` AVOption, distinct from a nonexistent TCP `family` option. This **does not prove Kodi sends the option** when `DVDFactoryInputStream` chooses FFmpeg. Sources: https://ffmpeg.org/ffmpeg-protocols.html and pinned FFmpeg 6.0.1 source.
- cURL `CURLOPT_PROXY` can configure per-easy-handle proxy routing; existing user-configured proxies, custom DNS, TLS and socket-family rules need careful precedence. Source: https://curl.se/libcurl/c/CURLOPT_PROXY.html

## Codex: first task — read-only attachment decision matrix
Inspect the actual source+runtime identity and public supported configuration of:
1. Native Kodi cURL HTTP and normal VFS player.
2. WatchNixtoons2, The Crew, Otaku, Seren, Umbrella and POV Python HTTP call sites **as actually installed**, or explicitly mark publisher/reference-only paths.
3. Kodi -> FFmpeg input creation and whether `http_proxy` can be safely passed per HTTP/HLS item without editing the shared FFmpeg library.
4. Independent inputstream add-ons and their supported proxy settings.
5. Existing Kodi user proxy preferences and their ownership; do not repurpose or override an owner's unrelated proxy.
For each call site, record **CAN_CONFIGURE_PROXY_SAFELY**, **REQUIRES_PROTECTED_MODIFICATION**, **NOT_APPLICABLE**, or **NOT_VERIFIED**, including how the request carries the setting, and what happens on a provider update. Distinguish proxy support in a library from a supported *injection point in the host provider*.

**Hard stop:** If a specific third-party provider requires modification to pass a proxy, or a shared dependency/transport must be changed, **report exact files/contract and request separate owner authorization**. Do not slip provider rewrites or FFmpeg edits into this task.

## Isolated proof of concept if an actual supported route exists
In a disposable research harness only, not in the 2103478 application:
- Start a loopback-only HTTP CONNECT + HTTP forward proxy (bind to 127.0.0.1 and/or ::1 as needed) with Infinity-owned lifecycle. Keep it off Cobra, never listen on LAN. A loopback port is accessible by other local apps: evaluate a per-client auth token, access controls and closed-by-default behavior.
- Outbound policy: Automatic = dual-stack with eligible bounded fallback; IPv4 Only = only AF_INET for **remote internet egress**; IPv6 Only = only AF_INET6 remote egress; a client-to-loopback connection is a local control hop, not proof that the origin uses the selected family. If unsupported/missing family, fail clearly and never silently bypass policy.
- HTTPS uses CONNECT pass-through (no TLS man-in-the-middle, no disabled certificate validation). Keep original hostname for TLS/SNI, preserve host headers, redirects, tokens, cookies, byte-range requests, chunked/streaming bodies and cancellation.
- Test controlled endpoints with A-only, AAAA-only and dual-stack DNS, IPv6-first/IPv4 fallback where eligible, refusal, redirects, authenticated request/cookie persistence, HLS segments/range seek and multi-megabyte continuous playback with bounded memory/backpressure.
- Prove actual **outbound** family at the gateway and prove which **clients actually sent requests to it**; unproxied provider traffic remains uncontrolled. Don't rely on appearance of the setting or a CONNECT handshake alone.
- Switching setting changes new outbound sessions, never silently restarts active video. Measure start latency, worker count, socket/FD/memory growth over repeated failures; no resource leaks, no global persistent proxy changes.

## Immutable separation/safety
- Cobra 2103445 untouched in source, APK, settings, networking, default proxy, Java/DEX and behavior. Infinity/Cobra share Android package; **never use app-wide Android VpnService, global JVM proxy properties, global `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`, global `urllib` opener, or Python socket monkeypatch** to advertise Infinity isolation.
- Do not modify Search All, provider internals, Trakt/watchlists, resume, playback logic, skin, other Infinity behavior, accounts or user data. No uninstall, wipe, rollback, cache purge or automatic retries of unrelated suites.
- Original signed 2103477 remains protected. The frozen signed 2103478/2103479 are **not accepted**; the current startup blocker (matched 77 first-start PASS vs 78 talloc constructor SIGSEGV and previous 78 pure-virtual SIGABRT) remains a **separate** release blocker. No signature/release/status claim based on gateway feasibility.
- GPT-6.1 reviews transport security, proxy/client coverage, family guarantees and compatibility. Astra reviews true Infinity-only isolation, test validity, source protection and crash/release blockers. Codex sole implementer/reconciler, no competing edits.

## Deliverable before any gateway production authorization
Return one table:
`client | installed source evidence | supported proxy configuration | attachment point | HTTPS/stream compatibility | update risk | result (supported / protected changes required / unverified)`.
Include a **single concrete 1-provider + 1-video HTTP/HLS prototype** with measured route/egress, or a precise no-go with source evidence. Report whether a real Infinity-only gateway is feasible **without modifying providers/Cobra**; do not claim coverage for non-adopters.

Only after the owner reviews those findings should Codex request a separately scoped production implementation. Restarted app or extra Fold test is **not** required for this exploratory assessment.
