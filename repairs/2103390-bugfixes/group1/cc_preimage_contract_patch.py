#!/usr/bin/env python3
"""Group #1: preserve two exact Command Center dependent hash guards.

Both script.infinity.uirepair and script.infinity.watchedbridge pin all 13
Command Center .20 source files. The Group #1 TV and movie source corrections
change precisely plugin.py and resume_hub.py. Without matching pinned hashes,
the already-installed first-party consumers refuse to load. This tool stages
only the two new trusted hashes in each existing JSON contract. It never edits
the guard code, weakens validation, changes persistence, or touches Cobra.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from movie_identity_patch import patch_bytes as verified_movie_patch
from tv_episode_route_patch import patch_bytes as verified_tv_patch

PREIMAGE_SHA256 = "f091b91bc4c8a62c06327348fa3f57d4411ecce58e44c883ff4aa888fe9edebf"
PINNED_NAMES = ("plugin.py", "resume_hub.py")
ORIGINAL = {
    "plugin.py": "11a741a694869eeca6f1fbdac17bb6ab02c9f807c73a3aa95a4b43323fc574fd",
    "resume_hub.py": "7794e25ec63348d29f74c45948d81db3e2fa1ba780437c329277fcffb1888eff",
}
STAGED = {
    "plugin.py": "ded5e435f1db7af205869ae33d9e2eab888825d95f5086095bc4615e09b05b4f",
    "resume_hub.py": "087860b6a551a23fdd8f7f11ab103b367f0ef44be32b5b42cadecf907e548784",
}
CONSUMERS = ("script.infinity.uirepair", "script.infinity.watchedbridge")
CONTRACT_NAME = "CONTROLLER-PREIMAGES.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def updated_contract(preimage: bytes, original_plugin: bytes, original_hub: bytes) -> bytes:
    if digest(preimage) != PREIMAGE_SHA256:
        raise ValueError("Unknown pinned Command Center dependency contract")
    expected = json.loads(preimage)
    if type(expected) is not dict or len(expected) != 13:
        raise ValueError("Expected 13 fully pinned Command Center files")
    if any(expected.get(key) != ORIGINAL[key] for key in PINNED_NAMES):
        raise ValueError("The original plugin/resume pins no longer match")
    if digest(original_plugin) != ORIGINAL["plugin.py"] or digest(original_hub) != ORIGINAL["resume_hub.py"]:
        raise ValueError("Not the original signed 2103390 Command Center")
    # Hash only the actual verified Group #1 staged output; no caller-supplied
    # digest is trusted. Fail closed if either independently staged patch drifts.
    produced = {
        "plugin.py": digest(verified_tv_patch(original_plugin)),
        "resume_hub.py": digest(verified_movie_patch(original_hub)),
    }
    if produced != STAGED:
        raise ValueError("Unexpected Group #1 Command Center patch content")
    text = preimage.decode("utf-8")
    for name in PINNED_NAMES:
        if text.count(ORIGINAL[name]) != 1:
            raise ValueError("Ambiguous original dependency pin: " + name)
        text = text.replace(ORIGINAL[name], produced[name], 1)
    updated = text.encode("utf-8")
    parsed = json.loads(updated)
    if set(parsed) != set(expected) or len(parsed) != len(expected):
        raise ValueError("Dependency validation keys changed")
    if {key: value for key, value in parsed.items() if key not in PINNED_NAMES} != {
        key: value for key, value in expected.items() if key not in PINNED_NAMES
    }:
        raise ValueError("Unrelated dependency guards changed")
    if updated == preimage:
        raise ValueError("No matching dependency update")
    return updated


def patch_both(original_addons: Path, candidate_addons: Path) -> dict[str, str]:
    original_addons = Path(original_addons).resolve()
    candidate_addons = Path(candidate_addons).resolve()
    if original_addons == candidate_addons:
        raise ValueError("Original signed sources must remain immutable")
    cc = original_addons / "script.infinity.commandcenter"
    originals = [(consumer, original_addons / consumer / CONTRACT_NAME) for consumer in CONSUMERS]
    inputs = [p.read_bytes() for _, p in originals]
    if inputs[0] != inputs[1]:
        raise ValueError("Both dependency contracts must match original 2103390")
    patched = updated_contract(inputs[0], (cc / "plugin.py").read_bytes(),
                               (cc / "resume_hub.py").read_bytes())
    # No staged output until ALL source hashes and contracts are verified.
    for consumer, _ in originals:
        out = candidate_addons / consumer / CONTRACT_NAME
        if out.resolve() == (original_addons / consumer / CONTRACT_NAME).resolve():
            raise ValueError("Refusing original contract overwrite")
    for consumer, _ in originals:
        out = candidate_addons / consumer / CONTRACT_NAME
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(patched)
    return {consumer: digest(patched) for consumer in CONSUMERS}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("original_addons", type=Path)
    p.add_argument("candidate_addons", type=Path)
    args = p.parse_args()
    print(json.dumps(patch_both(args.original_addons, args.candidate_addons), indent=2))
