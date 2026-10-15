# Cobra 2103273 Pro Sports + Soccer RC1 — acceptance contract

Locked rollback/source baseline: **2103271 Sports Data RC1**. The unverified 2103272 Sports-polish candidate is intentionally not the parent.

Required outcomes:
- Preserve existing Pro View when Sports is not selected.
- Main Pro navigation becomes six compact tabs: **All Channels / Favorites / Recents / Groups / Sports / Search**.
- One of the six Pro hero sources is permanently **LIVE SPORTS**; up to five regular channel sources remain.
- Selecting Sports shows **Live Now / My Teams / Upcoming / Leagues** inside the existing Pro browser area.
- Selecting a game drives the existing Pro hero instead of opening a separate Pro layout.
- Sports hero actions are **Watch Live / Stats / Multi-View**, reusing the locked 2103271 Sports functions.
- A unique strong game/channel match may preview through the existing Pro preview owner; ambiguity/no-match must never silently choose a wrong channel.
- Soccer uses the same repository, resolver, game-row, hero and Watch Live paths as other sports.
- **Premier League / Champions League / MLS** are enabled by default. **La Liga / Bundesliga / Serie A / Ligue 1 / Europa League** are present in the extensible league architecture.
- Soccer status remains sport-appropriate through the existing feed detail (half/minute, extra time/penalties when supplied), not baseball/football wording.
- Existing Sports data fetch, channel resolver, Watch Live owner, recording handoff, manual Multi-View, player, provider, timeshift and native engine methods remain preserved.
- Existing inherited Pro tests are superseded only where the approved UI now has six tabs and five regular hero slots plus one permanent Sports source.
- All inherited Cobra regressions and protected non-Pro renders must remain green.

A green CI result is an automated candidate, not a physical-device lock.
