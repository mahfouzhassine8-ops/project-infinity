# Read-only explanation of rejected 2103370

2103370 is not an implementation parent. No UI/player changes were cherry-picked from it. The following observations explain the reported leakage and the corrective tests required to prevent recurrence; they do not overrule the user's physical observations.

## Source-level leakage mechanism

The approved source's `cobraShowGuideShell` stores `cobra_primary_view=mobile` when switching to Mobile but intentionally retains the previous `guide_view_mode`. The latter remembers the selected guide experience and can remain `focus` after leaving Pro. `cobraGuideViewMode` reads that saved preference.

The old `cobraProPlayerSportsEnabled` predicate checked phone capability and `cobraGuideViewMode()==focus`; it did not require the currently active Pro hierarchy or current `mCobraGuideStyle`. The rejected patch used this predicate in the **shared** `cobraBuildPlayerChrome` to construct a new Pro fullscreen rail. Consequently, a prior Pro choice followed by an actual Mobile selection could still satisfy the predicate and construct Pro controls in Mobile. The same predicate gates score-ticker presentation. Saved preference is not current view ownership.

This is a concrete source-level mechanism consistent with the reported Mobile controls/scores, not a claim that source inspection alone certifies the device reproduction. Corrective runtime tests must traverse the actual mode-selection cards while leaving the saved preference dirty, then examine the attached fullscreen hierarchy, Back, recreation and PiP return.

## Independent scope errors in rejected controls

- `cobraBuildProFullscreenRail` constructed `Channels, Display, Multi-View, PiP, Status, More` for every context passing the broad Pro predicate, without a separate Sports-section check.
- Its Status glyph was `health`, not the existing mini-player Stats glyph.
- The rejected Pro hero expanded the original eight callbacks to ten, adding both PiP and a new Status action. The latter was not authorized in non-Sports Pro.
- The rejected rail also introduced arrow buttons and a swipe-instruction caption. The latest corrective requirements explicitly prohibit these.

The new work separates current **Pro ownership** from **Pro Sports context**. It retains original menu controls and callbacks; a new Stats control is allowed only in Pro Sports. The existing `CobraProUi.icon(..., "stats", ...)` implementation is reused. Runtime inventories must demonstrate prohibited-element absence rather than merely checking that required source strings exist.

## Read-only evidence identity

The rejected packaged `changes.patch` inspected for this explanation has SHA-256:

`8c1da2e1ff79918f6eafa5fc2c504cacef2a9270341ef2d3fe02b331dcf1d5b3`

Baseline behavior was independently checked in the verified 2103324 runtime source, including `cobraShowGuideShell`, `cobraSwitchMode`, `cobraGuideViewMode` and `cobraProPlayerSportsEnabled`. The fresh branch's parent is the approved 2103369 transport commit whose 24 Cobra-owned runtime files are byte-identical to 2103324.

No rejected source file is included in the new runtime input. This document is diagnostic evidence only.
