#!/usr/bin/env python3
"""Finalize Infinity 1.0.9 as one Android app with Infinity + Cobra experiences.

The existing AppShell source builder owns the two in-package Activities and the
startup experience chooser. This layer deliberately removes the secondary
Infinity Live launcher alias so Android exposes one Infinity app/icon only.
Cobra remains an internal experience in the same package and is entered through
the chooser or the app's internal switch path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import infinity_1_0_9_live_app_shell as shell
import infinity_1_0_8_deep_rebrand as deep

RELEASE = "1.0.9-2in1-SingleApp-Candidate-2"
VERSION_CODE = 2103132

GRADLE = shell.GRADLE
MANIFEST = shell.MANIFEST
SPLASH = shell.SPLASH
LIVE_ACTIVITY = shell.LIVE_ACTIVITY


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}")
    return text.replace(old, new, 1)


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def remove_secondary_launcher(manifest: Path) -> None:
    text = manifest.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\n\s*<activity-alias\s+android:name=\"\.InfinityLiveLauncher\".*?</activity-alias>\s*\n",
        re.DOTALL,
    )
    text, count = pattern.subn("\n", text, count=1)
    if count != 1:
        raise RuntimeError(f"secondary Infinity Live launcher: expected one alias, found {count}")
    manifest.write_text(text, encoding="utf-8")


def update_receipt(source: Path, receipt: Path) -> None:
    data = json.loads(receipt.read_text(encoding="utf-8"))
    data["release"] = RELEASE
    data["version_code"] = VERSION_CODE
    data["one_apk_two_environments"] = True
    data["one_android_launcher"] = True
    data["direct_live_launcher"] = False
    data["cobra_entrypoint"] = "startup chooser / internal experience switch"
    files = data.setdefault("files", {})
    for rel in (GRADLE, MANIFEST, SPLASH):
        entry = files.setdefault(str(rel), {})
        entry["after"] = sha(source / rel)
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_phase(source: Path, receipt: Path) -> None:
    source = source.resolve()

    # Build the already-audited two-environment AppShell first. Its own verifier
    # runs before we intentionally remove the old direct launcher alias.
    shell.source_phase(source, receipt)

    gradle = source / GRADLE
    manifest = source / MANIFEST
    splash = source / SPLASH

    text = gradle.read_text(encoding="utf-8")
    text = replace_once(
        text,
        f"versionCode {shell.VERSION_CODE}",
        f"versionCode {VERSION_CODE}",
        "single-app versionCode",
    )
    text = replace_once(
        text,
        f'versionName "{shell.RELEASE}"',
        f'versionName "{RELEASE}"',
        "single-app versionName",
    )
    gradle.write_text(text, encoding="utf-8")

    remove_secondary_launcher(manifest)

    text = splash.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "You can always switch apps later from Settings.",
        "You can always switch experiences later from Settings.",
        "single-app chooser wording",
    )
    splash.write_text(text, encoding="utf-8")

    update_receipt(source, receipt)
    verify_source(source)
    print("PASS: one Infinity launcher contains both Infinity and Cobra experiences")


def verify_source(source: Path) -> None:
    source = source.resolve()
    gradle = (source / GRADLE).read_text(encoding="utf-8")
    manifest = (source / MANIFEST).read_text(encoding="utf-8")
    splash = (source / SPLASH).read_text(encoding="utf-8")
    live_path = source / LIVE_ACTIVITY

    if f"versionCode {VERSION_CODE}" not in gradle:
        raise RuntimeError("single-app versionCode missing")
    if f'versionName "{RELEASE}"' not in gradle:
        raise RuntimeError("single-app versionName missing")
    if f"versionCode {shell.VERSION_CODE}" in gradle or f'versionName "{shell.RELEASE}"' in gradle:
        raise RuntimeError("stale AppShell Candidate 1 identity remains")

    for needle in (
        'android:name=".InfinityLiveActivity"',
        '@APP_PACKAGE@.action.OPEN_LIVE',
    ):
        if needle not in manifest:
            raise RuntimeError("missing in-package Cobra/Live owner: " + needle)

    for forbidden in (
        'android:name=".InfinityLiveLauncher"',
        'android:label="Infinity Live"',
    ):
        if forbidden in manifest:
            raise RuntimeError("secondary Android app/launcher identity remains: " + forbidden)

    launcher_category = '<category android:name="android.intent.category.LAUNCHER" />'
    if manifest.count(launcher_category) != 1:
        raise RuntimeError(
            f"expected exactly one Android launcher category, found {manifest.count(launcher_category)}"
        )

    for needle in (
        "Choose Your Experience",
        "INFINITY 2-IN-1",
        "INFINITY",
        "COBRA",
        "infinity_experience",
        "InfinityLiveActivity.class",
        'intent.putExtra("infinity_live_profile", "cobra")',
        "switch experiences later from Settings.",
    ):
        if needle not in splash:
            raise RuntimeError("missing one-app chooser contract: " + needle)
    if "switch apps later from Settings." in splash:
        raise RuntimeError("old two-app chooser wording remains")

    if not live_path.is_file():
        raise RuntimeError("InfinityLiveActivity.java.in missing")
    live = live_path.read_text(encoding="utf-8")
    for needle in (
        "class InfinityLiveActivity",
        "new ExoPlayer.Builder",
        "COBRA LIVE",
        "SWITCH PROFILE",
        "MULTI-VIEW",
        "returnToInfinity",
    ):
        if needle not in live:
            raise RuntimeError("missing Cobra/Live runtime contract: " + needle)


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
        print("PASS: Infinity + Cobra single-app source verification")
    elif args.cmd == "apk":
        configure_deep()
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        configure_deep()
        deep.verify_apk(args.apk)
        print("PASS: Infinity + Cobra single-app APK branding verification")


if __name__ == "__main__":
    main()
