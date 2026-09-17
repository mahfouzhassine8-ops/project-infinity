# Cobra 2103158 — Health, channel playback and presentation candidate

## Exact baseline and scope

This candidate branches from user-locked 2103157 at commit
`7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98`, passing run 35200244871.
The original locked branch is not moved or edited. No merge, release or new lock
is implied by the candidate build. Installation was confirmed by the user for
2103157; physical acceptance for this new build remains pending.

Locked APK SHA-256:
`3e8cda1e8587080802dca1129b5e05c12f881f69efae8f5221103c67948658e3`.
Locked Activity SHA-256:
`b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943`.
Permanent certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Matching UI remains the exact 1.3.9 ZIP. This is an Android presentation/runtime
update, not a Kodi engine rebuild or replacement skin/Cinema-mode package.

## Implemented features

### Drawer -> View

The drawer contains one View row with the current mode. Only activating it opens
Mobile, TV Grid, Compact, Cards and Focus. Their native vector previews, selected
state, descriptions, touch targets and keyboard/D-pad focus surfaces are separate
from the actual playback/guide layouts. Choosing a mode uses the existing
`cobraSwitchMode` contract. Opening the chooser does not dispose the live player.

Native font/vector rendering replaces no bitmap artwork. The drawer gets an
original Cobra mark, the COBRA wordmark, and "An Infinity experience" attribution.
Health/settings vector icons and new wrap-height detail rows avoid fixed-height
text clipping. New sheets use existing Light/Dark/OLED palette contracts; the
OLED sheet is opaque black. The existing five renderer classes, geometry policy,
first-layout repair and Follow System dark-variant preference are preserved.
This is a scoped branding/presentation pass, not a claim every legacy screen has
passed final visual acceptance. The inherited very-narrow large-text EPG ruler
crowding remains an explicit final-polish acceptance item.

### Cobra Health Center

Available from the drawer, Cobra Settings, and player settings. Opening it keeps
the existing guide/player underneath rather than navigating away and stopping it.
Observations are local: player state, video format, actual reported decoder-frame
and audio-output counts, dropped frames, first-frame timing, buffering duration,
last media-load bytes/duration/errors, view bounds/surface availability, retained
errors and automatic recovery status/budgets. The counter sample age is reported.

The source section shows enabled state, loaded channels, EPG request state,
last successful fetch, cached guide keys and partial-data status. Refresh is an
explicit action and retains existing EPG recovery/cache behavior. No automatic
provider scan, extra playback connection or network speed test is introduced.
Player count means this app's player objects, NOT provider-wide connection use.
A cache or READY player never becomes a fabricated "everything healthy" verdict.
Unknown observations remain unknown. The existing redacted save-as diagnostics
ZIP contains the additional session/recovery evidence.

### Per-channel playback

Channel actions or Player settings -> Channel playback. Preferences are keyed by
a full SHA-256 of length-prefixed profile, source and channel identifiers, so
identically numbered channels on different sources/profiles do not collide.
Stored data excludes provider URLs, account credentials and transient track IDs.
The namespace is bounded to 12,000 explicitly saved channel profiles.

Choices: inherited or explicit aspect including bounded custom scale, preferred
audio language, subtitles (inherit/off/automatic/language), configured fallback
allow/primary-only, and automatic-recovery inherit/on/off. Missing languages are
preferences, not promises of tracks supplied by the provider. Media3 retains
track matching; transient stream indexes are not persisted. Display-only or
recovery-only changes do not clear a user's manual track selection.

Reset removes ONLY the selected profile/source/channel preference key. No source,
favorite, recording, account or other settings are deleted. An obsolete settings
sheet cannot write into a newly selected profile. Fullscreen inherited aspect
uses the existing global choice; previews retain Best Fit unless that channel
has an explicit override. Multi-View audio ownership is not changed.

A missing caption presentation path was found while implementing subtitle
preferences. An app-owned, noninteractive overlay now consumes Media3 CueGroup
callbacks, supports basic text and bitmap cues, and clears immediately when the
channel selects Off. It never replaces Media3's TextureView/SurfaceTexture
listeners. It bounds cue count/text, but complete broadcast-caption styling,
vertical writing, accessibility preferences and hardware video/caption alignment
still require device acceptance; this is not a claim of full subtitle conformance.

### Guarded automatic video-surface recovery

A read-only application-thread observer samples counters and SurfaceTexture
presentation timestamps once per second only while the Activity is foreground.
It requires current binding/profile identity, a visible attached available
adequately sized TextureView, window focus, READY and actively requested playing
state, video plus audio formats, enabled video track and no playback error or
suppression. Paused, buffering, audio-only, background, PiP and obscuring Cobra
modal/drawer states do not qualify. Known sub-1-fps streams are excluded.

