# 2103224 onn. 4K Pro TV Native Remote Architecture RC7

Protected parent: **locked 2103223 — onn. 4K Pro TV Hardening RC6**.

This is a TV-only architecture pass for the 32-bit armeabi-v7a onn./Google TV build. The regular ARM64 phone/Fold line, Kodi native engine, providers, rewind/timeshift and the working 2103223 player presentation are protected.

## Physical-device findings after 2103223

- Fullscreen player transport and bottom tools now work with the remote.
- The player header still strands the upper-right **Favorite** and **Lock** controls.
- Multi-View picker is functionally blocked: focus moves only one or two channel rows, **All** and **Groups** are not reliably reachable, and Select/OK does not reliably choose a channel, so a second screen cannot be created.
- The TV Grid **Favorites** header/group surface is visually oversized and behaves like a full-width phone focus slab instead of a compact 10-foot TV control.
- The remaining failures share one cause: Android's generic focus search is still being used across surfaces that need deterministic TV navigation ownership.

## Architecture direction

Use TiviMate only as an interaction benchmark: fast, persistent, remote-first TV navigation. Do not copy proprietary code, branding, assets or pixel-for-pixel layouts.

### 1. Deterministic player header
- Explicit remote row: Return/Back ↔ Last Channel ↔ Favorite ↔ Lock.
- Up from transport lands on the usable header row; Down returns to Play/Pause.
- No Android focus guessing across the title spacer.

### 2. Native-TV Multi-View picker
- One focus owner and explicit zones: Search → Favorites/Recent/All/Groups → channel/group list.
- Left/Right moves exactly one filter.
- Up/Down moves exactly one list row and scrolls it into view for the entire list.
- Select/OK is explicitly dispatched to the selected list item.
- Groups opens its group list, then a selected group opens its channels.
- Selecting a channel must execute the existing selectCobraMultiChannel() path and actually create/replace a Multi-View screen.
- No child-button focus fighting the ListView.
- Back closes one layer and restores the control/tile that opened the picker.

### 3. TV Grid group/Favorites polish
- Replace the full-width highlighted group bar with a compact left-aligned TV group control.
- Keep safe edge padding so labels such as Favorites are never clipped.
- Focus is a restrained outline/surface around the control, not a giant blue strip.
- Playlist and Search remain on the right and are reachable by Left/Right.
- Guide header → time navigation → EPG is an explicit D-pad route.

### 4. Preservation / stability
- Keep 2103223 off-main cache loading, coalesced EPG updates, no display-mode switching, persistent guide/player surfaces and no decorative TV animation.
- Preserve working Channels / Display / Multi-View / More player footer and transport controls.
- Preserve package, permanent signer and exact locked ARMv7 native engine.
- 2103223 remains the rollback baseline until physical remote testing accepts 2103224.

## Required physical acceptance

Using only the onn. remote:
1. Player: Play/Pause → Up → Favorite → Lock → Last Channel → Down → transport.
2. TV Grid Favorites: compact group control fits inside the screen; Source/Search are reachable; Down reaches time/EPG.
3. Multi-View: open → All → traverse at least 30 rows → Select channel → second video appears.
4. Repeat with Favorites, Recent and Groups.
5. Add a third/fourth screen; change a tile; switch audio; Pause/Resume; Enlarge/Restore; Full screen/Return Multi.
6. No lost focus, dead Select button, invisible focus, shell rebuild, black transition regression or progressive slowdown.
