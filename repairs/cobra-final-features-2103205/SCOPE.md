# Cobra final additions — exact authorized scope

Parent: locked 2103204 OLED Blue, commit 166cf9dad40a8a0333563830a3c0965ce4e81da6.
User authorized implementation of the final scope on 2026-09-21.
Full signed/code/evidence rollback saved before edits; device-private data is outside this backup.

1. Ambient Mode: Off/Subtle/Immersive, contextual background/glass/accent/focus atmosphere only. Preserve existing layouts and controls; no recoloring or readback of video pixels.
2. Channel Quick Peek: compact independent muted live preview, Now/Next, Play, Favorite, basic channel/stream info. Never replace, steal or restart the main player. Respect provider connection capacity and decoder availability; metadata-only fallback when simultaneous preview is unsafe.
3. Smart Return: On/Off, bounded profile-specific useful UI/session context, one-shot source-ready restoration. Off follows existing default entry. Never recreate or resurrect timeshift buffers, override explicit Stop, or replace active resume/PiP/Multi-View ownership.
5. Instant Channel Recall: quick last 5–8 channels using existing recents, not duplicate history. Preserve complete Recent category elsewhere.
6. Network Intelligence: passive actual network type/state/instability/reconnection observations. Existing playback preferences, network-family choice, buffering, timeshift and recovery remain authoritative. No unsupported universal tuning.
7. Playback Session Card: within existing Health Center only; actual format, source FPS, current display Hz, buffer, timeshift, network, PiP and background/session state. Unknown remains unknown; no credential/provider URL leakage.
8. Safe Mode: temporary known-safe presentation session, no deletion of preferences/themes/playback data; normal configuration recoverable. No native engine changes.
9. Theme Preview/Sandbox: staged temporary appearance with fixed Keep Theme/Revert UI and monotonic timeout; unkept preview reverts after timeout/background/process restart. Preserve previous rollback and active players/surfaces/timeshift.
10. Night Cinema: optional fullscreen-only true-black restrained chrome, less secondary copy, faster guarded hide, existing touch/D-pad reveal and unified timeline. Existing transport/actions remain reachable.
12. Cobra Pulse: approved cobra emblem as subtle observation-only status. Blue normal/buffering, green timeshift/recording, white live edge, amber background, red network trouble, purple recovery. No duplicate badges or continuously busy normal animation.

Permanent recovery: Choose Your Experience → Cobra gear → Cobra Recovery → Restore Built-in Theme. It must be independent of imported theme styling. The parent source lacked this promised route; restore it explicitly while preserving existing chooser options.

Personalized welcome: default Welcome back; Custom Greeting preference accepts literal text. Brief emblem+text reveal only on explicit Choose Your Experience selection/switch into Cobra, not automatic launch, routine resume, rotation or PiP return. Respect text direction/window/font size and touch pass-through.

Excluded: #4 Command Palette HOLD/DO NOT IMPLEMENT; #11 dedicated Fold Continuity SKIP. Preserve existing legacy clock Ambient screen, other approved navigation/view modes, guide and native engine.

Defaults: new optional presentation/session modes Off to preserve parent behavior until selected. No additional settings or features beyond the authorized list.

Acceptance: source/static, host, Android/Robolectric, rendered fixtures, packaging/signing/reproducibility and physical-device observations must remain separate. Do not claim physical display/playback/provider/cellular/Fold/decoder/PiP/SystemUI/call-audio acceptance from automated tests. Freeze features after completion and verification; do not auto-lock a candidate without user instruction.
