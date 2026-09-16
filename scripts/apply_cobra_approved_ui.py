#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_approved_ui as approved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / "tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in"
    java = live.read_text(encoding="utf-8")
    java = approved.patch(java)
    approved.verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: approved Cobra collapsible-drawer/player/Multi-View UI applied")


if __name__ == "__main__":
    main()
