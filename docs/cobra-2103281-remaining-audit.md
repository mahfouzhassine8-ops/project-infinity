# Remaining Cobra audit from locked 2103280

Source lock: `ad18f93633ecc3ec74d121acf50bda873cd33cd0`.
APK: `Infinity-2103280-Audit-Followup-RC1.apk`, SHA-256 `e12654c0d81b6b04c4507f2c8bfde9e92761ab5a93ac16b86a3f89f9b7656870`.
Rollback branch: `rollback-cobra-2103280-before-remaining-audit-20261001`.
Forward audit branch: `candidate-cobra-2103281-remaining-audit`.

This first stage adds instrumentation only. It installs the exact locked APK and compiles a separate test package against the hash-verified archived source. No replacement product APK is built. It is not a completed audit or device-acceptance claim.

## Prior evidence reused

- 2103279 build/signing: run 36810766190, 519 tests and 20 protected renders.
- 2103279 Android runtime: job 110198831557 in run 36808284951, 21 scenarios on the identical final APK. The overall run failed an unrelated test fixture subsequently corrected.
- Additional exact-2103279 runtime: run 36816481777, 8/9 scenarios passed; natural recording completion was a genuine failure repaired in 2103280. Covers Multi-View PiP return, subtitles/audio, framework audio focus, menu bounds, bounded four-player observation and selected settings after process restart.
- 2103280 final build and recording runtime: run 36818383789, 522 tests, 20 unchanged protected renders, update over 2103279 and two recording scenarios including scrubber/rewind.
- Provenance correction: 34/35 inherited test files were byte-identical in 2103279, not 35/35. One test gained layout settling; its assertions were preserved.

## New executable checks

Consolidated exact-APK run 36822167443, instrumentation commit `847e0689b96b49acb5ab2298e37cf9fe82bd8413`: **12/14 scenarios passed**. The two failures reproduced stale Sports navigation callbacks. Initial run 36821571189 did not run app scenarios because the test APK filename in the harness was wrong; run 36821962403 was superseded/cancelled. The corrected run is the behavioral evidence.

1. Player lock/unlock and native long-press behavior.
2. Per-channel PiP disabled, Android Home and foreground return.
3. Display selection on the same active decoder.
4. Real DVR through Activity recreation, stop, second recording start/stop.
5. Sports Watch Live resolver and Smart Multi-View through generated provider broadcasts into actual decoding; Sports owner return.
6. Trailer callback URL handoff to Android. The destination is intercepted; this does not prove playback inside YouTube/browser.
7. Diagnostics action, Android document-result callback and real MediaStore content-provider ZIP writing. This does not exercise every third-party document provider.
8. More settings callbacks: display request, network policy, call policy, rewind buffer, Sports score/overlay and visual choices.
9. Separate force-stopped process persistence of those settings.

Some setup and controls use reflection/actual callbacks. Native pointer input is used for the long press; the earlier locked evidence also includes pointer-driven scrubber gestures. This does not establish exhaustive touch/accessibility coverage.

## Acceptance still requiring unavailable hardware or accounts

- Physical Fold inner/cover switching, Samsung split-screen/pop-up and live resizing on the device.
- Actual user channels/provider credentials, protected streams and provider-specific response formats.
- External YouTube/trailer playback, casting routes/hardware and third-party add-on outcomes.
- Physical telephone calls/audio routing; framework focus handling has passed separately.
- Hardware decoder capacity, frame rate, sustained memory/battery/thermal behavior under real streams.
- Exhaustive settings/control combinations and broader process-pressure recovery remain outside the completed evidence until explicitly tested.

These are unverified, not assumed to work. A lock is an approved baseline snapshot, not certification that all original acceptance requirements passed.

## Confirmed repairs in forward 2103281

- A delayed Watch Live resolver could open playback after a drawer move to Movies.
- A delayed Smart Sports Multi-View resolver could open panes after a drawer move to Shows.
- The Visual settings Immersive description still claimed fullscreen was suspended, although approved Watch controls/menu illumination is active.

The forward repair captures navigation generation, drawer owner, profile and a shared Sports action serial before resolving, and discards obsolete results before opening playback. Current actions retain the existing resolver and player ownership. The description matches the approved behavior. No locked source is modified.

The new APK will rerun all 522 regression tests and 20 render comparisons, plus the positive Sports action-to-playback scenario and both reproduced delayed-callback failures. The other 12 new checks remain recorded on the exact locked 2103280 APK; they are not being repeated without an affected code path. Build/runtime validation is pending.
