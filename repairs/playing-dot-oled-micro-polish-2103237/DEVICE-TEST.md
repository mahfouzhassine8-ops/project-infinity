# Cobra 2103237 — Playing Dot OLED Micro-Polish Device Acceptance

Install as an in-place update over the user-locked 2103236 build. Do not uninstall or clear app data.

This pass must not change where the dot lives, what playback session owns it, or Cobra's existing buffering animation. It only refines the shared playing-dot renderer used by TV Grid, Mobile, Compact, Cards and Focus.

1. Confirm the dot remains in the exact approved 2103236 position in all five Live TV views.
2. Tune Channel A, then tune Channel B while both rows/cards are visible. Playback ownership must change immediately. Visually, A's dot should softly fade while B's dot blooms in over about 180 ms.
3. Merely move focus/selection from A to B without tuning. The dot must remain on the actual playing channel with no handoff animation.
4. Switch between TV Grid / Mobile / Compact / Cards / Focus without changing channel. The indicator must remain attached to the same actual session; mode switching must not create a false playing state.
5. Change Ambient Mode while a channel is playing. The dot's accent should morph smoothly instead of snapping.
6. Toggle Night Cinema ON. The dot should smoothly morph into the locked warm amber/yellow #FFC247. Toggle it OFF and confirm a smooth return to the current Ambient accent.
7. Watch several pulse cycles on the Fold's OLED display. At the darkest point, the crisp center must remain visibly illuminated; it must never blink fully off.
8. Confirm the dot reads like a tiny emissive status LED: crisp colored core, small transparent bloom, no gray/black plate, no oversized halo.
9. Night Cinema keeps the slower/quieter pulse. Ambient Immersive may use the stronger existing glow, but the dot must stay restrained.
10. Trigger normal buffering. Cobra's existing buffering/recovery animation must remain the buffering language. The playing dot must not introduce a new buffering animation or alter recovery behavior.
11. Pause/stop/end/error without immediately switching to another channel: the dot must clear immediately rather than lingering as a handoff.
12. Exercise timeshift/rewind, Multi-View primary/audio selection, PiP/background return, Fold/unfold and rotation. Confirm no retune, player recreation, audio interruption, timeshift loss or playback-owner change caused by this polish.

Do not lock 2103237 until the OLED treatment and handoff are visually approved on the physical Fold.
