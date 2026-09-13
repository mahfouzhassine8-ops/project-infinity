#!/usr/bin/env python3
"""Deep-brand release wrapper for Infinity 1.0.9 Player Rotation."""
from __future__ import annotations

import argparse
from pathlib import Path
import infinity_1_0_8_deep_rebrand as deep

RELEASE = "1.0.9-Deep-Cleanup-1"
VERSION_CODE = 2103126


def configure() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def main() -> None:
    configure()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("source"); p.add_argument("--source", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-source"); p.add_argument("--source", type=Path, required=True)
    p = sub.add_parser("apk"); p.add_argument("--input", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk"); p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "source":
        deep.source_phase(args.source, args.receipt)
    elif args.cmd == "verify-source":
        deep.verify_source(args.source)
        print("PASS: Infinity 1.0.9 Player Rotation deep-brand source verification")
    elif args.cmd == "apk":
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        deep.verify_apk(args.apk)
        print("PASS: Infinity 1.0.9 Player Rotation deep-brand APK verification")


if __name__ == "__main__":
    main()
