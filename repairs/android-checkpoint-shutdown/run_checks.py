#!/usr/bin/env python3
"""Run source-component checks; this is not an Android APK or device test."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-source", type=Path, required=True,
                        help="Recovered exact 3334 native source, validated by the SQLite test")
    parser.add_argument("--report", type=Path,
                        help="Optional JSON verification report; no APK success is inferred")
    args = parser.parse_args()
    commands = [
        ("android_transaction", [sys.executable, str(HERE / "test_android.py")]),
        ("native_barrier", [sys.executable, str(HERE / "native/test_barrier.py")]),
        ("checked_sqlite", [sys.executable, str(HERE / "native/test_checked_sqlite.py"),
                            "--source-root", str(args.native_source.resolve())]),
        ("critical_file_io", [sys.executable, str(HERE / "native/test_file_checkpoint.py")]),
        ("resume_participant", [sys.executable, "-m", "unittest", "discover", "-s",
                                str(HERE / "resume"), "-p", "test_*.py", "-v"]),
    ]
    outcomes = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for name, command in commands:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, env=env)
        print(name + ": " + ("PASS" if result.returncode == 0 else "FAIL"), flush=True)
        print(result.stdout, end="", flush=True)
        outcomes.append({"suite": name, "passed": result.returncode == 0,
                         "exit_code": result.returncode, "output": result.stdout})
    manifest = {}
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".class":
            continue
        if args.report and path.resolve() == args.report.resolve():
            continue
        manifest[path.relative_to(HERE).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "host component tests only; no runtime integration or Android/device validation",
        "passed": all(item["passed"] for item in outcomes),
        "normal_close_integrated": False,
        "apk_built": False,
        "physical_device_verified": False,
        "results": outcomes,
        "source_sha256": manifest,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
