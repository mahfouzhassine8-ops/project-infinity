# Cobra 2103229 Multi-View Stability + Fill Screen device acceptance

Parent: exact locked 2103227 candidate. This candidate is intentionally limited to Multi-View playback recovery and Multi-View Fit / Fill Screen geometry.

## Playback stability

1. Start two live channels in Multi-View and leave both playing for at least 15 minutes.
2. Repeat with three and four channels when the device/provider permits it.
3. Confirm a healthy tile never pauses, retunes, flashes black, or restarts because another tile buffers or errors.
4. If one tile enters a recoverable IDLE/error/prolonged-buffer state, confirm only that tile shows \`Reconnecting this screen…\` and the other tiles continue uninterrupted.
5. Confirm manually paused tiles remain paused; automatic recovery must not resume them.
6. Long-press a failed tile and verify \`Retry this screen\` still works as the explicit destructive fallback for that tile only.
7. Exercise rotate, Fold/unfold, app background/foreground, Full Screen -> Return to Multi-View, Enlarge/Restore, add/remove screen, and change channel.
8. If a tile fails twice automatically and stays failed, export diagnostics before manually retrying. The bounded recovery must not loop indefinitely.

## Fit / Fill Screen

1. Long-press any Multi-View tile -> \`Multi-View layout\`.
2. Select \`Fit\`. Confirm framing matches the locked 2103227 behavior.
3. Select \`Fill Screen\`. With two videos in portrait, confirm the usable screen is two contiguous top/bottom regions with no layout-created center gap or unused bottom canvas.
4. With two videos in landscape, confirm side-by-side regions.
5. With three videos, confirm one large region plus two smaller regions uses the full usable canvas.
6. With four videos, confirm a true edge-to-edge 2x2 grid.
7. Confirm Fill Screen preserves proportions; center crop is allowed, stretching/distortion is not.
8. Confirm genuine navigation/cutout insets are respected.
9. Enlarge a tile and confirm the remaining tiles reflow into the leftover area without stopping playback.
10. Enter Full Screen and return; confirm the prior Multi-View layout mode is remembered.
11. Fold/unfold and rotate repeatedly; confirm tile geometry updates without channel retune, player recreation, audio interruption, or timeshift loss.

Physical-device acceptance remains required before locking 2103229 as the next baseline.
