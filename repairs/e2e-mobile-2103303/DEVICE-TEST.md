# Infinity 2103303 — device acceptance pending

This is an unlocked repair candidate for `com.projectinfinity.kodi`, based on 2103302. No physical Samsung test result is claimed. A successful build or automated test run does not satisfy the acceptance matrix.

Use the matched APK 2103303, skin 1.0.5.191 (`skin.infinity.diggz`) and Command Center 0.3.5.20. Keep the existing internal skin ID. Install the controller before the skin using Kodi's normal add-on ZIP installation, then restart with the matched APK. Do not uninstall Infinity or clear its data. Keep a device-side backup of the current add-ons and userdata before testing; the source rollback does not contain private device configuration.

The source rollback is `rollback-infinity-2103302-before-e2e-repair-20261003`. The exact 2103302 APK SHA-256 is `bcd316d398925f2cdb01f4d1ce5030664ea9a4007598d7acf6440adb240b9b50`. Restore the three matching prior components if rollback is needed. Android may restrict APK downgrades; do not uninstall to bypass that restriction and lose data.

## Required matrix

Repeat each applicable flow below in every row. Record a video, session ID, Android bounds, native requested/committed bounds, skin generation and responsive profile for layout or input failures. All rows are **NOT RUN** until actual device evidence is attached.

| Condition | State |
| --- | --- |
| Cover-screen portrait | NOT RUN |
| Unfolded square-ish inner display | NOT RUN |
| Portrait rotation | NOT RUN |
| Landscape rotation | NOT RUN |
| Split-screen | NOT RUN |
| Pop-up window | NOT RUN |
| Live resize and fold/unfold transitions | NOT RUN |
| Cold launch | NOT RUN |
| Warm launch | NOT RUN |
| Exit → immediate relaunch | NOT RUN |
| Exit → delayed relaunch | NOT RUN |
| Background → foreground | NOT RUN |
| With active playback | NOT RUN |
| Without active playback | NOT RUN |
| Light theme | NOT RUN |
| Dark/OLED theme | NOT RUN |
| Touch input | NOT RUN |
| Android keyboard open | NOT RUN |
| Android keyboard closed | NOT RUN |
| Android TV / remote-only fallback | NOT RUN |

## Flows and expected evidence

1. **Chooser and weather.** Confirm HM emblem only, no experience-card slogans, and exactly `TWO UNIVERSES.`. Leave the chooser visible for at least a minute, including a background/foreground cycle; this user delay must not count as slow Kodi startup. Kodi handoff starts only when Infinity is activated. With networking disabled, a valid prior Kodi weather snapshot still appears; with no snapshot, the existing unavailable state appears without delaying first draw. Selection, artwork and settings buttons retain their actions.

2. **Home and drawer.** At rest, only the logo/hamburger capsule occupies the top-left; no full-height mini rail or empty gutter. The hamburger does not start highlighted. Tap it: the existing drawer unfolds downward from that capsule over a slightly dimmed home, with no home relayout. Close, navigate, rotate and reopen; focus must clear after dismissal. Check every retained route. Movies opens Infinity Movies and TV Shows opens Infinity TV. Back returns to the previous Infinity screen; no generic empty Videos → Titles window or cross-hub leakage.

3. **Delayed takeover and idle responsiveness.** Leave Home idle for at least five minutes with Ambient Off, Subtle and Immersive, both with and without existing playback. Navigate periodically, fold, rotate and background during sampling. No unexpected foreground video layer or touch interception is allowed. Collect the raw evidence export if a freeze occurs; the original delayed-takeover owner has not been proven from the historical report.

4. **Dialogs, loading and source selection.** Ambient Home contains only Off/Subtle/Immersive and X in a tight panel. Keep skin? contains its logo, title, message and Keep/Revert actions inside the panel; X and Back perform safe cancellation/revert. Playback failure has readable text and X, without a floating OK button or retained focus after dismissal. Touch each button at its center and all visible edges. Loading treatment is intentionally positioned and disappears when complete. Select movie sources from each installed provider: title, artwork, metadata and source list stay contained; list scrolling stays inside; Back closes the overlay before leaving the movie. Provider-owned custom windows require their own runtime check.

