# Cobra Pro Teams — 2103312 candidate

## Exact parent

- Parent APK: **2103311**, `1.0.9-Kodi-Process-Isolation-RC1`, `com.projectinfinity.kodi`.
- Parent SHA-256: `49407bd19436e17a54579cfd1c4e59e99868962e5bc723eb56e57d47c6e20ab3`.
- Parent source: `70c4c31799879c9c8ad8d1debe3ec138cf1e3ab4`, successful workflow run `37391709971`.
- Bundled skin remains **skin.infinity.diggz 1.0.5.201**. All 3311 native libraries, assets and Android resources are reused byte for byte.
- Infinity chooser, process isolation, power route and all other non-Cobra DEX classes must match 3311. Candidate is **not locked** until device acceptance.

## Agreed additions

1. Favorite team > pinned team > followed team > other games. Apply consistently to My Teams, Live Now, Upcoming and the ready-to-watch Sports preview. Preserve existing follows. Explicit game selection is sticky; data refresh never retunes playback.
2. Favorite/pinned teams automatically receive one pregame notification per game, about five minutes before scheduled airtime. A persisted Android job refreshes opted-in schedules. Existing OS reminder alarms and reboot handling are reused.
3. Separate **Set a Reminder** in Game options for any upcoming game. Manual and team intent share one alarm; removing either does not erase the other. Preserve **Record / Schedule from guide**, Stats and Multi-View.
4. Extend existing Hide Scores to **Spoiler Protection**, in Sports settings, with per-game reveal and Reveal all. Apply to rows, hero, accessible text, ticker, Multi-View overlays and statistics entry points. Notifications contain matchup only.
5. Optional Live score ticker, disabled initially. Uses existing score polling and player presentation lifecycle; hides during PiP, background, lock, menus and Multi-View. Does not own a player or audio focus.
6. Remove both the decorative Muted word and speaker from the Pro preview. Existing audio controls and playback behavior remain.
7. Drawer Sports in Pro opens the same Sports view and preferences. No drawer destination is removed. Preserve the separate Sports hub for other modes.
8. Reuse glass materials, focus states, motion settings, score animations and Sports shrink/hold restore. Retain previous 3307 live rows, exact airtimes, no-game presentation, Groups highlighting, player channel Sports and explicit Multi-View picker.

## Verification

The workflow applies the declared source patch to the full verified 3311 source, compiles production Java, runs existing Cobra navigation/ambient/player/call/PiP/Multi-View and Infinity process tests plus new team/reminder/spoiler tests. It then runs the Android process-survival probe, compares all protected APK entries and every non-Cobra DEX class, and signs with the existing permanent certificate.

Sports UI tests use controlled feed data; no live provider, physical-device decoder, notification delivery latency or real provider recording is claimed by these tests. Android notification permission is required, and OS alarm/network restrictions can affect timing. Upcoming dates use the device timezone. The existing provider/EPG matching and recording implementation remains authoritative.
