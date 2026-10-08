# Infinity 2103330 / skin 1.0.5.204 — directory close and presentation repair

Status: candidate; physical Fold acceptance required. User-approved rollback is APK 2103327 and exact skin.infinity.diggz 1.0.5.201. No automatic lock, data reset, provider removal, or premature process termination.

## Evidence and limits

The supplied 2103329 export records three active `directory` jobs in the final `stop.cancel_jobs` wait, with no matching native-completion receipt for that capture. An earlier close completed. The final wait is proven; the innermost backend operation of each of those three workers is not symbolized by this export. The `live` field in the saved Kodi state describes its Activity and must not be treated as proof of process death. Historical ANRs and old receipts cannot be attributed to the current owner merely because they share an export.

The exact 3327 source has an Android background plugin-result wait that does not observe the existing global shutdown gate. It waits for a result or a language invoker's completion, although later shutdown still owns that invoker's finalization. The directory display job also lacks cancellation checkpoints around fetch/metadata work. The new host test reproduces the former behavior against the exact parent method and checks the repaired method. This is source-level evidence consistent with the device wait, not a claim that every possible network/backend stall is now proven fixed.

## Native delta on the exact 3327 map

Five files change: DirectoryProvider.cpp, ScriptRunner.cpp, ScriptInvocationManager.cpp/.h, and InfinityShutdownTrace.h. Background result waits now observe the existing shutdown gate and return a cancelled result. They do not mark a script done, stop/erase/detach its owner, or shorten its final join. Directory display work checks the existing cancellation contract before/after fetch and between metadata items. Trace records identify cancelled result waiters by native thread, script ID and add-on ID; no provider URL is recorded.

The original JobManager final wait, Python stop/escalation/GIL finalization, plugin handle-lock contract, settings/skin saves, database closing, native destruction and exit receipt remain unchanged. Genuine script owners still finish through the existing manager cleanup. Host tests use real threads and a test writer to demonstrate this lifetime separation, but fake Kodi/Python dependencies; they do not prove every third-party add-on's saved state on a real Fold.

## Presentation correction

Build Android from the exact accepted 3327 APK/source. Reuse 329's bounded read-only phase reader, not its added Activity. The final manifest and power bridge are byte-identical to 3327: no InfinityClosingActivity, no separate closing task, and no automatic card over the launcher. The only active live-status surface is the existing system notification, with actual native phase text, indeterminate activity and a chronometer. Tapping it opens the existing chooser route. A gap in native phases reads `Waiting for the next shutdown stage`; truncated evidence reads `Last reported`, never completed.

The existing 150-second short-service safety ceiling, owner/PID/session checks, nonsticky behavior and no-AUTO_CREATE lease remain. Dismissing a notification or ending that guard is not a clean-exit verdict. Android controls notification permission, placement, styling and heads-up display; no overlay permission or system-settings bypass is added.

The chooser's actual 3327 and 3329 Splash source matches. Preserve the accepted source and APK assets, rather than inferring a chooser redesign from slogans or device fonts in a screenshot.

## Skin .204

Exact parent ZIP SHA-256: c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5.
Only addon.xml and unified/DialogButtonMenu.xml change. Keep the normal Close Kodi route and all other power commands. The closing acknowledgment has a bold ASCII title, readable secondary text, a restrained optional icon pulse, and a pointer to notification status. Remove unsupported arrows and the static half-filled bar. The skin does not claim to animate or report live native progress after Kodi stops repainting.

All 2,938 other ZIP entries are unchanged. No Command Center replacement or add-on ID rename. Skin is delivered separately, not silently installed by the APK.

## Verification and acceptance

Native: exact full parent/postimage checks, executable parent-vs-repaired waiter test, seven waiter/ownership/GUI cases, original JobManager regression harness before the delta, and original cooperative Python registry/clock tests after it. Final joins/saves/handle-owner code is hash-protected. ARM64 compilation is separate from device acceptance.
Android: complete source-map check, narrow five-file presentation/identity delta, exact original manifest, no extra Activity registration, 265 tests across 19 suites, DEX/helper equivalence, resource/JNI/payload checks and permanent signer. New native artifact must match the exact required successful source/run; no old-engine fallback.

Fold: install the verified APK over the existing app (no uninstall/data clear), then .204 over the installed skin. Test a settled idle close and a close while provider widgets are still loading, plus playback/stop and repeated reopen. Confirm no floating card remains over the launcher, real notification stages change, actual owner cleanup completes and PID exits, and settings/resume/watched state and Cobra/provider playback still work. Export after the first two tests before replacing captures. A minute-long stall remains a failed candidate, not a reason to hide warnings or force-kill automatically.
