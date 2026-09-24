# Cobra 2103236 — All Live TV views true-playing indicator device acceptance

Install as an in-place update. Do not uninstall or clear app data.

The source of truth is unchanged from the device-approved 2103235 TV Grid indicator. This pass only adds that renderer to Mobile / Compact / Cards / Focus and corrects Night Cinema to warm amber/yellow.

1. Start one Live TV channel. Confirm TV Grid still shows the existing dot in the channel-name cell with no placement regression.
2. Switch view modes without changing channels: TV Grid → Mobile → Compact → Cards → Focus → TV Grid.
3. In every view, confirm the dot stays attached to the exact same actual playing channel. Merely focusing/selecting another row/card must not move it.
4. Mobile: dot is beside the channel name in the channel identity headline; it must not float over preview/bottom navigation.
5. Compact: dot is immediately beside the channel-name column without breaking the dense ON NOW layout.
6. Cards: dot is in the active card's identity/header hero and remains independent of SELECTED CHANNEL styling.
7. Focus: dot is at the far-right of the actual playing channel queue row. The existing selected-row marker remains a separate state.
8. Night Cinema ON: the active dot becomes warm amber/yellow (#FFC247) in every view, with the already-approved slower/quieter pulse.
9. Night Cinema OFF: the dot returns to the existing Cobra accent. Ambient Off/Subtle/Immersive retain the 2103235 pulse-strength behavior.
10. Pause the actual session: dot clears. Resume: dot returns. Normal buffering may keep the dot; terminal error/IDLE/ENDED clears it.
11. Multi-View: the guide indicator follows the existing selected audio/primary session rule from 2103235 only. Do not show all visible tiles as playing.
12. Exercise Fold/unfold, rotation, background/foreground, PiP return and repeated view-mode switches. Confirm no retune, ExoPlayer recreation, audio interruption, timeshift loss or session ownership change caused by the indicator.

Do not lock 2103236 until the four new placements and amber Cinema treatment are visually approved on the physical Fold.
