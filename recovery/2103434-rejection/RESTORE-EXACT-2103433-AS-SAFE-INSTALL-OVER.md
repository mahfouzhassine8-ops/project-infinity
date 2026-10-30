# P0 RECOVERY — REJECT 2103434; RESTORE THE EXACT 2103433 FUNCTIONAL BASELINE

**USER DECISION — October 30, 2026:** "The update is no good." "Whatever 433 was needs to go back." "The Cobra side does not even fix the main full screen cards issue. And infinity side that actual loading screen doesn't even work either." "So that proves to me that we cannot do Kodi and Cobra at the same time."

**THIS IS AUTHORIZATION TO RESTORE, NOT AUTHORIZATION TO IMPLEMENT MORE FEATURES.** User rejects the coordinated 2103434 update based on direct physical Galaxy Fold 8 Ultra testing. No new Cobra Cards layout changes, More-button patch, or Infinity seamless-loading feature is authorized for the immediate recovery.

## Protected identities

- Existing accepted **signed 2103433**: GitHub original-key signing run `41040277352`; source `6f6abe78fae65046e1ef475c558957eae873130f`; original APK `Infinity-2103433-Combined-Original-Signer.apk`; APK SHA256 `874db7007b9fc79478844e5b37d4795d43c4c58de770c553d943734e1014b986`.
- Original signed 433 exact component payload hashes:
  - `COBRA.zip`: `fb33f99a8ce134952536f8763396492c7accd26dfade9b9741665785daac932d`
  - `INFINITY.zip`: `16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c`
  - `MINIMAL_ANDROID_CONTRACT.zip`: `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`
  - `CHOOSER_SHELL.zip`: `17861e1c2c9fdb99bd62e6ed287937a2c9dce2f28af80f2f84c083c633332dd3`
- Rejected, installed-newer **signed 2103434** (run `41084477130`, original APK SHA256 `16f02a9625c057a3fe4d4b55da8a554fdb2bff0f1b19c8f567bdf56af41eb465`). It had both owner changes; signed and host passes did **not** predict the user's observed runtime failures.
- Original certificate SHA256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`; package `com.projectinfinity.kodi`.
- Recovery branch `recovery/restore-exact-2103433-after-rejected-2103434-20261030` was FORKED DIRECTLY from the 433 signing source, not from any 434 feature code. This document is the only intended new content initially; it does not alter the signed APK.
- Keep every historical signed 431, 432, 433 and rejected 434 artifact, GitHub branch, acceptance/recovery record and hash available. Do not overwrite/purge history.

## Required immediate recovery

1. **HALT further combined Cobra+Infinity feature changes, speculative corrections, and 434 promotion.** Quarantine/mark 434 rejected by user. Do not run another broad QA investigation or blindly patch 434.
2. Restoring the installed lower 433 APK via a normal Android installer would generally be blocked because `versionCode 2103433` is lower than installed `2103434`. **DO NOT tell the user to uninstall, clear data, reset profiles, or rely on unsupported version downgrade.**
3. Starting from exact signed433 owner payload and original source, prepare ONE **recovery-only original-key signed install-over APK**, with versionCode strictly GREATER than installed 2103434 (2103435 is suitable if not already issued; otherwise select next legitimate unused version under original authority). This is **version-bump/repackaging only**, not another product feature release. Use original source/owner, exact authorized 433 features and behaviors.
4. Preserve 433's `COBRA` and `INFINITY` code, resources, skin and native functionality **byte-identically** wherever possible; allow only strictly mandatory version metadata/manifest/component owner version fields required by the legitimate signing/anti-rollback gate. No 434-only Cards density, fullscreen More or Infinity seamless loader may survive in the recovery payload.
5. Chooser keeps the exact signed433 visual behavior and existing metadata format, with honest combined app/Cobra versioning for the recovery build where required. No new splash or theme changes. Preserve original package, certificate, current installed data, databases, profiles, addons, media/watched progress, caches, provider configs, playback and shutdown. No migrated data unless documented and separately authorized; no uninstall/reset.
6. **Verify 433 equivalence per actual packaged member** (all DEX classes/method bodies and non-version resources, module auth and matched components). Record exactly which members must differ for installer version-only policy; reject any unreviewed delta. No assumptions that source tree similarity implies APK parity.
7. Run only **essential focused build/source/owner/signature/install-over protection checks**. No shutdown tests, Android data wipe, Cobra feature changes, Infinity feature changes, or repetitive test APKs. Explicitly verify native files and essential writes are unchanged.
8. Deliver ONE actual original-key signed recovery APK with download link, 4 matching ZIPs, source commit, GitHub Actions run, APK SHA256, original signer identity, exact preservation comparison to signed433 and correct higher version. Clearly label **"Restores 2103433 functionality; version number is higher only for safe install-over"**.
9. This user will physically test the recovery and approve. **Do not auto-lock** until user confirms.

## Policy for future changes, after recovery

**One experience changes per release.** A combined single-package app still contains both experiences, but future feature releases should modify **either Cobra OR Infinity**, never both simultaneously. The other owner is frozen. Codex may investigate them separately, but do not combine unfinished changes just to save tool usage. Implement, verify, sign and present one owner change for Fold acceptance; only after approval consider a separate later change for the other owner.

Preserve the accepted 433 UI/behavior as the source-of-truth baseline. **The known unresolved 433 Cards fullscreen More bug and oversized unfolded Cards may remain after an exact restore**; they are intentionally NOT fixed in this emergency recovery. Infinity's selected-frame loading work was experimental and should be excluded completely. Correctness of the exact restore comes first. Address any remaining defect later with separate authorization and evidence, one experience at a time.

## Status of this instruction

This is a GitHub-documented recovery directive. It does not claim a recovery APK has been built, signed, downloaded, installed, or accepted. Never state an action completed until its actual original-key artifacts and verification exist.
