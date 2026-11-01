# Observed API37 QA command-output failure

Run 41284441609 completed the actual accepted 442 front Mobile, TV Grid, Compact,
Cards and Pro public-input switches and interior list gestures. It then failed
before the first resize or candidate installation. `CobraDrawerDriver.resize`
reported `Expected stable test display density required` in QA PID 5969.
The application remained active as PID 5400; the retained screenshot shows Cards
with decoded loopback video. No candidate runtime PASS is inferred.

The captured Android activity/window state explicitly reports base 1080x2520 at
320dpi, including the Cobra activity's current configuration. The QA's earlier
`gfx-before.txt` from the same `UiAutomation.executeShellCommand` helper is zero
bytes. The density command's actual raw output was not retained, so its exact
contents and the underlying Android pipe failure are not invented.

The previous fix changed the requested density but left that unverified command
output path intact. This correction is QA-only: execute OS commands from the
already authorized adb-shell QA process through `/system/bin/sh`, capture merged
output, require the actual exit status and retain the existing 8 MiB bound.
No privilege, APK byte, compatibility setting, app timer or readiness deadline
changes. Window-width and stable-density assertions remain strict; raw density
output is now retained before the assertion.

A selected preflight runs before installing either APK. It checks actual command
output for API37, 320dpi and 1080x2520, and stops with preserved output if any fails.
Only a successful preflight proceeds to the same signed 442/444 public journey.
The existing 30-second OS-operation budget applies; no timeout was increased.
The native QA JAR compiles; this compilation is not an Android runtime PASS.

The previous run's complete original artifact and a selected local evidence copy
are linked in `evidence-41284441609/EVIDENCE.json`. Production remains signed
source `1b7a4ef16524854fab77a1c974538aee8a1132bb` / APK SHA-256
`38dff935ffc0967e2c16e8d61e6e4bfd693fcb73bbaa130e8fa354e468b85a76`.
