# Infinity 7.1 Core-Uniform Audit

## Baseline

7.1 branches directly from the proven 7.0 checkpoint commit `09ed2a0c7f45e3fb6c8b5d9714bbb46dff245d6e`.

Observed Fold 8 Ultra behavior from 7.0:
- App installs and boots as Infinity alongside Kodi.
- Video lock appears and functions correctly.
- Android reports PiP permission/capability enabled, but Infinity does not reliably enter PiP.
- Inner/cover display resize causes a crash.
- Enabling the current dark-mode implementation causes a crash.

## Re-inspection findings

Kodi 21.2 Android native code still assumes a fixed fullscreen landscape window:
- `CXBMCApp::onConfigurationChanged()` intentionally ignores configuration changes.
- `CXBMCApp::onResizeWindow()` resets the native window and then explicitly does nothing because upstream assumes fixed fullscreen landscape.

The 7.0 APK-side patch attempted to compensate above the core by injecting `onConfigurationChanged`, PiP/multi-window callbacks, `requestLayout()`, and `invalidate()` into `Main.smali`. That can redraw the Android view but does not guarantee that Kodi's native GUI resolution, input mapping, renderer viewport, and window state all transition together. On a Fold, that mismatch is a plausible source of the resize crash / misaligned touch state.

The earlier v5.3 native renderer experiment successfully demonstrated a controlled source-level native build against official Kodi 21.2 and limited its patch to `LinuxRendererGLES.cpp`. That build path is the reference for how 7.1 must compile and inject a native core rather than layering all geometry behavior in smali.

## 7.1 architecture rule

One resize event must produce one coordinated state transition:

Android window/surface size
  -> native window size
  -> Kodi window-system dimensions
  -> GUI/graphics resolution
  -> touch/input coordinate transform
  -> video renderer viewport/destination rectangle

The upper Android layer must not invent a second independent geometry model.

## Core bridge rule

7.1 introduces a narrow Infinity bridge boundary. The core owns geometry-sensitive facts and exposes stable state/actions upward. Future features should call the bridge instead of repeatedly patching native internals.

Initial bridge responsibilities:
- current native-window width/height
- current display mode / resized-state notification
- PiP state notification
- Fold/multi-window settled-size notification
- safe request for GUI/input remap after a real native-window size change

Future bridge consumers may include system theme state and Health Center diagnostics, but those are not part of the 7.1 behavior test.

## Preserve from 7.0

Do not rewrite the working player lock implementation in 7.1.
Do not add new resume/theme UI in 7.1.
Do not enable the crashing 7.0 dark-mode patch in 7.1.

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

7.1 is a stabilization release. If a change does not directly support Fold resize, PiP, input/GUI geometry synchronization, or the bridge needed to keep those layers uniform, it does not belong in 7.1.
