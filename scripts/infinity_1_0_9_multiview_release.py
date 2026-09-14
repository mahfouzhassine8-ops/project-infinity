#!/usr/bin/env python3
"""Source/release owner for Infinity Live 2-up ExoPlayer Multi-View Candidate 1.

Multi-View is additive: it keeps Kodi's accepted single CApplicationPlayer path
unchanged and adds an Infinity-owned Android overlay controller for exactly two
simultaneous live feeds. Versioning advances from the accepted Live Candidate 1
source identity without rewriting any existing native/player owner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import infinity_1_0_8_deep_rebrand as deep

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/infinity-multiview/InfinityMultiViewController.java.in"
OLD_RELEASE = "1.0.9-Live-Candidate-1"
OLD_VERSION_CODE = 2103127
RELEASE = "1.0.9-Live-ExoPlayer-MultiView-Candidate-1"
VERSION_CODE = 2103130
GRADLE = Path("tools/android/packaging/xbmc/build.gradle.in")
INSTALL = Path("cmake/scripts/android/Install.cmake")
MAIN = Path("tools/android/packaging/xbmc/src/Main.java.in")
CONTROLLER = Path("tools/android/packaging/xbmc/src/InfinityMultiViewController.java.in")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one source anchor, found {count}")
    return text.replace(old, new, 1)


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def source_phase(source: Path, receipt: Path) -> None:
    source = source.resolve()
    gradle = source / GRADLE
    install = source / INSTALL
    main = source / MAIN
    controller = source / CONTROLLER
    for path in (gradle, install, main):
        if not path.is_file():
            raise FileNotFoundError(path)
    if controller.exists():
        raise RuntimeError("Unexpected pre-existing Infinity Multi-View controller")
    if not PATCH.is_file():
        raise FileNotFoundError(PATCH)

    before = {str(rel): sha(source / rel) for rel in (GRADLE, INSTALL, MAIN)}

    text = gradle.read_text(encoding="utf-8")
    dependency_anchor = "    implementation 'com.google.code.gson:gson:2.10.1'\n"
    dependencies = (
        "    implementation 'androidx.media3:media3-exoplayer:1.7.1'\n"
        "    implementation 'androidx.media3:media3-exoplayer-hls:1.7.1'\n"
        "    implementation 'androidx.media3:media3-exoplayer-rtsp:1.7.1'\n"
    )
    if "androidx.media3:media3-exoplayer:1.7.1" in text:
        raise RuntimeError("Media3 dependencies unexpectedly pre-existing")
    if text.count(dependency_anchor) != 1:
        raise RuntimeError("Media3 dependency anchor missing")
    text = text.replace(dependency_anchor, dependency_anchor + dependencies, 1)
    text = once(text, f"versionCode {OLD_VERSION_CODE}", f"versionCode {VERSION_CODE}", "Multi-View versionCode")
    text = once(text, f'versionName "{OLD_RELEASE}"', f'versionName "{RELEASE}"', "Multi-View versionName")
    gradle.write_text(text, encoding="utf-8")

    text = install.read_text(encoding="utf-8")
    text = once(
        text,
        "                  src/InfinityAudioFocusHook.java\n",
        "                  src/InfinityAudioFocusHook.java\n                  src/InfinityMultiViewController.java\n",
        "Install Infinity Multi-View controller",
    )
    install.write_text(text, encoding="utf-8")

    text = main.read_text(encoding="utf-8")
    text = once(
        text,
        "  private RelativeLayout mVideoLayout = null;\n",
        "  private RelativeLayout mVideoLayout = null;\n  private InfinityMultiViewController mInfinityMultiView = null;\n",
        "Multi-View field",
    )
    text = once(
        text,
        "    mVideoLayout.addView(mMainView, layoutParams);\n",
        "    mVideoLayout.addView(mMainView, layoutParams);\n    mInfinityMultiView = new InfinityMultiViewController(this, mVideoLayout, mMainView);\n",
        "Multi-View attach",
    )
    text = once(
        text,
        "  protected void onNewIntent(Intent intent)\n  {\n    super.onNewIntent(intent);\n",
        "  protected void onNewIntent(Intent intent)\n  {\n    super.onNewIntent(intent);\n    if (mInfinityMultiView != null && mInfinityMultiView.handleIntent(intent))\n      return;\n",
        "Multi-View intent handoff",
    )
    existing_configuration = (
        "  @Override\n"
        "  public void onConfigurationChanged(Configuration configuration)\n"
        "  {\n"
        "    super.onConfigurationChanged(configuration);\n"
        "    if (mInfinityBridge != null) mInfinityBridge.onWindowChanged();\n"
        "    if (mInfinityRefresh != null) mInfinityRefresh.apply(\"window\");\n"
        "  }\n"
    )
    text = once(
        text,
        existing_configuration,
        existing_configuration.replace(
            "    if (mInfinityRefresh != null) mInfinityRefresh.apply(\"window\");\n",
            "    if (mInfinityRefresh != null) mInfinityRefresh.apply(\"window\");\n"
            "    if (mInfinityMultiView != null) mInfinityMultiView.onConfigurationChanged(configuration);\n",
        ),
        "Multi-View joins responsive configuration callback",
    )
    text = once(
        text,
        "  public void onPause()\n  {\n    super.onPause();\n",
        "  public void onPause()\n  {\n    super.onPause();\n    if (mInfinityMultiView != null) mInfinityMultiView.onHostPause();\n",
        "Multi-View pause cleanup",
    )
    text = once(
        text,
        "    TvUtil.cancelAllScheduledJobs(this);\n",
        "    if (mInfinityMultiView != null)\n    {\n      mInfinityMultiView.close();\n      mInfinityMultiView = null;\n    }\n    TvUtil.cancelAllScheduledJobs(this);\n",
        "Multi-View destroy cleanup",
    )
    main.write_text(text, encoding="utf-8")
    controller.write_bytes(PATCH.read_bytes())

    verify_source(source)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        "schema": 1,
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "previous_release": OLD_RELEASE,
        "previous_version_code": OLD_VERSION_CODE,
        "multiview_api": 1,
        "player_engine": "androidx.media3.exoplayer 1.7.1",
        "max_simultaneous_feeds": 2,
        "audio_owners": 1,
        "kodi_application_player_changed": False,
        "kodi_renderer_changed": False,
        "android_overlay_controller": True,
        "runtime_tested": False,
        "files": {
            **{rel: {"before": digest, "after": sha(source / rel)} for rel, digest in before.items()},
            str(CONTROLLER): {"after": sha(controller)},
        },
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity ExoPlayer Multi-View source added as isolated two-feed Android overlay")


def verify_source(source: Path) -> None:
    gradle = (source / GRADLE).read_text(encoding="utf-8")
    for dependency in (
        "androidx.media3:media3-exoplayer:1.7.1",
        "androidx.media3:media3-exoplayer-hls:1.7.1",
        "androidx.media3:media3-exoplayer-rtsp:1.7.1",
    ):
        if dependency not in gradle:
            raise RuntimeError("Missing Media3 dependency: " + dependency)
    install = (source / INSTALL).read_text(encoding="utf-8")
    main = (source / MAIN).read_text(encoding="utf-8")
    controller = source / CONTROLLER
    if f"versionCode {VERSION_CODE}" not in gradle or f'versionName "{RELEASE}"' not in gradle:
        raise RuntimeError("Infinity Multi-View package version owner missing")
    if f"versionCode {OLD_VERSION_CODE}" in gradle or f'versionName "{OLD_RELEASE}"' in gradle:
        raise RuntimeError("Stale Infinity Live package version remains")
    if install.count("src/InfinityMultiViewController.java") != 1:
        raise RuntimeError("Infinity Multi-View controller install owner missing or duplicated")
    required_main = (
        "InfinityMultiViewController mInfinityMultiView",
        "new InfinityMultiViewController(this, mVideoLayout, mMainView)",
        "mInfinityMultiView.handleIntent(intent)",
        "mInfinityMultiView.onConfigurationChanged(configuration)",
        "mInfinityMultiView.onHostPause()",
        "mInfinityMultiView.close()",
    )
    for needle in required_main:
        if needle not in main:
            raise RuntimeError("Missing Main Multi-View integration: " + needle)
    if main.count("public void onConfigurationChanged(Configuration configuration)") != 1:
        raise RuntimeError("Multi-View must share the single responsive configuration callback")
    if not controller.is_file():
        raise RuntimeError("InfinityMultiViewController.java.in missing")
    java = controller.read_text(encoding="utf-8")
    for needle in (
        "new ExoPlayer.Builder",
        "DefaultHttpDataSource.Factory",
        "DefaultMediaSourceFactory",
        "setVideoTextureView(texture)",
        "clearVideoTextureView(texture)",
        "setAudible(index == mAudioTile)",
        "requires exactly two feeds",
        'TAG_SCHEME = \"infinity-multiview\"',
    ):
        if needle not in java:
            raise RuntimeError("Missing Multi-View controller contract: " + needle)
    forbidden = ("android.media.MediaPlayer", "new MediaPlayer(", "libmpv", "CobraTV", "cobratv")
    for needle in forbidden:
        if needle in java:
            raise RuntimeError("Unexpected third-party/native player dependency in Multi-View: " + needle)


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
        print("PASS: Infinity ExoPlayer Multi-View source verification")
    elif args.cmd == "apk":
        configure_deep()
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        configure_deep()
        deep.verify_apk(args.apk)
        print("PASS: Infinity Multi-View deep-brand APK verification")


if __name__ == "__main__":
    main()
