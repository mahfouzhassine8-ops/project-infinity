"""Original Infinity Power Close verification after real skin and add-ons load.

Unlike the historical 37 synthetic-service startup stress probe, this verifies
normal loaded Infinity Power Close. It does NOT waive the older red tests.
"""
import json
from pathlib import Path
import time


def require(ok, reason):
    if not ok:
        raise RuntimeError("INFINITY ACTUAL CLOSE FAILED: " + reason)


def validate_receipt(receipt, owner):
    require(receipt.get("phase") == "COMPLETE",
            "checkpoint did not complete: " + str(receipt.get("error", "missing terminal receipt")))
    require(receipt.get("owner") == owner.get("owner") and receipt.get("pid") == owner.get("pid"),
            "receipt belongs to a different native Infinity process")
    for field in ("checkpoint_saved", "authorization_consumed", "process_death_confirmed"):
        require(receipt.get(field) is True, "missing essential shutdown proof: " + field)
    require(receipt.get("exit_policy") == "essential_first_process_exit_v1",
            "not our approved Infinity Essential-First exit policy")
    native = receipt.get("native_receipt") or {}
    require(native.get("essential_writes_sealed") is True, "essential writes not sealed")
    require(native.get("essential_writes_durable") is True, "essential writes not durable")
    require(native.get("essential_write_blockers") == [], "essential write blockers remain")
    require(len(native.get("owners") or []) == 17 and
            len(native.get("essential_owners") or []) == 16,
            "17 owner / 16 essential owner proof incomplete")
    return {
        "phase": "COMPLETE", "checkpoint_saved": True, "essential_writes_durable": True,
        "engine_process_death_receipt": True, "shutdown_policy": receipt["exit_policy"],
        "owner": owner["owner"], "pid": owner["pid"],
        "whole_package_death_verified": False, "reopened_with_data": False,
    }


def loaded_close(probe, owner, out, report):
    """Run on disposable emulator AFTER genuine Infinity skin load."""
    out = Path(out)
    require(owner.get("phase") == "RUNNING", "missing actual running Infinity owner")
    report["close_action"] = "InfinityPowerControlActivity / com.projectinfinity.kodi.action.CLOSE_KODI"
    report["close_request"] = probe.shell(
        "am", "start", "-n",
        "com.projectinfinity.kodi/.InfinityPowerControlActivity",
        "-a", "com.projectinfinity.kodi.action.CLOSE_KODI",
    )
    deadline = time.monotonic() + 35
    receipt = {}
    while time.monotonic() < deadline:
        receipt = probe.read_json(probe.PRIVATE + "/files/infinity-checkpoint-close.json")
        if (receipt.get("owner") == owner.get("owner") and
                receipt.get("phase") in ("COMPLETE", "CHECKPOINT_FAILED")):
            break
        time.sleep(.25)
    # Write real receipt evidence even when the close fails. Never fabricate.
    (out / "CLOSE-RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    report["close_receipt_phase"] = receipt.get("phase", "MISSING")
    report["close_error"] = receipt.get("error")
    report["close_proof"] = validate_receipt(receipt, owner)
    live = probe.processes()
    report["post_close_processes"] = live
    require(not any(p["pid"] == owner["pid"] for p in live),
            "original Infinity Kodi-derived engine PID still alive after close receipt")
    # The physical TEST4 Close proof was engine termination, not universal whole
    # package termination. Preserve both separate fields; never call 1 == 2.
    report["original_engine_terminated"] = True
    for _ in range(10):
        if not probe.processes():
            break
        time.sleep(.2)
    remaining = probe.processes()
    report["post_close_package_processes"] = remaining
    report["whole_package_death_verified"] = not remaining
    require(not remaining, "Infinity package retains processes after native Close")
    report["close_certified"] = True
    report["close_proof"]["whole_package_death_verified"] = True

    # A clean Close isn't sufficient if user progress/settings disappear.
    report["reopen_request"] = probe.shell(
        "am", "start", "-W", "-n", "com.projectinfinity.kodi/.Splash")
    new_owner = probe.wait_ready(owner["owner"])
    require(new_owner.get("owner") != owner["owner"] and
            new_owner.get("pid") != owner["pid"], "reopen reused terminated native owner")
    selected = probe.rpc("Settings.GetSettingValue",
                         {"setting": "lookandfeel.skin"}).get("value")
    require(selected == "skin.infinity.diggz",
            "reopened Infinity lost its production skin")
    report["close_proof"]["reopened_with_data"] = True
    report["reopen_succeeded"] = True
    report["reopen_skin"] = selected
    # Actual database persistence and content-level Resume seek are separate
    # acceptance gates; this routine does not claim they were proved.
    return report["close_proof"]
