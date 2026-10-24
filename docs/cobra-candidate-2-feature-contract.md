# Infinity Cobra — Full Feature Candidate 2 Contract

Candidate 2 is an independent Infinity-owned implementation. CobraTV is used only as a public behavior/UX reference; no proprietary CobraTV code, assets, account backend, or bundled content are copied.

## Product contract

- One Android package and one launcher: `com.projectinfinity.kodi`.
- Infinity remains the normal Kodi-based experience.
- Cobra remains an internal experience in the same APK.
- `Open Cobra Live` remains available from Infinity's power/stop menu.
- Candidate 1 (`8778cada`) is the rollback baseline.
- Kodi's normal player/renderer contracts remain untouched.
- Cobra visual presentation must remain ZIP-updatable through `script.infinity.cobra.theme`; native rebuilds are reserved for native/runtime changes.

## Cobra behavior reference translated into Infinity-owned requirements

### Live TV + provider layer

- Xtream-compatible login with server, username and password.
- M3U/M3U8 playlists, XMLTV EPG, provider headers, redirects and plain HTTP provider support.
- Multiple enabled playlists/providers available at the same time.
- Each provider can be renamed, enabled/disabled, assigned a colour and icon, and refreshed independently.
- Combined favourites, recent channels and global search across enabled providers.
- Provider identity is visible on channels, movies and series.
- Large-list parsing must stay off the UI thread and must not block touch/D-pad navigation.
- Specific network/auth/provider errors; no generic `cannot load` dead end.

### Guide / EPG

- Multi-day guide with approximately seven days retained where supplied.
- Now/next in channel rows.
- Searchable programmes.
- Programme detail drawer/sheet with Play, Remind, Record and Catch-up actions where valid.
- Custom XMLTV URL per provider.
- EPG failure never invalidates a playable provider.

### Player

- Media3/ExoPlayer owns Cobra playback.
- HLS and MPEG-TS with provider-header support, redirect support and TS/HLS fallback.
- Decoder fallback, stall recovery and retry.
- Audio-track and subtitle-track selection.
- Aspect/fit controls and quick channel switcher.
- Touch and D-pad first: large targets, deterministic focus, no hidden focus traps.
- Fast player-to-guide and guide-to-player transitions.
- Limited in-memory live pause/timeshift buffer; provider catch-up used when available for longer rewind.

### Multi-View

- 2, 3 or 4 simultaneous live tiles where device/provider limits allow.
- Exactly one audible tile at a time.
- Tap/focus changes audio owner without recreating the whole Cobra Activity.
- Adaptive 1x2, 2x2 and portrait-stacked layouts.
- Per-tile error reporting rather than collapsing all feeds.

### DVR / recordings

- Record current live channel.
- Record from programme guide.
- Schedule future recording.
- Persistent scheduled-recording database/state.
- Foreground recording service so recording survives leaving the Cobra Activity.
- Recording library with play, rename and delete.
- Storage-space guard and graceful out-of-space failure.
- MPEG-TS direct recording and HLS segment recording.
- Watch one / record another when provider connection limits allow.
- Recording diagnostics must never expose provider credentials.

### Reminders

- Create/remove programme reminders.
- Persist reminders.
- System notification when a programme is due.
- Opening a reminder returns to the relevant Cobra channel/programme.

### Catch-up / archive

- Detect provider archive/catch-up capability.
- Expose past programmes as playable only when the provider marks the channel/archive as available.
- Build catch-up URLs from the user's own Xtream-compatible provider contract; no third-party service is bundled.

### Movies / Series / VOD

- Xtream movie categories and movie library.
- Xtream series categories, season selection and episode selection.
- Movie/episode playback through Cobra's Media3 player.
- Continue Watching with persisted position.
- Watchlist/My List.
- Search across enabled provider VOD catalogues.
- Provider badge remains visible on VOD entries.
- Resume/restart choice for partially watched items.

### Profiles / parental controls

- Multiple local Infinity Cobra profiles.
- Per-profile favourites, watchlist, recents and Continue Watching.
- Optional profile PIN.
- Optional adult-category filtering/locking.
- Credentials remain provider-level, not copied into profile exports.

### My Files

- Android document picker for user-owned local video/audio files.
- Play selected local media through Cobra Media3 where supported.
- No broad-storage permission requirement for user-picked documents.

### Discover shell

Candidate 2 provides an Infinity-owned Discover surface so Cobra is not just a channel list. The shell can host News, Weather, Radio, Podcasts, Audiobooks, Trivia, Recipes, Sports, NASA, World Clock, Ambient and My Files modules. Remote/public-content modules must use public/legal endpoints and may be expanded with fast ZIP updates; paid/bundled television content is explicitly out of scope.

### Cast / route handoff

- Expose a system media-route/cast handoff entry point where Android provides a compatible route.
- No CobraTV cloud/account dependency is copied.

### Health Center bridge

- Cobra writes a redacted diagnostics snapshot that Infinity/Kodi Health Center can collect.
- Snapshot includes: Cobra version, active screen, active provider ID/hash (not credentials), channel/media type, player state, Exo error code, retry count, buffer state, multiview tile count/audio owner, recording state, guide state and last provider/network failure class.
- Provider URLs/usernames/passwords, playlist URLs with credentials and stream URLs containing credentials must be redacted.
- Diagnostics are local and user-owned.

## Visual / interaction contract

The interaction model should be recognisably close to the reference app while remaining Infinity-authored:

- TV-first left navigation rail.
- Content stage with compact header/status treatment.
- Strong focused state with quick D-pad movement.
- Guide organised around provider/category/channel/programme hierarchy.
- Player chrome kept minimal and fast to dismiss.
- Dark, premium, low-glare surfaces with a restrained accent.
- Provider colour/icon badges.
- Smooth page transitions and no giant empty placeholders.
- Phone/Fold/tablet touch targets are larger than the visual glyphs.
- Theme/layout tokens live in the Cobra theme add-on so visual polish does not require a native APK rebuild.

## Build gates

Candidate 2 is not publishable unless CI proves the source contracts for:

1. one package / one launcher;
2. 2–4 feed Multi-View with one audio owner;
3. Xtream + M3U + XMLTV provider support;
4. multi-provider catalogue aggregation;
5. movie + series APIs;
6. DVR foreground service + schedule persistence;
7. reminders;
8. catch-up capability detection;
9. profiles + parental state;
10. redacted Health Center diagnostics;
11. external ZIP-updatable UI/theme contract;
12. no CobraTV proprietary package/code/assets;
13. no changes to the normal Kodi application player/renderer.

On-device acceptance is still required for the user's real provider, device decoders, connection limits, scheduled DVR timing and 4-feed thermal/performance stability.
