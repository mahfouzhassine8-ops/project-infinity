# Cobra 2103274 Sports Hub Soccer RC1 — acceptance contract

Locked rollback/source baseline: **2103273 Pro Sports + Soccer RC1**.

Required outcomes:
- Add a permanent first-class **SOCCER** section to the main Cobra Sports Hub.
- Place the Soccer section after global **LIVE NOW / MY TEAMS / UPCOMING** content and before the individual non-soccer league rails.
- Aggregate games from all currently enabled soccer competitions into that one Soccer rail.
- Keep the Soccer heading and **Leagues ›** entry visible even when no soccer matches are in the current window.
- **Leagues ›** opens a Soccer league directory showing enabled soccer competitions and their current-window match counts.
- Default enabled soccer competitions remain Premier League, Champions League and MLS.
- Extended soccer competitions remain available through existing Sports settings: La Liga, Bundesliga, Serie A, Ligue 1 and Europa League.
- Do not duplicate Premier League / Champions League / MLS as separate top-level main Hub rails once the aggregate Soccer rail is present.
- Soccer matches must still participate in global Live Now, My Teams and Upcoming sections.
- Existing 2103273 Pro Sports integration, permanent LIVE SPORTS hero source, Sports tab, Watch Live, Stats and Multi-View remain unchanged.
- Sports repository/data fetching, resolver, Watch Live owner, recording handoff, manual Multi-View, player, provider, timeshift and native engine remain preserved.

A green CI result is an automated candidate, not a physical-device lock.
