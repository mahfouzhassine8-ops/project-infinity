# Infinity network policy: actual attachment boundaries

Status: **partial native cURL implementation; universal enforcement not implemented; release blocked**.
Protected baseline: original-signed 2103477. Frozen evidence: signed 2103478/2103479.
This continuation changes no production source, provider, dependency, APK, account, or owner data.

## Setting to playback

1. The existing Infinity System Hub dispatches to `network_connections.open_connections()`.
   It persists `network_family` in Command Center's existing settings. It does not pass an HTTP client to providers.
2. `CCurlFile::ParseAndCorrectUrl()` reads that setting for new native HTTP/HTTPS operations.
   `InfinityNetworkFamily::Configure()` sets cURL's destination/proxy socket policy and bounded connection setup.
   Existing native diagnostics record requested and measured connected family, excluding URLs and credentials.
   They explicitly leave DNS answers and a remotely resolving proxy's origin family unmeasured.
3. Infinity Search's `_leased_directory()` invokes the provider's native `Files.GetDirectory(plugin://...)` route.
   The provider owns discovery and source-resolution networking in its interpreter. This RPC boundary has no
   supported argument for injecting an Infinity-owned Python Session or opener.
4. The provider's resulting playing item selects the actual input stream. In unchanged
   `DVDFactoryInputStream.cpp`, inputstream add-ons take priority; explicit FFmpeg inputs, many streaming
   protocols, `.m3u8`, and HLS MIME types select direct FFmpeg. Ordinary HTTP files can use Kodi CFile/VFS/cURL.
   A successful cURL MIME/redirect probe does **not** prove the subsequently selected stream uses cURL.

| Path | Actual policy coverage | Evidence and limit |
| --- | --- | --- |
| Native Kodi cURL HTTP/VFS, including artwork and ordinary HTTP-file playback | Implemented | Selected real Android family restrictions, redirects, TLS/error cases and HTTP playback advancement retained from 42774629373. Stop, cancellation, restart and recovery remain incomplete. |
| Provider-owned Python requests / urllib / urllib3 | Not enforced | Reviewed clients below construct and retain their own clients; no supported factory argument found in those call paths. |
| Direct FFmpeg HTTP/HLS/TCP | Not enforced | Pinned FFmpeg 6.0.1 TCP implementation uses `AF_UNSPEC`; its supported AVOptions do not include address family. |
| Inputstream networking delegated to Kodi VFS | Conditional, unverified per path | Only the actual delegated cURL operation is covered. |
| Inputstream add-on independent sockets | Not enforced | Separate transport owner; add-on-specific source and contract required. |
| Proxy origin resolved remotely | Unmeasured | Socket-family control of the proxy hop does not establish the origin family. |
| Android/system DNS query transport | Not controlled | Original resolver retained under the owner-approved contract. Historical five-second cleanup failure remains FAIL. |
| Cobra OkHttp / HttpURLConnection / Media3 | Outside scope, unchanged | Retained signed-member/source preservation; no JVM, Android, global socket or shared client mutation. |

## Provider source findings

These findings concern the named reviewed paths, not every socket a provider or external scraper may open.
Version equality alone is never source equivalence.

