# Infinity 2103329 / skin 1.0.5.203 — live closing presentation candidate

Locked functional rollback: user-approved APK 2103327 and skin 1.0.5.201.
Working APK parent: exact GitHub-passed 2103328, commit b659037704e603cc5163db92d90b0cff377e33cc, run 37699829878.
Parent APK SHA-256: f74f0f30047da89bd4d196f54ddd46b6be2ad972ab71346a0e42b4e1805bdcc6.
The native library remains the exact 2103327 bytes, SHA-256 a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c. No native compilation, modification, kill or persistence shortcut.

## Correction

328 posted a one-time notification and the skin drew a fixed-width pulsing strip. It never read the shutdown stage records. A skin animation cannot guarantee repainting during Kodi teardown; high channel importance also cannot guarantee an Android heads-up banner.

329 tails the existing, independently budgeted 327 critical trace on the existing default-process guard worker. It requires the exact engine, target PID, a new capture session after this close request, bounded elapsed timestamps, and complete JSON lines. It handles nested spans, duplicate/out-of-order events, partial writes, rotation, absent files and capture limits. Read budget is 128 KiB per 500 ms; lines are capped at 8 KiB. It neither writes the native trace nor asks Kodi to execute anything. A process.exit_requested event is explicitly NOT a clean-exit verdict.

The notification now displays actual current stage text with indeterminate progress and a system chronometer. It requests immediate foreground-service notification visibility on API 31+, without overriding disabled notifications, channel settings or DND. Same ID, same channel, no repeated sound/vibration. Existing guard deadline and owner lease behavior remain unchanged.

A small private Android Closing Infinity card is launched by the existing explicit normal-close bridge. It lives in the default process, not :kodi, and reads the same guard presentation state. This means its stage text, indeterminate animation and elapsed clock do not depend on the Kodi skin renderer or on a heads-up notification being displayed. The card is bottom-end aligned, fits current window bounds, follows Android light/dark mode, and respects system reduced-animation settings. Back hides the card only. It never starts/stops services or native playback, certifies completion or issues another quit. The pre-existing owner Watch dismisses it after the matching process lease is no longer live. Android may still impose activity-launch restrictions; verify real presentation on the Fold.

Normal Close dispatch, native completion receipts, the fixed 150-second guard ceiling, Force Close, Main, Python/JobManager fixes, database/settings persistence, health export and chooser ownership logic are byte-preserved where outside the explicit presentation bridge/guard changes. Only one unexported default-process activity is added to the manifest. No permissions or resources are added. All native libraries, APK assets/resources, JNI declarations and unrelated DEX behavior are checked.

## Skin

1.0.5.203 is built from the exact .202 ZIP (whose parent was locked .201). Only addon.xml metadata and the in-progress row in unified/DialogButtonMenu.xml change. Keep the normal pre-tap row and all commands. Remove missing-font arrows and the misleading fixed half-fill; show a bold closing acknowledgment, a quiet pulse and a clear pointer to the live closing card. There is no claim that this in-skin row continues animating once Kodi stops repainting. All 2,938 other ZIP entries are byte-preserved. Skin is delivered separately; APK does not silently replace it.

## Verification / delivery

All code is committed as readable Python, Java tests and a unified Android patch. Exact source preimages and postimages are checked before and after compilation; source is also retained in the validation artifact.

Host source/manifest ownership checks; 24 new Android/parser/presentation tests; all 241 inherited tests; exact source, DEX, payload and permanent signer checks are required. Two trace fixtures retain only sanitized native control-flow fields (new synthetic PID and origin; no user, owner, provider or network values). They exercise the native event format and order, not real Android process scheduling. No physical acceptance is claimed by CI.

Install the verified 329 APK over the existing application, then install skin .203. Do not uninstall/clear data. Test two normal closes, including one after playback. The real current stage should change (very fast phases can be skipped visually), the clock should advance while one phase remains active, the card should disappear after the Kodi process exits, and reopening should retain the 327 behavior. Test notification denied/banner suppressed, Back/Home during close, rotation/fold and light/dark. Export Health Center if anything stalls. Notification/popup dismissal is not by itself proof of clean native shutdown. Candidate remains unlocked until the user accepts the physical test.
