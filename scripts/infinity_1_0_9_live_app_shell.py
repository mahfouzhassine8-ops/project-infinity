#!/usr/bin/env python3
"""Install the isolated Infinity Live app-within-app Android environment.

The normal Infinity/Kodi environment remains the host. Infinity Live is a second
Activity in the same signed APK and owns Live-TV playback through Media3.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

import infinity_1_0_8_deep_rebrand as deep

OLD_RELEASE = "1.0.9-Live-Candidate-1"
OLD_VERSION_CODE = 2103127
RELEASE = "1.0.9-Live-AppShell-Candidate-1"
VERSION_CODE = 2103131

GRADLE = Path("tools/android/packaging/xbmc/build.gradle.in")
INSTALL = Path("cmake/scripts/android/Install.cmake")
MANIFEST = Path("tools/android/packaging/xbmc/AndroidManifest.xml.in")
SPLASH = Path("tools/android/packaging/xbmc/src/Splash.java.in")
LIVE_ACTIVITY = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
ANDROID_CONFIG = Path("cmake/platform/android/android.cmake")

# Gzip-compressed InfinityLiveActivity.java.in. This is Infinity-owned source;
# Cobra is used only as a behavior/reference checklist and no Cobra code/assets
# are embedded in this repository or APK.
LIVE_ACTIVITY_GZ_B64 = """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"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one source anchor, found {count}")
    return text.replace(old, new, 1)


