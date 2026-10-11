#!/usr/bin/env python3
"""Reconstruct the exact preservation lineage, apply the reviewed delta, compile.

This is a work-branch native build. It does not package/publish an APK, change
signing identity, accept a device result, or update an accepted rollback ref.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

import runtime_delta

HERE = Path(__file__).resolve().parent
OUT = Path("checkpoint-build")
DEPENDENCY_PROOF = Path("android-tools/INFINITY-DEPENDENCIES-COMPLETE.json")


def dependency_identity():
    manifest = json.loads((HERE / "runtime/native/manifest.json").read_text())
    inputs = {name: digest for name, digest in manifest["before"].items()
              if name.startswith("tools/depends/")}
    for name in inputs:
        if manifest["after"].get(name) != inputs[name]:
            raise ValueError("A reviewed dependency source changed; reuse requires a new identity")
    return {"schema": 1, "ndk": os.environ.get("NDK_VER"), "host": "aarch64-linux-android",
            "debug": True, "dependency_inputs_sha256": hashlib.sha256(
                json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "inherited_recipe_sha256": hashlib.sha256(Path("scripts/infinity_live_app_ci_2.sh").read_bytes()).hexdigest()}


def verify_dependencies():
    if not DEPENDENCY_PROOF.is_file() or json.loads(DEPENDENCY_PROOF.read_text()) != dependency_identity():
        raise ValueError("Completed dependency identity unavailable; rebuild required")
    prefix = Path(os.environ["DEPENDS"])
    for name in ("x86_64-linux-gnu-native/bin/cmake", "x86_64-linux-gnu-native/bin/pkg-config",
                 "aarch64-linux-android-21-debug/include", "aarch64-linux-android-21-debug/lib"):
        if not (prefix / name).exists():
            raise ValueError("Completed dependency prefix is incomplete: " + name)


def run(*command):
    subprocess.run(command, check=True)


def verify_engine_identity(source, binary):
    header = (source / "xbmc/platform/android/activity/InfinityShutdownTrace.h").read_text()
    tags = re.findall(r'constexpr const char\* ENGINE_TAG = "([^"]+)";', header)
    if len(tags) != 1:
        raise ValueError("Expected exactly one reviewed engine trace identity")
    for token in (b"SAFE_TO_TERMINATE", b"infinityRequestPersistenceCheckpoint",
                  b"infinityAuthorizeCheckpointTermination", b"CHECKPOINT_FAILED",
                  tags[0].encode(), b"scripts.target_before_join",
                  b"scripts.target_before_nonblocking_stop", b"os_tid.%u.stage.%s",
                  b"interpreter_retirement_receipt_limit", b"nonpersistent:ambient-glass", b"PIL._imaging",
                  b"python_bytecode_cache_boundary_rename", b"direct_sqlite_connect_observed",
                  b"full_blocker_inventory_v1", b"python_retirement_batch_v1"):
        if token not in binary:
            raise ValueError("Compiled engine is missing required identity/feature: " + repr(token))
    return tags[0]


def prepare():
    run(sys.executable, str(HERE / "test_native_engine_identity.py"))
    # This inherited recipe replays all accepted Infinity/Cobra/audio/Fold/
    # provider/player deltas and every intervening source guard. It does not
    # substitute an upstream engine. The complete 9374-file compiled-parent
    # manifest is additionally checked by runtime_delta before any new edit.
    run(sys.executable, "repairs/python-exit-2103334/native_ci.py", "prepare")
    run(sys.executable, str(HERE / "run_checks.py"), "--native-source", "kodi",
        "--report", str(OUT / "foundation-tests.json"))
    runtime_delta.apply("native", Path("kodi"))
    run(sys.executable, str(HERE / "native/test_file_checkpoint.py"))
    run(sys.executable, str(HERE / "writers/test_observer.py"))
    run(sys.executable, str(HERE / "writers/test_native_observer.py"), "--runtime", "kodi")
    run(sys.executable, str(HERE / "writers/test_weather_staging_contract.py"), "--runtime", "kodi")
    run(sys.executable, str(HERE / "writers/test_blocker_inventory.py"), "--runtime", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_addon_settings_runtime.py"), "--runtime", "kodi")
    run(sys.executable, str(HERE / "native/test_database_runtime.py"), "--source-root", "kodi")
    run(sys.executable, str(HERE / "native/test_playback_poll.py"), "--source-root", "kodi")
    run(sys.executable, str(HERE / "native/test_playback_freeze.py"), "--source-root", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_native_coordinator.py"), "--runtime", "kodi",
        "--fixture", str(OUT / "native-safe-fixture.json"))
    os.environ["INFINITY_RUNTIME_NATIVE"] = str(Path("kodi").resolve())
    run(sys.executable, str(HERE / "native/test_runtime_file_saves.py"))
    run(sys.executable, str(HERE / "native/test_runtime_dirty_owners.py"))
    run(sys.executable, str(HERE / "native/test_runtime_deferred_dialogs.py"))
    run(sys.executable, str(HERE / "runtime-tests/test_pending_gui_owners.py"),
        "--source-root", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_system_info_checkpoint_job.py"),
        "--runtime", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_pvr_event_job_contract.py"),
        "--source-root", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_pvr_lambda_contracts.py"),
        "--source-root", "kodi")
    for name in ("test_job_checkpoint.py", "test_job_manager_runtime.py",
                 "test_directory_checkpoint_admission.py", "test_texture_job_checkpoint.py", "test_completion_callbacks.py"):
        run(sys.executable, str(HERE / "runtime-tests" / name), "--runtime", "kodi")
    runtime_delta.materialize_commandcenter(OUT / "commandcenter")
    runtime_delta.materialize("embedded-addons", OUT / "embedded-addons")
    run(sys.executable, str(HERE / "native/test_compat_participant.py"),
        "--source-root", str(OUT / "embedded-addons"))
    run(sys.executable, str(HERE / "runtime-tests/test_script_contracts.py"),
        "--runtime", "kodi", "--command-center", str(OUT / "commandcenter"),
        "--embedded", str(OUT / "embedded-addons"))
    run(sys.executable, str(HERE / "runtime-tests/test_script_writer_lifetime.py"),
        "--runtime", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_pvr_checkpoint_admission.py"),
        "--source-root", "kodi")
    run(sys.executable, str(HERE / "runtime-tests/test_runtime_checkpoint.py"),
        "--runtime", str(OUT / "commandcenter"))
    run(sys.executable, str(HERE / "resume-speed/test_speed.py"),
        "--runtime", str(OUT / "commandcenter"))
    run(sys.executable, str(HERE / "runtime-tests/test_runtime_rpc_admission.py"),
        "--runtime", str(OUT / "commandcenter"))
    run(sys.executable, str(HERE / "runtime-tests/run_resume_preservation.py"),
        "--runtime", str(OUT / "commandcenter"))
    run(sys.executable, str(HERE / "runtime-tests/test_runtime_relaunch.py"),
        "--runtime", str(OUT / "commandcenter"))
    import importlib.util
    installed_spec = importlib.util.spec_from_file_location("installed_build", HERE / "installed/build.py")
    installed = importlib.util.module_from_spec(installed_spec)
    installed_spec.loader.exec_module(installed)
    installed.materialize(OUT / "installed-addons")
    shutil.copytree(OUT / "embedded-addons/service.infinity.refresh",
                    OUT / "installed-addons/service.infinity.refresh", dirs_exist_ok=True)
    run(sys.executable, str(HERE / "runtime-tests/test_script_contracts.py"),
        "--runtime", "kodi", "--command-center", str(OUT / "installed-addons/script.infinity.commandcenter"),
        "--embedded", str(OUT / "installed-addons"), "--compat-script", "runtime_service.py")
    run(sys.executable, str(HERE / "runtime-tests/test_runtime_checkpoint.py"),
        "--runtime", str(OUT / "installed-addons/script.infinity.commandcenter"))
    run(sys.executable, str(HERE / "resume-speed/test_speed.py"),
        "--runtime", str(OUT / "installed-addons/script.infinity.commandcenter"))
    run(sys.executable, str(HERE / "installed/test_compat82.py"))
    run(sys.executable, str(HERE / "runtime-tests/test_native_coordinator.py"), "--runtime", "kodi", "--installed-versions")
    for runtime in (OUT / "commandcenter", OUT / "installed-addons/script.infinity.commandcenter"):
        run(sys.executable, str(HERE / "system-stability-2103366/test_resume.py"), "--runtime", str(runtime))
    for name in ("test_installer.py", "test_jobs.py"):
        run(sys.executable, str(HERE / "system-stability-2103366" / name), "--runtime", "kodi")
    run(sys.executable, str(HERE / "system-stability-2103366/test_health.py"),
        "--receipt", str(HERE / "system-stability-2103366/protected-close-fixture.json"))
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
        verify_dependencies()
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
    else:
        complete = 'make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'
        assert stage.count(complete) == 1
        # Only emit this marker after the dependency make returned successfully.
        # Subsequent compile failures may safely preserve that completed prefix.
        mark = 'python3 "$GITHUB_WORKSPACE/repairs/android-checkpoint-shutdown/native_ci.py" mark-dependencies\n'
        stage = stage.replace(complete, mark + complete)
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
    engine_tag = verify_engine_identity(source, binary)
    shutil.copyfile(libraries[0], OUT / "libkodi.so")
    proof = {"schema": 1, "purpose": "unaccepted shutdown work-branch native validation",
             "source_commit": os.environ["GITHUB_SHA"], "parent_apk": 2103335,
             "parent_native": 2103334,
             "engine_tag": engine_tag,
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
    parser.add_argument("mode", choices=("prepare", "compile", "verify-dependencies", "mark-dependencies"))
    parser.add_argument("--completed-cache", action="store_true")
    args = parser.parse_args()
    # The marker call is made from tools/depends after its successful make.
    if args.mode == "mark-dependencies":
        os.chdir(os.environ["GITHUB_WORKSPACE"])
        DEPENDENCY_PROOF.parent.mkdir(parents=True, exist_ok=True)
        DEPENDENCY_PROOF.write_text(json.dumps(dependency_identity(), indent=2, sort_keys=True) + "\n")
        verify_dependencies()
        return
    if args.mode == "verify-dependencies":
        verify_dependencies()
        return
    OUT.mkdir(exist_ok=True)
    if args.mode == "prepare":
        prepare()
    else:
        compile_engine(args.completed_cache)


if __name__ == "__main__":
    main()
