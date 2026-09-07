from pathlib import Path

root = Path('kodi')
main = root / 'tools/android/packaging/xbmc/src/Main.java.in'
media = root / 'tools/android/packaging/xbmc/src/XBMCMediaSession.java.in'
manifest = root / 'tools/android/packaging/xbmc/AndroidManifest.xml.in'

for expected in (main, media, manifest):
    if not expected.exists():
        raise SystemExit(f'Infinity modernization preflight failed: expected Kodi Android source missing: {expected}')

# -----------------------------------------------------------------------------
# Android manifest modernization
# -----------------------------------------------------------------------------
manifest_text = manifest.read_text()

# Foldables and multi-window must be allowed to own the current window geometry.
# Kodi 21.3 hard-locks both activities to sensorLandscape, which fights cover /
# inner-display transitions and Android's freeform/split-screen window manager.
manifest_text = manifest_text.replace(
    'android:configChanges="orientation|keyboard|keyboardHidden|navigation|touchscreen|screenLayout|screenSize|colorMode"',
    'android:configChanges="orientation|keyboard|keyboardHidden|navigation|touchscreen|screenLayout|screenSize|smallestScreenSize|density|uiMode|colorMode"'
)
manifest_text = manifest_text.replace('android:screenOrientation="sensorLandscape"', 'android:screenOrientation="unspecified"')

# The landscape feature remains useful as a capability hint, but cannot be a hard
# requirement for a phone-first/foldable build.
manifest_text = manifest_text.replace(
    'android:name="android.hardware.screen.landscape"\n        android:required="true"',
    'android:name="android.hardware.screen.landscape"\n        android:required="false"'
)

# Add resizeability to Splash. PiP belongs only to Main.
splash_anchor = 'android:name=".Splash"\n            android:configChanges='
if splash_anchor in manifest_text and 'android:name=".Splash"\n            android:resizeableActivity="true"' not in manifest_text:
    manifest_text = manifest_text.replace(
        'android:name=".Splash"\n            android:configChanges=',
        'android:name=".Splash"\n            android:resizeableActivity="true"\n            android:configChanges=',
        1
    )

main_anchor = 'android:name=".Main"\n            android:configChanges='
if main_anchor in manifest_text and 'android:name=".Main"\n            android:resizeableActivity="true"' not in manifest_text:
    manifest_text = manifest_text.replace(
        'android:name=".Main"\n            android:configChanges=',
        'android:name=".Main"\n            android:resizeableActivity="true"\n            android:supportsPictureInPicture="true"\n            android:configChanges=',
        1
    )

manifest.write_text(manifest_text)

# -----------------------------------------------------------------------------
# Main activity modernization: one Android-facing state owner for lifecycle,
# window geometry, fold/multi-window transitions and PiP.
# -----------------------------------------------------------------------------
main_text = main.read_text()

imports = {
    'import android.app.NativeActivity;\n': 'import android.app.NativeActivity;\nimport android.app.PictureInPictureParams;\n',
    'import android.content.pm.ResolveInfo;\n': 'import android.content.pm.ResolveInfo;\nimport android.content.res.Configuration;\n',
    'import android.media.AudioManager;\n': 'import android.media.AudioManager;\nimport android.media.session.PlaybackState;\n',
    'import android.util.Log;\n': 'import android.util.Log;\nimport android.util.Rational;\n',
}
for anchor, replacement in imports.items():
    if replacement.splitlines()[-1] not in main_text:
        if anchor not in main_text:
            raise SystemExit(f'Infinity modernization failed: import anchor changed: {anchor.strip()}')
        main_text = main_text.replace(anchor, replacement, 1)

