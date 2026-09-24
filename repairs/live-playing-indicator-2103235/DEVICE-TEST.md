# Cobra 2103235 — True Live TV Playing Indicator device acceptance

Start from the 2103235 test candidate as an in-place update. Do not clear app data.

1. Open Live TV in TV Grid. Start a channel and return to the grid. Confirm exactly one small glowing/pulsing dot appears inside that channel's left channel-label cell.
2. Move focus/highlight to a different row without tuning it. The dot must remain on the actual playing channel.
3. Tune another channel successfully. The dot must move to the new active session.
4. Pause the active session. The dot must disappear. Resume it; the dot must return.
5. Allow a normal buffering transition. The dot may remain because the same requested Live session still owns playback; it must clear on terminal error/ENDED/IDLE.
6. Enter Multi-View. The dot follows the selected audio/primary Multi-View session only, never every visible tile. Change the audio tile and confirm the indicator owner changes accordingly.
7. Promote a Multi-View tile fullscreen and return. Confirm the dot follows the promoted session and restores correctly.
8. Toggle Ambient Mode Off / Subtle / Immersive. The indicator must keep the same playback truth while the glow adapts to the active accent.
9. Toggle Night Cinema. The indicator should use the restrained cinema-blue treatment and a slower/quieter pulse.
10. Fold/unfold, rotate, background/foreground, PiP return, and navigate the guide. Confirm there is no retune, player recreation, audio interruption, timeshift loss, or focus confusion caused by the indicator.

Do not lock 2103235 until the device verifies the visual placement and session truth.
