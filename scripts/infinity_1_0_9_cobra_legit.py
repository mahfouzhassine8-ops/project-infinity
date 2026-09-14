#!/usr/bin/env python3
"""Install the legitimate Cobra Live runtime into the one-package Infinity 2-in-1 APK.

This starts from the single-launcher AppShell candidate, replaces the prototype
Live Activity with the independently authored Cobra runtime, enables HTTP IPTV
providers explicitly, and keeps the Kodi/Infinity player path untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import infinity_1_0_9_single_app as single
import infinity_1_0_8_deep_rebrand as deep

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/infinity-cobra/InfinityLiveActivity.java.in"
THEME = ROOT / "addons/script.infinity.live/resources/cobra-theme.json"

RELEASE = "1.0.9-Cobra-Legitimate-Live-Candidate-1"
VERSION_CODE = 2103133

GRADLE = single.GRADLE
MANIFEST = single.MANIFEST
SPLASH = single.SPLASH
LIVE_ACTIVITY = single.LIVE_ACTIVITY


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def source_phase(source: Path, receipt: Path) -> None:
    source = source.resolve()
    if not PATCH.is_file():
        raise FileNotFoundError(PATCH)
    if not THEME.is_file():
        raise FileNotFoundError(THEME)

    # Preserve the already-audited one-package/one-launcher foundation.
    single.source_phase(source, receipt)

    gradle = source / GRADLE
    manifest = source / MANIFEST
    live = source / LIVE_ACTIVITY

    text = gradle.read_text(encoding="utf-8")
    text = once(
        text,
        f"versionCode {single.VERSION_CODE}",
        f"versionCode {VERSION_CODE}",
        "Cobra legitimate-live versionCode",
    )
    text = once(
        text,
        f'versionName "{single.RELEASE}"',
        f'versionName "{RELEASE}"',
        "Cobra legitimate-live versionName",
    )
    gradle.write_text(text, encoding="utf-8")

    # A large share of real Xtream/M3U services still use plain HTTP. Android
    # blocks cleartext traffic by default at this target SDK unless the app
    # explicitly opts in. This applies only to user-selected provider traffic.
    text = manifest.read_text(encoding="utf-8")
    if 'android:usesCleartextTraffic="true"' not in text:
        text = once(
            text,
            'android:requestLegacyExternalStorage="true">',
            'android:requestLegacyExternalStorage="true"\n'
            '        android:usesCleartextTraffic="true">',
            "IPTV HTTP transport opt-in",
        )
    manifest.write_text(text, encoding="utf-8")

    # Replace the prototype compressed activity with a clear, auditable source
    # implementation that owns provider login, channel loading and Exo playback.
    live.write_bytes(PATCH.read_bytes())

    verify_source(source)

    data = json.loads(receipt.read_text(encoding="utf-8"))
    data.update(
        {
            "release": RELEASE,
            "version_code": VERSION_CODE,
            "one_apk_two_environments": True,
            "one_android_launcher": True,
            "cobra_runtime": "legitimate-live-v1",
            "cobra_player": "androidx.media3.exoplayer 1.7.1",
            "xtream_provider_flow": True,
            "m3u_provider_flow": True,
            "xmltv_epg": True,
            "two_feed_multiview": True,
            "single_audio_owner": True,
            "cleartext_provider_opt_in": True,
            "external_theme_contract": (
                ".kodi/addons/script.infinity.live/resources/cobra-theme.json"
            ),
            "kodi_application_player_changed": False,
            "kodi_renderer_changed": False,
            "runtime_tested": False,
        }
    )
    files = data.setdefault("files", {})
    for rel in (GRADLE, MANIFEST, LIVE_ACTIVITY):
        entry = files.setdefault(str(rel), {})
        entry["after"] = sha(source / rel)
    data["theme_source_sha256"] = sha(THEME)
    receipt.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PASS: legitimate Cobra Live runtime installed inside one Infinity APK")


def verify_source(source: Path) -> None:
    source = source.resolve()
    gradle = (source / GRADLE).read_text(encoding="utf-8")
    manifest = (source / MANIFEST).read_text(encoding="utf-8")
    splash = (source / SPLASH).read_text(encoding="utf-8")
    live_path = source / LIVE_ACTIVITY

    if f"versionCode {VERSION_CODE}" not in gradle:
        raise RuntimeError("Cobra legitimate-live versionCode missing")
    if f'versionName "{RELEASE}"' not in gradle:
        raise RuntimeError("Cobra legitimate-live versionName missing")
    if f"versionCode {single.VERSION_CODE}" in gradle:
        raise RuntimeError("stale single-app candidate versionCode remains")
    if f'versionName "{single.RELEASE}"' in gradle:
        raise RuntimeError("stale single-app candidate versionName remains")

    if manifest.count('<category android:name="android.intent.category.LAUNCHER" />') != 1:
        raise RuntimeError("Infinity must expose exactly one Android launcher")
    if 'android:name=".InfinityLiveLauncher"' in manifest:
        raise RuntimeError("secondary Infinity Live launcher alias returned")
    if 'android:name=".InfinityLiveActivity"' not in manifest:
        raise RuntimeError("in-package Cobra Activity missing")
    if 'android:usesCleartextTraffic="true"' not in manifest:
        raise RuntimeError("plain-HTTP IPTV provider support is not enabled")

    for needle in (
        "Choose Your Experience",
        "INFINITY 2-IN-1",
        "COBRA",
        "InfinityLiveActivity.class",
    ):
        if needle not in splash:
            raise RuntimeError("single-app experience chooser missing: " + needle)

    if not live_path.is_file():
        raise RuntimeError("InfinityLiveActivity.java.in missing")
    java = live_path.read_text(encoding="utf-8")

    required_runtime = (
        "class InfinityLiveActivity",
        "player_api.php?username=",
        "get_live_categories",
        "get_live_streams",
        "/xmltv.php?username=",
        "parseM3u",
        "#EXTVLCOPT:",
        "#EXTHTTP:",
        "direct_source",
        "new ExoPlayer.Builder",
        "DefaultHttpDataSource.Factory",
        "setAllowCrossProtocolRedirects(true)",
        "setEnableDecoderFallback(true)",
        "setVideoTextureView",
        "openMultiView",
        "setMultiAudio",
        "Stream could not play",
        "Server not found. Check the address, Wi-Fi, VPN, or DNS.",
        ".kodi/addons/script.infinity.live/resources/cobra-theme.json",
        "returnToInfinity",
    )
    for needle in required_runtime:
        if needle not in java:
            raise RuntimeError("Cobra runtime contract missing: " + needle)

    forbidden = (
        "CobraTV_",
        "com.cobratv",
        "libmpv",
        "android.media.MediaPlayer",
        "new MediaPlayer(",
    )
    for needle in forbidden:
        if needle in java:
            raise RuntimeError("forbidden copied/legacy player owner: " + needle)

    theme = json.loads(THEME.read_text(encoding="utf-8"))
    for key in (
        "background",
        "rail",
        "panel",
        "panel2",
        "focus",
        "accent",
        "accent_soft",
        "text",
        "muted",
        "line",
        "row_height",
        "guide_row_height",
    ):
        if key not in theme:
            raise RuntimeError("Cobra external theme key missing: " + key)


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
        print("PASS: legitimate Cobra Live source verification")
    elif args.cmd == "apk":
        configure_deep()
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        configure_deep()
        deep.verify_apk(args.apk)
        print("PASS: legitimate Cobra Live APK branding verification")


if __name__ == "__main__":
    main()
