#!/usr/bin/env python3
"""APK-stage wrapper for Candidate 2 Extended Background Mode.

The accepted Candidate 2 feature/fixup code remains untouched. This wrapper
only supplies the distinct Extended Background release identity to the existing
APK branding and verification implementation.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_full_fixups as base
import infinity_1_0_8_deep_rebrand as deep

RELEASE = "1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background"
VERSION_CODE = 2103135


def configure() -> None:
    base.RELEASE = RELEASE
    base.VERSION_CODE = VERSION_CODE
    base.full.RELEASE = RELEASE
    base.full.VERSION_CODE = VERSION_CODE
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("apk")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk")
    p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    configure()
    if args.cmd == "apk":
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        deep.verify_apk(args.apk)
        print("PASS: Candidate 2 Extended Background APK branding verification")


if __name__ == "__main__":
    main()
