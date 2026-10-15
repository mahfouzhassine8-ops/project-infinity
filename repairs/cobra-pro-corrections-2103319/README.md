# Cobra Pro corrections candidate 2103319

Locked parent: exact APK 2103317, SHA-256 `7f21205b1abe980f398a6dc4b87825bf84190395b9972d939d26aaeaf7b0946c`; skin `skin.infinity.diggz` 1.0.5.201. Candidate 2103318 remains a reference, not a locked parent. No native rebuild or skin/data replacement.

`apply.py` applies the retained 2103318 changes to the verified 254-file locked source export, then fixes the user's reported defects in only `InfinityLiveActivity.java.in` (Cobra activity) and `CobraProUi.java.in`.

- Explicit row Play and fullscreen return own playback until a hero swipe restores the Preview panel. Browsing does not retune the owned player. Its texture is hidden while a different preview panel is selected, without releasing/pausing/tuning it. Tapping this preview panel does not hide its Preview action.
- Controls reserve the same bed and viewport when hidden or revealed; the Sports compact/hold gesture remains.
- The Sports tab stops and clears unrelated playback. Valid live-game broadcasts may continue; game completion invalidates a previously confirmed session. Resolver results prepare the sports selection only, and explicit Watch validates current live state before playback. A carousel swipe alone cannot stop an owned player and cannot show unrelated video as a sports preview.
- Appearance is resolved before ambient material policy. Light remains Light; Dark resolves to OLED; Follow System respects Android's Light/Dark state. Off disables effects without overriding appearance. Subtle button fills respect light ink/surfaces. Existing Immersive and Night Cinema policies remain.
- The candidate retains the 318 sports, schedules, teams, reminders, spoilers, ticker, recording callbacks, Multi-View resolution and allocation checks, Live-edge seek, Quick Peek, drawer, navigation selection, and Power sheet behavior.

The test suite updates two obsolete 318 expectations (player resizing and non-sports carryover) and adds regressions for user-reported behavior, all five view-mode palettes with all ambient settings, preference transitions, confirmed/expired Sports broadcasts, and carousel-only browsing. The other five retained suites still run.

Build through `.github/workflows/infinity-cobra-pro-corrections-2103319.yml`. The existing package gate verifies the 317 APK/source association, allowed source deltas, protected assets/resources/native payload equality, unchanged resource IDs, manifest identity, unchanged compiled families outside Cobra and documented equivalent compiler API bridges, and permanent signing certificate. Tests must pass with zero failures/errors/skips before packaging.

Physical device/provider decoding, Fold transitions, sustained Multi-View playback, reminder delivery, recording execution, and actual update-over-user-data acceptance remain hardware checks. Controlled Android tests and static renders must be reported as such. The locked base stays 2103317 / 1.0.5.201 until the user explicitly locks another candidate.
