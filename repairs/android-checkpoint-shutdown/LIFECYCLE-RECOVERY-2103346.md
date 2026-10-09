# Infinity lifecycle and failed-checkpoint recovery 2103346

Android follow-up over exact source commit 04128777ae7e7e635ea54fc595534be6e518f663 (2103345). Separate branch: work/infinity-lifecycle-recovery-2103346. The checkpoint branch, its running 2103345 build, native source manifest, installed add-ons, skin and permanent signing identity are preserved. This candidate is not locked or device accepted.

## Matched phone evidence

Infinity-Diagnostics-20261009-012031.zip identifies installed APK 2103344. Its latest engine is PID 8664, owner c943d71a-d9a8-4a11-be0f-8be868c5af2b, close session b3586296-2c51-4f8f-a2af-845cbc318120. Close requested at epoch_ms 1791523156601. The coordinator recorded CHECKPOINT_FAILED after 361 ms, naming repository.zeus768:service.py, invoker 16, with foreign_invoker_finished_without_persistence_receipt. Its script ledger independently names unidentified:infinity_native_ambient.py with external_or_opaque_writer_requires_explicit_participant. Neither proves which file was being saved or that Zeus caused the first ledger failure. Playback reports COMMITTED; other required owners remain pending. No saved checkpoint, SAFE authorization, termination command or confirmed engine death exists.

The chooser starts 62 ms after Close. After a home/background round trip, handoff.waitClosingOwner repeats through at least 67.956 seconds after chooser creation. This is a failed checkpoint presented as an ongoing close, not evidence of successful saving. The retained native cleanup marker belongs to older PID 23003 and cannot certify this close. This ZIP does not test 2103345.

## Resulting behavior

- Normal Close opens the phone's Home activity while the existing foreground coordinator continues the checkpoint. It does not finish NativeActivity or start the chooser. The notification still opens the chooser when the user explicitly selects it.
- A live failed checkpoint still blocks a second engine. The recovery dialog says the save check failed and offers Health Center and explicit Force Close; it no longer promises that waiting will finish that checkpoint. Pending saves retain the existing wait option. No failed receipt becomes SAFE or COMPLETE.
- Main has its own task affinity, explicitly remains in Recents, and no longer finishes on task restoration. The launch handoff strips inherited EXCLUDE_FROM_RECENTS while preserving deep-link data, extras and URI grants. Temporary entry/power tasks remain excluded, and Cobra's task attributes are unchanged. Android placement and Samsung's PiP/Recents presentation still require phone verification; the ZIP contains no Android task-manager dump proving the original exclusion mechanism.
- Restoring the still-owned Kodi task during a checkpoint opens shell recovery rather than enabling sealed Kodi controls. Close does not invoke the normal leave-hint PiP handler. Ordinary leave-hint playback behavior is preserved.

This change does not exempt opaque writers, fabricate save receipts, automatically Force Close, reset settings, remove add-ons, or claim to repair every script persistence blocker. It retains 2103345's raw/layered I/O repair and add-on settings null checks through exact engine reuse.

## Build and validation

The separate workflow compiles the full Android shell and runs inherited crash/exporter tests plus five Robolectric lifecycle cases. It waits for 2103345 run 37887463358, then requires that exact native job to have passed and verifies its source SHA, native manifest SHA-256, engine SHA-256, preservation proof and embedded engine identity. No native compilation occurs for 2103346. APK association compares protected assets/resources/JNI and permits only Main's three reviewed manifest attributes plus candidate version identity. Permanent signer verification remains required.

Local checks exercise production Snapshot presentation/gating and Home/Main intent builders using narrow host Android peers, manifest rules, notification recovery/authorization preservation, and packaging rejection of unrelated manifest/class/asset changes. All 262 Android source postimages were verified; all 257 preservation-parent inputs remain represented. Host checks do not establish Android UI, process lifecycle or device acceptance. Full Android compilation and Robolectric checks run in Actions.

## Phone acceptance

Install 2103346 over the existing app without clearing data. Enter Infinity, open Recents without video and again with video/PiP, and restore its card. Verify existing playback/session returns without a second engine. Compare the normal chooser and Cobra Recents paths.

Request Normal Close once; it should take you to Home. Reopen from the launcher/Recents during saving and after completion. If the checkpoint fails, the interface must show failure/recovery, not repeatedly claim "finishing." Export diagnostics before choosing Force Close. A shutdown pass still requires matched SAFE proof, consumed authorization, observed owner death and preserved resume/watched/settings/favourites. A failed save remains a shutdown failure even when routing and recovery work correctly. Rotate/fold/background the chooser and verify recovery state stays truthful.
