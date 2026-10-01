# Cobra remaining audit — forward work from locked 2103279

The user's 2103279 baseline is locked at `60e1893d8591a29fab7e952ea2d3caedb0b13fa5`.
The exact approved APK remains `cf7aedadded921e5ddc023ba08161638d8f6207dd7002f3258daf178073679cd`.
This follow-up does not change that lock or claim the entire brief is complete.

## Existing evidence reused

- Build/signing/regression run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36810766190
- Exact-APK runtime evidence: the successful Android job of run 36808284951; 21 scenarios.
- Existing 519-test result and 20 protected render comparisons are not being repeated for instrumentation-only work.
- The new branch is `candidate-cobra-2103280-audit-followup`. The initial follow-up tests install the exact locked 2103279 release APK. No new product APK is produced by this instrumentation-only workflow.

## Correction to the prior report

The earlier report's statement that all 35 inherited test source files were unchanged was incorrect.
Direct comparison of the archived staged sources from runs 36794611568 and 36810766190 shows **34 of 35 unchanged**.
`Cobra2103268ProductAuditTest.java` had one timing-only addition before locating the player drawer's row:
`f.ui.frames(15); f.ui.measure(a,800,600);`.
Every assertion in that test is preserved. All inherited test methods ran and passed, but source-byte identity must not be claimed for that file.

## Additional runtime scope

The added checks target previously unverified paths:

- Actual Android PiP and transport callbacks from 2-, 3- and 4-pane Multi-View, returning with the same channels, audio owner and paused state.
- Recording start, stop, actual saved bytes, local recording decode and return to Recordings.
- A recording that completes naturally must clear the player's active recording state.
- Two subtitle languages, two audio tracks, subtitle size, CC off and fullscreen/PiP transitions.
- Framework audio-focus interruption and recovery without replacing the decoder or undoing user mute. This is not a physical cellular-call test.
- Channels, Display and More in Light, Dark and OLED, including visible bounds and drawer insets.
- A bounded three-minute four-decoder observation with memory snapshots and release checks. This is not physical thermal/battery verification or proof of long-term leak freedom.
- Settings changed through real callbacks, then checked after a separate force-stopped process restart.

Initial runtime run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36816481777
Results are pending; no check above is marked passed merely because its test has been written.

## Access-dependent acceptance still required

No connected physical Fold or authenticated user provider is available in this environment.
Physical inner/cover/fold transitions, Samsung window behavior, real affected channels, external provider/add-on outcomes, phone-call audio routing, hardware casting and physical battery/thermal behavior remain unverified.
Generated HTTP content can verify app-owned handling, but cannot establish that a private provider or external service works for the user's account.

The remaining brief is still active. Any confirmed product repair belongs on this forward candidate, never on the locked branch.
