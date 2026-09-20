# Cobra 2103198 — Complete Product Audit / Polish / Stability Device Acceptance

This package is an **update test candidate**, not a fresh-install release. Install the 2103198 APK over the current Cobra build. **Do not uninstall, clear app data, or force a downgrade.**

## What this candidate changes

The automated pass keeps the exact 2103197 Cobra runtime behavior and its protected playback/timeshift/native stack. It corrects release/audit metadata, replaces the stale device-test document, removes one duplicated `RECEIVE_BOOT_COMPLETED` manifest declaration, and reruns the full inherited product regression stack. It does not redesign playback, provider routing, timeshift ownership, buffering, the Kodi native engine, or the theme ZIP.

## Real-device acceptance checklist

1. Launch Cobra normally. Confirm startup is responsive and no blank/black shell is shown.
2. Open the experience drawer and visit Live TV, Movies, Shows, Recordings, My List, Settings, then return to Live TV. Confirm no crash, stale page, or lost preview.
3. In Live TV, switch through all five views: Mobile, Grid, Compact, Cards, and Focus. Confirm one continuous preview surface and no layout clipping.
4. Open Settings. Confirm Appearance/theme management, Normal/Extended Background Mode, TV Sources, playback/display controls, Health & Diagnostics, and the existing source refresh controls are reachable without duplicated options.
5. Open TV Sources. Confirm the existing source manager opens and **+ ADD TV SOURCE** is available.
6. Start a known-good live channel. Confirm picture and audio, then open the original player menu. The top-level player settings should contain Channel playback, Health Center, Audio & subtitles, Aspect / Display, Cast / Route, Manage sources, and Close player without a second Player Options hub or Recent Channels strip.
7. Confirm the fullscreen toolbar is the approved four-action layout: Channels, Display, Multi-View, More.
8. Open Display / aspect choices. Confirm Fold Adaptive is available and persists when selected. Test both the cover display and the inner display, plus portrait and landscape.
9. Exercise rotation lock/unlock while video is active. Confirm PiP, split-screen/multi-window, and returning from background do not steal or leave orientation ownership stuck.
10. Enter PiP from fullscreen playback, return to Cobra, and confirm the app returns to a usable Cobra surface with correct status/navigation-bar treatment and no dead black top area.
11. Test mini-player behavior and Normal versus Extended Background Mode. Confirm background audio/media notification behavior only occurs in the intended mode and explicit stop/pause controls work.
12. Test Light, Dark, True OLED Black, and Follow System. Confirm Settings, drawers, player panels, source manager, dialogs, and guide views remain readable and visually consistent.
13. Open Health Center. Confirm playback defaults and diagnostic export are available. Export diagnostics once and confirm the file is created without exposing provider credentials.
14. Test rewind/timeshift on a known-good channel: play live, rewind, pause, resume, seek toward live, and return to live. Confirm playback ownership is not restarted unexpectedly.
15. Repeat the problem-channel scenario that previously buffered every few seconds. If it still occurs, export diagnostics while the problem is active; do not treat a provider/network limitation as a UI regression without evidence.
16. Leave Cobra running for an extended normal-use session. Move between guide, fullscreen, mini-player, PiP, Settings, sources, themes, and Fold states. Watch for crashes, ANRs, repeated buffering, duplicated controls, stuck overlays, black safe-area regions, or lost touch/D-pad focus.

## Acceptance boundary

Automated CI verifies source lineage, signer/native/resource preservation, Android presentation behavior, settings/player/source contracts, Fold behavior, PiP/background lifecycle policies, timeshift/network/parser invariants, diagnostics safety, and packaging integrity. It **does not** simulate your physical Samsung display/GPU, real provider transport, carrier/VPN path, hardware decoder, Android SystemUI implementation, or a long real-world playback session.

If every item above passes on-device, 2103198 can be considered for a lock. If any item fails, keep the current 2103197 rollback available and capture diagnostics/screenshots before changing the playback engine.
