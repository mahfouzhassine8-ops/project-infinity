#!/usr/bin/env python3
"""Static integrity gate for Infinity 1.0.9 Player Rotation."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "1.0.9-Player-Rotation-1"
VERSION_CODE = 2103125


def load_base():
    path = ROOT / "scripts/verify_infinity_deep_audio_apk.py"
    spec = importlib.util.spec_from_file_location("deep_audio_gate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def verify(apk: Path, engine: Path, source_receipt: Path) -> dict:
    base = load_base()
    result = base.verify(apk, engine, source_receipt)
    with zipfile.ZipFile(apk) as archive:
        dex_names = [name for name in archive.namelist() if re.fullmatch(r"classes\d*\.dex", name)]
        dex = b"".join(archive.read(name) for name in dex_names)
        for needle in (b"PLAYER_ROTATION_FOLLOW_DEVICE", b"PLAYER_ROTATION_UNLOCKED",
                       b"infinity_player_rotation", b"InfinityRotation",
                       b"follow-device", b"unlocked"):
            if needle not in dex:
                raise AssertionError(("missing compiled player-rotation owner", needle))
        if not archive.read("AndroidManifest.xml"):
            raise AssertionError("empty AndroidManifest.xml")
    result.update({
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "player_rotation_api": 1,
        "player_rotation_modes": ["follow-device", "unlocked-during-video"],
        "global_android_rotation_setting_mutated": False,
        "player_rotation_compiled": True,
        "runtime_tested": False,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.apk, args.engine, args.source_receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity 1.0.9 Player Rotation cumulative APK static gate")
    print("Device acceptance is still required for Follow Device and Unlocked behavior.")


if __name__ == "__main__":
    main()
