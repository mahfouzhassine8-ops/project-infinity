#!/usr/bin/env python3
"""Safe entry point for Cobra Full Feature Candidate 2.

The large Candidate 2 transform intentionally uses exact-match guards. One
Candidate 1 loop anchor occurs twice (category collection and channel filtering),
so this runner narrows only that parental-filter insertion before invoking the
reviewed transform. All other exact guards remain strict.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_full as full
import infinity_1_0_9_cobra_full_fixups as fixups

RELEASE = full.RELEASE
VERSION_CODE = full.VERSION_CODE
_ORIGINAL_INSERT_AFTER = full.insert_after


def candidate2_insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if label != "Candidate 2 parental live filter":
        return _ORIGINAL_INSERT_AFTER(text, anchor, addition, label)
    target = (
        "    String needle = mSearch.trim().toLowerCase(Locale.US);\n"
        "    for (Channel channel : mChannels) {\n"
    )
    replacement = target + addition
    if text.count(target) != 1:
        raise RuntimeError(
            f"{label}: filteredChannels anchor expected exactly once, found {text.count(target)}"
        )
    return text.replace(target, replacement, 1)


def transform_for_fast_test(java: str) -> str:
    previous = full.insert_after
    full.insert_after = candidate2_insert_after
    try:
        return fixups.harden_activity(full.patch_activity(java))
    finally:
        full.insert_after = previous


def source_phase(source: Path, receipt: Path) -> None:
    previous = full.insert_after
    full.insert_after = candidate2_insert_after
    try:
        fixups.source_phase(source, receipt)
    finally:
        full.insert_after = previous


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
        fixups.verify_source(args.source)
        print("PASS: Cobra Candidate 2 safe source verification")
    elif args.cmd == "apk":
        fixups.configure_deep()
        import infinity_1_0_8_deep_rebrand as deep
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        fixups.configure_deep()
        import infinity_1_0_8_deep_rebrand as deep
        deep.verify_apk(args.apk)
        print("PASS: Cobra Candidate 2 safe APK branding verification")


if __name__ == "__main__":
    main()
