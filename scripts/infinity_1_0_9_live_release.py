#!/usr/bin/env python3
"""Release/version wrapper for Infinity 1.0.9 Live Candidate 1.

The cumulative rotation pass already owns all native behavior. This wrapper only
advances Android package version metadata from the reviewed Deep Cleanup source
state to the Live candidate and reuses the established deep-brand APK phase.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import infinity_1_0_8_deep_rebrand as deep

OLD_RELEASE = "1.0.9-Deep-Cleanup-1"
OLD_VERSION_CODE = 2103126
RELEASE = "1.0.9-Live-Candidate-1"
VERSION_CODE = 2103127
GRADLE = Path("tools/android/packaging/xbmc/build.gradle.in")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def version_source(source: Path, receipt: Path) -> None:
    path = source / GRADLE
    text = path.read_text(encoding="utf-8")
    old_code = f"versionCode {OLD_VERSION_CODE}"
    old_name = f'versionName "{OLD_RELEASE}"'
    if text.count(old_code) != 1 or text.count(old_name) != 1:
        raise RuntimeError("Live release expected exact reviewed Deep Cleanup version owner")
    before = sha(path)
    text = text.replace(old_code, f"versionCode {VERSION_CODE}", 1)
    text = text.replace(old_name, f'versionName "{RELEASE}"', 1)
    path.write_text(text, encoding="utf-8")
    verify_source(source)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        "schema": 1,
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "previous_release": OLD_RELEASE,
        "previous_version_code": OLD_VERSION_CODE,
        "changed_file": str(GRADLE),
        "before_sha256": before,
        "after_sha256": sha(path),
        "native_behavior_changed": False,
        "runtime_tested": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity Live source version advanced without changing native behavior")


def verify_source(source: Path) -> None:
    text = (source / GRADLE).read_text(encoding="utf-8")
    if f"versionCode {VERSION_CODE}" not in text:
        raise RuntimeError("Infinity Live versionCode missing")
    if f'versionName "{RELEASE}"' not in text:
        raise RuntimeError("Infinity Live versionName missing")
    if f"versionCode {OLD_VERSION_CODE}" in text or f'versionName "{OLD_RELEASE}"' in text:
        raise RuntimeError("stale Deep Cleanup package version remains")


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
        version_source(args.source, args.receipt)
    elif args.cmd == "verify-source":
        verify_source(args.source)
        print("PASS: Infinity 1.0.9 Live source version verification")
    elif args.cmd == "apk":
        configure_deep()
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        configure_deep()
        deep.verify_apk(args.apk)
        print("PASS: Infinity 1.0.9 Live deep-brand APK verification")


if __name__ == "__main__":
    main()
