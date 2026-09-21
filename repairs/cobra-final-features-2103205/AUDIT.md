# Cobra 2103205 — Final Features RC1

## Release boundary

This is an Android/Java extension of locked build 2103204, not a new player or a replacement UI. The approved feature scope is in SCOPE.md. Command Palette and a dedicated Fold Continuity system are excluded. This candidate must not be described as a device-accepted or locked release.

The complete 2103204 product rollback was saved before runtime changes. It contains the signed APK, generated source, source recipes, evidence and restore instructions. Its SHA-256 is `7188f02e0ab7ebd0306f3a0c5f4a5b6c4e4bf1c509827bbeee94ab8c7808a9d8`. Device-private settings, provider credentials and recordings are not part of that backup; do not uninstall or clear application data to test this update.

## Implemented scope

| Addition | Runtime boundary and protection |
| --- | --- |
| Ambient Mode | Off, Subtle and Immersive use bounded contextual source tint on existing backgrounds and UI accents. Installed artwork remains the original layer beneath a transparent gradient; explicit theme colors/styles remain authoritative. Off restores the original drawable. No video sampling, filtering or recoloring. |
| Channel Quick Peek | Separate muted disposable player, Now/Next, Play, Favorite and retained channel actions. Main player, surfaces, timeshift and recents are not used for preview. |
| Smart Return | Opt-in bounded per-profile context, one-shot restore after sources are ready, cancellation on newer user navigation. A cold paused/stopped session restores browsing without autoplay. Warm playback uses the existing lifecycle owner. |
| Instant Recall | Existing Recents sheet shows up to eight distinct allowed channels. Hold Last Channel to open it. Full Recent browsing remains available. |
| Network Intelligence | Passive routing, validation, instability and reconnection observations. No speed test, automatic stream switching, buffer, retry or DNS policy changes. |
| Playback Session Card | Inside Health Center, reusing the existing live summary. Available format/decoder/source FPS/current display refresh, buffers, timeshift, network, PiP and background ownership; unknown values are not fabricated. |
| Safe Mode | Temporary activity-scoped safe presentation, no deletion of normal preferences or theme data. |
| Theme Preview | Immutable staged visual/legacy packages, fixed native Keep/Revert prompt, 20-second lease, cancellation on leaving and recovery after process loss. No player restart or external addon replacement for preview. |
| Night Cinema | Optional fullscreen-only restrained black chrome, less secondary programme copy and guarded 2.1-second auto-hide. Existing transport controls and actions retained. |
| Cobra Pulse | Scalable native trace of the approved Cobra emblem, restrained state colors and buffering/recovery motion. Existing error/paused text retained when an emblem would misrepresent playback. |
| Personalized welcome | Literal custom text, default Welcome back, brief emblem reveal only on explicit chooser entry. Not automatic startup, resume, rotation or PiP return. |
| Emergency restore | Choose Your Experience → Cobra gear → Cobra Recovery → Restore Built-in Theme. Native recovery is independent of installed visual styling. The promised route was absent in the immediate parent source and is restored here. |

Ambient, Smart Return and Night Cinema default Off. The existing clock-style Ambient screen is unchanged. New presentation effects respect reduced motion and lifecycle visibility.

## Honest limitations

Quick Peek cannot promise an additional provider connection or decoder. If simultaneous playback capacity is unknown, stale or exhausted while that source is in use, or recording/resource safety prevents preview, it shows channel information and Play without risking the current stream. Provider account limits outside Cobra remain outside its control.

Smart Return does not persist or manufacture a timeshift buffer across process death. It does not replace existing Multi-View/PiP ownership or guarantee restoration of a provider session that has expired.

Source FPS is stream metadata, not measured visible frame rate. Network transport and route changes do not prove throughput. App background/audio ownership does not prove audible playback during a phone call. These distinctions are included in diagnostic presentation.

## Verification requirements

The build workflow validates the frozen source and exact tests, all 500 inherited Android test identities, new feature tests, 56 byte-identical protected playback/transport/display members, permanent signer, package/version and unchanged native/assets/resources. Two independent replicas must produce identical signed APK bytes before delivery. The machine-readable ACCEPTANCE.json records the actual result; this document alone is not a passing test claim.

Local helper/policy tests and native-graphics render fixtures are not full-device tests. Full Android/Robolectric tests are distinct from physical decoder, provider, Fold, cellular, PiP, SystemUI and phone-call behavior. DEVICE-TEST.md is the required real-device acceptance checklist. No physical acceptance is claimed by this candidate.

The native Kodi engine is not rebuilt or modified. The final feature scope is closed; any further changes must be defect repairs or explicitly authorized additions.
