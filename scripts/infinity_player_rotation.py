#!/usr/bin/env python3
"""Install Infinity player-only rotation control over the locked 2103123 source stack.

Two modes are exposed through namespaced Android intent actions:
- FOLLOW_DEVICE: release orientation ownership back to Android/user settings.
- UNLOCKED: while real video playback is active, request FULL_SENSOR so the player
  follows physical device orientation even when the user's global auto-rotate is off.

The controller never writes Settings.System rotation state and automatically releases
its orientation request when playback stops, Infinity is backgrounded, PiP/multi-window
is active, or Follow Device is selected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RELEASE = "1.0.9-Deep-Cleanup-1"
VERSION_CODE = 2103126


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}")
    return text.replace(old, new, 1)


def patch_gradle(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "versionCode 2103123", f"versionCode {VERSION_CODE}", "versionCode")
    text = replace_once(text, 'versionName "1.0.8-Deep-Rebrand-Audio-1"',
                        f'versionName "{RELEASE}"', "versionName")
    path.write_text(text, encoding="utf-8")


def patch_manifest(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = '''            android:screenOrientation="unspecified"
            android:theme="@style/AppTheme">

            <!-- Tell NativeActivity the name of or .so -->
'''
    new = '''            android:screenOrientation="unspecified"
            android:theme="@style/AppTheme">

            <!-- Infinity player-only rotation control. These actions are handled
                 inside the existing singleInstance Main activity. -->
            <intent-filter>
                <action android:name="@APP_PACKAGE@.action.PLAYER_ROTATION_FOLLOW_DEVICE" />
                <action android:name="@APP_PACKAGE@.action.PLAYER_ROTATION_UNLOCKED" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>

            <!-- Tell NativeActivity the name of or .so -->
'''
    path.write_text(replace_once(text, old, new, "Main rotation intent filter"), encoding="utf-8")


def patch_main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "import android.content.Intent;\n",
                        "import android.content.Intent;\nimport android.content.SharedPreferences;\n",
                        "SharedPreferences import")
    text = replace_once(text, "import android.content.pm.ResolveInfo;\n",
                        "import android.content.pm.ActivityInfo;\nimport android.content.pm.ResolveInfo;\n",
                        "ActivityInfo import")
    text = replace_once(text, "  private InfinityRefreshController mInfinityRefresh;\n", '''  private InfinityRefreshController mInfinityRefresh;

  private static final String INFINITY_ROTATION_ACTION_FOLLOW =
      "@APP_PACKAGE@.action.PLAYER_ROTATION_FOLLOW_DEVICE";
  private static final String INFINITY_ROTATION_ACTION_UNLOCKED =
      "@APP_PACKAGE@.action.PLAYER_ROTATION_UNLOCKED";
  private static final String INFINITY_ROTATION_PREFS = "infinity_player_rotation";
  private static final String INFINITY_ROTATION_PREF_MODE = "mode";
  private static final int INFINITY_ROTATION_FOLLOW_DEVICE = 0;
  private static final int INFINITY_ROTATION_UNLOCKED = 1;
  private int mInfinityPlayerRotationMode = INFINITY_ROTATION_FOLLOW_DEVICE;
  private int mInfinityLastRequestedOrientation = Integer.MIN_VALUE;
''', "rotation state fields")
    text = replace_once(text,
                        "    super.onNewIntent(intent);\n    // Delay until after Resume\n",
                        "    super.onNewIntent(intent);\n    if (infinityHandlePlayerRotationIntent(intent)) return;\n    // Delay until after Resume\n",
                        "rotation onNewIntent interception")
    text = replace_once(text, '    mInfinityRefresh.apply("attach");\n',
                        '    mInfinityRefresh.apply("attach");\n'
                        '    infinityLoadPlayerRotationMode();\n'
                        '    infinityHandlePlayerRotationIntent(getIntent());\n'
                        '    infinityApplyPlayerRotation("attach");\n',
                        "rotation attach")
    text = replace_once(text, '    if (mInfinityRefresh != null) mInfinityRefresh.apply("resume");\n',
                        '    if (mInfinityRefresh != null) mInfinityRefresh.apply("resume");\n'
                        '    infinityApplyPlayerRotation("resume");\n',
                        "rotation resume")
    text = replace_once(text, "    mPaused = true;\n  }\n",
                        '    mPaused = true;\n'
                        '    infinityApplyPlayerRotation("pause");\n  }\n',
                        "rotation pause release")
    text = replace_once(text,
                        "  public void onStop()\n  {\n    if (mInfinityBridge != null) mInfinityBridge.onStop();\n    super.onStop();\n  }\n",
                        "  public void onStop()\n  {\n    infinityRequestPlayerOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED, \"stop\");\n"
                        "    if (mInfinityBridge != null) mInfinityBridge.onStop();\n    super.onStop();\n  }\n",
                        "rotation stop release")
    text = replace_once(text,
                        '        if (!mInfinityDestroyed && mInfinityRefresh != null)\n          mInfinityRefresh.apply("playback");\n',
                        '        if (!mInfinityDestroyed && mInfinityRefresh != null)\n'
                        '          mInfinityRefresh.apply("playback");\n'
                        '        if (!mInfinityDestroyed) infinityApplyPlayerRotation("playback");\n',
                        "rotation playback callback")

    # The cumulative source stack already owns these callbacks for the responsive
    # bridge and refresh controller. Extend their bodies; never declare duplicates.
    for callback, reason in (("onPictureInPictureModeChanged", "picture-in-picture"),
                             ("onMultiWindowModeChanged", "multi-window")):
        existing = (f"    super.{callback}(active, configuration);\n"
                    "    if (mInfinityBridge != null) mInfinityBridge.onWindowChanged();\n"
                    '    if (mInfinityRefresh != null) mInfinityRefresh.apply("window");\n')
        text = replace_once(text, existing,
                            existing + f'    infinityApplyPlayerRotation("{reason}");\n',
                            "rotation joins " + callback)

    anchor = "  void infinityPublishWindowSnapshot(int width, int height, int theme, int mode, boolean managed)\n"
    helper = r'''  @Override
  @SuppressWarnings("deprecation")
  public void onPictureInPictureModeChanged(boolean inPictureInPictureMode)
  {
    super.onPictureInPictureModeChanged(inPictureInPictureMode);
    infinityApplyPlayerRotation("picture-in-picture");
  }

  @Override
  @SuppressWarnings("deprecation")
  public void onMultiWindowModeChanged(boolean inMultiWindowMode)
  {
    super.onMultiWindowModeChanged(inMultiWindowMode);
    infinityApplyPlayerRotation("multi-window");
  }

  private void infinityLoadPlayerRotationMode()
  {
    SharedPreferences prefs = getSharedPreferences(INFINITY_ROTATION_PREFS, MODE_PRIVATE);
    int mode = prefs.getInt(INFINITY_ROTATION_PREF_MODE, INFINITY_ROTATION_FOLLOW_DEVICE);
    mInfinityPlayerRotationMode = mode == INFINITY_ROTATION_UNLOCKED ?
        INFINITY_ROTATION_UNLOCKED : INFINITY_ROTATION_FOLLOW_DEVICE;
  }

  private boolean infinityHandlePlayerRotationIntent(Intent intent)
  {
    if (intent == null) return false;
    final String action = intent.getAction();
    if (INFINITY_ROTATION_ACTION_FOLLOW.equals(action))
    {
      infinitySetPlayerRotationMode(INFINITY_ROTATION_FOLLOW_DEVICE);
      return true;
    }
    if (INFINITY_ROTATION_ACTION_UNLOCKED.equals(action))
    {
      infinitySetPlayerRotationMode(INFINITY_ROTATION_UNLOCKED);
      return true;
    }
    return false;
  }

  private void infinitySetPlayerRotationMode(int mode)
  {
    mInfinityPlayerRotationMode = mode == INFINITY_ROTATION_UNLOCKED ?
        INFINITY_ROTATION_UNLOCKED : INFINITY_ROTATION_FOLLOW_DEVICE;
    getSharedPreferences(INFINITY_ROTATION_PREFS, MODE_PRIVATE).edit()
        .putInt(INFINITY_ROTATION_PREF_MODE, mInfinityPlayerRotationMode).apply();
    infinityApplyPlayerRotation("mode");
  }

  private boolean infinityHasActiveVideoSafely()
  {
    try
    {
      return _infinityHasActiveVideo();
    }
    catch (LinkageError error)
    {
      Log.w("InfinityRotation", "Player-state bridge unavailable", error);
      return false;
    }
  }

  private void infinityApplyPlayerRotation(String reason)
  {
    boolean constrainedWindow = false;
    try
    {
      constrainedWindow =
          (Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode()) ||
          (Build.VERSION.SDK_INT >= 24 && isInMultiWindowMode());
    }
    catch (IllegalStateException ignored)
    {
      constrainedWindow = true;
    }

    final boolean television = getPackageManager().hasSystemFeature(FEATURE_LEANBACK);
    final boolean unlock = !mPaused && !mInfinityDestroyed && !television && !constrainedWindow &&
        mInfinityPlayerRotationMode == INFINITY_ROTATION_UNLOCKED && infinityHasActiveVideoSafely();
    infinityRequestPlayerOrientation(
        unlock ? ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR :
                 ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,
        reason);
  }

  private void infinityRequestPlayerOrientation(int requested, String reason)
  {
    if (mInfinityLastRequestedOrientation == requested) return;
    try
    {
      setRequestedOrientation(requested);
      mInfinityLastRequestedOrientation = requested;
      Log.i("InfinityRotation", "Player rotation=" +
          (requested == ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR ? "unlocked" : "follow-device") +
          " reason=" + reason);
    }
    catch (IllegalStateException | SecurityException error)
    {
      Log.w("InfinityRotation", "Android rejected player orientation request", error);
    }
  }

'''
    text = replace_once(text, anchor, helper + anchor, "rotation helper methods")
    path.write_text(text, encoding="utf-8")


def verify(source: Path) -> dict:
    gradle = source / "tools/android/packaging/xbmc/build.gradle.in"
    manifest = source / "tools/android/packaging/xbmc/AndroidManifest.xml.in"
    main = source / "tools/android/packaging/xbmc/src/Main.java.in"
    gradle_text = gradle.read_text(encoding="utf-8")
    manifest_text = manifest.read_text(encoding="utf-8")
    main_text = main.read_text(encoding="utf-8")
    if f"versionCode {VERSION_CODE}" not in gradle_text or f'versionName "{RELEASE}"' not in gradle_text:
        raise RuntimeError("release identity verification failed")
    for needle in ("@APP_PACKAGE@.action.PLAYER_ROTATION_FOLLOW_DEVICE",
                   "@APP_PACKAGE@.action.PLAYER_ROTATION_UNLOCKED",
                   'android:screenOrientation="unspecified"'):
        if needle not in manifest_text:
            raise RuntimeError("missing manifest rotation owner: " + needle)
    for needle in ("SCREEN_ORIENTATION_FULL_SENSOR", "SCREEN_ORIENTATION_UNSPECIFIED",
                   "infinityHandlePlayerRotationIntent", "infinityHasActiveVideoSafely",
                   'infinityApplyPlayerRotation("playback")', 'infinityApplyPlayerRotation("pause")',
                   'infinityApplyPlayerRotation("picture-in-picture")',
                   'infinityApplyPlayerRotation("multi-window")',
                   "infinity_player_rotation", "InfinityRotation"):
        if needle not in main_text:
            raise RuntimeError("missing Main rotation owner: " + needle)
    if "ACCELEROMETER_ROTATION" in main_text:
        raise RuntimeError("player rotation must not write Android global auto-rotate state")
    return {
        "schema": 1, "release": RELEASE, "version_code": VERSION_CODE,
        "modes": ["follow-device", "unlocked-during-video"],
        "unlocked_orientation": "ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR",
        "global_rotation_setting_mutated": False,
        "playback_gate": "_infinityHasActiveVideo", "pip_multiwindow_release": True,
        "lifecycle_callbacks": ["pause", "resume", "stop", "picture-in-picture", "multi-window", "playback"],
        "background_release": True,
        "files": {str(p.relative_to(source)): sha(p) for p in (gradle, manifest, main)},
    }


def apply(source: Path, receipt: Path) -> None:
    source = source.resolve()
    paths = [source / "tools/android/packaging/xbmc/build.gradle.in",
             source / "tools/android/packaging/xbmc/AndroidManifest.xml.in",
             source / "tools/android/packaging/xbmc/src/Main.java.in"]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    before = {str(path.relative_to(source)): sha(path) for path in paths}
    patch_gradle(paths[0]); patch_manifest(paths[1]); patch_main(paths[2])
    result = verify(source); result["before"] = before
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity player-only rotation source installed")


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("apply"); p.add_argument("--source", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify"); p.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "apply":
        apply(args.source, args.receipt)
    else:
        print(json.dumps(verify(args.source.resolve()), indent=2, sort_keys=True))
        print("PASS: Infinity player-only rotation source verified")


if __name__ == "__main__":
    main_cli()
