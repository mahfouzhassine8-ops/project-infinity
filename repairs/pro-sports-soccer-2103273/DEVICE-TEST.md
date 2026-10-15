# Cobra 2103273 Pro Sports + Soccer RC1 — physical device acceptance

Use the same Fold/provider setup that passed locked 2103271.

1. Install 2103273 over 2103271 and confirm update-over-install.
2. Open Cobra → Live TV → Pro. Confirm the existing Pro design remains intact.
3. Confirm six main tabs fit and remain reachable: All Channels, Favorites, Recents, Groups, Sports, Search.
4. Cycle the Pro hero sources. Confirm exactly one permanent **LIVE SPORTS** source and the other regular sources remain available.
5. Select Sports and verify **Live Now / My Teams / Upcoming / Leagues**.
6. Select a live game. Confirm the same Pro hero shows matchup, logos, score/status and **Watch Live / Stats / Multi-View**.
7. Verify a unique strong provider match previews/plays the correct existing Cobra channel. Ambiguous matches must require choice; no-match must not fabricate a stream.
8. Verify My Teams uses the existing Sports followed-team state.
9. Verify Upcoming does not imply a live score before kickoff/start.
10. Open Leagues and verify Football, Basketball, Baseball, Hockey and Soccer grouping.
11. Soccer: verify Premier League, Champions League and MLS; also verify La Liga, Bundesliga, Serie A, Ligue 1 and Europa League can be enabled and browse correctly.
12. Test a live soccer match through Pro: correct teams, score, half/minute/status, network and Watch Live resolution.
13. Test no-live-sports state: LIVE SPORTS source remains present and shows the next available game/schedule rather than disappearing.
14. Test Sports Multi-View from Pro and confirm existing manual pinned panes remain authoritative.
15. Switch back to All Channels/Favorites/Recents/Groups/Search and confirm normal Pro behavior is unchanged.
16. Test Light/OLED, inner Fold, cover display, portrait, landscape, split screen, pop-up and live resize.
17. Regression-test ordinary Live TV, timeshift/rewind, PiP/background, recordings, player controls, Movies, Shows, Settings and currently-playing state.

Do not lock until this matrix passes on the physical Fold.
