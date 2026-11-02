# INFINITY PREVIEW — Individual video resume memory
## User-requested feature addendum, November 2, 2026

**Status: Approved feature request / implementation specification, NOT implemented or signed.**
**Base:** exact user-locked 2103447 production player from `lock/infinity-cobra-2103447-user-locked-20261102`, with approved cinematic UI design and Light/Dark variants from `lock/infinity-preview-2103447-cinematic-ui-design-20261102`.
**New work branch:** `work/infinity-preview-2103447-per-video-resume-20261102`.
**Mission:** Remember a separate playback position for each seekable video opened through **Infinity Preview**, including after closing the player, switching videos and restarting the phone.

### User experience

- Open movie A, play to 01:17:35, Stop/Close/Back: remember A at 01:17:35. Open movie B, reach 00:09:42: remember B independently. Reopen A: offer **Resume at 01:17:35** and **Start Over at 00:00**. Reopen B: offer 00:09:42. No cross-video progress leakage.
- The resume choice should use the approved clean cinematic styling in **both Light and Dark mode**, with readable times and accessible focus/touch controls. Do not block or obscure a video indefinitely with a non-dismissible loading overlay.
- Save progress periodically while actively playing (e.g., ~10 seconds) and immediately for Pause, Stop, Back/Close, background, interruptions and normal lifecycle teardown. Persist it in **private Preview-owned storage** so process death/phone reboot does not discard it. Use non-blocking or bounded storage writes; never delay UI or trigger ANR.
- On next open, after the stream is prepared, restore the chosen position reliably (seek supported media only), and update elapsed time and scrubber accurately. Do not cause duplicate decoding/opening or race with incoming replacement video B.
- For a nearly finished video (e.g. last 30 seconds or 95% reached), mark it finished/reset resume so the next open starts from the beginning. Do not automatically resume from the last few seconds of credits.
- For items with very short progress (e.g. <30 seconds) and live/nonseekable streams, start normally without an unnecessary prompt. For an unsupported/revoked provider grant, show a helpful error; never launch Kodi to recover.
- Offer an isolated way to clear a video's remembered position or clear only Infinity Preview history; do not touch Kodi's watched state, bookmarks, databases or Cobra persistence.

### Media identity and cross-app coverage

- Store progress keyed to a stable video identity: use the best available canonical file/document identity and stable metadata where granted; include provider authority/document ID for SAF content URIs, and local path/file identity only with appropriate permissions. Use a collision-resistant keyed/hash representation for private progress records.
- **MiXplorer, Samsung My Files, Android Files, Downloads, Google Drive and other compatible external apps** all enter through the *same* existing Infinity Preview video gateway. No app-specific rules.
- The same underlying video opened from different apps should share progress **when the available URI/document identity can be reliably correlated**. A Google Drive cloud object and a separate local download, or two unrelated providers returning unrelated identifiers, cannot reliably be identified as the same media just because their filenames match. Never claim universal cross-provider identity.
- Never save full signed cloud URLs, credentials, auth headers, query tokens, private document contents or media bytes in history; do not try to retain/reuse a temporary permission grant. The user must still obtain valid access when reopening media.
- Invalidate or distinguish an existing resume point when the media has changed (replaced file, materially changed size/duration/version metadata), preventing seeking to a stale position. Keep the record store bounded and do not scan/hash huge video files on the UI thread.

### Absolutely protected functionality and scope

- Do **NOT** change the existing original Infinity Kodi VideoPlayer, Umbrella/add-ons, Continue Playing, watched/resume system, Cobra, native libs, shutdown, launcher or standard Choose Your Experience.
- Do **NOT** edit or replace the frozen signed **2103447** APK and locked branch. All feature changes occur on a new branch and must produce a separate, higher-version, original-key-signed install-over **testing APK** only after focused QA; no uninstall or data clearing.
- Preserve the **horizontal swipeable control strip**, **horizontal seek/scrub timeline**, all current 2103447 actions (Play/Pause, Stop, ±10s, Mute/Volume, Audio, Subtitles, Display Best Fit/Fill, rotation, source return, error/retry), independent player engine/process, URI/grant handling, request-order safety, and all other approved behavior.
- Preserve the separately locked **cinematic Light and Dark mode** UI design. The resume UI must function identically in both themes.
- Keep progress persistence **within Infinity Preview alone**, preferably a small isolated Preference/SQLite namespace with no migration of Kodi/Cobra settings or databases. No unexpected background service, timer after close or watcher that launches the engine.

### Focused acceptance checklist

1. A/B/A/B switching proves each video remembers its own timestamp; same file reopening and rapid replacement remain safe.
2. Close, Stop, Pause, Home, background, screen-off, process death and reboot preserve last committed progress; resumed player does not wake Kodi.
3. Resume/Start Over buttons actually seek or reset, correct seekbar/timing; completed/short/nonseekable and invalid media behave correctly.
4. URI identity is stable for repeat requests from each supported provider **where observable**; no token leakage or false merge of distinct same-named videos.
5. Player in cinematic **Light/Dark** mode retains all horizontal strip/seek gestures and complete controls on outer/inner Fold, landscape and compact windows.
6. Exact signed 2103447 preservation comparison shows only scoped Preview persistence/UI-owner and corresponding build/signature changes; Cobra/Kodi/native/other components byte-preserved.
7. Report separately which checks passed host tests, Android emulator and actual physical Galaxy Fold; do not label physical acceptance complete without user's test.

**Proceed with this as a narrowly scoped addition to Astra's Infinity Preview UI work. Do not restart, refactor unrelated components, or conflate it with Kodi's existing watched/resume system.**
