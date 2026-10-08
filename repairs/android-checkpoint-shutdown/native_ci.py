#!/usr/bin/env python3
"""Reconstruct the exact preservation lineage, apply the reviewed delta, compile.

This is a work-branch native build. It does not package/publish an APK, change
signing identity, accept a device result, or update an accepted rollback ref.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import runtime_delta

HERE = Path(__file__).resolve().parent
OUT = Path("checkpoint-build")


def run(*command):
    subprocess.run(command, check=True)


def prepare():
    # This inherited recipe replays all accepted Infinity/Cobra/audio/Fold/
    # provider/player deltas and every intervening source guard. It does not
    # substitute an upstream engine. The complete 9374-file compiled-parent
    # manifest is additionally checked by runtime_delta before any new edit.
    run(sys.executable, "repairs/python-exit-2103334/native_ci.py", "prepare")
    run(sys.executable, str(HERE / "run_checks.py"), "--native-source", "kodi",
        "--report", str(OUT / "foundation-tests.json"))
    runtime_delta.apply("native", Path("kodi"))
    run(sys.executable, str(HERE / "native/test_database_runtime.py"), "--source-root", "kodi")
    run(sys.executable, str(HERE / "native/test_playback_poll.py"), "--source-root", "kodi")
    run(sys.executable, str(HERE / "native/test_playback_freeze.py"), "--source-root", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_native_coordinator.py"), "--runtime", "kodi",
        "--fixture", str(OUT / "native-safe-fixture.json"))
    os.environ["INFINITY_RUNTIME_NATIVE"] = str(Path("kodi").resolve())
    run(sys.executable, str(HERE / "native/test_runtime_file_saves.py"))
    run(sys.executable, str(HERE / "native/test_runtime_dirty_owners.py"))
    runtime_delta.materialize_commandcenter(OUT / "commandcenter")
    run(sys.executable, str(HERE / "runtime-tests/test_runtime_checkpoint.py"),
        "--runtime", str(OUT / "commandcenter"))
    run(sys.executable, str(HERE / "runtime-tests/run_resume_preservation.py"),
        "--runtime", str(OUT / "commandcenter"))
    manifest = json.loads((HERE / "runtime/native/manifest.json").read_text())
    (OUT / "SOURCE-MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def compile_engine(use_cache):
    source = Path("kodi")
    manifest = json.loads((HERE / "runtime/native/manifest.json").read_text())
    runtime_delta.verify(source, manifest["after"])
    stage = Path("scripts/infinity_live_app_ci_2.sh").read_text()
    inherited = "python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json"
    assert stage.count(inherited) == 1
    stage = stage.replace(inherited, "python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi")
    if use_cache:
        old = '''rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz" "$TARBALLS/fontconfig-2.14.0.tar.xz.sha512"
make -C target/fontconfig FULL_URL=https://gstreamer.freedesktop.org/data/src/mirror/fontconfig-2.14.0.tar.xz download
make -j"$(nproc)"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'''
        cached = '''test -x "$DEPENDS/x86_64-linux-gnu-native/bin/cmake"
test -x "$DEPENDS/x86_64-linux-gnu-native/bin/pkg-config"
test -d "$DEPENDS/aarch64-linux-android-21-debug/include"
test -d "$DEPENDS/aarch64-linux-android-21-debug/lib"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'''
        assert stage.count(old) == 1
        stage = stage.replace(old, cached)
    marker = 'make -C "$BUILD_DIR" apk -j"$(nproc)"'
    assert stage.count(marker) == 1
    script = OUT / "compile-native.sh"
    script.write_text(stage[:stage.index(marker)])
    run("bash", str(script))
    # Build-generated files may appear. Every pre-existing reviewed file stays
    # protected, including every engine input unrelated to this architecture.
    runtime_delta.verify(source, manifest["after"])
    libraries = list(Path(os.environ["BUILD_DIR"]).rglob("libkodi.so"))
    assert len(libraries) == 1, libraries
    binary = libraries[0].read_bytes()
    for token in (b"SAFE_TO_TERMINATE", b"infinityRequestPersistenceCheckpoint",
                  b"infinityAuthorizeCheckpointTermination", b"CHECKPOINT_FAILED",
                  b"infinity-shutdown-2103334-v1"):
        assert token in binary, token
    shutil.copyfile(libraries[0], OUT / "libkodi.so")
    proof = {"schema": 1, "purpose": "unaccepted shutdown work-branch native validation",
             "source_commit": os.environ["GITHUB_SHA"], "parent_apk": 2103335,
             "parent_native": 2103334,
             "native_sha256": hashlib.sha256(binary).hexdigest(),
             "source_manifest_sha256": hashlib.sha256((HERE / "runtime/native/manifest.json").read_bytes()).hexdigest(),
             "enumerated_native_changes": manifest["changed"],
             "all_reviewed_inputs_preserved": True,
             "legacy_shutdown_implementations_retained": True,
             "new_apk_built": False, "device_accepted": False, "locked": False}
    (OUT / "ENGINE-PROOF.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    with (OUT / "elf-identity.txt").open("w") as output:
        subprocess.run(["readelf", "-h", "-n", "-W", str(OUT / "libkodi.so")], stdout=output, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "compile"))
    parser.add_argument("--completed-cache", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.mode == "prepare":
        prepare()
    else:
        compile_engine(args.completed_cache)


if __name__ == "__main__":
    main()
