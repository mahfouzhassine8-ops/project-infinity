# Cobra 2103199 — focused physical-device acceptance

Status: TEST CANDIDATE. No physical-device pass is implied by source, host, Robolectric, build, signature or APK-byte checks. Preserve the existing application data and exact 2103197 rollback. Do not uninstall or clear data to force an update/downgrade.

Record device/OS, installed version, active profile/source, appearance, Fold screen, orientation, network mode and actual network path. Use existing controls only. Capture a short video or screenshots when geometry, captions or SystemUI differs from the expected result. Export diagnostics immediately after a failure; note the action and wall-clock time. Do not publish provider credentials.

## 1. Installation and existing product

- Install over the current signed app. Confirm version 2103199, sources, profiles, preferences, recordings and existing theme selection remain available. This is the actual data-preserving update check.
- Confirm the same Home/experience choices, five guide views, original player menu and four-button toolbar. No extra player hub, recent-channel strip or new toggles should appear.
- Open TV Sources and refresh one known-good source. Cancel an edit; confirm nothing changed. Switch profiles and verify favorites/My List remain scoped correctly.

## 2. Playback and rewind — highest priority

Use the reference channel first, then the problem channel. Start fresh sessions rather than comparing cumulative counters across network changes.

1. Play live for at least three minutes. Record first-frame delay, audible/video stalls and diagnostics. READY means retained rewind history; it is not evidence a seek worked.
2. Enter rewind with the existing control. Confirm the actual picture/audio move backwards, the timeline moves continuously while playing, and there is only the existing unified blue timeline.
3. Drag and hold the scrubber for several seconds. Its preview must stay under your finger. Release at the oldest available point; then play for a few seconds and verify rewind becomes available again.
4. Pause, rewind, fast-forward, and enter/leave local rewind. None of those transport changes should unexpectedly resume a deliberately paused player.
5. If a source interruption occurs, press Pause during recovery. It must remain paused after data returns. Then Resume must work. Repeat in mini-player.
6. Jump back to live. Confirm current programme/picture, audio, position and live-edge indication agree. Change channels; old buffer/positions must not leak into the new channel.
7. Repeat mini-player → fullscreen → mini-player ten times, once while rewound and once while paused. Repeat a channel change during recovery. Check no old callback changes the replacement player.
8. Test provider catch-up separately on a source that actually supports it; do not count local rewind as a catch-up pass.

## 3. Every aspect/display mode — visible results, not preference values

Use a known test image/video with a circle, square grid and edge markers, plus ordinary 16:9 and 4:3 content. Repeat on inner/cover portrait/landscape, paused and playing. Open/close the channel drawer, switch between channels with different saved aspect choices, rotate, then return from PiP. Observe the actual picture and subtitle placement.

| Existing option | Visible acceptance |
|---|---|
| Best Fit | Entire source visible, correct source shape; remaining bars follow the source/viewport ratios. |
| Crop / Fill | Viewport filled, source shape maintained, symmetric intentional crop. |
| 16:9 | Existing forced 16:9 presentation visibly applied. |
| 4:3 | Existing forced 4:3 presentation visibly applied. |
| Wide 1.10x | Existing horizontal enlargement visibly applied. |
| Wide 1.25x | More horizontal enlargement than 1.10x. |
| Wide 1.40x | More horizontal enlargement than 1.25x. |
| Short + Wide | Existing horizontal/vertical modification applied consistently. |
| Zoom 1.25x | Existing proportional zoom, centered intentional crop. |
| Zoom 1.50x | More proportional zoom than 1.25x. |
| Zoom 2.00x | More proportional zoom than 1.50x. |
| Custom Width / Height | New untouched values really show 100%/100%; width and height controls act on their named axes; reset restores 100%/100%. Existing saved custom values remain respected. |
| Fold Adaptive | Actual usable viewport drives recalculation after Fold/rotation/drawer changes. Preserve source shape and the existing conservative crop policy; no stale dimensions or unexplained extra regions. |

For each mode verify saved global default, per-channel override and Reset this channel separately. PiP intentionally uses Best Fit and restores the selected mode after returning. Expected bars in a fit mode are not a defect; unexplained unused screen outside its viewport is.

