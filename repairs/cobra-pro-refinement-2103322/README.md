# Cobra Pro 2103322 refinement candidate

Locked parent: 2103321 / skin.infinity.diggz 1.0.5.201. Exact parent APK SHA-256 9c581733e803b7b41b35373ec67ab5ecae574964b642f34871062a097520422b; source 50ae3f9ffab6178912d730e24c614d93a676a8f7; run 37561829546. Candidate 2103322 is NOT locked.

## Approved changes
- Sports overlay strip: Pause/Play, Favorite, Subtitles, Unmute/Audio, Fullscreen, Stats, Multi-View, More. Existing callback indices preserved; only child order changes. Non-Sports retains six actions.
- Control-strip gestures retain ownership from DOWN through UP/CANCEL, including scroll edges, movement outside bounds, and wheel events. Long drags do not hide the strip. Reentrant/repeated action taps are bounded without stacking animations.
- Pro mini-player score alert is a child of the Hero badge row, six dp after the source badge (LIVE SPORTS for Sports), on the same top/height. Width is content-clamped before the reserved right-side status/watermark region, with one-line ellipsis. Insets are converted into Hero coordinates without adding parent-consumed insets twice. No video geometry is changed. Actual fullscreen player's separate chrome placement is retained.
- Retain meaningful-event fingerprints, favorite/pin/follow queue priority, coalescing, six seconds visibility and 380 ms fade. Exclude cached disabled leagues, suppress immediately for drawers/sheets/Power, cancel obsolete fade removal, and retain active alert lifetime when its overlay host changes.
- Sports Subtitles opens the existing Audio & subtitles sheet on the current mini-player session, including submenu returns; regular preview CC behavior remains unchanged.
- Preserve paused Main/Sports/Preview session, pane and mute state on Pro view-mode return. Explicit Hero pane changes still release playback; stopped panes do not acquire playback.
- Report rejected Sports broadcast lookup with actionable feedback while preserving the active session.

## Preservation and validation
Only CobraProUi.java.in and InfinityLiveActivity.java.in change in the 254-file Android source map. The build merges only the compiled Android layer/version into exact 2103321. Native libraries, Kodi payload, assets/resources, skin ID/version, manifest identity/contracts, resource IDs, permanent signing identity and protected compiled behavior are checked against that APK. No native rebuild, provider reset, database reset or skin change.

The six inherited suites are retained, with the single superseded top-right mini-alert geometry assertion replaced by badge adjacency. Three focused suites cover control dispatch/gestures, score geometry/queue/suppression and paused-session return/rejected lookup. Production Android views and controlled player/feed fixtures are used on API 35 Robolectric; screenshots contain no decoded provider video.

Runtime results must be taken from the successful candidate run, not inferred from this recipe. Physical fold/cutout hardware, phone calls, real decoder/provider playback, second-stream decoding, time-shift buffers, reminder delivery, recording and install-over data retention still require actual device/provider acceptance. 2103321 remains the user-locked base.
