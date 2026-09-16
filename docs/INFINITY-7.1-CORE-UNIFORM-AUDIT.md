# Infinity 7.1 Core-Uniform Audit

## Baseline

7.1 branches directly from the proven 7.0 checkpoint commit `09ed2a0c7f45e3fb6c8b5d9714bbb46dff245d6e`.

Ground truth is Kodi **21.3 Omega**. The 21.3 source tag is `21.3-Omega` at commit `a3a448d26b8d560a65655dab2cd122994dc4e146`.

Observed Fold 8 Ultra behavior from Infinity 7.0:
- App installs and boots as Infinity.
- Video lock appears and functions correctly.
- Android reports PiP permission/capability enabled, but Infinity 7.0 does not reliably enter PiP.
- Inner/cover display transition can crash.
- Enabling the current Infinity OLED/theme experiment can crash.

Observed Fold 8 Ultra behavior from Infinity Engine Standalone V1:
- PiP works.
- No Infinity player lock is present.
- The app physically resizes between Fold display sizes, but the resized UI/input state becomes unresponsive/misaligned, matching the tablet symptom.
- Standalone is a separate package/build and is not interchangeable with Infinity 7.0.

## Donor matrix

7.1 is a controlled conjoin, not a blind APK merge.

Use Infinity 7.0 as the identity/UI donor for:
- `com.projectinfinity.kodi` Infinity package line
- known-working player lock UI and lock lifecycle
- existing Infinity branding/custom UI that is not implicated in crashes

Use Standalone V1 as the behavior reference/donor for:
- working PiP lifecycle
- Android 12+ auto-enter PiP behavior
- PiP parameter refresh/entry behavior

Do not transplant an entire APK or native library wholesale. The two APKs have materially different Java/Dex and native-core bodies. Port the working behavior at the matching layer and keep package/core ownership uniform.

Local binary inspection of the supplied APKs found that Standalone V1 contains a richer PiP path in its Android code, including symbols for `enterInfinityPictureInPicture`, `updateInfinityPictureInPictureParams`, `setAutoEnterEnabled`, `setPictureInPictureParams`, `onUserLeaveHint`, and `onPictureInPictureModeChanged`. Infinity 7.0 exposes only the simpler PiP entry/callback path. This is the first concrete donor target for 7.1.

## 21.3 re-inspection findings

Official Kodi 21.3 Android native code still carries the old fixed-fullscreen assumption:
- `CXBMCApp::onConfigurationChanged()` intentionally ignores configuration changes.
- `CXBMCApp::onResizeWindow()` resets the native window and then does nothing because upstream assumes a fixed fullscreen landscape window.

That means the Fold problem is not solved by Android view resizing alone. The 7.0 APK-side patch injected `onConfigurationChanged`, PiP/multi-window callbacks, `requestLayout()`, and `invalidate()` into the Android layer. That can redraw the Java view while Kodi's native GUI resolution, input mapping, native window, and renderer still retain stale geometry.

Standalone V1 proves the outer Android window can resize without crashing, but its post-resize input becoming unresponsive shows the remaining shared defect is deeper geometry synchronization.

## 7.1 architecture rule

One resize event must produce one coordinated state transition:

Android window/surface size
  -> native window size
  -> Kodi window-system dimensions
  -> GUI/graphics resolution
  -> touch/input coordinate transform
  -> video renderer viewport/destination rectangle

The upper Android layer must not maintain an independent geometry model.

## Core bridge rule

7.1 establishes a narrow Infinity bridge boundary so later features can talk to native state without repeatedly rewriting core internals.

Initial bridge responsibilities:
- current native-window width/height
- current PiP state
- current display/window mode
- Fold/multi-window settled-size notification
- safe request for GUI/input remap after a real native-window size change
- diagnostic readout for Health Center later

Theme switching and other feature work may consume this bridge later, but the crashing 7.0 OLED/theme implementation is not enabled in the 7.1 stabilization build.

## Preserve from 7.0

- Keep the working player lock unchanged unless a compatibility edit is strictly required.
- Keep Infinity package identity/branding.
- Do not enable the crashing OLED/theme experiment in 7.1.
- Do not add unrelated resume/UI features to the 7.1 test build.

## Import from Standalone V1

Port the PiP lifecycle behavior, not the Standalone package identity:
- configure PiP parameters while playback/window state is valid
- enable Android 12+ auto-enter where supported
- retain explicit Home/Recents fallback entry
- refresh PiP parameters when video/window dimensions change
- keep PiP state callbacks synchronized with the native/core bridge

## 7.1 acceptance gate

A build is not promoted unless all of these pass on the Z Fold 8 Ultra:
1. Cold boot on inner display.
2. Inner -> cover while idle: no crash.
3. Cover -> inner while idle: no crash.
4. Scroll and tap top/middle/bottom controls after each transition; touch targets remain aligned.
5. Start video, Home/Recents: PiP actually enters when video is active.
6. Return from PiP: video and GUI recover without black screen or crash.
7. Repeat PiP -> full screen and inner/cover transitions multiple times.
8. Existing video lock remains present and functional.
9. Kodi installed alongside Infinity remains untouched.

## 7.1 scope lock

7.1 is a stabilization release. If a change does not directly support working Standalone-style PiP, Fold resize, input/GUI geometry synchronization, the existing lock, or the bridge needed to keep those layers uniform, it does not belong in 7.1.
