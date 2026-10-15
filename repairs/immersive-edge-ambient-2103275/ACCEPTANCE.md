# Cobra 2103275 Immersive Edge Ambient RC1 — acceptance contract

Locked rollback/source baseline: **2103274 Sports Hub Soccer RC1**.

This pass changes only Cobra's existing **Immersive** Ambient Mode. It does not add another user-facing ambient setting.

Required behavior:
- **Off** remains the approved no-ambient behavior.
- **Subtle** remains the approved restrained contextual/static ambient treatment.
- **Immersive** becomes a live, content-reactive edge-projection effect inspired by the MIT-licensed x-ambient reference implementation.
- The renderer samples the already-visible Cobra mini-player TextureView at a tiny **144 px wide** working resolution, with adaptive height.
- Live frame refresh is capped to roughly **12 fps / 83 ms**.
- The top, bottom, left and right video edges project independently and directionally across the surrounding Cobra interface.
- Multiple simultaneous scene colors must remain spatially distinct rather than collapsing to one dominant color.
- Use a broad soft blur, boosted saturation, exponentially fading directional rays and temporal smoothing so scene cuts do not flash the whole UI.
- The ambient layer is physically **behind** the mini-player and Cobra glass/content. It must never recolor, cover, dim or replace video pixels.
- The old uniform Immersive live-blue backdrop is suppressed while the live edge renderer is active; existing Cobra glass keeps only a restrained tint so projected frame colors stay authoritative.
- One shared renderer must work in **Mobile / TV Grid / Compact / Cards / Pro** modes.
- The effect is active only for the embedded/mini-player while Immersive is selected.
- **Fullscreen playback, Multi-View, PiP and background playback suspend the live frame renderer.**
- Returning from fullscreen/PiP/background to the embedded mini-player restores the effect smoothly from the current frame.
- Paused mini-player may keep the last sampled atmosphere; it must not wastefully continue high-rate sampling while paused.
- If TextureView sampling is unavailable, the ambient layer fails closed and playback remains untouched.
- OLED/dark and Light appearances both remain readable.
- Safe/presentation-disabled mode must not activate the live renderer.
- No telemetry, screen export or network work is introduced. Sampling stays on-device.
- x-ambient MIT attribution/license is included in the packaged source/resources.
- Preserve locked 2103274 Sports Hub Soccer, Pro Sports, resolver, Watch Live, recording, player, timeshift/rewind, PiP/background ownership, native engine and Infinity skin.

CI green means automated candidate only. Physical Fold playback acceptance is required before lock.
