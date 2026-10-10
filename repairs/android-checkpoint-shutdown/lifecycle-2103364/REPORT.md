# Infinity 2103364 — independent Resume + Lifecycle repair candidate

**Parent:** exact running 2103363 Resume Speed head `97990023c245d8e513fffa14a380e29e05387e76`.
**Parent run:** `38089925835`, untouched.
**Candidate branch:** `work/infinity-lifecycle-2103364`.
**Version:** `2103364` / `1.0.9-Resume-Lifecycle-RC1`.

## Preserved from 2103363

All 2103363 Resume Hub cache invalidation, early saved-state publication, one-listing provider checks, exact installed-script installer upgrade, existing 2103362 repairs, playback/skin/settings preservation, permanent signing and signed APK comparison remain inherited. The original 2103363 workflow, branch and source commit are unchanged.

## Implemented, narrow, fail-closed lifecycle repairs

1. Rebase each *specific loaded add-on settings instance* when its synchronous `SaveFile` actually succeeds. Another owner with divergent outstanding changes still fails conflict verification.
2. For Android's optional `system.posix_acl_access` that appears in a file attribute list but returns `ENODATA`, accept absence only after repeat `ENODATA` observations, identical attribute-name list and unchanged inode, owner, mode, timestamps and size. All other ACL and metadata failures remain blockers. This requires physical filesystem testing.
3. Installer does not publish a phantom download entry when the background `AddJob` is rejected with job ID zero. A failed `CAddonDatabase::AddPackage` no longer masquerades as success.
4. Android coordinator and chooser require the same observed complete save, consumed termination authorization, ordered command and verified old-process death before declaring `COMPLETE`.
5. Review identities and native/Android full-overlay SHA256 manifests are updated. Candidate source contracts are checked separately.

## Deliberately unresolved (NOT bypassed)

- Full installer/uninstaller durable files, database and completion-callback receipts are not verified by this narrow patch; ambiguous jobs remain blockers. No add-on updates are forcibly cancelled.
- Active PVR/Live TV persistence is not newly certified; it remains fail-closed.
- Nothing declares 17/17 shutdown owners durable without receipts, or deletes noisy historical diagnostics.
- Health Center companion APK remains separate. Fold shutdown and Resume Hub launch timings are not yet proven.

## Validation and device acceptance

The independent `2103364` GitHub workflow runs the source-contract test, inherited native + Android + Resume Hub tests, ARM64 native build, permanent APK signing and exact 2103362 unrelated-entry preservation. CI green is not proof of Fold shutdown.

If green, install over current data without clearing it; keep 2103362 rollback. Check 6 normal Close/reopen cycles; 17 owner receipts, consumed authorization and old `:kodi` PID death; Ser(en)/POV/Umbrella settings, provider updates, keyboard/peripherals, watched/checkmarks, Play/PiP, fold and relevant PVR. Export diagnostics for any failing owner.
