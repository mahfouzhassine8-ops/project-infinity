# Cobra 2103270 Sports Hub — physical device acceptance

Use the same device/provider setup that passed locked 2103269.

1. Install 2103270 over 2103269. Confirm update-over-install succeeds and Cobra/Infinity existing settings remain.
2. Open Cobra → Sports from the drawer. Confirm the dedicated Sports Hub appears without rebuilding or breaking Live TV.
3. Verify live/upcoming games refresh with real team names, status, scores, and broadcast labels. Leave/re-enter Sports and verify state persists.
4. Follow/unfollow teams. Confirm My Teams updates. Enable Hide Scores and verify no score leaks from hub cards, Game Spotlight, completed listings, or Sports Multi-View overlays.
5. Test a game with one reliable channel match: Watch Live must launch the correct existing Cobra channel/player.
6. Test a game with multiple plausible provider channels: Cobra must show Watch On choices rather than silently picking one.
7. Test a game with no reliable match: Cobra must say no matching current-provider channel and must not fabricate/launch a stream.
8. Smart Multi-View: test Live Games and a league scope with 2, 3, and 4 resolved games. Confirm it uses the existing Cobra layouts.
9. Start with one/two manual Multi-View panes, then Smart fill; manual panes must remain. With all four panes manually occupied, Smart fill must refuse replacement.
10. Open a Sports Multi-View pane full screen and Back. Confirm the exact Multi-View session returns and other panes survive.
11. Where EPG recording is supported, schedule/record from Game Spotlight; confirm it reaches the existing Cobra recording action and correct event.
12. Test Stats and Standings; if remote detail fails, Live TV and Watch Live must remain functional.
13. Test OLED/dark and Light appearance, inner Fold, cover display, portrait, landscape, Samsung split screen, pop-up window, live resize, and fold/unfold while Sports is open.
14. Regression: ordinary Live TV, Movies, Shows, Recordings, My List, Settings, timeshift/rewind, PiP, background playback, call handling, Display, player chrome, manual Multi-View, and currently-playing indicator must behave exactly as locked 2103269.
15. Capture diagnostics for any wrong channel match: game/league, broadcasts, top resolver candidates/confidence, EPG evidence, and selected channel.

Only after this matrix passes on-device should 2103270 be considered for lock/promotion.
