# Infinity Lifecycle Repair RC3 — Android-only candidate

VersionCode 2103138; versionName 1.0.9-Infinity-Lifecycle-Repair-RC3.
Predecessor: exact Background Control RC2 (2103137), run 35067545383,
source 90d4efd2796828795f5e6d4e436d8cd4e43a6a6b.
Predecessor APK SHA-256:
d709c9dbf7224a9cfe4198cffb3adf523449fdc34af8c373f1c4463cdb494930

## Confirmed fault and change

A delayed source-loading completion reached InfinityLiveActivity.loadGuideAsync
on a destroyed Activity and submitted work to its terminated executor, causing
an uncaught main-thread RejectedExecutionException. The app shares one process,
so that Java crash also closed Infinity.

RC3 fences all six Activity I/O submission sites, ten UI completion sites and
eleven delayed scheduling sites. Destruction marks the Activity dead before
player teardown, clears only its owned Handler queue, and shuts down its pool.
Callbacks recheck the instance lifetime when they execute. The check/execute
shutdown race is caught specifically. No pool is resurrected, and rejected
network work is never executed on the UI thread. Network interruption remains
best-effort; an in-flight request may finish, but cannot update a dead screen
or schedule successor work.

Normal/Extended service, control Activity, Main Activity, PiP/Fold/rotation,
provider configuration formats, playback pause/resume policy, resources and
Kodi native libraries are not changed. The only reconstructed Android source
changes from RC2 are InfinityLiveActivity.java.in and Gradle version identity.
No skin files or add-on packages are updated. Keep locked skin 1.0.5.139.

## Install and device acceptance

Update-install this APK over matching-signed Infinity. Do not uninstall or
clear data. No skin ZIP is required. Confirm installed versionCode 2103138.

1. From Infinity System Hub, open Cobra and return to Infinity while source or
   guide loading is still in progress. Repeat; no whole-app crash should occur.
2. Reopen Cobra and let loading finish; channels and guide must still populate.
3. Check manual pause, single-player and Multi-View, actual PiP, Fold/rotation,
   and return-to-Infinity. Normal / Extended controls should behave as before.
4. In Extended, confirm its notification, background with Home/Recents (not
   swipe-away or force-stop), then return after 15–20 minutes. Record the result.
   Foreground-service importance does not prevent a crash or guarantee retention.
5. Leave the locked skin and provider data alone. Capture fresh diagnostics if
   any failure remains. No claim of Android/Fold runtime testing is made by CI.

## Preservation and recovery

CI archives the exact RC2 APK/source and the new source/tests/audits. Its original
run40 native/resource/JNI/signing checks remain intact; an additional comparison
requires the RC3 manifest to differ from RC2 only in version and every non-DEX,
non-manifest, non-signature APK payload member to be byte-identical.

The skin 1.0.5.139 lock SHA-256 remains:
f4f39e5bc1e9fb5d865c6252f856d4ad736b1b517927a15f06973dc0bde05438

The RC2 archive is an exact recovery source, not a guarantee Android permits a
lower-version APK install. Do not uninstall to force a downgrade. A same-key
forward recovery APK may be required. An APK archive does not back up userdata.
RC3 is a candidate until explicit acceptance; no existing lock is overwritten.
