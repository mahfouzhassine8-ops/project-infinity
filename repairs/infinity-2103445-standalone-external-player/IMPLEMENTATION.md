# Isolated external video and Infinity Preview integration

The sole production foundation is signed 2103445, source
`6cf75639a46ec6b0c858ae32abc102450fdc0974`. No rejected 2103446 playback patch is
included. The existing Kodi player and every original Infinity class are retained.

## Android ownership and naming

Only Splash `onCreate` and `onNewIntent` gain an external-video route. The complete
original instructions remain on their existing non-video paths. The gateway
stages the latest request in one main-queue handoff, allowing already queued
Android intent transactions to be delivered before handing it to one nonexported Activity in `:externalplayer`, using
Android framework MediaPlayer. It does not load Kodi, use Cobra Media3, start an
experience service or access a user database. The native/shared executable,
resource table, icons, original player and shutdown code are unchanged.

The application's label and original launcher filter remain **Infinity**. The
existing Splash video VIEW filter and video SEND filter have **Infinity Preview**
as their handler label. Audio/image matching retains its original filter. There
is one public video gateway and no new public player entry or launcher icon.

Android `ResolveInfo.loadLabel` exposes the scoped video label. Applications that
instead show only the application label, ignore filter labels, or display the
raw Activity name control that presentation themselves. Renaming the technical
Splash class or globally changing the launcher's label is not used to compensate.
No MiXplorer-specific string replacement is present.

## Request and playback lifecycle

The private Activity keeps one current request, a fresh launch identity and
generation-checked decoder callbacks. URI, MIME, grants, ClipData and relevant
extras are forwarded. Content uses the granted descriptor; HTTP headers are
handled through the public media API without credential logging. Unsupported
protocols and unavailable sources report errors in the private player. Kodi-owned
content providers are rejected before contacting them, so they cannot wake Kodi
as a side effect of independent playback.

Loading is request-owned and ends on actual preparation, failure or cancellation.
The source preparation limit reports failure rather than fabricated readiness.
Provider/decoder operations run on one worker, not the Android UI thread. A single
position updater runs only during playback and is removed on pause/release.
Stop/Back finish only the private player. Backgrounding releases its decoder and
retains an in-memory position. Rotation/resize keeps the same Activity and player.
Natural completion offers replay without reusing the ending position.

The player exposes native-supported video, audio tracks and timed-text subtitles.
It does not promise arbitrary DRM, codec, cloud-link or image-subtitle support.
The private player has no new PiP or background playback service; existing
Infinity/Cobra PiP and background playback remain their owners' responsibility.

## Preservation and verification boundaries

The builder compares every original class and method with the exact component
bundles: 578 original Infinity classes unchanged; 151 original shell classes
unchanged, with only the two reviewed methods in Splash modified. New helper
classes are registered under their owners. Single-threaded DEX assembly makes
runtime-tested outputs reproducible byte-for-byte in the signing producer.

The release comparison permits exactly four APK payload changes: `classes.dex`,
`classes3.dex`, `AndroidManifest.xml`, and truthful component-version metadata.
It rejects every other added, removed or modified payload member. Cobra's entire
ZIP is copied byte-for-byte. The manifest exception is derived from the exact
signed 2103445 manifest; it cannot authorize shared executable or artwork changes.
The sole original signer is retained behind the existing source and ownership
gates. The accepted registry and recovery lock are unchanged.

Fourteen focused host request/state tests and six release-guard/negative-tamper
checks pass. The three new host checks cover queued latest-request ownership,
normal-launch replacement and independent/canceled gateway cleanup. Actual Android journey results and source binding are recorded
separately in final evidence; no incomplete journey is treated as a PASS. Early
QA failures and platform compatibility notices are retained. Physical Fold
acceptance and named third-party app/account checks are distinct from emulator
evidence. See `FOLD-ACCEPTANCE.md`.
