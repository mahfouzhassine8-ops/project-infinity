#!/usr/bin/env python3
"""Compile the complete current Android shell as a non-distributed donor.

The parent APK supplies stable resource IDs and audited asset preimages. This
partial donor contains only the reviewed compatibility overlay and participant
archive; it does not merge a native engine, sign, or produce a device candidate.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import zipfile

import runtime_delta
import participant_asset
import importlib.util
_spec = importlib.util.spec_from_file_location("installed_build", Path(__file__).resolve().parent / "installed/build.py")
installed_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installed_build)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "mobile-regressions-2103304"))
spec = importlib.util.spec_from_file_location("checkpoint_shell_factory", HERE.parent / "mobile-regressions-2103304/package_candidate.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

COMPAT_FILES = tuple("service.infinity.compat/" + name for name in
                     ("service.py", "compat_runtime.py", "checkpoint_runtime.py"))


def stage_compat_assets(base, assets, evidence, runtime_root=None):
    """Stage the exact three-file overlay, proving its APK/source associations.

    The other parent assets are protected inputs for a future association step;
    they are intentionally absent from this partial compilation donor.
    """
    parent = json.loads((HERE / "PARENT.json").read_text())
    parent_digest = hashlib.sha256(base.read_bytes()).hexdigest()
    if parent_digest != parent["parent_apk_sha256"]:
        raise ValueError("Wrong preservation APK for embedded compatibility assets")
    folder = (runtime_root or HERE / "runtime") / "embedded-addons"
    manifest = json.loads((folder / "manifest.json").read_text())
    before, after = manifest["before"], manifest["after"]
    if (set(manifest["changed"]) != set(COMPAT_FILES)
            or manifest["added"] != ["service.infinity.compat/checkpoint_runtime.py"]
            or manifest["deleted"]
            or set(after) != set(before) | set(COMPAT_FILES)
            or any(after[name] != digest for name, digest in before.items()
                   if name not in COMPAT_FILES)):
        raise ValueError("Embedded asset delta exceeds the reviewed compatibility files")
    payload = {}
    for name in COMPAT_FILES:
        data = runtime_delta.checked_path(folder / "overlay", name).read_bytes()
        if hashlib.sha256(data).hexdigest() != after[name]:
            raise ValueError("Reviewed compatibility payload hash mismatch: " + name)
        payload[name] = data
    classification = json.loads((folder / "classification.json").read_text())
    classified = {}
    for script in classification["scripts"]:
        for item in [script] + script["dependencies"]:
            name, digest = item["path"], item["sha256"]
            if name in classified and classified[name] != digest:
                raise ValueError("Conflicting native script classification: " + name)
            if after.get(name) != digest:
                raise ValueError("Native script classification/postimage mismatch: " + name)
            classified[name] = digest
    if not set(COMPAT_FILES).issubset(classified):
        raise ValueError("Native classification lacks a compatibility dependency")
    contract_name = "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp"
    native_folder = folder.parent / "native"
    native_manifest = json.loads((native_folder / "manifest.json").read_text())
    contracts = (native_folder / "overlay" / contract_name).read_bytes()
    contract_digest = hashlib.sha256(contracts).hexdigest()
    if native_manifest["after"].get(contract_name) != contract_digest:
        raise ValueError("Native script contract source hash mismatch")
    native_pins = {}
    for name, digest in re.findall(r'\{"([^"\n]+)", "([0-9a-f]{64})"\}', contracts.decode("utf-8")):
        native_pins.setdefault(name, set()).add(digest)
    if any(after[name] not in native_pins.get(name, set()) for name in COMPAT_FILES):
        raise ValueError("Native compiled contract/compatibility postimage mismatch")
    with zipfile.ZipFile(base) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate preservation APK entries")
        for name, digest in before.items():
            apk_name = "assets/addons/" + name
            if apk_name not in names or hashlib.sha256(archive.read(apk_name)).hexdigest() != digest:
                raise ValueError("Embedded source/APK preimage mismatch: " + name)
        for name in manifest["added"]:
            if "assets/addons/" + name in names:
                raise ValueError("New compatibility file already exists in preservation APK")
        parent_assets = {name: hashlib.sha256(archive.read(name)).hexdigest()
                         for name in names if name.startswith("assets/") and not name.endswith("/")}
    targets = {name: runtime_delta.checked_path(assets / "addons", name) for name in COMPAT_FILES}
    if any(path.exists() for path in targets.values()):
        raise ValueError("Compatibility compile overlay requires fresh target paths")
    # All input validation above precedes the first staged-file mutation.
    for name, path in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload[name])
    staged = {}
    for name, path in targets.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != after[name]:
            raise ValueError("Staged compatibility postimage mismatch: " + name)
        staged["assets/addons/" + name] = {"before": before.get(name), "after": digest}
    protected = {name: digest for name, digest in parent_assets.items() if name not in staged}
    receipt = {
        "schema": 1, "parent_apk_sha256": parent_digest,
        "purpose": "reviewed compatibility assets for a partial Android compilation donor",
        "partial_compile_donor": True, "full_apk_associated": False,
        "device_ready_apk": False, "native_engine_merged": False,
        "staged_assets": staged,
        "native_classification_postimages_verified": classified,
        "native_contract_source_sha256": contract_digest,
        "protected_parent_assets": protected,
        "protected_parent_asset_count": len(protected),
        "protection_semantics": "Must remain byte-identical in a later full APK association; absent from this partial donor",
    }
    evidence.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("PASS: 3 compatibility asset postimages staged; " + str(len(before)) + " embedded preimages and "
          + str(len(protected)) + " remaining parent assets enumerated; partial compile donor only")
    return staged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("source", "base", "build", "out"):
        parser.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    parent = json.loads((HERE / "PARENT.json").read_text())
    if hashlib.sha256(args.base.read_bytes()).hexdigest() != parent["parent_apk_sha256"]:
        raise ValueError("Wrong 2103335 preservation APK")
    args.out.mkdir(parents=True, exist_ok=True)
    runtime_delta.apply("android", args.source)
    factory.BASE_APK_SHA256 = parent["parent_apk_sha256"]
    factory.VERSION_CODE = 2103335  # Component donor only; no new device candidate identity.
    factory.RELEASE = "1.0.9-Checkpoint-Work-Compile-Only"
    factory.prepare(args.source.resolve(), args.base.resolve(), args.build.resolve(), args.out.resolve())
    asset = participant_asset.build()
    digest = hashlib.sha256(asset).hexdigest()
    installer = args.source / "tools/android/packaging/xbmc/src/InfinityCheckpointAddonInstaller.java.in"
    if 'ASSET_SHA256 = "' + digest + '"' not in installer.read_text():
        raise ValueError("Participant installer/asset mismatch")
    target = args.build / "xbmc/assets/infinity/checkpoint-controller.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(asset)
    installed_assets = installed_build.stage(args.build / "xbmc/assets")
    for filename, installer_name in [('checkpoint-controller-20.zip', 'InfinityCheckpointController20Installer'),
                                     ('checkpoint-compat-82.zip', 'InfinityCheckpointCompat82Installer')]:
        code = (args.source / ('tools/android/packaging/xbmc/src/'+installer_name+'.java.in')).read_text()
        if 'ASSET_SHA256 = "'+installed_assets['assets/infinity/'+filename]+'"' not in code:
            raise ValueError('Installed participant installer/asset mismatch: '+filename)
    compat_assets = stage_compat_assets(args.base, args.build / "xbmc/assets",
                                       args.out / "COMPAT-ASSET-ASSOCIATION.json")
    # Keep the inherited native-trace exporter regression running against the
    # actual new exporter, in addition to coordinator/persistence host tests.
    tests = args.build / "xbmc/src/test/java/com/projectinfinity/kodi"
    tests.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE.parent / "health-native-bridge-2103335/NativeTraceBridge335Test.java",
                    tests / "NativeTraceBridge335Test.java")
    shutil.copyfile(HERE / "runtime-tests/CheckpointCrashExportTest.java",
                    tests / "CheckpointCrashExportTest.java")
    shutil.copyfile(HERE / "runtime-tests/CheckpointLifecycleTest.java",
                    tests / "CheckpointLifecycleTest.java")
    with (args.build / "xbmc/build.gradle").open("a") as output:
        output.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "2g"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
    (args.out / "COMPILATION-SCOPE.json").write_text(json.dumps({
        "schema": 1, "source_commit": os.environ.get("GITHUB_SHA"),
        "parent_apk_sha256": parent["parent_apk_sha256"],
        "participant_asset_sha256": digest,
        "installed_participant_assets": installed_assets,
        "compatibility_asset_postimages": compat_assets,
        "partial_asset_donor": True, "full_apk_asset_association_verified": False,
        "purpose": "complete Android source compilation and exporter regression",
        "native_engine_merged": False, "device_ready_apk": False,
        "permanent_signing_changed": False, "device_accepted": False, "locked": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
