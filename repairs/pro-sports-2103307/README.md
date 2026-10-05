# Cobra Pro 2103307 — candidate, device acceptance pending

Parent: locked `com.projectinfinity.kodi` APK 2103306, `1.0.9-Power-Route-RC1`, SHA-256 `55f1d47bb3ec647b92a5dfbb9de0c0b926027404d9bfecd75a761fd1ed749bc0`. Installed skin remains `skin.infinity.diggz` 1.0.5.201; rollback 1.0.5.200. No skin update is included.

Only `InfinityLiveActivity.java.in` and `CobraProUi.java.in` change within the authenticated 250-file Android export inherited from 2103305. All other source files remain identical. Packaging retains every original native library, asset, resource and JNI registration. Only Android DEX, manifest version and signatures differ in the candidate. Original permanent signer required. No native build or data migration.

## Changes

- Existing Pro Sports list: league/team marks, centered live score/status/network, exact local upcoming date/time/timezone, play and options controls. Hide scores respected. No production fixture events.
- Empty sports hero hides stale matchup marks. Existing controls and empty-state message remain.
- **Main Pro Sports tab**: tap compacts the embedded video; hold restores its original size. This is separate from the video-only fullscreen Channels panel. Video surface/session is preserved.
- Pro fullscreen Channels panel adds Sports alongside Favorites/Recent/All/Groups, with real live rows. Other modes retain their tabs and panel geometry.
- Groups highlight follows the displayed content.
- Pro Multi-View opens a picker across live leagues, resolves broadcasts with explicit ambiguity selection, deduplicates channels, respects four-screen capacity and pinned streams, and reports unavailable matches/launch failures.
- Score polling refreshes presentation without retuning the active hero. Multi-View assignments refresh to the current game data.
- 340ms interruptible resize, 230ms staggered row entrance, 240ms changed-score reveal, press feedback. System disabled motion is respected.

## Automated evidence

CI compiles the actual Java sources and runs production-view Robolectric tests, existing sports parsing/resolution, navigation, player controls, and Ambient suites. PNG evidence is rendered from the production views. Build receipt records every protected entry, test totals, source hashes, candidate SHA and signer. An automated pass is not physical acceptance.

## Required Fold acceptance

1. Confirm installed APK and skin baseline, update candidate without uninstalling; verify provider data, settings and Infinity Kodi remain intact.
2. Live Now: actual live events across MLB/NFL/NHL/soccer show correct logos and scores. Observe a real score/clock refresh while video/audio and scroll position remain continuous. Check hide scores.
3. Upcoming: verify local date/time/timezone against real provider schedules; no invented time or scores. Empty live list keeps its message; hero has no stale team marks.
4. On main Pro screen tap Sports, interrupt/repeat animation, hold Sports to restore. Test cover/inner, portrait/landscape, split and popup windows, larger fonts, disabled motion, all themes. Check player aspect/crop and list space.
5. Video-only fullscreen: Channels has Sports in Pro, Groups remains highlighted, live rows tune correctly. Other modes keep existing tabs.
6. Multi-View: choose two/four real broadcasts, ambiguity choice, no-match feedback, cancel/reopen, stale game and provider removal, pinned stream preservation, one failed stream, audio ownership, fullscreen promotion/return.
7. Enable Ambient and verify its established visible effect through resizing, rows, settings, player and Multi-View transitions. Exercise Mini Player, Fill/Fit, PiP/background, calls/audio focus, rewind/Go Live, favorites and recents.
8. Require real visible behavior across combined flows before locking. Build/test success alone does not close this gate.
