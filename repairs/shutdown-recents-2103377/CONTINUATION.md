# 2103377 continuation — 2026-10-13

Resumed, not restarted, from c727f3964419ec0010b6bf0e9e620c5605980d44 on the existing work branch. Locked APK 2103376 and Skin 1.0.5.211 are not changed. No APK is packaged, signed, installed, promoted or locked by the verification workflow.

## Completed verification of the saved implementation

Android compilation and all 207 unchanged approved regression tests passed in runs 38350414590 and 38351036138. Test-source/fixture hashes, the exact 207 JUnit case names, original suite counts, and the 262 unchanged compiled runtime files were independently enforced. These are host Robolectric tests, not physical Fold or complete shutdown tests.

The first new test harness mistakenly wrote the exported diagnostic filename rather than InfinityKodiShutdown.STATE. This produced three false-positive failures. Commit 6574ec8c08055c8ed935dd66d4b40dfb6824b22a fixes the new fixture and checks the production reader's initial PID, owner and liveness before each case. None of the 207 approved cases changed.

Run 38351036138 (artifact 11790294835) executes that corrected fixture against the original saved production bytes and confirms five failures among 27 targeted cases:

- Missing owner-state file was treated as permission to remove a task.
- An observed, still-held owner lease did not prevent task removal inside the retirement method.
- An owner replacement published during task lookup was not rechecked.
- API 21 and API 28 each throw NoSuchFieldError for the unconditional taskId access.

## Targeted correction in this checkpoint

Only retireConfirmedClosedKodiTask changes relative to the saved coordinator. Reject missing owner evidence and an unretired owner; use persistentId before API 29 and a baseIntent component before API 23; reread owner state after task-manager IPC; recheck local completion authority before removal. Durable checkpoint, authorization consumption, old-owner death, failure reporting, timeout, and Home/background paths remain byte-identical outside that method. NativeLease remains exactly as saved in c727.

The original six source-contract assertions remain, with the expected candidate guard hash updated to the actual corrected bytes; two stricter preservation assertions are added. The Java verification reruns every original case plus the same 27 targeted cases. Do not claim these pass until the new run finishes successfully.

## Dependency finding: whole add-on is not proven dead weight

Read-only inspection of the approved Skin 211 ZIP (SHA-256 460762f78ad2a1cb2d54639e973d20a5958de0c22575a0d7f228b7f1cdc73815) finds Playlist Browser routes in the active unified layout, refresh-all shortcuts, guarded preview paths, and resources/lib/infinity_playlist_registry.py. Across layout copies, 221 matching text lines occur in 21 files; this is not 221 independent dependencies. The add-on is not a mandatory import in the skin's addon.xml, and no directly packaged add-on path was found in the approved APK. This does not prove installation origin or automatic-service necessity.

The registry reads compatible installed source contracts and cached source aliases; its existence is not proof that automatic background refresh must run. Conversely, removing the whole add-on would discard a real optional integration. Therefore leave both add-on and service intact until necessity and installed source are verified. Do not alter Skin 211, Cobra, general Kodi/PVR/M3U/EPG support, settings, playlists, favorites, credentials or caches.

## Remaining shipping blockers — not declared fixed

1. The diagnostic ZIP lacks the byte-exact installed plugin.video.playlistbrowser/addon.xml, main.py and service.py, and does not identify the blocked VFS backend. Need these code files plus redacted operation/backend/cancellation/return evidence and installed dependent/usage evidence before service retirement or a targeted read-cancellation correction. Do not export private URLs, queries, credentials or user configuration unnecessarily.
2. The second owner read detects the reproduced replacement-during-lookup case, but is not atomic with Android finishAndRemoveTask. A replacement after the last observation or before its asynchronous publication remains a race to address through verified lifecycle/entry coordination. No unconditional replacement-owner safety claim is justified.
3. No corrected native cancellation build, real early-versus-loaded shutdown, Android multi-process lifecycle restoration, chooser/deep-link acceptance, or physical Fold multi-window test has passed for this candidate. Existing save barriers must not be bypassed to manufacture success.
4. Package and permanently sign one update-compatible 2103377 APK only after the remaining mandatory gates pass. Never change version 2103376 bytes or label a source/host-test green as an APK green.

The initial README is retained as the record of the original source-only checkpoint. This continuation records the new Android compilation, reproduction and narrower correction work; neither document authorizes shipping while the above gates remain open.
