from pathlib import Path

root = Path('kodi')
main = root / 'tools/android/packaging/xbmc/src/Main.java.in'
media = root / 'tools/android/packaging/xbmc/src/XBMCMediaSession.java.in'

if not main.exists() or not media.exists():
    raise SystemExit('Infinity Phase 1 preflight failed: expected Kodi Android source missing')

main_text = main.read_text()

# Infinity state is deliberately embedded in Main.java.in for Phase 1.
# Kodi's Android packaging only templates a known set of .java.in files; adding a
# brand-new .java.in left @APP_PACKAGE@ unresolved and caused the previous build
# to fail near the end. Embedding the state class here keeps it inside Kodi's
# existing templating/compilation path and avoids hard-coding a package name.
if 'import android.content.res.Configuration;' not in main_text:
    main_text = main_text.replace(
        'import android.content.pm.ResolveInfo;\n',
        'import android.content.pm.ResolveInfo;\nimport android.content.res.Configuration;\n'
    )
if 'import android.media.session.PlaybackState;' not in main_text:
    main_text = main_text.replace(
        'import android.media.AudioManager;\n',
        'import android.media.AudioManager;\nimport android.media.session.PlaybackState;\n'
    )

class_anchor = 'public class Main extends NativeActivity implements Choreographer.FrameCallback\n{\n'
state_class = '''public class Main extends NativeActivity implements Choreographer.FrameCallback\n{\n  /**\n   * Central Android-facing state owned by Infinity Engine.\n   * Lives below skins/OSDs so Diggz or another skin cannot remove the state\n   * used by Fold, PiP, background playback and persistent Player Settings.\n   */\n  public static final class InfinityEngineState\n  {\n    private static final String TAG = "InfinityEngine";\n    private static volatile boolean sPlaying = false;\n    private static volatile boolean sVideo = false;\n    private static volatile boolean sInPictureInPicture = false;\n    private static volatile int sWindowWidth = 0;\n    private static volatile int sWindowHeight = 0;\n    private static volatile int sOrientation = Configuration.ORIENTATION_UNDEFINED;\n\n    private InfinityEngineState() {}\n\n    public static void updatePlaybackState(PlaybackState state)\n    {\n      if (state == null)\n      {\n        sPlaying = false;\n        return;\n      }\n\n      final int value = state.getState();\n      sPlaying = value == PlaybackState.STATE_PLAYING ||\n                 value == PlaybackState.STATE_BUFFERING ||\n                 value == PlaybackState.STATE_FAST_FORWARDING ||\n                 value == PlaybackState.STATE_REWINDING;\n      Log.d(TAG, "playback=" + sPlaying + " state=" + value);\n    }\n\n    public static void setVideoPlaying(boolean video)\n    {\n      sVideo = video;\n      Log.d(TAG, "video=" + sVideo);\n    }\n\n    public static boolean isPlaying() { return sPlaying; }\n    public static boolean isVideoPlaying() { return sPlaying && sVideo; }\n\n    public static void setPictureInPicture(boolean inPip)\n    {\n      sInPictureInPicture = inPip;\n      Log.d(TAG, "pip=" + sInPictureInPicture);\n    }\n\n    public static boolean isInPictureInPicture() { return sInPictureInPicture; }\n\n    public static void updateWindow(Main activity, Configuration configuration)\n    {\n      if (activity == null)\n        return;\n\n      final Rect rect = activity.getDisplayRect();\n      sWindowWidth = Math.max(0, rect.width());\n      sWindowHeight = Math.max(0, rect.height());\n      if (configuration != null)\n        sOrientation = configuration.orientation;\n\n      Log.d(TAG, "window=" + sWindowWidth + "x" + sWindowHeight +\n                 " orientation=" + sOrientation);\n    }\n\n    public static int getWindowWidth() { return sWindowWidth; }\n    public static int getWindowHeight() { return sWindowHeight; }\n    public static int getOrientation() { return sOrientation; }\n  }\n\n'''
if 'public static final class InfinityEngineState' not in main_text:
    if class_anchor not in main_text:
        raise SystemExit('Infinity Phase 1 failed: Main.java.in class anchor changed')
    main_text = main_text.replace(class_anchor, state_class, 1)

config_anchor = '  @Override\n  public void onPause()\n'
config_method = '''  @Override\n  public void onConfigurationChanged(Configuration newConfig)\n  {\n    super.onConfigurationChanged(newConfig);\n    InfinityEngineState.updateWindow(this, newConfig);\n  }\n\n'''
if 'InfinityEngineState.updateWindow(this, newConfig);' not in main_text:
    if config_anchor not in main_text:
        raise SystemExit('Infinity Phase 1 failed: Main.java.in onPause anchor changed')
    main_text = main_text.replace(config_anchor, config_method + config_anchor, 1)

resume_anchor = '  public void onResume()\n  {\n    super.onResume();\n'
if 'InfinityEngineState.updateWindow(this, getResources().getConfiguration());' not in main_text:
    if resume_anchor not in main_text:
        raise SystemExit('Infinity Phase 1 failed: onResume anchor changed')
    main_text = main_text.replace(
        resume_anchor,
        resume_anchor + '\n    InfinityEngineState.updateWindow(this, getResources().getConfiguration());\n',
        1
    )

main.write_text(main_text)

media_text = media.read_text()
old = '''  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n  }\n'''
new = '''  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n    Main.InfinityEngineState.updatePlaybackState(mystate);\n  }\n'''

# Handle both a clean Kodi checkout and a tree patched by the older Phase 1 script.
media_text = media_text.replace(
    '    InfinityEngineState.updatePlaybackState(mystate);\n',
    '    Main.InfinityEngineState.updatePlaybackState(mystate);\n'
)
if 'Main.InfinityEngineState.updatePlaybackState(mystate);' not in media_text:
    if old not in media_text:
        raise SystemExit('Infinity Phase 1 failed: XBMCMediaSession.java.in anchor changed')
    media_text = media_text.replace(old, new, 1)
media.write_text(media_text)

# Fast hard checks: fail before the expensive dependency/native build.
main_check = main.read_text()
media_check = media.read_text()
assert 'public static final class InfinityEngineState' in main_check
assert 'InfinityEngineState.updateWindow(this, newConfig);' in main_check
assert 'Main.InfinityEngineState.updatePlaybackState(mystate);' in media_check
assert 'InfinityEngineState.java.in' not in str(list((root / 'tools/android/packaging/xbmc/src').glob('InfinityEngineState.java.in')))
print('Infinity Engine Phase 1 source patch applied and verified')
