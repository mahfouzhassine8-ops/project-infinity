#!/usr/bin/env python3
"""Apply one allowlisted helper edit over the verified 2103304 Android source."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = "tools/android/packaging/xbmc/src/InfinityPowerMenuRoutes.java.in"
PREIMAGE = "7c162799c8ac0a0c507e70767b475f3fe9dcd7f53533201eb2002213199faf22"
PARENT_COMMIT = "70309e66ab33d3f12df93b7a46ddb153f1f02f97"


def manifest(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["apply", "verify"])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--parent-proof", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "verify":
        receipt = json.loads(args.receipt.read_text())
        require(manifest(args.source) == receipt["after"], "Source preservation failure")
        print("PASS all 250 sources match the final manifest")
        return
    proof = json.loads(args.parent_proof.read_text())
    require(proof["source_commit"] == PARENT_COMMIT, "Wrong parent source commit")
    require(len(proof["files"]) == 250, "Wrong parent file count")
    before = manifest(args.source)
    require(before == proof["files"], "Parent source preservation failure")
    require(before[TARGET] == PREIMAGE, "Wrong Power route preimage")
    replacement = (HERE / Path(TARGET).name).read_bytes()
    require(hashlib.sha256(replacement).hexdigest() != PREIMAGE, "Empty repair")
    (args.source / TARGET).write_bytes(replacement)
    after = manifest(args.source)
    require(set(before) == set(after), "Unexpected source addition/removal")
    changed = sorted(name for name in before if before[name] != after[name])
    require(changed == [TARGET], "Unexpected source delta")
    receipt = {
        "schema": 1, "baseline_apk": 2103304, "baseline_skin": "1.0.5.195",
        "parent_source_commit": PARENT_COMMIT, "before": before, "after": after,
        "changed": changed, "native_changed": False, "skin_changed": False,
        "weather_changed": False, "shutdown_policy_changed": False,
        "installable_apk": False, "device_verified": False,
        "historical_native_shutdown_hang_resolved": False,
        "deferred_movie_video_framing_changed": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("PASS one route helper edited; 249 sources preserved")


if __name__ == "__main__":
    main()