class_anchor = 'public class Main extends NativeActivity implements Choreographer.FrameCallback\n{\n'
state_class = '''public class Main extends NativeActivity implements Choreographer.FrameCallback\n{\n  /**\n   * Infinity's Android-facing state owner. Kodi remains the media/add-on core,\n   * while modern Android window/lifecycle state is kept here below skins.\n   */\n  public static final class InfinityEngineState\n  {\n    private static final String TAG = "InfinityEngine";\n    private static volatile boolean sPlaying = false;\n    private static volatile boolean sInPictureInPicture = false;\n    private static volatile boolean sInMultiWindow = false;\n    private static volatile int sWindowWidth = 0;\n    private static volatile int sWindowHeight = 0;\n    private static volatile int sOrientation = Configuration.ORIENTATION_UNDEFINED;\n    private static volatile long sWindowGeneration = 0;\n\n    private InfinityEngineState() {}\n\n    public static void updatePlaybackState(PlaybackState state)\n    {\n      if (state == null)\n      {\n        sPlaying = false;\n        return;\n      }\n\n      final int value = state.getState();\n      sPlaying = value == PlaybackState.STATE_PLAYING ||\n                 value == PlaybackState.STATE_BUFFERING ||\n                 value == PlaybackState.STATE_FAST_FORWARDING ||\n                 value == PlaybackState.STATE_REWINDING;\n      Log.d(TAG, "playback=" + sPlaying + " state=" + value);\n    }\n\n    public static boolean isPlaying() { return sPlaying; }\n\n    public static void setPictureInPicture(boolean inPip)\n    {\n      sInPictureInPicture = inPip;\n      Log.d(TAG, "pip=" + sInPictureInPicture);\n    }\n\n    public static boolean isInPictureInPicture() { return sInPictureInPicture; }\n\n    public static void setMultiWindow(boolean inMultiWindow)\n    {\n      sInMultiWindow = inMultiWindow;\n      Log.d(TAG, "multiWindow=" + sInMultiWindow);\n    }\n\n    public static boolean isInMultiWindow() { return sInMultiWindow; }\n\n    public static void updateWindow(Main activity, Configuration configuration)\n    {\n      if (activity == null)\n        return;\n\n      final Rect rect = activity.getDisplayRect();\n      final int width = Math.max(0, rect.width());\n      final int height = Math.max(0, rect.height());\n      final int orientation = configuration != null\n          ? configuration.orientation : Configuration.ORIENTATION_UNDEFINED;\n\n      if (width != sWindowWidth || height != sWindowHeight || orientation != sOrientation)\n      {\n        sWindowWidth = width;\n        sWindowHeight = height;\n        sOrientation = orientation;\n        sWindowGeneration++;\n        Log.d(TAG, "window#" + sWindowGeneration + "=" + sWindowWidth + "x" +\n                   sWindowHeight + " orientation=" + sOrientation);\n      }\n    }\n\n    public static int getWindowWidth() { return sWindowWidth; }\n    public static int getWindowHeight() { return sWindowHeight; }\n    public static int getOrientation() { return sOrientation; }\n    public static long getWindowGeneration() { return sWindowGeneration; }\n  }\n\n'''
if 'public static final class InfinityEngineState' not in main_text:
    if class_anchor not in main_text:
        raise SystemExit('Infinity modernization failed: Main.java.in class anchor changed')
    main_text = main_text.replace(class_anchor, state_class, 1)
else:
    # A workflow checkout is clean today, but fail loudly rather than accidentally
    # stacking an incompatible older state class if that assumption ever changes.
    raise SystemExit('Infinity modernization failed: checkout already contains InfinityEngineState')

# Shared relayout path. Android can resize a Fold window without recreating the
# NativeActivity, so explicitly request layout/invalidation across the Java view
# hierarchy while leaving native playback alive.
on_new_intent_anchor = '  @Override\n  protected void onNewIntent(Intent intent)\n'
helpers = '''  private void refreshInfinityWindow(Configuration configuration)\n  {\n    InfinityEngineState.updateWindow(this, configuration);\n\n    if (mDecorView != null)\n    {\n      mDecorView.requestLayout();\n      mDecorView.invalidate();\n    }\n    if (mVideoLayout != null)\n    {\n      mVideoLayout.requestLayout();\n      mVideoLayout.invalidate();\n    }\n    if (mMainView != null)\n    {\n      mMainView.requestLayout();\n      mMainView.invalidate();\n    }\n  }\n\n  public void updateInfinityPictureInPictureParams()\n  {\n    if (Build.VERSION.SDK_INT < VERSION_CODES.O)\n      return;\n\n    runOnUiThread(new Runnable()\n    {\n      @Override\n      public void run()\n      {\n        final int width = InfinityEngineState.getWindowWidth();\n        final int height = InfinityEngineState.getWindowHeight();\n        final int safeWidth = width > 0 ? width : 16;\n        final int safeHeight = height > 0 ? height : 9;\n        PictureInPictureParams.Builder builder = new PictureInPictureParams.Builder()\n            .setAspectRatio(new Rational(safeWidth, safeHeight));\n        if (Build.VERSION.SDK_INT >= 31)\n          builder.setAutoEnterEnabled(InfinityEngineState.isPlaying());\n        setPictureInPictureParams(builder.build());\n      }\n    });\n  }\n\n  private void enterInfinityPictureInPicture()\n  {\n    if (Build.VERSION.SDK_INT < VERSION_CODES.O ||\n        !InfinityEngineState.isPlaying() || isInPictureInPictureMode())\n      return;\n\n    try\n    {\n      updateInfinityPictureInPictureParams();\n      final int width = InfinityEngineState.getWindowWidth();\n      final int height = InfinityEngineState.getWindowHeight();\n      final int safeWidth = width > 0 ? width : 16;\n      final int safeHeight = height > 0 ? height : 9;\n      PictureInPictureParams params = new PictureInPictureParams.Builder()\n          .setAspectRatio(new Rational(safeWidth, safeHeight)).build();\n      enterPictureInPictureMode(params);\n    }\n    catch (IllegalArgumentException | IllegalStateException e)\n    {\n      Log.w(TAG, "Infinity PiP request rejected", e);\n    }\n  }\n\n'''
if on_new_intent_anchor not in main_text:
    raise SystemExit('Infinity modernization failed: onNewIntent anchor changed')
