"""Host-only CPython 3.11 proof runner. Does not modify Kodi or build an APK."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "proof-output"
OUT.mkdir(exist_ok=True)
CASES = ["baseline", "ordered", "reuse", "sqlite", "savefail", "hang", "moduleclear", "blockedworker"]
results = []

for mode in CASES:
    db = OUT / f"{mode}.db"
    marker = OUT / f"{mode}.marker"
    for p in (db, marker):
        if p.exists():
            p.unlink()
    cmd = [str(ROOT / "proof"), mode]
    if mode in ("sqlite", "savefail"):
        cmd.append(str(db))
    elif mode == "moduleclear":
        cmd.append(str(marker))
    began = time.monotonic()
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=3 if mode == "hang" else 12)
        stdout, stderr, exit_code, timed_out = run.stdout, run.stderr, run.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
        exit_code, timed_out = None, True

    rows = None
    if db.exists():
        with sqlite3.connect(db) as connection:
            rows = connection.execute("SELECT COUNT(*) FROM persisted").fetchone()[0]

    predicates = {
        "baseline": (not timed_out and exit_code == 0
                     and "BASELINE_CHILDREN_AFTER_350MS=1" in stdout
                     and "BASELINE_NOT_CLEANLY_FINALIZED_BY_DESIGN" in stdout),
        "ordered": (not timed_out and exit_code == 0
                    and "CHILDREN_BEFORE=1" in stdout
                    and "THREADING_SHUTDOWN_COMPLETED" in stdout
                    and "CHILDREN_AFTER=0" in stdout
                    and "EARLY_MODULE_CLEANUP_FINISHED" in stdout
                    and "PYTHON_FINALIZE_STATUS=0" in stdout),
        "reuse": (not timed_out and exit_code == 0 and "REUSE_FUTURE_COMPLETE" in stdout
                  and "PYTHON_FINALIZE_STATUS=0" in stdout),
        "sqlite": (not timed_out and exit_code == 0 and rows == 1
                   and "PERSISTENCE_CALLBACK_COMMITTED" in stdout
                   and "PYTHON_FINALIZE_STATUS=0" in stdout),
        "savefail": (not timed_out and exit_code == 0 and rows == 0
                     and "THREADING_SHUTDOWN_FAILED" in stdout
                     and "NO_CLEAN_RETIREMENT_RECEIPT" in stdout
                     and "PYTHON_FINALIZE_STATUS=0" not in stdout),
        "hang": (timed_out and "STUCK_CALLBACK_ENTERED" in stdout
                 and "CHILDREN_BEFORE=0" in stdout),
        "moduleclear": (not timed_out and exit_code == 0 and not marker.exists()
                        and "MODULES_CLEARED_BEFORE_PY_END_INTERPRETER" in stdout
                        and "ATEXIT_CALLBACK_EXECUTED" not in stdout),
        "blockedworker": (not timed_out and exit_code == 0
                          and "BLOCKING_WORKER_ACTIVE=1" in stdout
                          and "NO_PERSISTENCE_RECEIPT_WHILE_WORKER_ACTIVE" in stdout
                          and "WORKER_RELEASED_COOPERATIVELY" in stdout
                          and "CHILDREN_AFTER=0" in stdout),
    }
    passed = bool(predicates[mode])
    result = {
        "scenario": mode,
        "passed_expected_observation": passed,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.monotonic() - began, 3),
        "sqlite_committed_rows": rows,
        "callback_marker_created": marker.exists() if mode == "moduleclear" else None,
        "stdout": stdout,
        "stderr_tail": stderr[-2500:],
    }
    results.append(result)
    print(f"TEST {mode}: {'PASS' if passed else 'FAIL'}", flush=True)
    print(stdout, flush=True)
    if not passed:
        print(stderr[-1600:], file=sys.stderr, flush=True)

report = {
    "scope": "isolated CPython 3.11 host test only, no Kodi or Android native build",
    "python_executable": sys.executable,
    "python_version": sys.version,
    "results": results,
}
(OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
if not all(item["passed_expected_observation"] for item in results):
    raise SystemExit("FAIL: Some expected host observations were not reproduced")
print(f"PASS: {len(results)}/{len(results)} expected host observations reproduced; "
      "the deliberately hung callback is NOT a successful shutdown, and "
      "real Infinity persistence gates remain untested.", flush=True)
