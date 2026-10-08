#!/usr/bin/env python3
"""Compile and exercise real POSIX file checkpoints plus injected failures."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


class FileCheckpointTest(unittest.TestCase):
    def test_posix_checkpoint(self):
        source = Path(__file__).with_suffix(".cpp")
        compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++")
        if not compiler:
            self.fail("A C++17 compiler is required to validate the checkpoint helper")
        with tempfile.TemporaryDirectory(prefix="infinity-checkpoint-build-") as build:
            binary = Path(build) / "test_file_checkpoint"
            compiled = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-O2", str(source), "-o", str(binary)],
                text=True, capture_output=True, timeout=60,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(binary)], text=True, capture_output=True, timeout=30)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertIn("PASS:", tested.stdout)


if __name__ == "__main__":
    unittest.main()
