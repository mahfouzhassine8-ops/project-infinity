# Cobra 2103158 — Health Center, channel playback, guarded surface recovery and UI convergence

## Release decision

**TEST CANDIDATE. HOLD official release / new lock until physical-device acceptance.**
Source and host tests are not hardware video or provider acceptance. The build
workflow may upload an installable test candidate only after real Android
compilation, permanent signing, native/assets/resource comparisons, all twelve
Android tests without skips, and the inherited regression suites pass.
No release, merge, installation, original-branch mutation or automatic lock occurs.

## Immutable baseline and rollback

Build only from locked 2103157, commit
`7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98`, passing run `35200244871`.
APK SHA-256: `3e8cda1e8587080802dca1129b5e05c12f881f69efae8f5221103c67948658e3`.
Generated Activity SHA-256:
`b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943`.
Permanent certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
The drawer selector from `f806926ae0e31a31892cd6c38f62b6de97f5751d` is included.

Before applying the new delta, CI reconstructs exact 2103157 using its immutable
recipe and compares every generated source receipt entry against the passing
artifact. It preserves the exact APK, matching UI 1.3.9, source receipts, full
repository, generated Android source, protected native-source patch and retained
2103155/2103156 rollback. Device userdata is NOT backed up by CI. Do not uninstall,
clear app data, or force a downgrade; Android can reject a lower versionCode.
The locked branch and all historical build recipes remain untouched.

## 1. Cobra Health Center

Available directly from the drawer and Cobra Settings. Opening it from Live does
not dispose the preview or replace the guide. It reports actual bound-player
state, requested/actual playback, suppression, exposed video format, surface
attachment/availability/size, recovery attempts and observation state, EPG request
and snapshot counts, Multi-View audio owner index, recording/PiP and available
system memory. No player or unavailable data is explicitly identified; neither
READY nor an existing cache is described as proof of healthy playback.

Actions: refresh observations, refresh the current guide through the unchanged
safe refresh path, edit current-channel preferences, toggle guarded recovery,
view a detailed fresh snapshot, and open the existing Crash & Diagnostics ZIP
export. No cache deletion, automatic upload, credential export, player restart or
invented crash-free status is introduced. The existing bounded/redacted exporter
and its native/ANR privacy exclusions are unchanged.

## 2. Per-channel playback preferences

A separate schema-versioned SharedPreferences file stores display mode, custom
width/height, audio language/format identity/role, subtitle policy and language/
format identity/role, and permission for surface recovery. Keys are SHA-256 of
length-prefixed profile + source + channel identifiers. No raw URL, channel name,
provider credentials, or track index is persisted. Same names on other sources
and other profiles remain independent. Stale-profile callbacks cannot write.

Audio/subtitle choices resolve against the currently supported format groups;
reordered track indices do not select the wrong saved track. An unavailable
choice falls back via Media3 language/default selection. Reconciliation is guarded
against callback recursion; errors are reported rather than crashing playback.
VOD remains session-specific. Existing global display defaults are read as a
fallback, never overwritten by the new live-channel settings. Live position,
play/pause intent, volume and Multi-View audio ownership remain session-owned;
loading preferences does not resurrect playback or override the audio owner.

The new store is capped at 1,024 channel records, with an explicit capacity
message rather than silent data eviction. Malformed/unknown-schema records fall
back safely. Reset requires a confirmation and removes only the selected channel
for the captured current profile. Custom dimensions use an explicit Apply size
button for both touch and D-pad; Back cancels an unsaved adjustment.

## 3. Automatic video-surface recovery

Uses the existing foreground presentation tick, with no extra permanent timer,
no replacement SurfaceTextureListener and no alternate playback owner. It reads
the assigned TextureView's acquired-buffer timestamp and playback position, not
pixel brightness or the first-frame callback alone. It waits at least 12 seconds
without a new frame and requires advancing playback before considering recovery.
Black scenes with continuing frames are not classified as failure.

Eligibility requires the current live binding, resumed foreground, non-PiP,
non-background state, explicit global/per-channel permission, attached/shown/
available nonzero-sized texture, selected video track, READY + play requested,
no suppression and no player error. Paused, buffering, audio-only, ended,
detached, hidden, unavailable and obsolete sessions do not trigger rebinds.
Surface/track/lifecycle transitions restart the observation grace, not the budget.

