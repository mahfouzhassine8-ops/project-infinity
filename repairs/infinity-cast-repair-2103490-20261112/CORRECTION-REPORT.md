# Cast-only correction directly on signed 2103490

Baseline APK SHA-256: `63b1e380d9ff079e47793b0a182725561a9265cd63a0de288fc8357dfb1d7733`.
Matching signing source: `d311f22ddd30d3c7313a3f8f009c8f8a8e3325cd`.
The owner designated this as the development foundation, not an accepted release.
Neither 2103488 nor 2103486 is an APK input to this correction or its matching recovery.

## Evidence and attribution

The supplied private `VID_20261112_190202.mp4` (owner reference `22306.mp4`)
shows a video receiver receiving the movie title, remaining on its loading
presentation, and subsequently returning home. The phone eventually displays
“Returned to phone playback.” A touch near Cancel/Disconnect occurs before the
original connection-only deadline. Exposure prevents reliable reading of every
intermediate phone status. No movie frames playing on the TV are confirmed.

The video does not expose media URLs, container/codec, relay request/response
traces or receiver error codes. No exact-attempt Kodi/logcat log was supplied or
assumed. The exact cause of that physical failure remains unproven. In
particular, metadata appearing on the TV does not establish that media bytes
were fetched. The raw video and extracted frames are not published to GitHub.

## Confirmed defects and implemented corrections

| Production file | Exact correction |
|---|---|
| `InfinityCastSession.java` | Replace the still-active connection-only deadline during later phases with bounded, individually owned connect, source preparation, media-load, phone-handoff, receiver-seek and receiver-start phases. A load's window begins at dispatch, including a missing callback. Cancel/return/cleanup invalidates stale timers. Existing native cancellation/commit ownership remains intact. |
| `InfinityCastSession.java` | Consume the existing SDK's `onMediaError(MediaError)` callback; report its numeric detailed code when supplied, along with media-load/seek/play rejections and receiver player/idle transitions. No custom data, exception strings, source URLs, credentials or cookies are logged. A zero numeric diagnostic is the existing “no detailed code” sentinel when the SDK provides none. |
| `InfinityCastSession.java` | Preserve the failure explanation after returning successfully to the existing phone player. Log explicit return requests separately. Device connection and load acknowledgment still do not establish Now Casting; actual receiver PLAYING is required. |
| `InfinityCastSource.java` | Parse the bounded EBML header DocType rather than declaring every EBML file WebM. Genuine Matroska and WebM share the same initial magic. Malformed/unknown EBML and Matroska are no longer advertised as WebM. Valid WebM, MP4, HLS and DASH handling remains. |
| `InfinityCastRelay.java::probe()` | Verify WebM bytes rather than trusting only its HEAD MIME/hint. Refuse detected Matroska explicitly before receiver load, preserving local playback and providing the format limitation. No transcoder, DRM bypass or provider rewrite is added. |

The actual unmodified 2103490 controller was compiled with deterministic
SDK/native backends. A quick successful flow passed. A legitimate 12-second
connection, 5-second source preparation and 6-second load was aborted by the
old 20-second connection timer. The corrected controller completed the same
flow. This proves the timer defect; it does not attribute the filmed failure
to that timer.

Separately, actual FFmpeg-generated H.264/AAC Matroska and VP9/Opus WebM files
were both labeled `video/webm` by the original production parser. The corrected
parser distinguishes them. This proves the container defect; the owner's
stream container is unknown.

## Focused verification

- PASS: 15 actual-controller host assertions covering successful and delayed
  transfers, bounded missing connection/source/load/seek outcomes, cancellation,
  late load completion, receiver rejection, original phone restoration and
  retained failure reasons. SDK/native test backends are explicit; this is not
  real receiver or Kodi player execution.
- PASS: 38 actual progressive HTTP range/authentication/privacy/retirement checks.
- PASS: 57 actual adaptive HTTP and FFmpeg decoding/seeking assertions, retaining
  MPEG-TS/fMP4/separate-audio HLS, HLS AES-128 and DASH templates/timelines/ranges.
- PASS: genuine Matroska/WebM classification boundary probe.
- PASS: seven narrow metadata/registry guard cases, including rejection of an
  older APK as the declared 2103490-based input.
- PASS: Android API 36 component run `43335737427`, using the exact signed
  2103490 baseline. Actual progressive/HLS/DASH relay requests, private headers,
  origin-scoped response cookies, resource identity, five cleanup cycles and
  idle listener release passed. No real receiver or full Kodi JNI player is
  present in this component probe.
- REUSED: verified ARM64 engine from 2103490, SHA-256
  `3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75`.
  It is not rebuilt or replaced. Native source is unchanged.
- NOT TESTED: physical TV playback/codec compatibility, Fold appearance,
  physical phone return/tracking continuity, or post-Cast shutdown. These are
  the owner's single consolidated acceptance session.

## Preservation and packaging

The allowlist was frozen at `b8320fe5` before production edits. Exactly three
production files changed; all are existing Cast files. The prior adaptive
rewriter, native integration, compact dialog, clock channel, credential
isolation and source-bound native command implementation remain.

Complete staging `43336490642` starts with the authenticated signed 2103490 APK
and passed full member comparison:

- Candidate 2103492: only `classes6.dex`, typed `AndroidManifest.xml` versionCode,
  and `assets/experience-component-updates.properties` Infinity version differ.
  **7,772 payload members remain byte-identical; no additions or removals.**
- Forward recovery 2103493: restores 2103490 functionality directly from that
  same signed APK. Only the two APK/Infinity version metadata members differ;
  **7,773 members remain identical**. This does not restore an older feature set.

Both retain the exact 2103490 native binary, original five DEX, Command Center,
skin, Cobra, Movies/Infinity Movies, TV, Home Continue Watching, providers,
Search, tracking/resume/Watchlists, Python startup, all shutdown/persistence
protections and settings schemas. User profiles, accounts, databases and
settings are neither read nor modified by packaging. Old signed releases and
historical recovery artifacts remain unchanged.

Packaging tooling adds only the narrowly bound next-version registry operation,
Cast class ownership from the compiled component, input checks and selected
install/recovery verification. It uses the existing sole original signer and
unchanged signing implementation. The higher recovery's normalized shared
contract is identical to the candidate: it preserves that component identity
and does not request a new shared-runtime change.

## Honest limitations

The receiver must support the actual media codec/container. Matroska is not
WebM; this correction does not promise Matroska remuxing/transcoding. Unsupported
formats fail with a reason while retaining phone playback. DRM, unsupported
adaptive extensions and unavailable legitimate source authorization remain
unsupported. Existing supported HLS/DASH/progressive delivery is retained.

No shutdown code, deadline, SQLite rule, TMDb Helper code or provider is changed.
The owner-observed post-Cast shutdown failure is not attributed to a specific
writer from this recording. If it persists, the independent blocker must be
identified before any separately authorized shutdown change.

This is a functional Cast correction plus narrow failure reporting in one QA
candidate. It is not physical acceptance or an automatic baseline promotion.
