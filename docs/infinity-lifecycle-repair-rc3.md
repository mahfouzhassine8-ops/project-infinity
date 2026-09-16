# Infinity Lifecycle Repair RC3 — candidate, not a new skin lock

## Repair and exact lineage

Base Android source: RC2 commit `90d4efd2796828795f5e6d4e436d8cd4e43a6a6b`.
Base signed RC2 APK: SHA-256 `d709c9dbf7224a9cfe4198cffb3adf523449fdc34af8c373f1c4463cdb494930`.
RC3: `com.projectinfinity.kodi`, versionCode **2103138**,
versionName **1.0.9-Infinity-Lifecycle-Repair-RC3**.

A confirmed main-thread RejectedExecutionException occurred when a late
loadAllEnabledSources callback called loadGuideAsync after onDestroy had terminated
Cobra's executor. Six task-submission sites and ten UI-publication sites now go
through per-Activity lifecycle guards. Teardown marks the instance closed before
cancelling its Handler queue, shutting down I/O and releasing players. Late work is
not run on the UI thread and the executor is never resurrected. Only shutdown-related
rejections are contained; unrelated live-executor failures remain visible.

Temporary onPause/onStop, PiP, Fold reflow and the shared Infinity Extended
Background service are NOT treated as terminal destruction. Existing buffering,
manual-pause and per-player resume policy remains unchanged. Pending in-flight HTTP
may still take its existing timeout to finish; its stale UI result is discarded.

## Protected state

Keep the exact locked **Infinity skin 1.0.5.139** installed. Its SHA-256 is
`f4f39e5bc1e9fb5d865c6252f856d4ad736b1b517927a15f06973dc0bde05438`.
There is no skin ZIP, UI rollback or companion update in this repair.
Cobra in System Hub, polished Infinity Power, Performance & Display and
Normal/Extended controls remain as installed. No provider credentials or source
configuration are changed, reset or included in this repository.

The existing Kodi engine is reused exactly, not recompiled or patched:
`9783527356ec108fb3bdd61213dc6c7af9b227da3b81051163aa893a9fa358d0`.
All native libraries, assets and compiled Android resources must match both run 40
and RC2. The manifest may differ from RC2 only in version identity. The permanent
signing certificate must remain the existing Infinity certificate.

## Install and device acceptance

Update-install the RC3 APK over matching-signed RC2. Do not uninstall or clear data.
If Android refuses the update, stop and preserve the error; do not bypass it by
uninstalling. Confirm versionCode 2103138 and keep skin 1.0.5.139.

1. Open Cobra with an existing provider and quickly Return to Infinity while the
   sources/guide are loading. Repeat several times, including with slow networking.
   No crash, stale screen rebuild or unexpected reopened player should occur.
2. Let source/guide loading finish normally; confirm channels and guide still load.
3. Recheck Normal and Extended, including notification on/off, Home/Recents return,
   a manually paused player, a buffering player, PiP and Multi-View.
4. Recheck Fold/cover and rotation, System Hub Cobra, and Infinity Power. Keep the
   current skin and add-on data throughout.

A foreground service does not prevent Java/native crashes or guarantee a 20-minute
session. Host race tests and APK verification do not replace Android device tests.

## Recovery

The workflow preserves the exact RC2 APK, RC2 source snapshot and reconstructed
pre-fix Android source. These are rollback evidence, not a promise that Android
will accept a lower-version APK. Do not uninstall to force a downgrade. A same-key,
higher-version recovery APK would need to be prepared separately if required.