Policy: at least 20 seconds of eligibility, at least 12 seconds without video
progress, and recent advancing audio-output buffers AND playback position.
Alternatively a previously progressing surface timestamp can stall despite
advancing decoded output. A never-changing/unknown timestamp alone is not proof
of a bad surface. Seeks, track/decoder changes, lifecycle gaps and clock/counter
resets restart the observation grace period, not the attempt budget.

A qualifying attempt clears and reassigns ONLY the same TextureView on the same
ExoPlayer. It does not restart/recreate a player, seek, change URL, change volume,
choose a decoder, acquire another provider connection, or overwrite the surface
listener. At most TWO attempts per player session, at least 60 seconds apart;
the attempt is consumed before the external call, including when it fails.
Subsequent first-frame callbacks and exhausted budgets are explicit evidence.
The default is On with an off switch and independent channel overrides.

The inherited buffering watchdog previously had no session retry cap. Its
existing retry mechanism is retained but limited to two attempts per binding,
so it cannot undermine the new no-restart-loop safeguards. The configured URL
fallback remains separate, single-use existing behavior and honors Primary only
both before scheduling and at delayed delivery. No new fallback URL is invented.

These signals detect a class of missing/stalled output, not pixel correctness.
A black frame intentionally supplied by a broadcaster is not detected as a broken
picture merely because it is black. Decoder counters are not proof a physical GPU
presented the correct image; SurfaceTexture timestamps are supplementary evidence.
Unrecoverable device/decoder failures remain visible diagnostics, not a promise
that two reattachments will always repair playback.

## Evidence and gates

Locally executed before the initial push:
- 1,905 assertions against the production recovery/preference policy classes.
- 32 source-integration guards, exact baseline preimage rejection and preservation
  of 375 unrelated Activity methods, all five renderers and the guide-size fix.
- 66 full-guide and 9 short-guide production-algorithm cases.
- 42,339 inherited algorithm assertions and 12,171 unchanged geometry assertions.

CI reconstructs exact 2103157, verifies every original source receipt entry,
preserves rollback before mutation, reruns the prior diagnostic tests and all
new policy/EPG/inherited tests, and compiles the complete Android shell against
its existing Media3 1.7.1 dependencies. It keeps original resource/JNI mapping,
permanent signer and byte-for-byte native/asset gates. No test dependency or test
class may enter the separately staged release APK.

Upload requires all FOUR unchanged locked navigation/rendering cases and SEVEN
new native-graphics Android test cases to pass, without skipped tests. New cases
exercise real drawer/chooser/health/preferences views, persistence and scoped
reset, caption drawing, retained error export, disposal and the actual recovery
adapter using an explicitly declared ExoPlayer double. Synthetic guide data,
cues, timestamps and player doubles are NOT real-provider or hardware decoding
acceptance. The archive contains XML, logs and screenshots, including all six
original navigation screenshots plus the new presentation evidence.

The pipeline never treats test startup, a generated screenshot, an APK existing,
or a green host-only test as a completed Android gate. Acceptance.json records
the actual completed automated gates and retains all device/official flags false.

## Required before "official"

Install the signed candidate over Infinity without uninstalling/clearing data.
Verify Drawer -> View and every mode with touch/D-pad, Light/Dark/System OLED,
Fold/cover/rotation and larger text. Confirm repeated Live TV -> Movies/Shows ->
Live TV returns with picture/audio and no regression to the 1x1 host.

Open Health Center during real playback; compare observed decoder/counter/load
state to the device, export a ZIP to a chosen location, and review redaction.
Test language/display/subtitle choices on channels that actually offer them,
provider/profile isolation across restart, scoped reset and Multi-View audio.
Test long healthy playback, intentional pauses, muted Multi-View, buffering,
network loss, PiP/background, device surface interruption and limited recovery.
Ensure no healthy-stream interruptions, surprise URL switches or infinite loops.

Run an adversarial review of source/receipts, frozen rollback, signing/native
integrity and all five views. Final branding/caption/accessibility and physical
recovery acceptance remain open until supported by device evidence. Neither a
thinking-level label nor this candidate's compilation makes it official.

## Rollback

`Cobra-2103157-Complete-Rollback-For-2103158` contains the exact locked APK/UI,
repository archive, generated Android source, receipts and hash ledger. Device
userdata is NOT in CI. Android may reject downgrading versionCode: do not uninstall
or clear data to work around that. Preserve a separate user-data backup and use a
reviewed rollback/update path. All earlier locked references remain unchanged.

## Primary API references used in review

- https://developer.android.com/media/media3/exoplayer/track-selection
- https://developer.android.com/reference/androidx/media3/exoplayer/DecoderCounters
- https://developer.android.com/reference/android/graphics/SurfaceTexture
- https://developer.android.com/reference/androidx/media3/exoplayer/ExoPlayer
- https://developer.android.com/reference/androidx/media3/exoplayer/video/VideoFrameMetadataListener

Frame-metadata callbacks are "about to render" and not used as proof of a visible
frame. This implementation does not replace an existing frame-metadata listener.