5. **Tap versus hold.** On Install from repository and representative items across home, add-ons, settings, sources and context lists, repeat ordinary taps, quick consecutive taps, deliberate holds, scrolls, a hold followed by scroll, a fold during contact and a cancelled contact. Each tap performs one primary action. Only an intentional stationary hold opens the context menu. Verify its placement and touch targets near each screen edge.

6. **Settings and branding.** Check General, Home, Customize, Appearance, Advanced, Widgets, Infinity and Extras with long labels/values. Labels and switches must not overlap; row and switch taps change state exactly once. Categories use two columns when wide and one when narrow, with no clipped breadcrumb/title. Resize without leaving the screen. Audit logo assets in home, capsule, expanded drawer, settings, dialogs, notifications, loading and player.

7. **Android IME.** Exercise global/add-on search, File Manager, source names, paths, URLs, repository addresses, credentials, text settings, PIN, numeric, IP, date and time inputs using Samsung Keyboard and the selected alternative IME when available. No Kodi keyboard appears on mobile. Test Unicode, selection, cursor replacement, paste, password masking, enter/search and numeric validation. First Back hides the IME; the next Back cancels the text dialog. Resize/fold while editing, then background and return. Android TV retains its remote keyboard path.

8. **Movie and player.** Open details, sources and an explicitly requested trailer. Only the intended foreground layer owns input, and Back unwinds one layer at a time. The deferred movie-video rectangle must match the baseline. The player header keeps title/year/duration/chapter/clock and has no inert arrow. The single swipeable rail order is Drawer, Volume, Back 30, Previous, Play/Pause, Next, Forward 30, Stop, Subtitles, Display, Repeat, Lock. No second row, More or overflow. Rail swipes must not seek through the scrubber above it.

9. **Volume.** Enter volume mode during playback. Only the vertical glass capsule remains; no header, scrubber, timestamps or normal rail. The speaker is at the bottom; volume rises upward, with readable percentage. Test drag, increment, decrement and mute. It may extend beyond the old rail footprint. Back or the inactivity timeout restores normal controls. Playback must continue throughout.

10. **Lifecycle and performance.** Repeat normal exit/relaunch and background/foreground with and without playback. A successful normal exit records `native.CXBMCApp.Destroy.complete` for that PID/session and does not use a force-stop timer. Main must not reopen while its previous owner is closing. If a controlled test stalls teardown beyond 15 seconds, the chooser offers explicit recovery; merely observing a stall must never kill/reset the app. Inspect five-minute idle and background CPU/RSS samples and Android exit records. Background optional sampling/observers must stop; no persistent invalidation, decoder leak, new crash, black relaunch or teardown stall is accepted.

11. **Health Center.** Export raw trace evidence after each lifecycle or freeze test. Distinguish official Android crash, official ANR, internally observed stall/recovery, actual slow startup, chooser user delay and normal exit. Confirm real Android bounds and current native requested/committed geometry; a destroyed surface may legitimately report cleared native geometry, but a visible initialized window must not remain 0×0. The square inner display uses the approved retained `unified` profile with its selection reason, exact session and skin generation. Old retained traces must be identified as historical.

## Open evidence requirements

Historical SIGSEGVs cannot be symbolicated reliably from the provided lossy text export. Obtain the original binary tombstones and exact build-ID-matched libraries for each crashed build. The three recorded crashes predate the completion of the 2103302 build; do not attribute them to that APK based only on a current version label. Current symbol files and future raw traces must be kept together.

Acceptance remains blocked until the matrix passes and the delayed overlay, crash ownership, CPU, cleanup and relaunch behavior are demonstrated on the target device. No change to the deferred movie-video vertical framing is included.
