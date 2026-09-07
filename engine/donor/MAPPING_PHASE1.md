# Infinity Engine Donor Mapping — Phase 1

## Inputs mapped

- User-provided `Infinity.apk` from `kodi original.apk.zip`
- `Infinity-Stable-2.zip`
- Official Kodi `21.3-Omega` Android source templates

## 1. Native engine identity

The donor APK and Stable 2 contain the exact same native engine binary:

- path: `lib/arm64-v8a/libkodi.so`
- SHA-256: `cfa76e099972e78537b3384d7db6361153dbd30fec3a35fb93f673d575097dd6`
- byte-for-byte comparison: identical

Conclusion: Stable 2's later lock/UI behavior was not produced by a different `libkodi.so`. The native media engine remained unchanged between the donor APK and Stable 2.

## 2. Stable 2 delta from donor APK

APK file-by-file comparison found only these functional content additions/changes outside signing metadata:

### Added in Stable 2

- `assets/addons/skin.estuary/media/osd/fullscreen/buttons/infinity-lock.png`
- `assets/addons/skin.estuary/media/osd/fullscreen/buttons/infinity-unlock.png`
- `assets/addons/skin.estuary/xml/Custom_1199_InfinityVideoLock.xml`

### Changed in Stable 2

- `assets/addons/skin.estuary/xml/VideoOSD.xml`
- `assets/addons/resource.language.en_gb/resources/strings.po`
- `classes.dex` changes resolve to two Infinity branding strings in `Splash$StateMachine`:
  - `Infinity requires access...`
  - `Starting Infinity...`
- signing metadata / resources package bytes changed as expected after rebuild/signing

Conclusion: the proven Stable 2 lock feature is primarily a skin/UI-layer feature. It is not a separate native engine implementation.

## 3. Android activity layer

Decompiled donor/Stable 2 `Main` class is `com.projectinfinity.kodi.Main`, extends `android.app.NativeActivity`, and exposes the same main JNI bridge methods as upstream Kodi 21.3:

- `_onNewIntent`
- `_onActivityResult`
- `_doFrame`
- `_onVisibleBehindCanceled`
- `_callNative`

Its lifecycle shape also matches upstream Kodi 21.3: `onCreate`, `onStart`, `onResume`, `onPause`, `onDestroy`, `doFrame`, delayed intents, input listener, immersive-mode handling and creation of `XBMCMainView`.

No explicit `enterPictureInPictureMode`, `setPictureInPictureParams`, `setAutoEnterEnabled`, `onUserLeaveHint`, or `onPictureInPictureModeChanged` implementation exists in the donor/Stable 2 Java/smali `Main` class.

The decoded Stable 2 manifest also does not declare `android:supportsPictureInPicture="true"` on `Main`.

Conclusion: the behavior we observed as PiP on-device is not represented by an obvious custom PiP implementation in this donor APK's Java activity layer. That behavior therefore needs to be mapped separately at runtime/system level before we reproduce it natively.

## 4. Surface/video bridge

The donor contains `com.projectinfinity.kodi.XBMCVideoView`. Its structure matches the upstream Kodi 21.3 `XBMCVideoView.java.in` design:

- `SurfaceView` + `SurfaceHolder.Callback`
- native callbacks `_surfaceCreated`, `_surfaceChanged`, `_surfaceDestroyed`
- `setSurfaceRect(...)` updates layout margins and calls `requestLayout()` on the UI thread
- the actual surface dimensions are forwarded to native through `_surfaceChanged(holder, format, width, height)`

This is the main seam we should own for Fold and PiP viewport/surface resizing.

## 5. Media-session bridge

The donor contains `XBMCMediaSession`, and upstream 21.3 already has a native-backed Android `MediaSession` bridge for play/pause/seek/stop/media-button commands.

This is valuable donor functionality to preserve, but it is not yet a full Android foreground media service/background-playback architecture.

## 6. First replacement-engine boundaries

Based on the mapping, the new Infinity engine should not blindly rewrite decoding/playback. The first native-owned seams should be:

1. `Main` / Android lifecycle and Fold window state
2. `XBMCVideoView` / surface dimensions and renderer viewport synchronization
3. explicit Infinity playback state exported from native player state
4. explicit PiP state machine owned by Infinity rather than relying on incidental system behavior
5. persistent Player Settings controls independent of the active skin
6. foreground/background media service built around the existing MediaSession bridge

## 7. Important correction to prior assumption

The uploaded donor's `libkodi.so` is a valuable 21.3 runtime donor/reference, but Stable 2 itself does **not** contain a different custom native engine. Stable 2 and the uploaded donor use the exact same `libkodi.so`.

That means our new engine work should use this binary as a compatibility/runtime fingerprint while implementing new Fold/PiP/background behavior in source-controlled Android/native seams.

## Next mapping pass

- map `XBMCVideoView` JNI registrations to their exact native C++ functions
- map Android configuration/window-size events to native display-resolution handling
- map native player-start/player-stop callbacks to the cleanest Java/JNI playback-state bridge
- map Kodi settings classes so Infinity controls can live in Player Settings instead of Estuary/Diggz OSD files
- verify what Android/One UI mechanism generated the observed PiP behavior in Stable 2 despite no explicit PiP API calls in the decoded activity