## 4. Lifecycle, Fold and SystemUI

- Perform ten inner↔cover transitions and ten portrait↔landscape transitions across Live, Movies/Shows, Recordings, Settings and Profiles. Check current page, scroll, pending loading state and controls remain usable.
- Enter/exit multi-window and PiP; return by tapping PiP and by reopening the app. Check the intended destination, no stale overlays, no unexplained top black region, status/navigation-bar colors and correct safe areas/cutouts.
- Test rotation lock/unlock, screen lock/unlock, Home→resume, and a phone call. Preserve established audio-focus/video behavior; no second audio owner or surprise autoplay.
- Test Normal and Extended background behavior separately, including existing notification pause/stop controls. Verify Stop actually ends playback and an old callback cannot restart it.
- Test those same Normal/Extended actions from the existing Kodi skin bridge as well as Cobra Settings. Confirm a separate untrusted application cannot start the background-control activity; this Android permission enforcement has not been physically tested.
- Stop or change channel while a provider read is stalled. Confirm the old request/session ends, its cache is eventually removed, and repeated Stop does not create repeated cleanup work.

## 5. UI, themes, input and captions

- Repeat the player menu, Channel playback, Health Center, aspect chooser, source manager and settings in Light, Dark, True OLED Black and Follow System (both system appearances). Headings, detail rows, close icons and focused/selected states must remain readable.
- Rapidly move D-pad focus while source/settings rows animate. No displaced rows, delayed focus, trapped navigation or double activation. Repeat using touch and a paired D-pad on the Fold.
- With many profiles on short landscape, scroll to and activate the last existing profile. Check source and subscription labels during rapid source switching/loading.
- Set channel subtitle default Off, then explicitly select an available subtitle for the current session. Cues should appear; explicit Off should hide them. Start a new session to verify the saved default remains Off. Open the player drawer and confirm captions follow the video viewport.
- Check guide, recordings, schedules, Movies/Shows and Continue Watching text wraps as lines rather than displaying literal backslash-n.
- Test installed-theme reset/restore using existing recovery controls. Built-in palette tests do not certify every imported theme.

## 6. Buffering comparison and long session

- Compare reference and problem channels for at least ten minutes each on the same path, with fresh sessions. Repeat on a second already available path (such as existing Wi-Fi/VPN) when relevant; record exact switch times.
- Classify startup connection failure, sustained slow media arrival, upstream delivery pauses, and decoder/frame-drop behavior separately. Do not declare a buffer-size fix from a faster network session.
- Run at least one 60-minute session plus 30 channel changes and 20 mini/full/PiP/background transitions. Check memory trend, heat, dropped video/audio, responsiveness and eventual resource release.
- Export before and after any failure. Confirm display_geometry, playback/session, network-family, buffer/rewind and attachment-age fields match the observed state. A TextureView matrix is computed geometry, not proof of rendered pixels. Diagnostic history is bounded; old attached logs are not current-session proof.

## 7. Recordings and inherited media integrations

- Record and replay an ordinary direct TS channel, an HLS media playlist, and an HLS master playlist with muxed TS audio/video. Confirm real A/V content, relative/redirected segment loading, duration, Stop, schedules and retained files using existing controls.
- Stop an HLS recording during download and during playlist polling. Stop should be observed between reads; an already blocked request may still wait for the existing timeout (20 seconds HLS, 30 seconds direct). Cancellation should not produce a false provider-error notification.
- Encrypted HLS, initialization maps, byte ranges and separate-audio variants are not supported by the existing TS concatenator. Confirm they report through the existing recording error path instead of appearing successfully recorded as playlist text.
- Exercise existing external media/search/recommendation artwork and YTDL playback integrations. Confirm ordinary redirects and streaming still work and stalled/cyclic endpoints fail cleanly. The separate exported file-provider authorization finding requires benign caller/consumer testing before release acceptance.

## Release gate

Record PASS/FAIL/NOT TESTED for each item with evidence. Any failure in playback, rewind, aspect, Fold, PiP, SystemUI, update/data retention or good-channel regression blocks a final lock. All physical items start NOT TESTED. Retain the candidate as a test build until those results and unresolved audit findings are reviewed.
