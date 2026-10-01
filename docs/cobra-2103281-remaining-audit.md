# Remaining Cobra audit from locked 2103280

Source lock: `ad18f93633ecc3ec74d121acf50bda873cd33cd0`.
APK: `Infinity-2103280-Audit-Followup-RC1.apk`, SHA-256 `e12654c0d81b6b04c4507f2c8bfde9e92761ab5a93ac16b86a3f89f9b7656870`.
Rollback branch: `rollback-cobra-2103280-before-remaining-audit-20261001`.
Forward audit branch: `candidate-cobra-2103281-remaining-audit`.

The initial baseline stage added instrumentation only. It installs the exact locked APK and compiles a separate test package against the hash-verified archived source. That stage did not build a replacement product APK. The repair stage below produces the forward 2103281 candidate. It is not a completed audit or device-acceptance claim.

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
10. Late Sports Watch Live result after drawer navigation (failed on 2103280).
11. Late Smart Sports Multi-View result after drawer navigation (failed on 2103280).
12. Extended background service starts, survives Home, and stops when Normal is selected.
13. Profile PIN rejection and favorite isolation/restoration through profile APIs.
14. System document-result callback supplies a real MediaStore content URI that decodes and seeks, then returns to Movies. The picker launch is intercepted; this is not a manual system-picker walkthrough.

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

The new APK passed all 522 regression tests and 20 byte-identical render comparisons, plus the positive Sports action-to-playback scenario and both reproduced delayed-callback failures. The other 12 new checks remain recorded on the exact locked 2103280 APK; they are not being repeated without an affected code path. Build/runtime validation passed in run 36823023157 on source commit `85126e37c322067718b6309e11246697b29ccd2e`.

## Captured-screen review

Reviewed the baseline runtime captures for Watch playback, Smart Multi-View, local-file playback, Display selection, recording recreation, long-press behavior and the post-restart main screen. The captured controls and Display rows are readable and within bounds. Transient Android toasts overlap some controls in the captures; they are not treated as permanent layout defects. These are generated-content emulator captures, not a comprehensive visual acceptance of every theme, screen or physical Fold configuration.

## Candidate delivery and final validation

- APK: `Infinity-2103281-Remaining-Audit-RC1.apk`, version 2103281 / `1.0.9-Remaining-Audit-RC1`; 93,536,543 bytes.
- SHA-256: `4c119343d623be5c15233e7b1ed7fa82e3d1f92c3a5ec56f7d3f85b0707cbfe5`.
- Existing certificate retained: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Build job 110242492248: successful packaging/signing, 522 tests, 20 protected renders unchanged, 232 other shell source files unchanged. Only Activity source and version declaration changed in the reconstructed shell.
- Runtime job 110244131340: install locked 2103280, update in place to 2103281, launch and all three Sports scenarios passed on Android API 30. This is emulator update evidence, not a user-data update test on the Fold.
- Candidate artifact 11144128927; source/regression evidence 11144069407; runtime evidence 11144740658.
- 46 native libraries, 4,039 assets and Android resources remain byte-identical. Local independent comparison checked 4,151 native/asset/resource entries against the locked APK.
- Reviewed the two repaired navigation screenshots: delayed actions no longer open video or Multi-View over the selected Movies/Shows destinations. These empty fixture catalogs do not validate real provider catalogs. No fatal-exception, native-fatal-signal or ANR markers were found in this bounded runtime log.

The APK is an **unlocked forward candidate**. Both 2103279 and 2103280 locked branch refs were rechecked and remain unchanged. This closes the two reproduced defects and the additional executable checks above; it does not certify the full original brief. Hardware/account acceptance and the explicitly unexercised combinations listed above remain outstanding. Historical flags in the inherited source manifest describe accumulated implementation history, not additional runtime test results; the scoped verification JSON is the current evidence summary.