main_text = main_text.replace(on_new_intent_anchor, helpers + on_new_intent_anchor, 1)

# Refresh geometry after the view tree exists.
create_anchor = '    mVideoLayout.addView(mMainView, layoutParams);\n'
if create_anchor not in main_text:
    raise SystemExit('Infinity modernization failed: onCreate view anchor changed')
main_text = main_text.replace(
    create_anchor,
    create_anchor + '\n    mVideoLayout.post(new Runnable()\n    {\n      @Override\n      public void run()\n      {\n        refreshInfinityWindow(getResources().getConfiguration());\n        updateInfinityPictureInPictureParams();\n      }\n    });\n',
    1
)

# Fold / rotation / density / screen-size changes are consumed in-place instead
# of killing and recreating Kodi's native activity.
pause_anchor = '  @Override\n  public void onPause()\n'
lifecycle_methods = '''  @Override\n  public void onConfigurationChanged(Configuration newConfig)\n  {\n    super.onConfigurationChanged(newConfig);\n    refreshInfinityWindow(newConfig);\n    updateInfinityPictureInPictureParams();\n  }\n\n  @Override\n  public void onMultiWindowModeChanged(boolean isInMultiWindowMode)\n  {\n    super.onMultiWindowModeChanged(isInMultiWindowMode);\n    InfinityEngineState.setMultiWindow(isInMultiWindowMode);\n    refreshInfinityWindow(getResources().getConfiguration());\n  }\n\n  @Override\n  public void onPictureInPictureModeChanged(boolean isInPictureInPictureMode)\n  {\n    super.onPictureInPictureModeChanged(isInPictureInPictureMode);\n    InfinityEngineState.setPictureInPicture(isInPictureInPictureMode);\n    refreshInfinityWindow(getResources().getConfiguration());\n  }\n\n  @Override\n  protected void onUserLeaveHint()\n  {\n    super.onUserLeaveHint();\n    // Android 12+ uses auto-enter params; this keeps Android 8-11 working too.\n    if (Build.VERSION.SDK_INT < 31)\n      enterInfinityPictureInPicture();\n  }\n\n'''
if pause_anchor not in main_text:
    raise SystemExit('Infinity modernization failed: onPause anchor changed')
main_text = main_text.replace(pause_anchor, lifecycle_methods + pause_anchor, 1)

resume_anchor = '  public void onResume()\n  {\n    super.onResume();\n'
if resume_anchor not in main_text:
    raise SystemExit('Infinity modernization failed: onResume anchor changed')
main_text = main_text.replace(
    resume_anchor,
    resume_anchor + '\n    refreshInfinityWindow(getResources().getConfiguration());\n    updateInfinityPictureInPictureParams();\n',
    1
)

main.write_text(main_text)

# -----------------------------------------------------------------------------
# Media session -> unified playback state -> PiP policy.
# -----------------------------------------------------------------------------
media_text = media.read_text()
old = '''  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n  }\n'''
new = '''  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n    Main.InfinityEngineState.updatePlaybackState(mystate);\n    if (Main.MainActivity != null)\n      Main.MainActivity.updateInfinityPictureInPictureParams();\n  }\n'''
if old not in media_text:
    raise SystemExit('Infinity modernization failed: XBMCMediaSession.java.in anchor changed')
media_text = media_text.replace(old, new, 1)
media.write_text(media_text)

# -----------------------------------------------------------------------------
# Fast hard checks before the expensive dependency/native build.
# -----------------------------------------------------------------------------
main_check = main.read_text()
media_check = media.read_text()
manifest_check = manifest.read_text()
checks = [
    ('public static final class InfinityEngineState', main_check),
    ('onConfigurationChanged(Configuration newConfig)', main_check),
    ('onMultiWindowModeChanged(boolean isInMultiWindowMode)', main_check),
    ('onPictureInPictureModeChanged(boolean isInPictureInPictureMode)', main_check),
    ('enterInfinityPictureInPicture()', main_check),
    ('Main.InfinityEngineState.updatePlaybackState(mystate);', media_check),
    ('android:supportsPictureInPicture="true"', manifest_check),
    ('android:resizeableActivity="true"', manifest_check),
    ('android:screenOrientation="unspecified"', manifest_check),
    ('smallestScreenSize|density|uiMode', manifest_check),
]
for needle, haystack in checks:
    if needle not in haystack:
        raise SystemExit(f'Infinity modernization hard check failed: {needle}')

print('Infinity unified Android modernization patch applied and verified')
