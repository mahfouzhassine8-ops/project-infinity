#!/usr/bin/env python3
"""Compile an unintegrated fence prototype and reproduce the existing seal gaps.

These are host tests. They do not certify Kodi, Android process death, an APK,
or complete filesystem/SQLite hook coverage. Never package on these results.
"""
import argparse
import ctypes
import sqlite3
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES = [
    "unwired-runtime-refused",
    "blocked-optional", "optional-failure", "shared-writer", "shared-failure",
    "retired-shared", "reuse-shared", "opaque", "observer-missing", "symlink",
    "hardlink", "cache-overlap", "late-admission", "concurrent-admission",
    "native-barrier-raw-file-gap",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory(prefix="essential-fence-") as folder:
        folder = Path(folder)
        binary = folder / "test"
        subprocess.run([
            "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
            "-I", str(HERE), "-I", str(ROOT / "repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc"),
            str(HERE / "test_fence.cpp"), "-o", str(binary),
        ], check=True)
        shared = folder / "native-barrier.so"
        subprocess.run([
            "g++", "-std=c++17", "-shared", "-fPIC", "-pthread", "-I", str(HERE),
            "-I", str(ROOT / "repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc"),
            str(HERE / "test_fence.cpp"), "-o", str(shared),
        ], check=True)
        library = ctypes.CDLL(str(shared))
        for name in ("begin", "ready", "seal", "sealed"):
            getattr(library, "infinity_test_" + name).restype = ctypes.c_bool
        database = folder / "shared-protected.db"
        connection = sqlite3.connect(database)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE saves(v)")
        connection.commit()
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("INSERT INTO saves VALUES(42)")
        assert connection.in_transaction
        assert library.infinity_test_begin()
        assert library.infinity_test_ready()
        assert library.infinity_test_seal()
        connection.commit()
        assert library.infinity_test_sealed()
        connection.close()
        with sqlite3.connect(database) as reopened:
            assert reopened.execute("SELECT v FROM saves").fetchall() == [(42,)]
        observation = "REPRODUCED: real Python SQLite transaction commits after native seal\n"
        print(observation, end="")
        results.append({"case": "native-barrier-raw-sqlite-gap", "exit_code": 0, "output": observation})
        for case in CASES:
            p = subprocess.run([str(binary), case, str(folder / case)], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            results.append({"case": case, "exit_code": p.returncode, "output": p.stdout})
            print(p.stdout, end="")
    report = {
        "scope": "unintegrated host fence prototype; raw native-seal negative controls",
        "prototype_sha256": hashlib.sha256((HERE / "InfinityEssentialScriptFence.h").read_bytes()).hexdigest(),
        "results": results,
        "all_expected_observations": all(x["exit_code"] == 0 for x in results),
        "production_integrated": False,
        "protected_write_hook_coverage_verified": False,
        "android_process_death_verified": False,
        "reopening_verified": False,
        "native_arm64_compiled": False,
        "candidate_deliverable": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    assert report["all_expected_observations"], results

if __name__ == "__main__":
    main()