| Provider | Evidence identity | Relevant owner / function | Attachment boundary |
| --- | --- | --- | --- |
| WatchNixtoons2 | Reference 0.14.24; not current Fold source proof. `lib/network.py` SHA-256 `6cd59019db4fddeb86d83596cc163bd56176f181efcd3f21cf4313554b564d66` | Module-owned `requests.session()`, `rqs_get()`, `request_helper()`; provider can remount TLS adapters | No injected client/factory argument. Mutating the returned singleton would change provider-owned state. |
| POV | Actual installed export dated 2026-11-08, version 6.11.02; not a fresh current-Fold inventory. `resources/lib/modules/session.py` SHA-256 `4f9ece685c857d6f0f596c290dd78cf04b237ca852539fb65be3e9df845bfc2c`; `lib/pov/modules/client.py` SHA-256 `943248a9e3de0350ba12fe409d17ea23d07fb875c5a9ed6e2bc88b1afb8e54b7` | Provider-owned PoolManager and TimeoutSession instances, including separate scraper client | No injected factory/client argument in inspected constructors. |
| Umbrella | Publisher reference 6.8.00; installed export does not include HTTP clients. Publisher ZIP SHA-256 `c803b88e0834871c6210d5d2c48f7e78e31949131cee0c3b2fdff4e04e75e0b5` | `modules/client.request()` builds urllib openers; `modules/trakt.py` owns a separate requests Session | No injected opener/client factory in inspected path. Installed HTTP-source equivalence unproven. |
| The Crew | Publisher dependency `script.module.thecrew` 3.2.28; ZIP SHA-256 `c2b7ac78303575c167e7fd1aacfb3b41bdfebb8b05c9f598bedfff78166c3149` | `HTTPClient.get_session(api_type='default', pool_connections=20, pool_maxsize=20, max_retries=3)` caches internally created Session/adapters; `client.request()` and `indexers/movies.py: Movies.__init__()` own additional clients | Pool sizes/retries are arguments, client/adapter factories are not. Remounting the cached returned Session changes provider state. Installed version/source unverified. |
| Otaku | Publisher reference 5.3.4, Goldenfreddy0703/Otaku commit `f6d542131c958ca63105e37bcf7cd414c9c55684`; `ui/client.py` Git blob `0e34df10df7f88bef86edbdc8c0cdcf7958ec60d` | `request(..., use_session=False, tls_version=None)` builds urllib openers and manages provider cookie/opener caches | No injected opener/client argument. Installed version/source unverified. |
| Seren | Publisher 3.0.1, nixgates/plugin.video.seren tree `b4f4b63bf59b38b93bd565a8503e121f64c91e30` | `TraktAPI` and `RealDebrid` create cached requests Sessions/adapters internally | Constructors accept no factory. Existing provider requests monkeypatch is for its cancellation, not an authorized Infinity hook. Installed version/source unverified. |

Publisher reference URLs: [Crew distribution](https://github.com/thecrewwh/zips),
[Otaku pinned source](https://github.com/Goldenfreddy0703/Otaku/tree/f6d542131c958ca63105e37bcf7cd414c9c55684),
[Seren publisher](https://github.com/nixgates/plugin.video.seren),
[FFmpeg TCP 6.0.1](https://github.com/FFmpeg/FFmpeg/blob/n6.0.1/libavformat/tcp.c),
[FFmpeg HTTP 6.0.1](https://github.com/FFmpeg/FFmpeg/blob/n6.0.1/libavformat/http.c).
FFmpeg TCP Git blob: `a11ccbb913aa69edac135ddd63316dc9a883958c`;
HTTP blob: `7bce8215354acf845dd6c78556b3332744504647`.
The local Kodi dependency pin is 6.0.1, archive SHA-512
`945e34840092dc0fd3824eb1af2be79868af2afb4fe13159b19a9bcfc464cc4d53243c13ff065199290e9393ddbf4b1c5c8abccf83a31a31d6c7490e499fd1fc`.
The upstream files are reference source, not a new independent verification of the previously built dependency archive.

## Why an unused adapter is not a correction

Bundled urllib3 2.2.3 does not accept an arbitrary pool `family=` option. An adapter can configure
`source_address` for a Session Infinity owns, but wildcard binding is not DNS-family filtering, does not
control a remotely resolving proxy's origin, and supplies no attachment point to a different interpreter's
provider-owned singleton. No direct requests/urllib3/urlopen networking caller was found in the protected
Command Center sources. An uncalled adapter would therefore not change the actual connection chain.

Universal enforcement needs a legitimate provider-owned client/factory contract, or specific authorization
to change the affected protected provider/dependency. Direct FFmpeg sockets need a separately authorized
shared-dependency correction because no supported family option exists at this pin. Inputstreams need
their individual supported contract. Those individual changes are stopped under the owner's explicit
scope boundary; none has been implemented through a global socket patch or invented option.

## Actual Fold failure remains unclassified

Owner reports 2103478 / Command Center 0.3.5.76 on Galaxy Fold8 Ultra / Android17, regular Wi-Fi,
with unsuccessful playback under both strict modes. Provider, title and exact error were not recorded.
Blade Queen is an example only. The named `Infinity-Diagnostics-20261110-034510.zip` is described by the owner
as version evidence without playback/network traces and may predate the attempts; it was not located in this workspace.
No DNS, TCP, TLS, authentication, resolver, decoder or transport cause can be assigned from that evidence.
No repeated playback attempt was selected or run in this continuation.
