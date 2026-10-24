# Infinity Background Control RC2

This matched Android/skin integration moves user control of Extended Background Mode into Infinity itself.

## Android runtime

- Base: Background/Resume RC1 exact run-40 native engine reuse.
- New identity: versionCode 2103137, versionName `1.0.9-Infinity-Background-Control-RC2`.
- Adds one tiny exported control Activity with two explicit package-scoped actions:
  - `com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL`
  - `com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED`
- The Activity delegates only to `InfinityExtendedBackgroundService`; it does not own playback, rendering, rotation, PiP, providers, or Kodi native state.
- The service stays non-exported.
- The temporary Cobra Settings toggle is removed. The setting is Infinity-owned.
- If notifications are unavailable, Extended opens Android notification settings and does not pretend the service is active.
- Normal disables the service and restores the ordinary Android lifecycle.
- Extended requests the visible foreground-service session; the persistent Infinity notification is the runtime confirmation.

## Skin contract

The companion skin candidate is derived from locked Infinity 1.0.5.133 and adds a Background Mode section to Performance & Display, next to the refresh controls:

`NORMAL | EXTENDED`

Normal means the existing Android lifecycle. Extended requests Infinity session continuity through the Android bridge. The UI must not claim guaranteed process survival; Android may still reclaim the app.

## Preservation

No Kodi/libkodi.so rebuild or patch. Existing native libraries, assets, compiled resources, Cobra playback behavior, PiP, Fold/rotation, provider state and locked 1.0.5.133 remain protected. Device acceptance is still required before promotion.
