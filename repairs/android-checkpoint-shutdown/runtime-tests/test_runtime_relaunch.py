#!/usr/bin/env python3
"""Exercise actual CC journal handoff in distinct host processes.

The harness supplies native startup registration before Python reads the profile.
It does not test Android lifecycle, JNI startup timing, or owner-death detection.
An incorrect prior owner must fail; the OS subprocess exit supplies the harness's
old-owner-death proof. Runtime source files are imported directly, never copied.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


CHILD = r'''
import json, os, sys, uuid
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import checkpoint_runtime as runtime
from persistence_participant import OperationResult, PersistenceError

profile = Path(sys.argv[2])
cycle = int(sys.argv[3])
control = profile / ".android-checkpoint"
control.mkdir(exist_ok=True)
previous = runtime.read_protocol(control / "engine.json")
current = {"schema": 1, "native_api": 1, "pid": os.getpid(), "owner": str(uuid.uuid4())}
if previous:
    current["previous_owner"] = {"pid": previous["pid"], "token": previous["owner"]}
    if sys.argv[4] == "wrong-prior":
        current["previous_owner"]["token"] = str(uuid.uuid4())
runtime.durable_json(control / "engine.json", current)
try:
    store = runtime.store_for(profile)
except PersistenceError:
    if sys.argv[4] != "wrong-prior":
        raise
    print("rejected")
    raise SystemExit(0)
if sys.argv[4] == "wrong-prior":
    raise AssertionError("foreign previous owner was accepted")

data = store.read("continue-watching.json", {})
assert data.get("cycles", 0) == cycle - 1, data
store.update("continue-watching.json", {}, lambda data: dict(
    data, cycles=cycle, position=417.125, playcount=4))
ok = OperationResult(True)

class Hooks:
    def capture_final_playback(self):
        return ok, {"position": 417.125}
    def persist_final_playback(self, snapshot, writer):
        return ok
    def freeze_playback(self):
        return ok
    def drain_required_events(self, writer):
        return ok
    def persist_session(self, writer):
        writer.update("session.json", {}, lambda data: dict(data, cycle=cycle))
        return ok

receipt = store.checkpoint(str(uuid.uuid4()), Hooks())
assert receipt["status"] == "PARTICIPANT_COMPLETE"
assert receipt["global_safe_to_terminate"] is False
assert store.read("continue-watching.json", {})["playcount"] == 4
print(os.getpid())
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=500)
    args = parser.parse_args()
    runtime = args.runtime.resolve(strict=True)
    if args.cycles <= 0:
        parser.error("cycles must be positive")
    started = time.monotonic()
    pids = set()
    with tempfile.TemporaryDirectory(prefix="infinity-relaunch-") as directory:
        for cycle in range(1, args.cycles + 1):
            result = subprocess.run(
                [sys.executable, "-c", CHILD, str(runtime), directory, str(cycle), "valid"],
                capture_output=True, text=True, timeout=15, check=True)
            pids.add(int(result.stdout.strip()))
        final = json.loads((Path(directory) / "continue-watching.json").read_text())
        bad = subprocess.run(
            [sys.executable, "-c", CHILD, str(runtime), directory, str(args.cycles + 1), "wrong-prior"],
            capture_output=True, text=True, timeout=15, check=True)
        assert bad.stdout.strip() == "rejected"
    print(json.dumps({
        "result": "PASS", "cycles": args.cycles, "distinct_processes": len(pids),
        "elapsed_s": round(time.monotonic() - started, 3), "state": final,
        "foreign_previous_owner": "rejected",
        "scope": "Actual CC journal; harness supplies startup registration and prior-owner death proof",
    }))


if __name__ == "__main__":
    main()
