# Cobra final additions — physical-device acceptance

Status: PENDING. Automated tests, rendered fixtures and source verification are not physical acceptance.
Keep locked 2103204 and the complete pre-change rollback. Test as an in-place update; do not uninstall, clear data, or remove providers/recordings.

Record device/One UI/Android version, build, appearance, screen/window/font size, source type and redacted evidence. Never send provider credentials or full stream URLs.

## Preserve the working product

1. Confirm all sources, favorites, full recents, profiles, themes, recordings, channel preferences, guide/view modes and settings survive update. Check existing chooser and emergency recovery.
2. With new optional modes Off, compare approved 204 screens and actions: Light, Dark, OLED, Follow System, guide all five modes, Movies, Shows, Recordings, My List, Settings, sources, Health Center and player. No missing/moved working function.
3. Known-good and problem-channel playback: startup, 30+ switches, local rewind/seek/live-edge/pause/live jump, provider catchup distinction, fullscreen/mini handoff, subtitles, rotation/Fold fit, PiP/multiview restoration, background controls and call-audio behavior. New features must not change transport or native engine behavior.

## Safety first

4. From Choose Your Experience → Cobra gear → Cobra Recovery, verify Restore Built-in Theme is readable and reachable with normal, dark, enlarged-text, malformed and intentionally blank custom presentation. Recovery must not inherit the installed theme's unsafe colors or geometry.
5. Safe Mode: enter temporarily, confirm known-safe presentation, browse/play, then leave/re-enter normally. Confirm original theme, settings, source/library data, preferred experience, playback preferences and recordings remain intact. Repeat rotation, process recreation and PiP return.
6. Preview a valid theme: choose Keep Theme once, verify persistence. Preview another and do nothing: previous appearance restores after deadline. Repeat with Back, backgrounding, rotation just before deadline, app process death, rapid A→B requests and Keep/timeout races. Deadline must not reset or keep an unconfirmed theme.
7. Attempt corrupt ZIP, missing required theme data, hostile huge images and interrupted staging. Confirm exact prior theme/history survives, no blank trapping, no partial installed generation, and the fixed recovery/Keep/Revert UI remains accessible.
8. While playing live with a rewind buffer, preview/Keep/Revert/timeout modern and supported legacy themes. Confirm exact live session, audio, position, rewind depth and Multi-View panes continue. No channel restart simply to redraw presentation.

## Approved feature behavior

9. Ambient Off/Subtle/Immersive: inspect contextual atmosphere on existing browsing screens, drawers/sheets and selection. Off matches baseline. Never tint/crop/recolor the video or subtitles. Inspect white/light readability and black/OLED contrast, reduced-motion settings and imported-theme authority.
10. Quick Peek: hold a channel (not scrubber/programme action); inspect Now/Next, live muted preview when capacity permits, Play/Favorite/info and retained channel/schedule actions. Confirm main video/audio/rewind never switch until Play. Confirm unavailable/unknown provider capacity gives clear metadata-only state with no extra connection; verify real provider permits concurrent stream before expecting live preview.
11. Open/dismiss/reopen Peek 30–50 times; navigate/back/background/PiP/change profile/source during connection and late first-frame/error callbacks. No leaked decoder, stale callback, main retune/audio-focus claim or unexpected favorite/recents changes. Test resource-limited hardware and single-connection providers separately.
12. Smart Return On: leave/re-enter at several guide positions/view modes/screens and fullscreen/mini states, warm and cold. Off follows normal entry. Change profile/source/hidden/adult filters while away; stale saved context must not bypass restrictions. User navigation during loading wins. Explicit paused/stopped cold state never autoplays; warm existing player/PiP/multiview remains authoritative. Do not expect a dead process's old local timeshift buffer to return.
13. Instant Recall: last up to eight unique allowed channels, correct order/current programme, one-tap tune. Selecting current channel does not restart it. Full Recent list still available through existing category. Verify profile isolation and deleted/disabled sources.
14. Network Intelligence/Health Session Card: Wi-Fi→cellular→VPN/offline/reconnected, captive portal, airplane toggle and repeated flaps. Compare Android system state and actual player observations. No false throughput/provider-health claim from transport name. Card stays inside Health Center and shows unknown values honestly; no extra automatic tuning or override of IPv4/IPv6/buffer preferences.
15. In Session Card compare known format/resolution/source FPS, actual display refresh changes, decoder, buffer, rebuffer counts, timeshift depth/state, live distance, PiP and background/session audio. Source FPS is not measured rendered FPS; app cannot prove call-time audibility. No player→card mismatches in Multi-View or after channel switch.
16. Night Cinema only in fullscreen: true black chrome, restrained accents/minimal secondary information and fast guarded hide. All existing play/pause/seek/timeline/channel/display/subtitle/More/lock/rotation functions remain reachable. Tap/D-pad reveals; active drag, open menu, lock or PiP prevents inappropriate hide. No bright flash entering/exiting or on Light browsing return.
17. Pulse: actual Cobra hood/emblem, restrained normal blue, buffering pulse, timeshift/recording green, live-edge white, background amber, network-trouble red, recovery purple. Compare to actual diagnosed state. No expensive normal looping, no false network alarm merely from provider buffering, no interaction blocked or effect on actual video. Hidden/PiP/background/reduced-motion cleanup behaves correctly.
18. Custom Greeting: default Welcome back; test custom name, long literal text, emoji and RTL at 200% font. Brief text reveal beside emblem only when explicitly choosing/switching to Cobra. Never routine auto-launch, resume, rotation or PiP return; no delay in playback/navigation, no permanent overlay or intercepted touch.

## Extended acceptance

19. Cover/inner display, portrait/landscape, fold/unfold, cutouts, split window and resizing: no stale geometry, unreachable menu, lost insets/status bar/navigation area, or hidden recovery. No dedicated new Fold Continuity system should appear.
20. Long session and repeatedsettings/theme/peek/navigation cycles: monitor memory, decoder counts, callbacks, battery/heat, responsiveness, audio/video continuity and crashes/ANRs. Preserve known-good channels.

Only the specified additions are authorized. Command Palette remains held, dedicated Fold Continuity skipped. Freeze features after acceptance; do not add more settings or redesigns during testing.
