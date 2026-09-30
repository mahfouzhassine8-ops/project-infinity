# Cobra 2103272 Sports Hub Polish RC1 — physical device acceptance

Use the locked 2103271 device/provider setup.

1. Install 2103272 over 2103271 and confirm update-over-install succeeds.
2. Open Cobra → Sports. Confirm the large dead space is reduced and the top summary reads sports information (LIVE / UPCOMING / UPDATED), not the generic channel/source status.
3. Confirm Refresh, Hide Scores and Smart Multi-View occupy a compact glass action surface and remain easy to tap.
4. Verify LIVE NOW: larger live card, clear red LIVE treatment, larger score/team marks, broadcast and inning/period still correct.
5. Verify Upcoming: no fake 0–0 score before game start. Matchup, date/time and broadcast remain visible.
6. Verify league rails and **See All ›** navigation.
7. Confirm horizontal rails have intentional next-card peeking without awkward clipping.
8. Test My Teams and Hide Scores; score hiding must remain consistent.
9. Test Light and OLED appearances on Fold inner display, cover display, portrait, landscape, split screen, pop-up window and live resize.
10. Open a game and test Watch Live, ambiguous Watch On choices and no-match behavior.
11. Test Smart Sports Multi-View and manual pinned panes; no behavioral regressions are allowed.
12. Regression-test Live TV, player controls, timeshift/rewind, PiP/background playback, recordings, Movies, Shows, Settings and currently-playing state.

Do not lock until the physical Fold presentation and functional regression test passes.
