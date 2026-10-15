#!/usr/bin/env python3
"""Compile Java 8 protocol core and execute host tests; keep generated classes in scratch."""
import pathlib
import shutil
import subprocess
import tempfile

root = pathlib.Path(__file__).resolve().parent
sources = sorted(str(path) for directory in ("src", "test") for path in (root / directory).rglob("*.java"))
with tempfile.TemporaryDirectory(prefix="infinity-checkpoint-tests-") as output:
    if shutil.which("javac"):
        compiler = ["javac", "--release", "8"]
    else:
        compiler = ["java", "com.sun.tools.javac.Main", "--release", "8"]
    subprocess.run(compiler + ["-Xlint:all", "-Werror", "-d", output] + sources, check=True)
    subprocess.run(["java", "-ea", "-cp", output,
                    "com.projectinfinity.kodi.shutdown.ShutdownTransactionTest"], check=True)
