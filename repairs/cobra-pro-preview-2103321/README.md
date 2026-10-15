# Cobra Pro 2103321 candidate — locked 2103320 parent

Locked base: APK 2103320 / skin.infinity.diggz 1.0.5.201, commit 8413ef73805411e0469138868118fab38e295659, run 37546291952. Base APK SHA256 b2e08c08c2db3a70f531bf22e4bcb1bdd9160ba03e2fbc3ce79b2503f012c8d1. Source map: 254 exact files, SHA256 bd357112b0999e4e2ad8555604588c7dd0fa3ba696de24c5179e01dc52b3c854. Candidate 2103321 is not a new lock.

## Required behavior
- Exactly seven panes: Main, five regular Preview panes, independent Sports. Sports data refresh never substitutes extra sports preview panes.
- User clarification on October 7 UTC: swipes restore Preview-ready artwork and program context, and WAIT for a Preview tap. No swipe/focus autoplay. Leaving any pane releases the previous video.
- Preview tap starts muted within the same Hero. Unmute changes audio on that same session, exposes controls, retains Hero context and pane, and never writes Main's remembered channel.
- Regular channel-row Play overrides Preview, routes to Main, and starts muted. Main remembers only explicitly played regular channels, not Sports. After swipe-away Main returns stopped with Play ready.
- Sports Watch/Play stays in dedicated Sports, starts muted, retains its own game and leaves Main untouched. Only confirmed live broadcasts are playable. No inherited non-sports or expired video.
- Fullscreen transfer and return preserve the session and mute choice. Return does not revert to Preview or overwrite Main with Sports.
- Keep overlay controls and constant full video geometry. Sports horizontal controls retain all six playback actions plus Stats and Multi-View. Control-strip gestures never navigate panes.
- Sports cards reuse actual-playing dot policy: live gameplay or selection alone is insufficient. Preserve cyan and Night Cinema amber.
- Match approved Live Now header: league identity and small red LIVE indicator together at left; no detached red pill. Preserve score, teams, broadcaster, period/clock, Play and options.
- Compact translucent score notifications near safe top edge, wrap content rather than cross video. Six-second display then fade. All live games eligible; favorites lead queued alerts. Coalesce per game, expire at two minutes, ignore identical/clock-only refresh. Honor Spoiler Protection and ticker preference, regardless of player-control visibility. Keep feed polling cadence.
- Preserve exact Game Options path fix (fullscreen > Channels > Sports > options), teams, settings, reminders, recording, Multi-View, timeshift, appearances/Ambient, Power, drawer and all five view modes.

## Preservation and validation
Only InfinityLiveActivity.java.in and CobraProUi.java.in are source changes. Build and sign over the exact locked APK with resource IDs, manifest identity, signer, native libraries and assets protected. Verify protected compiled instructions including exact compiler API helper bodies. Run the six inherited regression suites with only explicitly superseded expectations corrected and focused new integration cases added; retain unrelated tests. Capture actual production Android views from API35 controlled fixtures. No physical-device, decoder/provider playback, reminder delivery or recording-execution claim follows from these tests. Report the candidate's real results and blockers.
