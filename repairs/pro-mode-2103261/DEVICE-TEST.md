# 2103261 Pro Mode — PHONE/FOLD TEST CANDIDATE

Parent: locked 2103260, commit 9501d191282e0c2911fa1966df6d9368c365f0d7.

## Scope lock

This candidate changes **Focus Mode only**. Focus is shown to the user as **Pro** while its existing internal mode key remains `focus` for compatibility.

Do not treat this candidate as a new stable lock until physical-device acceptance and an explicit **Lock** instruction.

No native engine rebuild. No provider, timeshift/rewind, fullscreen-player, Multi-View, Movies, Shows, drawer, Compact, Cards, TV Grid, Choose Your Experience, Health Center, Recovery, or other protected subsystem redesign.

## Install

1. Install over locked 2103260 as an update.
2. Do **not** uninstall, clear app data, or press Start Fresh.
3. Open Cobra Live TV and select **Pro** where Focus previously appeared.

## Pro behavior to verify

### Resting hero
- One large video/hero pane only. There must be **no thumbnail/source rail below it**.
- The active source label is inside the hero, such as **FROM FAVORITES**, **RECENTLY WATCHED**, **CONTINUE WATCHING**, **RECENT CHANNEL**, or **FROM CHANNELS**.
- Program/channel metadata is inside the hero.
- The hero is paused and muted.
- At most six hero sources are available.

### Swipe
- Swipe left/right directly on the video pane.
- The hero changes source/channel in-place.
- The selected item returns to the Resting state: paused + muted.
- Source label and metadata update with the selected item.

### Preview
- Press **Preview**.
- The same hero starts playing muted.
- Audio must not leak.
- Do not enter fullscreen automatically.

### Watching
- Press **Unmute**.
- The same preview session should continue rather than intentionally creating a new player.
- Audio comes on through the existing player/audio-focus behavior.
- Program metadata moves to the existing Focus-style area immediately below the video.
- Existing preview/player controls become available.
- No duplicate player or duplicate Now Playing block should appear.

### Fullscreen
- Enter fullscreen only by the existing fullscreen control.
- Existing preview-to-fullscreen handoff must be used.
- Returning from fullscreen should restore the same Cobra/Pro context without inventing a separate player path.

### Lower Focus foundation
- Channels / Up Next remain present.
- Selecting a lower channel should make it the Pro hero in Resting state instead of silently redesigning the guide.
- Existing channel/program data remains intact.

## Regression checks

Verify **TV Grid, Compact, and Cards** look and behave exactly as they did in 2103260. Also sanity-check Movies, Shows, Multi-View, Health Center and Recovery. Report any difference; do not accept it as Pro-related polish.

Test Pro in Light, Dark and OLED appearance, plus portrait, unfolded Fold, landscape and multi-window. Confirm no clipping, overlapping, trapped focus or unreachable controls.

CI proves source scope, build/signing integrity and prior automated regressions. It cannot prove real-stream continuity, real provider timing, Samsung audio behavior or physical Fold rendering; those require this device test.
