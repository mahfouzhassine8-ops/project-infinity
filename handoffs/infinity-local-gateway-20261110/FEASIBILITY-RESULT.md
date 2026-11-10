# Infinity Local Gateway: proxy attachment findings

Research input: `d7a5f059337a0f3714db0c51d2f9ba32cda3d872`, parent `7fd0364c`.
Protected baseline: 2103477. Frozen engineering APKs: 2103478/2103479.

**Decision: a local gateway is technically plausible for clients explicitly routed to it, but no safe,
unmodified installed-provider-to-video workflow was established. No production implementation is authorized
by this research result.** The missing piece is attaching the selected proxy to the provider's real requests.
Library proxy support alone does not provide that attachment.

## Attachment decision matrix

| Client | Installed source evidence | Supported proxy configuration | Attachment point | HTTPS / stream compatibility | Update risk | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Kodi native cURL / ordinary HTTP VFS | Retained protected-source provenance; existing frozen native implementation | `CCurlFile::SetProxy()` configures the individual instance | An Infinity-owned caller holding that instance; automatic attachment to every native caller is not implemented | Existing proxy/TLS support; gateway route, streaming and cancellation not exercised | Native API and proxy-precedence contract must remain pinned | **CAN_CONFIGURE_PROXY_SAFELY**, capability only; actual gateway integration **NOT_VERIFIED** |
| WatchNixtoons2 | Reviewed reference 0.14.24, not current Fold source proof | Requests Session supports proxies at library level | `request_helper()` has no proxy argument or reviewed proxy setting | No gateway routing demonstrated | Provider updates can change internal Session/adapters | **REQUIRES_PROTECTED_MODIFICATION** for the reviewed provider request path |
| POV | Actual installed-source export dated 2026-11-08, 6.11.02; not a fresh current-device inventory | `TimeoutSession.request(*args, **kwargs)` would forward explicit Requests `proxies=` | Reviewed real provider callers do not supply it; no proxy setting found in exported Python/settings | A synthetic call to this class would establish helper capability only, not actual provider discovery/source-resolution routing | Provider and Requests dependency versions must be verified for any future integration | **REQUIRES_PROTECTED_MODIFICATION** to plumb policy through actual callers |
| Umbrella | Publisher reference 6.8.00; installed export does not contain HTTP helper | `client.request(proxy=None)` exists | Its proxy branch installs a **global** urllib opener and explicitly maps HTTP only | Not an acceptable isolated HTTPS attachment; not executed | Reference-only contract; global side effects and alternate Cloudflare clients | **REQUIRES_PROTECTED_MODIFICATION**; current branch is not safe under this scope |
| Otaku | Pinned publisher 5.3.4, commit `f6d542131c958ca63105e37bcf7cd414c9c55684`; installed equivalence unverified | `ui/client.request(proxy=None)` exists | Proxy branch uses global `install_opener()` and HTTP-only mapping | HTTPS route unproven; global opener forbidden | Provider may change opener/cookie handling | **REQUIRES_PROTECTED_MODIFICATION** |
| The Crew | Publisher dependency `script.module.thecrew` 3.2.28; installed version/source unverified | `client.request(..., verify=True, proxy=None)` builds a local opener with HTTP/HTTPS proxy mapping | Real provider callers still need explicit proxy plumbing | Reviewed helper disables hostname/certificate checks even with `verify=True`; unsuitable as a secure HTTPS proof | Reference-only helper and provider call sites can change independently | **REQUIRES_PROTECTED_MODIFICATION** for actual flow and safe HTTPS behavior; no security change made |
| Seren | Publisher 3.0.1 reference; installed equivalence unverified | Requests Session proxy capability | Reviewed TraktAPI/RealDebrid callers expose no provider proxy configuration contract | No gateway routing demonstrated; other scraper clients may differ | Separate provider and external scraper updates | **REQUIRES_PROTECTED_MODIFICATION** for reviewed flows; others **NOT_VERIFIED** |
| Kodi direct FFmpeg HTTP/HLS input | Six relevant SDK files hash-match both retained baseline77 and compiled78 source maps; see SOURCE-BINDINGS.json | **Existing per-item** `proxy.type=http`, `proxy.host`, `proxy.port`, `proxy.user`, `proxy.password` | `ListItem.setProperty()` → CFileItem → `CDVDInputStreamFFmpeg::GetProxy*()` → `CDVDDemuxFFmpeg::GetFFMpegOptionsFromInput()` → `http_proxy` | Pinned FFmpeg reference forwards proxy through HTTPS/TLS to CONNECT. HLS segments, keys, range seeking, certificate validation and real playback remain **NOT_VERIFIED** | Final provider-created playing item must retain properties; proxy conflicts and bypass rules require proof | **CAN_CONFIGURE_PROXY_SAFELY**, per-item capability only; provider-to-player attachment **NOT_VERIFIED** |
| Independent inputstream add-ons | Inspected dependency-cache adaptive21.5.25; not Fold identity | No explicit proxy property/settings contract established in inspected public metadata; generic config needs version-specific review | Only declared namespaced item properties are forwarded | Own sockets, manifests, segments and licenses cannot be assumed covered | Add-on-specific API/version changes | **NOT_VERIFIED** |
| Existing Kodi user proxy preferences | Protected Kodi settings source | `network.usehttpproxy`, server/type/port/credentials | Persistent shared Kodi preferences, not an Infinity-owned per-client attachment | Must remain owner-controlled; do not repurpose them for this experiment | Conflicting existing proxies require explicit handling | **NOT_APPLICABLE** as an Infinity-only gateway shortcut |

