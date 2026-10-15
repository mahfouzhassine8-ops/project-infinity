# PRO MODE — LOCKED IMPLEMENTATION SPEC

Parent: locked 2103260 (9501d191282e0c2911fa1966df6d9368c365f0d7)

## Absolute scope

Replace **Focus presentation/state orchestration only** with Pro. The internal compatibility value `focus` remains.

Do not redesign or rewrite TV Grid, Compact, Cards, drawer/navigation, Movies, Shows, Choose Your Experience, settings, Health Center, Recovery, Multi-View, providers, native engine, playback engine, timeshift/rewind, subtitles/audio, PiP/background playback or fullscreen player.

If Pro appears to require changing one of those protected systems, stop rather than expanding scope.

## Reuse

Reuse the existing Focus guide/player foundation, existing preview ExoPlayer/session, Favorites, Recents, last/recent channel data, existing preview controls, existing fullscreen handoff, existing Light/Dark/OLED state and existing adaptive/Fold/window layout.

Do not create a second player architecture.

## Locked interaction

**Resting Hero -> Preview (muted) -> Unmute/Watching -> Fullscreen**

The **video pane itself is the carousel**. Swipe left/right directly on that pane.

There is **no thumbnail carousel, source rail, or permanent card row underneath the video pane**.

Use at most six available existing-data slots. Each active item identifies why it is present using a restrained label **inside the hero**, e.g. FROM FAVORITES, RECENTLY WATCHED, CONTINUE WATCHING, RECENT CHANNEL or FROM CHANNELS. Do not invent unavailable data.

### Resting
- hero is paused and muted
- source/program/channel metadata lives inside the hero
- lower Focus channel foundation stays intact

### Preview
- Preview resumes the same hero session muted
- no automatic fullscreen

### Watching
- Unmute uses the same existing preview player/session
- metadata transitions to the existing Focus Now Playing area under the video
- existing approved preview/player controls appear
- no duplicate player or duplicate metadata block

### Fullscreen
- explicit existing fullscreen control only
- existing preview-to-fullscreen transfer path only
- no new fullscreen/player implementation

## Preservation and acceptance

No "polish" additions outside this specification.

CI passing is not physical approval. The candidate becomes a stable baseline only after device testing and an explicit user instruction: **Lock**.
