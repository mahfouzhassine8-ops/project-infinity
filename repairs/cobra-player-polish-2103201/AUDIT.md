# Cobra 2103201 — player controls and presentation repair

Parent: exact verified 2103200, recipe commit `3a74876701abfd9e1382e466c07a5f3388abaef4`. This candidate carries forward the prior complete audit and provider-boundary repairs. It requires final CI, independent packaging verification and physical-device acceptance; a passing automated test is not a physical pass.

## Repairs

### Timeline touch and seek ownership

The buffer could report READY while the player still used its live proxy and the actual SeekBar remained hidden. The visible blue progress line did not own input, so holding it reached the fullscreen background long-press handler and opened the Live TV drawer.

The existing timeline now owns its touch area even when seeking is unavailable. Once retained local history is ready, the thumb is usable; completing a seek invokes the existing local-rewind activation and applies the requested position when that same player becomes ready. Dragging previews the position and commits once on release. Cancellation, rebuilt controls and replaced player/session ownership reject obsolete gestures. Rewind Off remains authoritative. Supported finite native live windows also use the existing timeline. Keyboard/accessibility changes renew the chrome timeout.

The existing buffer, ingest, playlist, provider catch-up implementation, recovery and native engine are preserved. Source guards compare the protected transport classes and activation/recovery methods byte for byte. Actual media timestamps, first-seek behavior and device playback still need the focused checklist.

### Subtitles and saved language preferences

The screenshot lists audio and no subtitle track. The old current-track sheet always displayed an Off action, while the saved preference picker offered common languages even when the stream supplied none. That alone does not prove a decoding failure.

The current-track sheet now identifies real supported tracks, uses readable language labels, marks actual selected/disabled state and explicitly explains missing or unsupported subtitle tracks. Disabling subtitles clears displayed cues immediately. Track discovery refreshes the open sheet without replacing it; obsolete rows and sessions cannot alter playback. Preview CC follows the current player and refreshes during handoff, host recreation and stop.

Saved settings are labeled **Preferred subtitles**, with **when available** language details. Session track overrides remain separate from saved defaults. No subtitle extractor, decoder or provider settings are changed. A preference cannot create captions absent from the stream.

A separate preview-button defect was confirmed against the exact Media3 1.7.1 selection rules: merely enabling text and allowing undetermined language need not select a normal English track. Explicit preview On now selects a supported current track, preserving a valid existing choice and preferring the saved language. If discovery is delayed, the pending request selects a track once it appears; Off cancels that intent. Neither path changes saved preferences. `SUBTITLE-EVIDENCE.md` records the upstream evidence and focused regression assertions.

### Fold Adaptive

The old policy added up to 6% zoom for near-matching large viewports. A reproduced 1920×1080 source in a 2000×1200 viewport extended 60 pixels beyond each horizontal edge. Fold Adaptive now fits the entire source proportionally inside the actual measured video pane, centered and reaching one pair of viewport edges.

The existing geometry ownership follows inner/cover display, rotation, multi-window and drawer changes. Different source and viewport ratios can require bars. This change removes arbitrary crop; it does not stretch the picture. All other aspect algorithms and PiP's established Best Fit behavior remain intact.

### Menu cleanup and motion

The duplicate **Aspect / Display** row is removed from Options. The existing dedicated Display button retains the full aspect menu. Unique functions, the four-action player toolbar and saved channel preferences remain available.

Player chrome uses a short fade while controls keep their coordinates. Interrupted animations normalize transforms and delays; pending hides respect menus, dragging, lock and PiP. Removed or replaced panels cannot continue controlling current views. Existing icon focus feedback is restrained and preserves runtime disabled-button dimming. Shared list/panel helpers respect system-disabled animations. Video surfaces and playback transport are not animated.

## Regression integrity

The complete 316 inherited Android testcase identities are retained. The new suites exercise real Android MotionEvents, menu actions, selected subtitle state, cue clearing, handoff, cancellation, actual TextureView matrices and animation timing with disclosed controlled player inputs.

Six inherited test/harness files receive guarded, recorded adaptations in temporary CI checkouts: the explicitly removed duplicate menu route, the clearer subtitle-preference label, the new whole-frame Fold expectation, and additional extracted-method collaborators for the same 14 host timeline assertions. No inherited case is silently dropped. The historical committed tests remain unchanged.

Local evidence already reproduces the gesture and Fold/motion failures against the untouched parent. The delivered report records final combined CI counts and APK identity only after verification. Host tests do not decode video; Robolectric does not establish OEM display, Binder or physical playback behavior.

The first combined run executed all 357 cases in both replicas and stopped on two new focus assertions. The subtitle fixture requested focus while still in touch mode and never checked whether initial focus existed. An API34 Android probe reproduced that precondition failure and confirmed replacement-row focus survives layout after entering focus navigation. The corrected test explicitly establishes and verifies that precondition. The icon fixture now matches the real 46×46 control slot, distinguishes focus acceptance from animation progress, and waits a bounded number of frames for actual unfinished motion before disabling the button. Its original compound assertion cannot identify focus versus frame timing as the exact failing subcondition; zero width alone did not reproduce failure. All original behavior assertions and testcase identities remain, with stronger precondition/unfinished-motion checks. Production source is unchanged by these fixture corrections. Final combined CI must still pass before delivery.

## Rollback and release limits

`Cobra-2103200-Complete-Product-Rollback-20260921.zip` was preserved and saved before changes. SHA-256:

`26fd3b1b4242489a3c935215006e2d01eb64a03e2c8a7bb5d4c4acd5964d58b7`

It contains the exact signed APK, all 220 generated inputs, source recipes, receipts, verification and restore instructions. It excludes device-private data and signing secrets. Normal Android downgrade may be rejected; do not uninstall or clear data to force rollback.

No physical Android/Fold endpoint is accessible in this environment. Installation/data retention, actual subtitles supplied by the channel, live rewind, buffering, GPU rendering, Fold/PiP/SystemUI and long-session checks remain device acceptance gates. Prior 16 KiB native compatibility and provider cached-artwork limitations remain as documented in the 2103200 report. Do not lock this candidate solely because CI passes.
