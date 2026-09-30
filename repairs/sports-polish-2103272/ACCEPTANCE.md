# Cobra 2103272 Sports Hub Polish RC1 — acceptance contract

Locked rollback/source baseline: **2103271 Sports Data RC1**. This pass is presentation-only.

Required outcomes:
- Sports data behavior remains byte-for-byte equivalent outside the bounded presentation methods.
- Player, provider, Watch Live resolver, recording handoff, Smart Multi-View and manual Multi-View ownership remain unchanged.
- Main Sports status becomes a dedicated local summary: live count, upcoming count and refresh time.
- The generic channel/source status is hidden only on the Sports Hub main page and is restored automatically on other Cobra pages/subpages.
- Refresh / Hide Scores / Smart Multi-View become one compact responsive liquid-glass action surface.
- Smart Multi-View receives stronger Cobra accent emphasis without changing behavior.
- LIVE NOW uses larger hero cards, a restrained red LIVE pill, larger score and larger team marks.
- Upcoming cards never present pregame 0–0 as an actual score; they show matchup + time/network instead.
- Card/rail density is tightened while preserving deliberate next-card peeking.
- League rows use a polished **See All ›** action.
- OLED/dark and Light use existing Cobra palette/glass APIs; no separate theme system is introduced.
- Narrow, Fold, landscape and resized windows use current actual-window helpers rather than fixed physical-display dimensions.
- All inherited locked tests and protected non-Sports renders remain unchanged.

CI green means automated candidate only. Device acceptance on the Fold is still required before promotion/lock.
