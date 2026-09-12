#!/usr/bin/env python3
"""Cumulative audio-policy entry point for the current Responsive v5 contract.

The validated audio recipe is preserved in infinity_audio_policy_source_base.py.
Current Responsive v5 additionally owns the launcher round-icon binding and the
self-verifying refresh controller. Native-media intentionally changes the
manifest before v5, while the validated audio stack already contains the older
1.0.8 refresh lifecycle. This adapter performs strict ownership handoffs for
those two intentional overlaps and leaves every other capability hash-gated.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/infinity_audio_policy_source_base.py"


def load_base():
    spec = importlib.util.spec_from_file_location("infinity_audio_policy_source_base", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


base = load_base()


def prepare_current(source: Path, receipts: Path) -> None:
    receipts.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/infinity71.py"), "source", "--source", str(source)],
        check=True,
    )
    for script, receipt in (
        ("infinity_1_0_6_source.py", "source-1.0.6.json"),
        ("infinity_1_0_7_compat_source.py", "source-1.0.7.json"),
        ("infinity_diagnostics_source.py", "exit-diagnostics.json"),
        ("infinity_1_0_8_refresh_source.py", "source-1.0.8.json"),
        ("infinity_1_0_8_media_source.py", "source-native-media.json"),
    ):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), str(source), "--receipt", str(receipts / receipt)],
            check=True,
        )

    v5 = base.module(ROOT / "scripts/infinity-responsive-v5.py")
    contract = v5.load_contract()
    manifest_rel = "tools/android/packaging/xbmc/AndroidManifest.xml.in"

    # Versioning belongs to the audio/deep release owners. Manifest presentation
    # has a semantic handoff because native-media legitimately adds appCategory.
    exact_paths = [
        rel for rel in v5.TRANSFORMS
        if not rel.endswith("build.gradle.in") and rel != manifest_rel
    ]
    for rel in exact_paths:
        if base.digest(source / rel) != contract["preimage_files"][rel]:
            raise ValueError("Responsive preimage changed: " + rel)
    for rel in exact_paths:
        path = source / rel
        path.write_text(v5.TRANSFORMS[rel](path.read_text(encoding="utf-8")), encoding="utf-8")

    manifest_path = source / manifest_rel
    manifest = manifest_path.read_text(encoding="utf-8")
    if manifest.count('android:appCategory="video"') != 1:
        raise ValueError("Native-media video appCategory owner missing or ambiguous")
    if manifest.count('android:icon="@drawable/project_infinity_icon"') != 1:
        raise ValueError("Infinity launcher icon owner missing or ambiguous before responsive handoff")
    if "android:roundIcon=" in manifest:
        raise ValueError("Unexpected pre-existing round-icon owner before responsive handoff")
    manifest = v5.TRANSFORMS[manifest_rel](manifest)
    if manifest.count('android:roundIcon="@drawable/project_infinity_icon"') != 1:
        raise ValueError("Responsive round-icon binding was not installed exactly once")
    if manifest.count('android:appCategory="video"') != 1:
        raise ValueError("Responsive handoff changed native-media appCategory")
    manifest_path.write_text(manifest, encoding="utf-8")

    # The older cumulative audio baseline already wires InfinityRefreshController,
    # so current v5's installer correctly avoids duplicating the field/callbacks.
    # Upgrade only the missing close lifecycle, then install the current controller
    # bytes and run the current self-verifying refresh contract.
    main_path = source / "tools/android/packaging/xbmc/src/Main.java.in"
    main = main_path.read_text(encoding="utf-8")
    if "mInfinityRefresh.close()" not in main:
        old = "    mInfinityBridge = null;\n    mInfinityRefresh = null;\n"
        new = (
            "    if (mInfinityRefresh != null) mInfinityRefresh.close();\n"
            "    mInfinityRefresh = null;\n"
            "    mInfinityBridge = null;\n"
        )
        if main.count(old) != 1:
            raise ValueError("Legacy refresh destroy lifecycle owner changed")
        main = main.replace(old, new, 1)
        main_path.write_text(main, encoding="utf-8")

    v5.install_refresh_controller(source)
    v5.verify_refresh_controller(source)
    print("PASS: current Responsive v5 capability, launcher and refresh owners applied over native-media stack")


base.prepare = prepare_current


if __name__ == "__main__":
    base.main()
