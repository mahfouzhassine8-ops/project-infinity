# RC23 physical onn 4K Pro acceptance — not yet executed

Install as an update over the current TV build. Do not clear data. Keep the exact RC22 APK and exported settings/providers available. Record pass/fail, build version, channel/provider, actions, time and diagnostics for each failure.

## First checks

1. Open Power from Live TV, Movies and Shows. Move through Switch to Infinity, Exit and Cancel. Focus must stay in Power, every action must work, and Cancel/Back must restore usable focus. Repeat 25 times, including opening another menu immediately after closing Power.
2. More -> Channel playback: one Down per visible row through Recents, Restart live playback, Live TV Rewind, Configured stream fallback, Automatic video-surface recovery and Reset this channel. Up reverses. Never activate reset while only testing focus.
3. Hold the dedicated Play/Pause key: one toggle per physical press. Also test short/long Select on channel rows so Quick Peek and normal selection still work. Deliberate Pause must stay paused.
4. Player controls should fade after inactivity. Move through controls near the timeout and verify they remain available while interacting. Back closes an open submenu, then hides visible controls, then exits fullscreen on a subsequent press. Check the same hierarchy after Multi-View fullscreen promotion.
5. Movies and Shows: select the single inline search field; Android TV's own keyboard opens. Type an exact title, partial title and genre, then press Search/Done immediately. Current results should appear and receive focus without disappearing underneath it. Clear the query to restore the cinematic landing page.
6. Search cards and collection cards: poster, title, metadata/rating and continuation progress must fit; focused edges must not clip. Check both Movies and Shows, long names and 1080p/4K output.

## Complete navigation and UI

- Cold launch and warm relaunch; Choose Experience; enter Cobra; return to Infinity through Power. Verify package update retains preferences and sources.
- Drawer -> Groups -> Channel list/grid -> preview -> fullscreen -> return, 50 cycles. Try alternating fast separate Left/Right taps and held keys. Preserve Right=Select and Left=Back only in their approved Live TV drawer/directory contexts; normal horizontal rails/EPG/search-cursor movement must remain normal.
- Favorites, Recents, All channels, Groups and playlist/source picker: all rows reachable, counts accurate, focus visible, no hidden focus or freezes. Include a large group and one with no channels.
- No old multiline PLAYING label in a channel row. The original pulsing dot remains visually unchanged and follows actual playback, not merely a playback request. Confirm buffering/paused/ended streams do not misleadingly claim playing.
- Movies/Shows hero, Popular Now, Recent Releases, Genres, Continue Watching, My List, details, trailers where available, seasons/episodes, playback and Back. Sections must not jump to Live TV unless selected through the drawer.
- Start opening details, then quickly change section or open another item. The old metadata request must not reopen the old details screen. Repeat with person/collection browsing.
- All Settings controls, Audio & subtitles, language/size choices, Display, More, provider/file access, Recordings and Power must perform their existing actions. No new/removed controls or placeholders.

## Playback and Multi-View

- Observe several known-good channels for at least 30 minutes. Test channel changes, fullscreen/preview handoff, rewind/timeshift, Go Live, Last Channel, subtitles and audio continuity.
- Compare any buffering to RC22 using the same channel/provider/network. Do not label an intentional Pause as a buffer defect. Export Health Center diagnostics for a genuine freeze or repeated buffering.
- Test audio-focus interruption, sleep/wake and background/foreground. Respect system/user pause; the app must not force playback on simply because a delay expired.
- Multi-View with 2, 3 and 4 streams: navigate all filters and channel rows, change audio tile, cancel selection, enlarge/return, remove a tile and verify the 2-to-1 survivor. A failed/removed stream must not destroy a healthy peer.
- Change a Multi-View filter immediately after selecting a row; stale selection must not choose a row from the replacement list.

## Soak, performance and visual acceptance

Repeat search edits, clear/re-enter, navigate sections, open/close menus and fullscreen for an extended session. Record progressive slowdown, memory pressure, ANRs, crashes, black screens or lost focus. Compare cold/warm startup and navigation responsiveness to RC22 rather than guessing improvements from CI speed.

Check TV viewing-distance readability, safe edges/overscan, long text, card/panel proportions, focus contrast, light/dark or cinema appearance and restrained animation feel. No real-time blur, new visual modes or redesign is intended.

**Acceptance:** CI regression and payload verification are prerequisites, not proof of physical playback quality. RC22 stays the rollback; RC23 is not locked until the user accepts it.
