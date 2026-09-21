# Cobra 2103207 — scoped feature refinement candidate

Parent: locked 2103206, commit 6f18a77e83f961a870975e6686154bf7e5a3126f.
Do not replace the locked build until device acceptance passes.

## Corrections

- Mini-player CC reflects a supported, selected text track, not merely a saved/requested language. Focus has a transparent center and separate outline.
- Cobra Pulse draws the existing vector emblem without its black disc. No asset replacement or native-engine rebuild.
- Welcome occupies only the existing header title region. Text slides beside the mark, holds 2.4 seconds, retracts/fades, then restores the header. Existing explicit-entry gating, reduced motion and lifecycle dismissal remain.
- Quick Peek refreshes stale Xtream connection capacity before deciding. It shares existing player construction with Multi-View; secondary audio/text renderers stay disabled. Main video/audio, focus, timeshift and history are not touched while opening/closing the preview. Selecting its tile follows the existing channel-tuning path; this is promotion, not a promise of gapless decoder transfer. Unknown/exhausted capacity and active recording remain guarded, with a specific explanation.
- Calls mute the existing session, not its transport. The existing opt-in key/default remain. Explicit speaker unmute retries media audio; no Play/Pause, prepare, seek, source change, or reconnect is issued by that action. A fresh audio session may renew only the AudioTrack after an accepted explicit request; Android owns audibility/routing. Call end restores prior mute intent subject to focus, while retaining a later explicit mute.
- The full-player audio sheet exposes the same media mute action; no new settings screen or toggle. Mini/full sheet labels refresh on focus/mode changes. System PiP/background controls report the actual video transport state, not a fictitious paused state for muted audio.

## Audit scope and evidence boundaries

The reconstructed 206 parent must first pass all original 665 cases. The candidate reruns that exact identity inventory with explicit generated-fixture supersessions for requested CC copy, welcome motion/timing, and speaker-vs-Play call behavior. Additional 207 cases cover mute restoration, no transport mutations, stateful CC drawing, transparent emblem, header-bound greeting and capacity freshness.

Inherited regression suites cover TV Grid/navigation, all Multi-View layouts, timeshift/rewind, PiP/background ownership, providers, Smart Return, Instant Recall, Network Intelligence, session diagnostics, Safe Mode, theme preview/recovery, Ambient, Night Cinema, and welcome entry rules. Passing controlled tests is not end-to-end physical-device acceptance of these features.

Only three runtime Java templates change. Native libraries, assets, resource payload, class registration, manifest capabilities, approved layouts, transport/timeshift policies and source-boundary policies remain protected. Build verification compares payload bytes with the locked 206 APK and checks the original signing certificate. No live provider credentials or media streams are used in CI.

Outstanding acceptance: physical UI/animation appearance, actual simultaneous hardware decoding and provider spare connection, call audibility/Android Auto route, real PiP/background transitions, update installation preserving user data. CI screenshots are native Android fixture renders, never presented as phone screenshots.