def live_activity_source() -> str:
    raw = gzip.decompress(base64.b64decode(LIVE_ACTIVITY_GZ_B64)).decode("utf-8")
    if "public class InfinityLiveActivity" not in raw:
        raise RuntimeError("embedded Infinity Live Activity source is invalid")
    return raw


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def source_phase(source: Path, receipt: Path) -> None:
    source = source.resolve()
    gradle = source / GRADLE
    install = source / INSTALL
    manifest = source / MANIFEST
    splash = source / SPLASH
    live = source / LIVE_ACTIVITY
    android_config = source / ANDROID_CONFIG
    for path in (gradle, install, manifest, splash, android_config):
        if not path.is_file():
            raise FileNotFoundError(path)
    if live.exists():
        raise RuntimeError("Unexpected pre-existing InfinityLiveActivity")

    before = {str(rel): sha(source / rel) for rel in (GRADLE, INSTALL, MANIFEST, SPLASH, ANDROID_CONFIG)}

    text = gradle.read_text(encoding="utf-8")
    anchor = "    implementation 'com.google.code.gson:gson:2.10.1'\n"
    deps = (
        "    implementation 'androidx.media3:media3-exoplayer:1.7.1'\n"
        "    implementation 'androidx.media3:media3-exoplayer-hls:1.7.1'\n"
        "    implementation 'androidx.media3:media3-exoplayer-rtsp:1.7.1'\n"
    )
    if "androidx.media3:media3-exoplayer:1.7.1" in text:
        raise RuntimeError("Media3 dependencies unexpectedly pre-existing")
    text = once(text, anchor, anchor + deps, "Media3 dependency anchor")
    text = once(text, f"versionCode {OLD_VERSION_CODE}", f"versionCode {VERSION_CODE}", "AppShell versionCode")
    text = once(text, f'versionName "{OLD_RELEASE}"', f'versionName "{RELEASE}"', "AppShell versionName")
    gradle.write_text(text, encoding="utf-8")

    text = install.read_text(encoding="utf-8")
    text = once(
        text,
        "                  src/InfinityAudioFocusHook.java\n",
        "                  src/InfinityAudioFocusHook.java\n                  src/InfinityLiveActivity.java\n",
        "Install Infinity Live Activity",
    )
    install.write_text(text, encoding="utf-8")

    manifest_block = '''        <!-- Infinity Live is a second, isolated Android environment inside
             the same Infinity package. It owns Live-TV playback and can be
             launched directly without making Kodi the Live player. -->
        <activity
            android:name=".InfinityLiveActivity"
            android:configChanges="orientation|keyboard|keyboardHidden|navigation|touchscreen|screenLayout|screenSize|smallestScreenSize|colorMode"
            android:exported="true"
            android:launchMode="singleTask"
            android:screenOrientation="unspecified"
            android:theme="@style/AppTheme">
            <intent-filter>
                <action android:name="@APP_PACKAGE@.action.OPEN_LIVE" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>
        </activity>

        <activity-alias
            android:name=".InfinityLiveLauncher"
            android:targetActivity=".InfinityLiveActivity"
            android:exported="true"
            android:enabled="true"
            android:icon="@drawable/ic_launcher"
            android:label="Infinity Live">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
                <category android:name="android.intent.category.LEANBACK_LAUNCHER" />
            </intent-filter>
        </activity-alias>

'''
    text = manifest.read_text(encoding="utf-8")
    receiver = '        <receiver android:name=".XBMCBroadcastReceiver"\n'
    text = once(text, receiver, manifest_block + receiver, "Infinity Live manifest insertion")
    manifest.write_text(text, encoding="utf-8")

    old_start = '''  protected void startXBMC()
  {
    // Run @APP_NAME@
    Intent intent = getIntent();
    intent.setClass(this, @APP_PACKAGE@.Main.class);
    intent.addFlags(Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP);
    startActivity(intent);
    finish();
  }
'''
    new_start = '''  private static final String INFINITY_EXPERIENCE_PREFS = "infinity_experience";
  private static final String INFINITY_EXPERIENCE_DEFAULT = "default";

  protected void startXBMC()
  {
    Intent incoming = getIntent();
    if (incoming != null && incoming.getAction() != null &&
        !Intent.ACTION_MAIN.equals(incoming.getAction()))
    {
      launchInfinityExperience("infinity");
      return;
    }

    String preferred = getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE)
        .getString(INFINITY_EXPERIENCE_DEFAULT, "");
    if ("live".equals(preferred) || "infinity".equals(preferred))
    {
      launchInfinityExperience(preferred);
      return;
    }
    showInfinityExperienceChooser();
  }

  private void showInfinityExperienceChooser()
  {
    final String[] choices = {
      "Infinity — Movies, Shows, Add-ons & Media",
      "Infinity Live — Live TV, Guide & Multi-View"
    };
    final int[] selected = {0};
    AlertDialog dialog = new AlertDialog.Builder(this)
        .setTitle("Choose your Infinity experience")
        .setSingleChoiceItems(choices, 0, (whichDialog, which) -> selected[0] = which)
        .setPositiveButton("Launch & remember", (whichDialog, which) -> {
          String value = selected[0] == 1 ? "live" : "infinity";
          getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
              .putString(INFINITY_EXPERIENCE_DEFAULT, value).apply();
          launchInfinityExperience(value);
        })
        .setNeutralButton("Just this time", (whichDialog, which) ->
          launchInfinityExperience(selected[0] == 1 ? "live" : "infinity"))
        .setNegativeButton("Exit", (whichDialog, which) -> finish())
        .setCancelable(false)
        .create();
    dialog.show();
  }

  private void launchInfinityExperience(String experience)
  {
    Intent intent = getIntent();
    if (intent == null)
      intent = new Intent();
    intent.setClass(this, "live".equals(experience) ?
        @APP_PACKAGE@.InfinityLiveActivity.class : @APP_PACKAGE@.Main.class);
    intent.addFlags(Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP);
    startActivity(intent);
    finish();
  }
'''
    text = splash.read_text(encoding="utf-8")
    text = once(text, old_start, new_start, "Infinity startup chooser")
    splash.write_text(text, encoding="utf-8")

    live.write_text(live_activity_source(), encoding="utf-8")

    verify_source(source)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        "schema": 1,
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "previous_release": OLD_RELEASE,
        "previous_version_code": OLD_VERSION_CODE,
        "live_app_shell_api": 1,
        "one_apk_two_environments": True,
        "host_environment": "Infinity/Kodi",
        "live_environment": "InfinityLiveActivity",
        "direct_live_launcher": True,
        "startup_chooser": True,
        "live_player_engine": "androidx.media3.exoplayer 1.7.1",
        "features": [
            "m3u", "xtream-compatible-source", "xmltv-guide", "search",
            "categories", "favorites", "recents", "picture-in-picture",
            "two-feed-multiview", "single-audio-owner", "fold-responsive-layout",
            "return-to-infinity"
        ],
        "kodi_application_player_changed": False,
        "kodi_renderer_changed": False,
        "cobra_code_bundled": False,
        "runtime_tested": False,
        "files": {
            **{str(rel): {"before": digest, "after": sha(source / rel)} for rel, digest in before.items()},
            str(LIVE_ACTIVITY): {"after": sha(live)},
        },
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: isolated Infinity Live Activity installed inside the Infinity APK")


