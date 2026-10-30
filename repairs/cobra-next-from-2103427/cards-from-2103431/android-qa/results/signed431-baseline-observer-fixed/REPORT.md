# Exact431 observer-fixed baseline — run41002818185

The unchanged signed431 APK imports the local20,226-channel source and renders Mobile. The run fails when UIAutomator cannot obtain an idle hierarchy before pressing Views; Cards itself was not reached.

| Observation | Actual evidence |
|---|---|
| APK | Original v1/v2/v3 signature and exact installed431SHA256 verified. |
| Cold launch | One COLD `am start -W`: TotalTime4556ms, WaitTime4561ms. Welcome observer14.327s includes known compatibility-notice/accessibility overhead; not first-frame or chooser-transition timing. |
| Source entry | All3normal fields filled; TEST&SAVE pressed in actual visible bounds. HTTP200 for M3U, XMLTV and syntheticqa1stream. |
| 011–015 | 011dump returned code0 plus `ERROR: null root node returned by UiTestAutomationBridge.`;012–015returned code0 plus `ERROR: could not get idle state.`. Existing finite poll budget consumed each miss. |
| 016 | Fresh XML confirms Mobile, actual20,226channel count, nativeQA1/QA2cards, current/next EPG, player controls and Views. Source save therefore succeeded. |
| 017 | Next strict action-target observation fails with `ERROR: could not get idle state.`. No Views press is injected from stale XML. |
| Terminal | Independent PNG captured and actually inspected: fully rendered Mobile with video, player controls, EPG, first cards and Views. Cobra remains resumed/visible. No fatal/ANR/SIGBUS/SIGSEGV/OOM marker in retained log. |
| Remaining measurements | No Cards-first-card, Cards-warm-return, Cards scrolling or new-scope resource snapshot completed. No speed/FPS/thermal or stability improvement established. |

This distinguishes the framework idle-observation gate from an application crash. It does not identify what continuously generates accessibility events or prove the app always remains responsive. No deadline/attempt inflation or additional CI run was performed by the monitor. First failure41001477356 remains intact. The actual official66-file artifact hash is aa37ae909af82dd52155e6fd87ccd40c286e2a3b65b7f98817e7c0d4f48468ab; EVIDENCE.json records every file hash and the private inspected terminal image.

Any next harness approach needs root review and must capture fresh native UI state without weakening feature assertions or changing production timers. No app/native changes, shutdown test or physical Fold acceptance occurred.
