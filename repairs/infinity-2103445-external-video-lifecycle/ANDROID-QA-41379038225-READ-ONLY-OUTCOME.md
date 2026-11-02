# Existing Android QA run — read-only outcome

Run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41379038225

Run source: `34b059d2bcda0df6e020782b5364785a0980ed52`. This run was already underway when the read-only dependency report was integrated. This continuation did not dispatch or rerun it, change its harness, or sign a release.

## Observed result

The run completed with FAILURE at 2026-11-02T02:46:21Z. Job logs were read through the GitHub connector. The Android37 emulator booted at 02:46:16Z, but neither baseline nor corrected application playback was exercised.

The emulator action executed the YAML `script` lines as separate `/usr/bin/sh -c` commands. The baseline path assignment did not survive into the next command, and the backslash-continued Python command was executed without its argument lines. The precise first failure was:

    live_external_qa.py play: error: the following arguments are required: --apk, --media, --out, --phase

The probe exited with code2 during argument parsing, before entering `play()`, installation, or ACTION_VIEW delivery. Both recorded summary cases are `NOT_RUN_OR_PREPARATION_BLOCKED`. Therefore the run provides no first-frame, loading-dialog, Stop, Back, reopen, MiXplorer, or physical Fold result. It does not demonstrate an application crash or establish that the emulator can execute Kodi.

The preparation step did finish, including baseline input hash checks, `PASS_EXACT445_EXTERNAL_INTENT_ONLY_DEX_DELTA`, and construction of an ephemeral QA-only package. That package is explicitly not original-key signed, is not a release/install-over candidate, and must not be delivered for user installation. No successor original-key signing result exists in this run.

## Smallest harness correction, not executed here

The complete stateful sequence must run in one shell, for example by invoking a single checked-in wrapper script from the emulator action. Keep its baseline path assignment and complete Python arguments together. This addresses the observed shell/argument failure without changing application bytes, timers, input assertions, native libraries, or playback behavior. A later selected execution would still need to establish whether Kodi initializes successfully; boot alone does not resolve the historical native-constructor blocker.

The existing probe also uses synthetic `file://` plus `video/mp4`, and KEYCODE_MEDIA_STOP rather than a tapped player Stop control. Even a successful future execution cannot verify the actual MiXplorer content URI/MIME/grant path, the reported overlay owner, or physical Fold acceptance. Existing test selection and preservation restrictions remain binding. This read-only continuation does not authorize or perform a rerun.

## Artifact access and preservation

GitHub reports artifact `13112368845`, 13,097 bytes, digest `sha256:395aa72b6a0fb88f4b53ff41b0392d7a860385a932f44c1adbcd18b192736e22`. A local CLI download attempt returned HTTP403 Forbidden at the redirected artifact-blob GET; the archive was not materialized or inspected here. No retry or access bypass was attempted. The specific failure and both NOT_RUN results above were independently available in the readable job logs.

The remote QA and authorization-note commits were retained when integrating the independent read-only dependency report; no force push or rollback was used. Repository authorization prose does not override the current user's instruction to retain unresolved mandatory verification and withhold successor signing. Production race correction and its nine passing host tests remain unchanged and were not rerun. No Cobra, chooser/Splash, native/shared, shutdown, persistence, or user-data change was made by this continuation.

Remaining causal limits are recorded in [READ-ONLY-WORKER-DEPENDENCIES.md](READ-ONLY-WORKER-DEPENDENCIES.md): worker starvation is conditional, queued playback callback and import-lock ownership are unknown, historical producer identity remains unbound, and actual external intent/dialog metadata is absent from the supplied diagnostic review.