def verify_source(source: Path) -> None:
    source = source.resolve()
    gradle = (source / GRADLE).read_text(encoding="utf-8")
    install = (source / INSTALL).read_text(encoding="utf-8")
    manifest = (source / MANIFEST).read_text(encoding="utf-8")
    splash = (source / SPLASH).read_text(encoding="utf-8")
    live = source / LIVE_ACTIVITY
    android_config = (source / ANDROID_CONFIG).read_text(encoding="utf-8")

    if f"versionCode {VERSION_CODE}" not in gradle or f'versionName "{RELEASE}"' not in gradle:
        raise RuntimeError("AppShell package identity missing")
    if f"versionCode {OLD_VERSION_CODE}" in gradle or f'versionName "{OLD_RELEASE}"' in gradle:
        raise RuntimeError("stale Live Candidate package identity remains")
    if "set(TARGET_SDK 34)" not in android_config:
        raise RuntimeError("AppShell must retain Android target SDK 34")
    for dependency in (
        "androidx.media3:media3-exoplayer:1.7.1",
        "androidx.media3:media3-exoplayer-hls:1.7.1",
        "androidx.media3:media3-exoplayer-rtsp:1.7.1",
    ):
        if dependency not in gradle:
            raise RuntimeError("Missing Media3 dependency: " + dependency)
    if install.count("src/InfinityLiveActivity.java") != 1:
        raise RuntimeError("Infinity Live Activity install owner missing or duplicated")
    for needle in (
        'android:name=".InfinityLiveActivity"',
        'android:name=".InfinityLiveLauncher"',
        '@APP_PACKAGE@.action.OPEN_LIVE',
        'android:label="Infinity Live"',
    ):
        if needle not in manifest:
            raise RuntimeError("Missing Live manifest owner: " + needle)
    for needle in (
        "Choose your Infinity experience", "Launch & remember",
        "Infinity Live — Live TV, Guide & Multi-View", "infinity_experience",
        "InfinityLiveActivity.class",
    ):
        if needle not in splash:
            raise RuntimeError("Missing startup chooser owner: " + needle)
    if not live.is_file():
        raise RuntimeError("InfinityLiveActivity.java.in missing")
    java = live.read_text(encoding="utf-8")
    for needle in (
        "class InfinityLiveActivity", "new ExoPlayer.Builder", "DefaultHttpDataSource.Factory",
        "DefaultMediaSourceFactory", "MULTI-VIEW", "XTREAM", "loadXmlTv",
        "FAVORITES", "RECENTS", "SOURCES", "SETTINGS", "returnToInfinity",
    ):
        if needle not in java:
            raise RuntimeError("Missing Live Activity contract: " + needle)
    for forbidden in ("CobraTV", "cobratv", "libmpv", "android.media.MediaPlayer", "new MediaPlayer("):
        if forbidden in java:
            raise RuntimeError("Forbidden copied/legacy player owner in Live Activity: " + forbidden)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("source")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-source")
    p.add_argument("--source", type=Path, required=True)
    p = sub.add_parser("apk")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk")
    p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()

    if args.cmd == "source":
        source_phase(args.source, args.receipt)
    elif args.cmd == "verify-source":
        verify_source(args.source)
        print("PASS: Infinity Live AppShell source verification")
    elif args.cmd == "apk":
        configure_deep()
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        configure_deep()
        deep.verify_apk(args.apk)
        print("PASS: Infinity Live AppShell APK verification")


if __name__ == "__main__":
    main()
