"""Compile exact 2103460 native VideoNav successor; no APK, keys or device mutation.

The trusted 2103451 source restoration comes from the original verified
compiler inputs. Reconstruct 2103460 VideoNav exactly, verify its source digest,
then replace ONLY that native file with the scoped source candidate.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "controlled-native"
BRANCH = "work/infinity-2103460-skin-script-scoped-fixes-20261106"
BASE = "a4c1d751c32b3a978ee86ab4ed9a7b38783956dc"
NAV = "xbmc/video/windows/GUIWindowVideoNav.cpp"
SOURCE = "repairs/infinity-2103458-six-corrections-20261105/integration-048/native/" + NAV
RELEASE_SOURCE = ROOT / SOURCE
OLD_SHA256 = "06e225a5ca9ce552dbdd00c270a0f0423c779b755a5d758fd550955a30e83c1f"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


touch = module(ROOT / "repairs/infinity-native-touch-2103451-20261105/compile_only.py",
               "preserved_native_restore")
touch.OUT = OUT


def preflight():
    assert os.environ["GITHUB_REPOSITORY"] == "mahfouzhassine8-ops/project-infinity"
    assert os.environ["GITHUB_REF"] == "refs/heads/" + BRANCH
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == os.environ["GITHUB_SHA"]
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], check=True)
    changes = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], text=True).splitlines()
    approved = {
        SOURCE,
        "repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/library_navigation.py",
        "repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py",
        "repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/default.py",
        "repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/resources/lib/infinity_library_navigation.py",
        "repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml",
        "repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml",
        "repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml",
        ".github/workflows/infinity-2103460-scoped-arm64.yml",
    }
    assert SOURCE in changes
    assert all(n in approved or n.startswith("repairs/infinity-2103460-skin-script-20261106/") for n in changes), changes
    old = subprocess.check_output(["git", "show", BASE + ":" + SOURCE])
    assert sha(old) == OLD_SHA256
    current = RELEASE_SOURCE.read_bytes()
    assert current != old and b"infinity-downloads-only" in current
    assert b"infinity-library-direct" in current
    assert b"g_SkinInfo->ID() == \"skin.infinity.diggz\"" in current
    assert b"CMediaSourceSettings::GetInstance().DeleteSource" not in current
    assert b"SourceManagement" not in current
    print("PASS: exact signed2103460 source, branch scope and guarded successor")
    return old


def restore_exact_native(old):
    touch.restore()  # Original signed 2103451 native map, pinned tar and patch.
    maps = OUT / "NATIVE-SOURCE-MAP.json"
    base_map = json.loads(maps.read_text())
    assert len(base_map) == 9411
    stage = ROOT / "kodi" / NAV
    stage.parent.mkdir(parents=True, exist_ok=True)
    stage.write_bytes(old)
    baseline460 = touch.hashes(ROOT / "kodi")
    assert set(baseline460) == set(base_map)
    assert {n for n in baseline460 if baseline460[n] != base_map[n]} == {NAV}
    assert baseline460[NAV] == OLD_SHA256
    (OUT / "SIGNED460-NATIVE-SOURCE-MAP.json").write_text(
        json.dumps(baseline460, sort_keys=True, indent=2))
    shutil.copyfile(RELEASE_SOURCE, stage)
    successor = touch.hashes(ROOT / "kodi")
    assert {n for n in successor if successor[n] != baseline460[n]} == {NAV}
    assert successor[NAV] == sha(RELEASE_SOURCE.read_bytes())
    maps.write_text(json.dumps(successor, sort_keys=True, indent=2))
    (OUT / "SOURCE-BINDING.json").write_text(json.dumps({
        "signed_base": 2103460, "base_source_commit": BASE,
        "source_commit": os.environ["GITHUB_SHA"], "native_file": NAV,
        "before_sha256": OLD_SHA256, "after_sha256": successor[NAV],
        "changed_native_files": [NAV], "native_inputs_reviewed": 9411,
        "Cobra_changed": False, "APK_signed": False, "physical_Android": "NOT_RUN"
    }, sort_keys=True, indent=2))
    print("PASS: 9411 source files, only VideoNav changed from 2103460")


def compile_native():
    sys.path.insert(0, str(ROOT / "repairs/universal-persistence-2103401"))
    producer = module(ROOT / "repairs/universal-persistence-2103401/build.py",
                      "frozen_full_engine_producer")
    producer.OUT = OUT
    proof = producer.compile_engine()
    assert proof["complete_native_engine_compiled"] is True
    assert proof["reviewed_file_count"] == 9411
    lib = OUT / "libkodi.so"
    assert lib.is_file()
    tool = Path(os.environ["ANDROID_HOME"]) / (
        "ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf")
    hdr = subprocess.check_output([str(tool), "-h", str(lib)], text=True)
    symbols = subprocess.check_output([str(tool), "--dyn-syms", "--wide", str(lib)], text=True)
    assert "ELF64" in hdr and "AArch64" in hdr
    assert "InfinityCommandCenterIdentityV1" in symbols
    assert b"infinity-downloads-only" in lib.read_bytes()
    (OUT / "ELF-ABI.txt").write_text(hdr)
    (OUT / "SCOPED-NATIVE-VERIFIED.json").write_text(json.dumps({
        "status": "PASS_ARM64_FULL_LINK_ONLY",
        "source_commit": os.environ["GITHUB_SHA"],
        "native_sha256": sha(lib.read_bytes()),
        "base": 2103460, "source_reviewed": 9411,
        "only_native_delta": NAV,
        "APK": "NOT_BUILT", "original_signing": "NOT_RUN",
        "Fold": "NOT_RUN"
    }, indent=2))
    print("PASS: complete ARM64 link; no APK or device acceptance claimed")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["preflight", "restore", "compile"])
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.stage == "preflight":
        preflight()
    elif args.stage == "restore":
        restore_exact_native(preflight())
    else:
        preflight()
        compile_native()
