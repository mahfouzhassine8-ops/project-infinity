#!/usr/bin/env python3
"""Apply the audited Cobra UI Runtime v3 to the reconstructed Android shell."""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_ui_runtime as runtime


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / "tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in"
    java = live.read_text(encoding="utf-8")
    java = runtime.patch(java)
    runtime.verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra UI Runtime v3 applied; ZIP owns presentation, native lifecycle remains protected")


if __name__ == "__main__":
    main()
