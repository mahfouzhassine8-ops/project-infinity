# Android 11 first-touch interception — experimental correction

Continue the four repairs on `work/infinity-post-2103384-feature-restoration`.
Do not promote this candidate or reinterpret a failed workflow as accepted.

## Retained failure and causal evidence

Run [39118989328](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39118989328),
commit `837fe2b2f442d0e758e816e83a66369b08aa3bc2`, retained the first-tap screenshot
as well as the menu and dismissal screenshots. All media and add-ons in this
workflow are generated public test fixtures.

* Before/after the first tap on the left tile, selection remains Fixture 01.
* Holding the same coordinates selects Fixture 00 and opens its menu.
* Dismissal leaves Fixture 00 selected on the same page.
* Android logs `nav_input_consumer created` after the Rotate intent/resume
  sequence, then `nav_input_consumer dismissed` at the first tap.

Thus the failing dismissal comparison spans an earlier, missed first tap.
The assertion remains valid and unchanged: this candidate must deliver the
first touch and preserve the selected identity through hold/dismissal.

Android 11's DisplayPolicy creates this consumer when navigation bars are
hidden with `BEHAVIOR_SHOW_BARS_BY_TOUCH`. It consumes the first touch to reveal
the bars. AndroidX's `WindowInsetsControllerCompat.Impl30` documents a framework
bug: `Window.setAttributes` can unexpectedly clear the controller behavior.
Its compatibility implementation uses the legacy immersive flag on API 30.

Primary sources:

* [AOSP Android 30 DisplayPolicy](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/android-30/+/refs/heads/main/com/android/server/wm/DisplayPolicy.java)
* [AndroidX WindowInsetsControllerCompat](https://github.com/androidx/androidx/blob/androidx-main/core/core/src/main/java/androidx/core/view/WindowInsetsControllerCompat.java)
* [Platform behavior documentation](https://developer.android.com/reference/android/view/WindowInsetsController#BEHAVIOR_SHOW_BARS_BY_TOUCH)

The exact installed 2103385 bytecode confirms Main.onResume uses the direct
framework behavior call. Subsequent refresh/window paths call setAttributes.
The APK's bundled older AndroidX Impl30 also directly calls the framework, so
merely changing to that bundled wrapper would not install the workaround.

Run [39120219487](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39120219487)
on API 35 failed before gestures: the observer read zero rows, then NumItems=13,
as the asynchronous provider populated between reads. Commit `c422f636` requires
a populated, consistent snapshot and records OS window/input state around
gestures. It returns to API 30; no priming touch or assertion waiver is added.

## Minimal correction and preservation

`systembars_patch.py` adds the equivalent of `JAVA_ADDITION` immediately after
the existing behavior call, inside its existing controller-null guard:

```java
if (Build.VERSION.SDK_INT == 30) {
  int flags = mDecorView.getSystemUiVisibility();
  mDecorView.setSystemUiVisibility(
      (flags & ~View.SYSTEM_UI_FLAG_IMMERSIVE) | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
}
```

This retains every other flag and affects only API 30. Other Android versions
keep the existing path. It adds no timer, listener, service, input replay,
synthetic tap, player change, or shutdown bypass.

The build reuses the exact permanently signed 2103385 APK, SHA-256
`f0cda703ae43c3e41c952411c5d71622c9473cb6db92d17355cf21cf135e9240`.
Main and onResume have exact preimage hashes. Pinned baksmali/smali tools
reassemble the one modified DEX; all 7,855 decoded classes are compared to the
original plus that exact instruction insertion. The existing instruction
comparison permits only documented encoding/alignment equivalents, including
omitted trailing static false/null defaults as specified by the
[DEX format](https://source.android.com/docs/core/runtime/dex-format#class-def-item).
Nonzero values, instance fields and changed instructions are not normalized.
The second DEX and every native library, resource and asset remain byte-identical.
Only `AndroidManifest.xml` (version fields) and `classes.dex` change.

Candidate: APK **2103386**, `1.0.9-UI-Restoration-Fold-TEST02`.
Skin **1.0.5.227** and UI helper **0.1.0** remain the already built exact packages.
The packaged engine remains
`4b61414f05d67eb6df1f8a32f46d6b96c4991f91674401727d6ea4987f0d01af`;
the raw unstripped compiler artifact is separately identified by `fcd206cd...`.

## Required result, not a source-level claim

The correction is experimental until the new signed APK passes the same full
API 30 UI/Stop/Close/reopen assertions and API 35 regression, plus the unchanged
fresh and existing-data-upgrade Essential-First probes. Each workflow retains
failures. Physical Galaxy Fold acceptance remains required.

The separately reported physical post-Stop status-139 exit has no established
crash-time native stack. This Android input correction is not a crash fix.
