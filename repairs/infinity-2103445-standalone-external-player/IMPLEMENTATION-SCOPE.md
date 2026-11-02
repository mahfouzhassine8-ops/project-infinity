# External video player from signed 2103445

The user authorized the complete master brief on this branch. Signed source
`6cf75639a46ec6b0c858ae32abc102450fdc0974` and its signed APK are the only
production inputs. No 2103446 code is incorporated.

## Selected implementation and tests (recorded before execution)

- Audit the actual manifest, Splash DEX and four signed component bundles.
- Add an early, video-only Splash route, before ContainerUpgrade, persistence
  entry, chooser bootstrap and Kodi preparation. Preserve the original instruction
  sequence for every request not selected by this route.
- Add one private Activity in `:externalplayer`, with a distinct private task
  affinity and no exported intent filter. Reuse the existing visible Splash entry.
- Use Android framework MediaPlayer and its public track/audio APIs. There is no
  Media3/Cobra dependency, native library loading, Kodi JNI, shared controller,
  database access, service, persistent playback state or background playback.
- Add only the private Activity manifest registration and a video-only SEND
  filter on Splash. Preserve existing filters and normal chooser behavior.
- Select host request/permission/state/preservation tests; actual Android
  decoding, changing video/audio samples, real touch controls, seek, track menu,
  cold/warm/rapid requests, content grants/revocation, errors, natural end,
  Stop/Back/source return, foreground/background, resize/rotation and process
  isolation. Check protected component and class/method equality. No shutdown
  scenario or unrelated feature suite is selected.

## Baseline findings

The actual signed APK has no custom Application class. All three Kodi content
providers are explicitly assigned to `:kodi`. Splash is a singleInstance
Activity in the default process. Its constructor only initializes fields and an
idle Handler. onCreate calls ContainerUpgrade and ShellJavaPersistence before
starting the chooser bootstrap; onNewIntent can call startXBMC. These two
methods are the required narrow interception points. Existing pause/resume/
destroy cleanup tolerates absent bootstrap/watch objects and is retained.

The Android framework player requires none of the existing Cobra-owned Media3
classes. Original INFINITY classes, including Main and Main$3, remain identical.
New player classes are INFINITY-owned; the routing helper is CHOOSER_SHELL-owned;
only the authorized manifest additions belong to MINIMAL_ANDROID_CONTRACT.

## Behavior boundaries

Compatible VIEW requests supply a video MIME type, a recognized streaming MIME,
or a recognized video filename with absent/octet-stream MIME. SEND requires one
video stream URI (no SEND_MULTIPLE). No audio/image/share default is captured.
Provider grants and ClipData are forwarded; access uses ContentResolver, never
a guessed filesystem path. Opaque explicitly MIME-less content cannot be
classified safely and retains the existing route. Android's implicit resolver
normally resolves a content provider's MIME before selecting Splash.

Unsupported protocols, inaccessible grants, non-video media and engine errors
produce a local error with Retry/Close. No fallback wakes Kodi. Android framework
codec/container/stream support applies; DRM and arbitrary cloud webpage links
are not promised. Text subtitle tracks supported by MediaPlayer are offered;
unsupported subtitle encodings are not claimed. No external-player PiP is added.

Back/Stop close only this Activity. A singleTask private affinity prevents parallel
external Activities. Each accepted launch gets a fresh request identity; each
MediaPlayer callback is checked against its current request. Lifecycle pause
stops playback, releases audio focus and retains an in-memory position; no
service or notification keeps decoding in the background.

Physical Samsung source applications, grants and Fold acceptance remain the
user's final checks. Host tests do not prove decoding; Android fixture results
will be reported separately.

## Selected final release protocol checks

Run `tests/test_release447.py` for exact protected-source guard preservation,
sole signer ordering, narrow manifest exception and negative tamper rejection,
unchanged original signer/assembler, and exact APK member allowlist rejection.
The existing eleven request/state checks are retained; no unrelated runtime or
shutdown checks are added. The next selected Android run corrects the observed
two-notice setup accounting, verifies deterministic DEX output, and adds real
audio-track and timed-text selection on the same synthetic granted MP4.
