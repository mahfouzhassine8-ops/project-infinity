# Existing Android observation — startup setup blocked playback

Run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41379570028

Source: `b2db7578264fb1151d9258a7fd833b500a8e41ed`. Workflow finished SUCCESS (run metadata updated at 2026-11-02T02:56:03Z); **functional classification: BLOCKED BEFORE PLAYER — no playback PASS**.

## Provenance and authorization boundary

The QA harness commits `180cf085` and `b2db7578` arrived on the remote branch during this read-only continuation. GitHub identifies this run's event as `push` and its actor/triggering account as `mahfouzhassine8-ops`. This identifies the recorded account, not a verified human author. This continuation did not author those harness edits, dispatch the workflow, change production code, or sign a successor release. The pre-existing observation was allowed to finish and its evidence was inspected once; no further run is selected here.

The harness changes are confined to disposable observation infrastructure: one wrapper shell and its invocation from the QA workflow. The wrapper fixes the command splitting reported for run41379038225. Its ephemeral QA signing identity is not the original release signer, and its isolated emulator uninstall/install sequence is not an install-over test or permission to touch user application data. A repository authorization note does not override the user's latest read-only/no-successor-signing instruction.

## Actual bytes and visual inspection

Artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41379570028/artifacts/13113142146

The new artifact was downloaded through the GitHub connector's supported file reference, materialized locally, and checked as a CRC-valid ZIP: **1,884,155 bytes**, SHA256 `0456443089126f89d4429d5ae11fd200c65dbaacb5e56e0fd8b57d3e5627e8ae`. This is CI evidence, not the original private physical-device diagnostics. The earlier run's CLI artifact download remains a separate HTTP403 result; it was not retried.

All eight PNGs were opened and visually inspected, with matching UI XML, RESULT.json, startup logs and media-session dumps reviewed. Both phases show the same sequence:

| Observation label | Exact baseline445 | Corrected disposable QA package |
|---|---|---|
|after-rapid-A-B|Android App Compatibility notice|Same notice|
|after-stop|Same compatibility notice remains|Same notice remains|
|after-back|Infinity media/file-access explanation with Continue|Same explanation|
|after-reopen-B|Same media/file-access explanation remains|Same explanation remains|

The notice states that native LOAD/RELRO alignment is not16KB compatible and that Android will use compatibility mode. No compatibility setting, native library, Don't Show Again preference or permission was modified by this review. The subsequent explanation reads that Infinity requires media/file access and offers Continue. Neither phase has completed ordinary first-launch setup.

The captured startup logs show `splash.create`, `splash.firstFrame`, and `permissions.required`. The intent outputs identify `.Splash`, including subsequent intents delivered to the running Splash instance. No screenshot shows the Kodi player or either synthetic video. All recorded media-session filename checks are false. The zero fatal-string count does not demonstrate native playback stability when the player was never reached.

## What passed and what did not

- Preparation/recording completed. The workflow exits zero to retain both phases' observations; its green status is not a playback assertion.
- Both phases report `OBSERVATIONS_CAPTURED_NOT_AUTOMATIC_PLAYBACK_PASS`. `Baseline=0 Candidate=0` means the recording functions completed, not that their named lifecycle operations reached Kodi.
- The baseline APK hash matches signed445: `b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400`.
- The QA pack report records only `classes3.dex` as a changed nonsignature member and explicitly prohibits user installation. This archive contains the preservation report, not the QA APK for an independent post-signing member comparison.
- The rebuilt owner report has the same candidate DEX hash `d4f5f5003afe9e890d947505515f54d2ad507bf4b4fd3126ed5e2cdab751afe6`, three original modified methods, two added helper classes, exact original fields/annotations and unchanged remaining lifecycle methods. The existing correction and its nine passing host tests remain unchanged and were not rerun.
- Initial/second-file playback, latest-request delivery to native Kodi, automatic Loading dismissal, native Stop/Back, return/reopen and player cleanup are **NOT VERIFIED** by this run.
- The Stop input is KEYCODE_MEDIA_STOP, not a tapped Stop button. Here it was sent while a compatibility notice was visible. Back moved between startup prompts; it did not verify Back during video playback.
- The selected intent is synthetic ACTION_VIEW `file://` with `video/mp4`, not MiXplorer. No actual MiXplorer MIME/URI/grant path was captured. Splash timing is not a first-video-frame or external-playback performance measurement.

This run neither reproduces nor resolves the historical native-constructor crash. It stopped at an earlier setup boundary, so no conclusion about native execution compatibility can be drawn from the absence of fatal strings.

## Exact remaining blocker and smallest next step

The immediate observation blocker is incomplete disposable-emulator first-launch setup, positively established by all screenshots and UI XML. A separately selected future runtime check would need to complete ordinary compatibility acknowledgement/media-access setup and positively establish Kodi/player readiness before sending A/B, Stop or Back. This is a harness prerequisite, not a reason to alter protected Splash, native compatibility settings or libraries. No rerun or harness edit is performed under this read-only continuation.

The actual repair's other mandatory causal gaps remain: actual MiXplorer intent metadata, Loading-dialog operation identity/completion, pending playback callback identity/priority/phase, and the dependency/lock owner behind the reported occupied native workers. The worker-admission finding remains conditional; see [READ-ONLY-WORKER-DEPENDENCIES.md](READ-ONLY-WORKER-DEPENDENCIES.md). The existing export cannot supply absent intent/dialog metadata, and historical ANR/tombstone producer versions remain unbound.

Locked2103445, Cobra, chooser/Splash, native/shared components, shutdown/durability and user data remain protected. No new production edit, native workaround, additional test loop, successor original-key signing, release promotion or lock was performed.
