#!/usr/bin/env python3
"""Compile the complete current Android shell as a non-distributed donor.

The parent APK only supplies stable resource IDs. This script does not merge a
native engine, permanently sign, distribute an APK, or claim device acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import runtime_delta
import participant_asset

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "mobile-regressions-2103304"))
spec = importlib.util.spec_from_file_location("checkpoint_shell_factory", HERE.parent / "mobile-regressions-2103304/package_candidate.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


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
    # Keep the inherited native-trace exporter regression running against the
    # actual new exporter, in addition to coordinator/persistence host tests.
    tests = args.build / "xbmc/src/test/java/com/projectinfinity/kodi"
    tests.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE.parent / "health-native-bridge-2103335/NativeTraceBridge335Test.java",
                    tests / "NativeTraceBridge335Test.java")
    with (args.build / "xbmc/build.gradle").open("a") as output:
        output.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "2g"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
    (args.out / "COMPILATION-SCOPE.json").write_text(json.dumps({
        "schema": 1, "source_commit": os.environ.get("GITHUB_SHA"),
        "parent_apk_sha256": parent["parent_apk_sha256"],
        "participant_asset_sha256": digest,
        "purpose": "complete Android source compilation and exporter regression",
        "native_engine_merged": False, "device_ready_apk": False,
        "permanent_signing_changed": False, "device_accepted": False, "locked": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
