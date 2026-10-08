#!/usr/bin/env python3
"""Compile/run standalone barrier tests; does not build or claim a working APK."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parent
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++")
    if not compiler:
        raise SystemExit("A C++17 compiler is required")
    with tempfile.TemporaryDirectory(prefix="infinity-persistence-barrier-") as tmp:
        binary = Path(tmp) / "test_barrier"
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-pthread", "-Wall", "-Wextra", "-Werror",
             str(root / "test_barrier.cpp"), "-o", str(binary)],
            check=True,
        )
        subprocess.run([str(binary)], check=True, timeout=30)


if __name__ == "__main__":
    main()