## The useful new finding

The previous review correctly found no FFmpeg TCP address-family option. This separate investigation
confirms that **proxy routing is a different supported route**: Kodi already passes per-input proxy properties
to FFmpeg. A FFmpeg library change is therefore not inherently required to route a caller-owned video item.

Raw URL options such as `|http_proxy=...` are ignored by Kodi's reviewed protocol-option allowlist;
the existing `proxy.*` item properties are the demonstrated source attachment point. This is source evidence,
not an executed Android playback test. Automatic, safe attachment to the provider's final playing item is unresolved.

FFmpeg 6.0.1's HTTP and TLS reference source still consults environment `no_proxy` even with an explicit
proxy option. Therefore a configured proxy alone is not proof of fail-closed routing. No environment variable
was modified. Kodi constructs the FFmpeg proxy URL by concatenating credentials, so any future experiment
must use unpredictable URL-safe credentials and check that logs do not expose them.

## Why no provider-plus-video prototype was run

The handoff permits an isolated prototype **if an actual supported route exists**, and permits a precise no-go
instead. The installed-provider attachment condition was not met. Calling plain Requests, inventing a new
provider caller, or manually invoking POV's class with `proxies=` would not demonstrate that existing provider
discovery/source resolution uses the gateway. The Crew helper's proxy parameter is a real capability, but
its reference source is not installed proof, and its HTTPS verification behavior fails this experiment's contract.

No gateway server, provider execution, synthetic playback, Android test, APK build, signing operation or
additional Fold test was started. This avoids producing a successful transport demonstration that does not
answer the requested provider-integration question. All network/stream/resource acceptance cases are **NOT RUN**.

## Exact boundary requiring a separately scoped decision

The handoff's hard stop says: “If a specific third-party provider requires modification to pass a proxy,
or a shared dependency/transport must be changed, report exact files/contract and request separate owner authorization.”

For the only reviewed installed HTTP implementation, POV6.11.02, that means explicit per-request proxy
plumbing at the existing callers of `resources/lib/modules/session.py` and the separate
`lib/pov/modules/client.py` Session. Changing provider singleton defaults is not a substitute. No such edit
is made here. Other providers need their own supported contract or separately authorized caller changes;
the single System Hub setting cannot safely force non-adopting clients through a proxy under current constraints.

Concrete installed-export examples are `resources/lib/indexers/tmdb_api.py: get_tmdb()` (request at line21)
and `resources/lib/indexers/trakt_api.py: call_trakt()` (line26). Their existing request keyword arguments
omit `proxies`. A narrowly authorized first provider experiment could target the metadata caller alone;
Trakt authentication changes are not needed or authorized for that experiment. This identifies a future
attachment contract, not permission to edit either file now.

If that boundary is later authorized, the smallest meaningful experiment is one named provider's real request
path plus one final playing item using the existing proxy properties. The gateway must authenticate before
opening upstream sockets, bind only loopback, preserve client TLS validation through opaque CONNECT,
respect existing owner proxies, snapshot mode per upstream session, bound buffers/tasks/DNS work, and
prove remote socket family independently of the localhost hop. A local relay cannot create IPv6 connectivity
where the current network/server lacks it; IPv6 Only must fail accurately in that case.

## Preservation and separate release blockers

Only research records are added. No production/provider/dependency code, APK, signing material, global proxy,
environment, urllib opener, Android/JVM/socket behavior, Cobra component, user setting or data was changed.
Original2103477 remains protected and original2103478/79 remain frozen. The previous pure-virtual SIGABRT
and matched-control talloc SIGSEGV remain unresolved release evidence; no startup test was repeated here.
Gateway feasibility provides no release clearance. Full Infinity performance work remains separate.

Review: GPT-6.1 examined proxy/client/security attachment; Astra examined isolation, proxy ownership,
inputstream limits and resource acceptance conditions. See evidence excerpts and SOURCE-BINDINGS.json.
