# Cast-only correction from original-signed 2103488

Development APK: **2103488**, SHA-256
`4217b217bca06084121572bbde71164abe67d05ef49741c78d4f83c5c5d4a566`.
Protected functional recovery: **2103486**, SHA-256
`550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197`.
Original certificate:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

## Confirmed source defects and corrections

| Cast source | Correction and preservation boundary |
|---|---|
| `InfinityCastSource.java` | Recognize HLS/DASH and other supported video MIME types; sniff opaque streams. Accept explicitly declared current-item manifest/stream headers through the existing strict header parser. Reject declared DRM, unsupported transport overrides and injected headers. |
| `InfinityCastAdaptive.java` (new) | Rewrite HLS playlists/renditions/init/key/segment URLs and DASH representation/segment templates, timelines, lists and base URLs into registered local capabilities. Resolve relative URLs on the sender. Reject DRM, external XML, unsupported manifest extensions and unbounded manifests/resources. |
| `InfinityCastRelay.java` | Deliver those registered assets through the existing private HTTP client, with byte ranges and authenticated source requests. Keep credentials, cookies, source URLs and cross-origin redirect credentials away from the receiver. Close listener, clients and upstream calls on cancellation. Permit legitimate GET media when HEAD is rejected. Maintain source-issued cookies in bounded per-transfer RAM with origin/path/secure/expiry checks; no global or persisted cookie store. |
| `InfinityCastSession.java` | Auto-transfer on explicit video-receiver selection; distinguish media loading from actual receiver PLAYING. Remove the optional recorder acknowledgment as a prerequisite for playback, while permitting remote progress only after its existing identity acknowledgment. Reconcile return with actual native phone state and release resources after failed/end/disconnect paths. Close Controls keeps an active transfer/session. |
| `InfinityCastGateway.java` | Run one cleanup continuation after the actual terminal native result. A committed operation is reconciled rather than represented as undone. |
| `InfinityCastRpc.java` | Retain read-only theme queries; remove the Python-script channel-registration path from Cast cleanup. |
| `InfinityCastDialog.java` | Compact bounded-width/content-height dialog, video receivers only, no standalone Play before transfer, hidden inactive timeline/transports, clear status and separate Close Controls/Disconnect. Existing skin entry points are unchanged. |
| `InfinityCastDiagnostics.java` (new) | Credential-safe outcome/stage/status codes. No provider URL, title, cookie, sensitive header or exception message is logged. |
| `InfinityCastNative.cpp` | Cast-only bounded header/DRM capture, item-bound RAM channel registration, pure RAM release even after the original video stops, and terminal error results for retired/oversized native outcomes. Use Kodi's actual `SetProperty` API. No persistence owner, file write, shutdown hook or protected admission change is added. |

The old implementation explicitly refused HLS/DASH, required an optional
observer acknowledgment before transfer, displayed Connected before confirmed
receiver playback, retained state after some return/end failures, and could
return an ambiguous pending native result after a terminal outcome. These are
source-supported defects. They do **not** establish the exact cause of every
owner-reported receiver or shutdown failure.

## Evidence and remaining acceptance

- **PASS:** 38 progressive/authentication/privacy/cancellation HTTP checks.
- **PASS:** 57 authenticated adaptive HTTP checks, including actual FFmpeg
  decoding/seeking of MPEG-TS HLS, fMP4 HLS, separate audio/video HLS renditions,
  HLS AES-128, DASH templates/timelines and single-file byte-range lists.
- **PASS:** Android API 36 component run **43321698528**: progressive byte ranges, HLS/DASH manifest and
  segment delivery, property headers, origin-scoped response cookies, resource
  isolation, released idle callbacks and five repeated
  failed-transfer cleanup cycles. Its disposable probe has no real Kodi JNI
  player or real receiver; it does not claim phone-return/TV playback acceptance.
- **PASS:** focused actual Cast C++ translation-unit tests using mocked
  player/GUI/message backends and six focused release-guard cases.
- **PASS:** full Android ARM64 compile/link run **43314732573**, retaining all
  71,213 protected native exports and the same 11 library dependencies. Current
  Cast overlay hashes match the compiled artifact. Final packaging/signing is
  recorded separately. Run **43307594150** exposed an actual Kodi API
  mismatch (`CGUIWindow::ClearProperty`); the source was corrected to the
  supported `SetProperty` call. That failed run is retained as failure evidence.
- **NOT RUN:** real receiver media transfer, physical Fold UI behavior and
  post-Cast normal shutdown. These are the one owner acceptance session.

The owner reports normal startup-to-exit succeeded in 2.659 seconds and exit
after a failed Cast attempt reached its checkpoint deadline. The two named
November 12 diagnostic ZIPs are not exposed in this workspace or the accessible
private Pages. Their exact pending operations were not invented. Cast cleanup
was corrected within its ownership boundary; the shutdown engine, deadlines
and persistence protections remain unchanged. Any independently demonstrated
remaining shutdown blocker requires separate authorization.

## Exact release boundary

[SCOPE.json](SCOPE.json) froze the Cast production allowlist before editing.
Candidate packaging starts with the exact signed **2103488** APK and permits
only four existing payload members to change:

1. `classes6.dex` — already isolated Cast component only.
2. `lib/arm64-v8a/libkodi.so` — only the Cast source changes above, with all other
   native source hashes and existing ABI/dependencies preserved.
3. `AndroidManifest.xml` — typed versionCode only.
4. `assets/experience-component-updates.properties` — Infinity version only.

There are no candidate additions/removals. The original five DEX, Command Center
0.3.5.83, skin 1.0.5.274, both Cast entry-point locations, all Movies/Home/TV code,
Search/provider implementations and Cobra 2103445 remain byte-identical.
All old class owners remain unchanged; only the Adaptive/Diagnostics source roots and the exact private Cast SDK
root `castdeps/hg` from the compiled isolated component are added to the existing ownership policy.

The matching higher-version recovery is derived from the verified signed
**2103489** recovery to protected **2103486** functionality. It retains the
already signed CC84 and skin275 recovery metadata, preventing a module downgrade.
Only its APK/Infinity version labels advance again. This deliberate recovery
restores protected functionality; it is not the normal Cast feature installer.
Neither accepted baseline pointer nor any existing signed artifact is modified.

The unchanged original assembler and established workflow **397702717** perform
signing after source/member/owner checks. Physical acceptance is never inferred
from compilation, component tests, signing or PackageManager installation.

Supported sources still depend on receiver codecs, available legitimate source
credentials and a supported direct local IPv4 route. DRM/SAMPLE-AES, unsupported
HLS variables/content steering, unavailable authentication or unsupported receiver
formats/routes fail without claiming successful movie playback. No provider
implementation, global network policy, tracker or database is replaced.

See [FOLD-QA.md](FOLD-QA.md) for the single combined acceptance session.
