# Reuse completed baseline journey; observe live warm returns

Run 41285455894 passed the strict OS-command preflight and all selected accepted
442 front/inner mode switches, list swipes, drawer open/close, resizing and cover
return. Its `native/OUTCOME.json` is `PASS_SELECTED_PUBLIC_INPUT_MODE_SCROLL_RESIZE`.
The entire workflow still failed, before candidate installation, when the legacy
CLI `uiautomator dump` did not create `/sdcard/cobra-launch-notice-qa.xml` after
Home and a successful warm `am start`. The launch result says the existing task
was brought forward, `Status: ok`, WaitTime103ms. That time alone does not prove
content readiness. The missing XML is not a production crash result.

Use the already reviewed `ImmediateObserver` and its original pinned build,
platform preflight, current-root validation and3.5-second notice-target guard
through the existing `capture_ui` callback. Its source, root budget and notice
allowlist are unchanged. Apply it consistently at baseline warm return, candidate
launch and candidate warm return. Required compatibility/error dialogs are never
suppressed; only the exact known informational OK can be pressed.

The completed baseline matrix is reused by exact signed APK hash, original
outcome hash, unchanged drawer-driver hash and unchanged journey-source prefix.
The next disposable runtime performs the normal source form setup on exact442,
closes the previously blocked warm observation, installs the same signed444 with
`-r`, verifies original signature/installed bytes/UID, and executes the full
candidate journey and warm return. It does not repeat the already passing442
matrix. This is explicit evidence reuse, not relabeling the failed workflow.

No production, timeout, native library, app-setting or signing change is made.
Whole-app speedups will not be inferred from separate emulator runs. The existing
matched host measurements remain the controlled performance comparison.
