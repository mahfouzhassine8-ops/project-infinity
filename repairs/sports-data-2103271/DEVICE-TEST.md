# Cobra 2103271 Sports Data RC1 — physical device acceptance

1. Install 2103271 over the current Cobra build.
2. Open Cobra → Sports and confirm real schedules populate instead of the all-leagues unavailable state.
3. Press Refresh and confirm the page remains responsive while loading.
4. Verify NFL, NBA, MLB, NHL, NCAA Football and NCAA Basketball individually. A league with no scheduled games must show an empty/no-games state, not a feed-failure state.
5. Confirm live scores/status update when a game is in progress and upcoming games appear when nothing is live.
6. Open a real game and test Watch Live against the configured provider. One strong match should launch; ambiguous matches must show choices; no match must not fabricate a stream.
7. Test Smart Sports Multi-View with available live games. Manual pinned panes must remain authoritative.
8. Verify My Teams, Hide Scores, Stats and Standings.
9. Test Light and OLED appearances, Fold inner/cover, rotation, split screen and pop-up window.
10. Regression-test ordinary Live TV, player controls, timeshift/rewind, PiP/background, recordings and manual Multi-View.
11. If Sports still reports unavailable, capture the exact league + HTTP/network error now shown in the UI/diagnostics.

Do not lock until this matrix passes on the physical Fold.