Only the same player's assigned TextureView is cleared and rebound. The new
recovery code NEVER calls prepare, play, setMediaItem, stop, release, setVolume,
setAudioAttributes, or an engine/decoder restart. No healthy peer is restarted.
Limit: two attempts per binding lifetime, at least 30 seconds apart, plus four
attempts across this Activity in five minutes. A failed attempt consumes its
budget before the operation; successful frames and toggling recovery do not
replenish the per-session budget. Probe/rebind failures are bounded diagnostics,
not restart loops. Persistent trouble is visible in Health Center/export.

This is deliberately conservative: it cannot promise to fix every decoder,
provider, DRM or hardware defect. Existing buffering watchdog and configured URL
fallback policy are not replaced by this surface-only feature.

## 4. Branding and UI convergence

Cobra-facing Settings labels use consistent names and casing. The Health Center,
channel settings and existing View chooser share the Cobra sheet/focus system.
Long sheet labels and drawer destinations get content height for larger text.
OLED sheets and mode panel/rail surfaces use true black; Light and Dark remain
independent and follow the existing system-dark preference. All five view
renderers and geometry, navigation generations, EPG, player transfer, lock,
recording, Infinity handoff, package identity, signer, native engine and Cinema/
Infinity skin remain protected. Legitimate Infinity handoff and Kodi log labels
are intentionally retained; internal class/action/storage names are not rebranded.

Drawer: one View row -> original illustrated Mobile / TV Grid / Compact / Cards /
Focus chooser. The existing selected marking, cancel and switch callback remain.
Matching UI ZIP stays exact 1.3.9; these runtime features require the candidate APK,
not a pretend theme-only installation or native rebuild.

## 5. Adversarial audit and evidence boundaries

Local exact-source tests execute the production recovery inspector and policy
with disclosed view/player doubles: 152 assertions, all eligibility gates,
healthy-frame noninterference, session/global limits, failure consumption, stale
sessions, nonadvancing playback, invalid preferences and scoped-key isolation.
The patch reverses every enumerated changed member and appended byte, requiring
exact recovery of the original whole Activity. Unlisted mutation is rejected.
Unknown or already-patched preimages are refused. Protected view/EPG/layout/
provider/handoff methods are independently compared byte for byte.

Inherited local suites: 66 full-guide cases, 9 short-guide cases, 42,339 production
algorithm assertions, 12,171 layout assertions and 26 diagnostic runtime checks.
The EPG harness gets only a disclosed no-op for the new presentation observer;
its assertions are unchanged. Recovery itself is separately executed, not stubbed
in the recovery tests. These counts describe host tests, not live-provider tests.

CI compiles actual Android/Media3 APIs, retains all four original 2103157 Android
cases unchanged, and adds eight tests for View/Health navigation, preference
profile/source/channel isolation and reload, confirmed reset, corrupt/capacity
handling, reordered real Media3 track format objects, custom-size save/cancel,
Light/Dark/OLED with large text, and real Media3 parameter/peer-volume isolation.
The tests use fixture guide data and no real network stream/physical decoding.
Twelve discovered/executed tests with no failures/errors/skips and at least ten
rendered screenshots are required before uploading a test candidate. Production
DEX must include all features and exclude test classes. Every native, asset and
resource entry must match locked 2103157; the permanent certificate must match.

### Remaining physical acceptance before official / lock

Install as a normal update over 2103157 without uninstalling or clearing data.
Verify actual video/audio across all five views, channel zapping, guide->fullscreen
and back, drawer Movies/Shows/Settings return, long sessions, Fold/orientation,
background/resume and PiP. Verify genuine track choices persist after process
relaunch and do not leak across providers/profiles or VOD. Confirm touch/D-pad
focus, large text and all palettes, including the new dialogs.

Use controllable test streams to distinguish a real lost video surface from
normal buffering, pause, audio-only content and black scenes. Check the recovery
limits, a failed rebind, same-player/position/audio ownership and one affected
Multi-View tile without disturbing its peers. Export while the issue is present;
check diagnostic accuracy/redaction and storage/provider errors on the device.
Verify the matched rollback package and a reviewed data-preserving restore path.
Physical success and final user visual approval must be recorded for the exact
APK hash before any official designation/new lock. CI success alone is not enough.
