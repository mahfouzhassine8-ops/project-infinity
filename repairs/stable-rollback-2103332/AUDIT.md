# Infinity 2103332 + skin 1.0.5.206 — exact restoration audit

## Scope and immutable references

The user explicitly requested the original 2103327 APK and 1.0.5.201 skin, delivered with higher version metadata. Do not merge later shutdown experiments, remove original behavior, introduce cleanup/migrations, or describe this as a new shutdown repair.

- Original APK: 2103327, `1.0.9-JobManager-Close-RC1`, SHA-256 `02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5`.
- Source/validation: `2bb8f12f700ee69fe5d86629e6639bc0b1a0b79e`, run `37687616440`.
- Original packaged native: `a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c`.
- Original skin ZIP: `c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5`.
- The 2103332 / 1.0.5.206 identifiers had no matches in the version/branch/commit searches performed before reserving this restoration branch. That is a point-in-time check, not a global version registry.

## File audit, not a device claim

Independent local comparison of the supplied original and 2103331 APKs found identical entry sets. Only AndroidManifest.xml and the three META-INF signing entries differ. All 4,170 other entries, including both complete DEX files, every native library, resources, and assets, match. The 2103331 whole-file SHA-256 is `b4cf1e83ed44e53b17bb5b8b3c86542eed568ec69a53ab270d2ba67eef4c130d`.

The original .201 and previous .205 skin likewise have identical entry sets; only the root add-on version in addon.xml changed. The other 2,939 entries match, including DialogButtonMenu.xml. The .205 archive hash is `0e020362683c81b2e78abea96d83836687e1affbfa242e2c590ae1abca2c37c5`. Differences in ZIP compression/layout do not establish differences in decoded payloads.

Therefore the prior rollback files were genuinely based on the requested originals. They were not evidence that the phone had installed, loaded, or successfully closed those versions.

## Notification ownership established from the effective 327 source

The validated source archive from run 37687616440 contains InfinityCloseGuardService.java.in. Its complete source map matches the 327 SOURCE-PRESERVATION receipt, canonical map digest `7a40be4f2515ed1304af01debb25529298b1db043c1af20fce7397b368c31e15`.

Original settings:
- Channel ID `infinity_normal_close`, default IMPORTANCE_LOW.
- Notification ID 10936.
- Title `Closing Infinity`, text `Finishing Kodi cleanup`.
- Bounded 150,000 ms guard, BIND_IMPORTANT and no AUTO_CREATE lease.
- The guard calls stopForeground(true) during its existing end path; ending it or releasing the owner lease is explicitly not a clean-exit verdict.

These are retained. The post-327 `infinity_normal_close_v2` presentation, InfinityCloseProgress reader and InfinityClosingActivity are not part of the delivered original DEX. No new activity, bottom card, live-stage skin row, or 3330 native directory repair is included.

Android channel settings are persistent OS state, not executable app code. A channel appearing in Settings is not proof of an active notification. A current scoped notification/process snapshot is needed to identify any actual residual notification. No channel deletion or notification suppression was added, because that would exceed a metadata-only restoration without establishing its cause.

The original InfinityPowerMenuRoutes only validates/patches the two existing close commands. Its source is retained; it does not create the experimental closing row. The exact .201 Power XML already has the approved Android route plus non-Android fallback, so its route validation is designed to preserve those bytes. No user skin files are silently cleaned or reset by this candidate.

## Evidence limitation and remaining shutdown risk

The latest supplied device export identifies installed APK 2103329. It contains one completed capture and another capture still in stop.cancel_jobs after approximately 84.4 seconds, with three directory jobs. The native completion receipt in that export belongs to a different PID than the stalled capture. Its `live:false` saved Activity field is not proof that the native process exited. The earlier 327 export has matching native completion evidence for its latest capture.

There is no fresh supplied export of the currently installed 2103331 or new 2103332. Consequently the current stalled-close cause, live notification channel, installed skin bytes, active process owner and runtime loaded native mapping are NOT VERIFIED. The old 329 trace cannot be relabelled as 331 evidence. A source-compatible remaining directory wait is a risk, not a newly proven diagnosis of the user's current phone.

An exact 327 restore deliberately retains the original shutdown algorithm and its limitations. It cannot truthfully promise a notification-free or universally stall-free shutdown. A new hang remains a failed physical acceptance test and must not be hidden by an automatic kill or falsified receipt.

## Candidate creation and verification

APK 2103332: modify only binary manifest versionCode and versionName; retain package ID and all other manifest bytes. Re-sign with the permanent certificate `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. Require full original-versus-331 and original-versus-candidate payload comparisons, original/candidate signature checks, v2/v3 signatures, Android badging, alignment, exact manifest normalization, and 12 fail-closed metadata/ZIP tests.

Rerun the 239 original Android tests across 17 suites against the verified original 327 source. This is a validation-only Android build. Neither its DEX nor any newly built native code is used for delivery. Those tests are not a physical Fold or third-party-provider persistence test.

Skin .206: built locally from the exact .201 ZIP with only the add-on version changed. The local binary verification checks ZIP entry identity/CRC, all payloads, XML parsing, dependencies, Power UI/actions and absence of the experimental closing property. All 2,939 non-addon.xml entries match the original. Skin ZIP SHA-256: `c25315925c5839c8278c164c2a3e66e248f2bac4e29231e759290f46c8146eba`. Full per-file inventories accompany delivery. GitHub records the skin result; the actual skin binary build/check is local, not falsely represented as a GitHub binary build.

## Installation and acceptance

Keep original 327/.201 immutable. Install the new APK in place and the .206 ZIP through Install from ZIP; never uninstall, clear storage, reset databases or delete providers. Same package/certificate and increased version are verified install-over prerequisites, not proof of an actual installation on this phone.

Confirm Android/Health Center version 2103332 and installed skin .206. The skin's preserved description may still mention .201; the root add-on version is authoritative. Read-only desktop verification can pull the installed APK, hash its packaged native library, compare installed skin files and collect scoped notification/service/process snapshots. Restricted paths must produce UNKNOWN, not an empty-file or clean-exit claim. Packaged native identity is not by itself a proof of the running process's mapped library.

Physical acceptance remains open: cold launch/reopen, settled idle Normal Close, close during widget loading, close after playback, correct Force Close availability, no experimental UI, no stale notification after genuine exit, matched native receipt and process disappearance, and retained settings/resume/watched/provider/Cobra behavior. Export evidence before repeated tests rotate the relevant capture. No automatic lock.
