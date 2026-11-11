#!/usr/bin/env python3
"""Exact signed-2103480 shutdown source: one-file native ARM64 build.

This script cannot sign, package, install, reset data, or approve Android Close.
It reuses retained source restoration and compiler recipes only after checking
the exact shipped native hash/map and the isolated approved one-file delta.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "shutdown82-native-evidence"
NATIVE = ROOT / "kodi"
BRANCH = "work/infinity-2103480-shutdown-apk-build-20261110"
SOURCE_PARENT = "59efeb8962ff7dbdac5cd1a7766fdba7a42f0df0"
SOURCE = "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
ORIGINAL = "e8f617ac615d657ec0b37d1bef39d277ceafa8e2ad20bb2b6118cebae7f0350f"
CANDIDATE = "2273becee60a25e81b2c5844f052fe32eaa8d03335311672cd67b66bc3738648"
ENGINE = "ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794"
MAP_SHA = "f48df24caabdf36fee25d69d47b0a2ad3c98df3936949c8dcd6d07a92e2f0412"
APK_SHA = "9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2"
BASELINE_MAP = ROOT / "repairs/infinity-watchlist-playback-2103466-20261108/contract-evidence/BASE466-NATIVE-SOURCE-MAP.json"
PATCHED = ROOT / "repairs/infinity-close-startup-2103480-20261110/native/overlay" / SOURCE
BASELINE = ROOT / "repairs/infinity-close-startup-2103480-20261110/BASELINE-SOURCE-BINDINGS.json"
ALLOWED = {
    ".github/workflows/infinity-2103480-shutdown-native-build.yml",
    "repairs/infinity-close-startup-2103480-20261110/build_candidate/native_build.py",
}

def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def require_scope():
    assert os.environ.get("GITHUB_REPOSITORY") == "mahfouzhassine8-ops/project-infinity"
    assert os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
    assert os.environ.get("GITHUB_SHA") == subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
    altered = set(subprocess.check_output(
        ["git", "diff", "--name-only", SOURCE_PARENT, "HEAD"], text=True, cwd=ROOT).splitlines())
    assert altered == ALLOWED, ("OUT_OF_SCOPE_SOURCE_CHANGE", sorted(altered ^ ALLOWED))
    assert sha(BASELINE_MAP) == MAP_SHA
    assert sha(PATCHED) == CANDIDATE
    binding = json.loads(BASELINE.read_text())
    assert binding["APK"] == 2103480 and binding["APK_sha256"] == APK_SHA
    assert binding["native_engine_sha256"] == ENGINE
    assert binding["native_source_map_sha256"] == MAP_SHA
    assert binding["matched_native_sources"][SOURCE] == ORIGINAL
    # Do not alter the original signer or any existing provider/skin/engine source.
    for protected in ("repairs/dual-experience-isolation-2103420/assemble.py",
                      "repairs/dual-experience-isolation-2103420/signer_policy.py",
                      "repairs/universal-persistence-2103401/build.py",
                      "repairs/infinity-three-corrections-20261108/compile_native.py",
                      "repairs/infinity-close-startup-2103480-20261110/provider-compat/service.adulthideout.core/service.py"):
        now = (ROOT / protected).read_bytes()
        prior = subprocess.check_output(
            ["git", "show", SOURCE_PARENT + ":" + protected], cwd=ROOT)
        assert now == prior, "PROTECTED_SOURCE_CHANGED:" + protected

def prepare():
    require_scope()
    assert not NATIVE.exists(), "refuse unclean/reused native build directory"
    # The retained three-corrections restorer reconstructs exactly the original
    # signed77 native generation. Its historical branch/request guard is not a
    # build authorization for this task; our stricter require_scope owns that.
    restorer = load(ROOT / "repairs/infinity-three-corrections-20261108/compile_native.py",
                    "retained_exact77_source_restorer")
    restorer.OUT = OUT
    restorer.scope = lambda: None
    restorer.prepare()
    expected = json.loads(BASELINE_MAP.read_text())
    hasher = load(ROOT / "repairs/infinity-native-touch-2103451-20261105/compile_only.py",
                  "original_full_source_hasher")
    baseline_actual = hasher.hashes(NATIVE)
    assert len(expected) == 9411 and baseline_actual == expected, "SIGNED80_NATIVE_MAP_MISMATCH"
    assert sha(NATIVE / SOURCE) == expected[SOURCE] == ORIGINAL

    apks = list((ROOT / "signed80").rglob("*.apk"))
    assert len(apks) == 1 and sha(apks[0]) == APK_SHA, "SIGNED80_APK_PIN_MISMATCH"
    with ZipFile(apks[0]) as archive:
        original_library = archive.read("lib/arm64-v8a/libkodi.so")
    assert hashlib.sha256(original_library).hexdigest() == ENGINE
    (OUT / "baseline80-libkodi.so").write_bytes(original_library)

    shutil.copyfile(PATCHED, NATIVE / SOURCE)
    changed = hasher.hashes(NATIVE)
    expected_after = dict(expected)
    expected_after[SOURCE] = CANDIDATE
    assert changed == expected_after, "ONLY_ONE_PRODUCTION_NATIVE_FILE_MAY_CHANGE"
    save("NATIVE-SOURCE-MAP.json", changed)
    save("SOURCE-PRESERVATION.json", {
        "status": "PASS_SIGNED80_EXACT_9411_SOURCES_PLUS_ONE_REVIEWED_DELTA",
        "baseline_apk_sha256": APK_SHA,
        "baseline_engine_sha256": ENGINE,
        "baseline_map_sha256": MAP_SHA,
        "modified_source": SOURCE,
        "before_sha256": ORIGINAL,
        "after_sha256": CANDIDATE,
        "unchanged_production_native_files": 9410,
        "Cobra": "SOURCE_UNTOUCHED",
        "APK": "NOT_BUILT", "signed": False, "Android_Close": "NOT_RUN",
        "Fold_acceptance": "NOT_RUN", "unknown_python_native_writer": "STILL_FAIL_CLOSED",
        "source_commit": os.environ["GITHUB_SHA"],
    })
    print("PASS exact signed80 native source and 9410-byte-identical source files", flush=True)

def compile_native():
    require_scope()
    expected = json.loads((OUT / "NATIVE-SOURCE-MAP.json").read_text())
    assert len(expected) == 9411 and sha(NATIVE / SOURCE) == CANDIDATE
    compiler = load(ROOT / "repairs/universal-persistence-2103401/build.py",
                    "retained_original_full_arm64_builder")
    compiler.OUT = OUT
    proof = compiler.compile_engine()
    assert proof["complete_native_engine_compiled"] and proof["reviewed_file_count"] == 9411
    lib = OUT / "libkodi.so"
    assert lib.is_file() and sha(lib) == proof["native_sha256"]
    readelf = Path(os.environ["ANDROID_HOME"]) / (
        "ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf")
    def abi(file):
        header = subprocess.check_output([str(readelf), "-h", str(file)], text=True)
        assert all(x in header for x in ("ELF64", "AArch64", "DYN")), "INVALID_ARM64_ELF"
        symbols = subprocess.check_output([str(readelf), "--dyn-syms", "--wide", str(file)], text=True)
        dynamic = subprocess.check_output([str(readelf), "-d", str(file)], text=True)
        exported = set()
        for line in symbols.splitlines():
            fields = line.split()
            if len(fields) >= 8 and fields[4] == "GLOBAL" and fields[5] in ("DEFAULT", "PROTECTED") and fields[6] != "UND":
                exported.add(fields[7])
        assert "InfinityCommandCenterIdentityV1" in exported
        needed = set(re.findall(r"Shared library: \[([^\]]+)\]", dynamic))
        return exported, needed
    old_exports, old_needed = abi(OUT / "baseline80-libkodi.so")
    exports, needed = abi(lib)
    assert old_exports == exports, "UNRELATED_NATIVE_EXPORT_ABI_CHANGED"
    assert old_needed == needed, "UNRELATED_SHARED_LIBRARY_DEPENDENCIES_CHANGED"
    assert not list(ROOT.glob("*.apk")), "APK_CREATED_OUTSIDE_ORIGINAL_SIGNER"
    save("ARM64-NATIVE-BUILD.json", {
        "status": "PASS_FULL_ARM64_ENGINE_AND_BASELINE_ABI",
        "source_commit": os.environ["GITHUB_SHA"],
        "native_sha256": sha(lib),
        "baseline_native_sha256": ENGINE,
        "source_delta": {SOURCE: {"before": ORIGINAL, "after": CANDIDATE}},
        "original_exports_preserved": len(exports),
        "original_dependencies_preserved": sorted(needed),
        "APK_built": False, "signed": False, "Android_Close": "NOT_RUN",
        "data_preserving_reopen": "NOT_RUN", "Fold_acceptance": "NOT_RUN",
        "core_service_patch_in_APK": False,
        "unknown_native_writer_still_blocks_unsafe_termination": True,
    })
    (OUT / "baseline80-libkodi.so").unlink()
    print("PASS full ARM64 engine, native ABI and fail-closed source preservation; APK NOT BUILT", flush=True)

if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("prepare", "compile")
    {"prepare": prepare, "compile": compile_native}[sys.argv[1]]()
