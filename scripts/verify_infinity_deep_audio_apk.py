#!/usr/bin/env python3
"""Reject incomplete Deep Rebrand + Audio cumulative APKs.

This is a static/package integrity gate. It proves that the final branded APK
still contains the source-built Responsive Bridge v5, native-media layer,
Audio Policy API 1, current Infinity upper layer, and byte-identical compiled
engine members. It does not prove device/runtime behavior or Samsung features.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FINAL_RELEASE = "1.0.8-Deep-Rebrand-Audio-1"
FINAL_VERSION_CODE = 2103123
ADDONS = ("service.infinity.compat", "service.infinity.refresh", "script.infinity.audiopolicy")


def load_cumulative_module():
    spec = importlib.util.spec_from_file_location(
        "infinity_cumulative", ROOT / "scripts/verify_infinity_cumulative_media.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_addon_files() -> dict[str, bytes]:
    expected: dict[str, bytes] = {}
    for addon_id in ADDONS:
        root = ROOT / "addons" / addon_id
        if not root.is_dir():
            raise FileNotFoundError(root)
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                name = f"assets/addons/{addon_id}/" + path.relative_to(root).as_posix()
                expected[name] = path.read_bytes()
    return expected


def verify(apk: Path, engine: Path, source_receipt: Path) -> dict:
    cumulative = load_cumulative_module()
    presence = cumulative.inspect(apk)
    if not presence["static_presence_gate_passed"]:
        raise AssertionError(("missing cumulative media owners", presence["missing"]))

    receipt = json.loads(source_receipt.read_text(encoding="utf-8"))
    assert receipt["bridge_version"] == 5, receipt
    assert receipt["platform_hook_api"] == 2, receipt
    assert receipt["audio_policy_api"] == 1, receipt
    assert receipt["versionCode"] == 2103120, receipt

    expected = expected_addon_files()
    with zipfile.ZipFile(engine) as base, zipfile.ZipFile(apk) as final:
        assert final.testzip() is None
        names = final.namelist()
        assert len(names) == len(set(names)), "duplicate APK members"

        dex_names = [n for n in names if re.fullmatch(r"classes\d*\.dex", n)]
        dex = [final.read(n) for n in dex_names]
        classes = set().union(*(cumulative.dex_classes(data) for data in dex))
        assert "Lcom/projectinfinity/kodi/InfinityAudioFocusHook;" in classes
        assert "Lcom/projectinfinity/kodi/InfinityPlatformHooks;" in classes
        assert "Lcom/projectinfinity/kodi/InfinitySystemMediaHook;" in classes
        for needle in (b"Published responsive v5", b"acquireAudioFocus", b"releaseAudioFocus", b"updateAudioPolicy"):
            assert any(needle in data for data in dex), needle

        native = final.read("lib/arm64-v8a/libkodi.so")
        for needle in (
            b"Infinity.NativeDeviceMode",
            b"Infinity.NativeWidthDp",
            b"Infinity.AudioPolicyApi",
            b"Infinity AudioPolicy API 1 AudioTrack:",
            b"infinity-audio-policy.json",
        ):
            assert needle in native, needle

        # Packaging/branding is not allowed to mutate the source-built engine.
        for name in base.namelist():
            if name.startswith("lib/") or re.fullmatch(r"classes\d*\.dex", name):
                assert base.read(name) == final.read(name), name

        for name, data in expected.items():
            assert final.read(name) == data, ("upper-layer mismatch", name)

        audio_contract = json.loads(final.read("assets/addons/script.infinity.audiopolicy/contract.json"))
        assert audio_contract["api"] == 1

        po = final.read("assets/addons/resource.language.en_gb/resources/strings.po").decode("utf-8")
        assert 'msgid "About Infinity"' in po
        assert "Kodi Foundation" in po

    return {
        "schema": 1,
        "release": FINAL_RELEASE,
        "version_code": FINAL_VERSION_CODE,
        "apk_sha256": sha(apk.read_bytes()),
        "engine_sha256": sha(engine.read_bytes()),
        "bridge_version": 5,
        "platform_hook_api": 2,
        "audio_policy_api": 1,
        "responsive_v5_present": True,
        "current_upper_layer_present": True,
        "engine_bytes_preserved": True,
        "source_receipt": receipt,
        "runtime_tested": False,
        "audio_track_policy_verified_on_device": False,
        "samsung_audio_eraser_eligibility": "unknown",
        "note": "Static/package pass only. Device acceptance remains required.",
    }


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
    print("PASS: Deep Rebrand + Responsive v5 + native media + Audio Policy API 1 cumulative APK")
    print("Device tests still required; this does not prove Samsung Audio Eraser eligibility.")


if __name__ == "__main__":
    main()
