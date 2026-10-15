#!/usr/bin/env python3
"""Test reviewed compat staging against the actual preservation APK, without Gradle."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import android_ci


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="infinity-compat-assets-") as temporary:
        root = Path(temporary)
        source = android_ci.HERE / "runtime/embedded-addons"
        runtime = root / "runtime"
        shutil.copytree(source, runtime / "embedded-addons")
        native_folder = runtime / "native"
        native_folder.mkdir()
        shutil.copyfile(android_ci.HERE / "runtime/native/manifest.json", native_folder / "manifest.json")
        contract_name = "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp"
        contract = native_folder / "overlay" / contract_name
        contract.parent.mkdir(parents=True)
        shutil.copyfile(android_ci.HERE / "runtime/native/overlay" / contract_name, contract)
        manifest_path = runtime / "embedded-addons/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        classification_path = runtime / "embedded-addons/classification.json"
        classification = classification_path.read_text()
        assets = root / "valid/assets"
        assets.mkdir(parents=True)
        # The frozen controller asset and unrelated donor entries stay untouched.
        marker = assets / "infinity/checkpoint-controller.zip"
        marker.parent.mkdir(parents=True)
        marker.write_bytes(b"frozen-participant-untouched")
        result = android_ci.stage_compat_assets(args.base, assets, root / "valid.json", runtime)
        assert len(result) == 3
        assert marker.read_bytes() == b"frozen-participant-untouched"
        assert {str(path.relative_to(assets)) for path in assets.rglob("*") if path.is_file()} == {
            "infinity/checkpoint-controller.zip",
            *["addons/" + name for name in android_ci.COMPAT_FILES],
        }
        receipt = json.loads((root / "valid.json").read_text())
        assert receipt["partial_compile_donor"] and not receipt["full_apk_associated"]
        assert len(receipt["protected_parent_assets"]) == receipt["protected_parent_asset_count"]
        assert receipt["protected_parent_asset_count"] > 4000
        assert "assets/addons/service.infinity.compat/addon.xml" in receipt["protected_parent_assets"]
        for name in android_ci.COMPAT_FILES:
            assert hashlib.sha256((assets / "addons" / name).read_bytes()).hexdigest() == manifest["after"][name]

        def rejected(label, expected, base=None):
            target = root / label
            try:
                android_ci.stage_compat_assets(base or args.base, target, root / (label + ".json"), runtime)
            except ValueError as error:
                assert expected in str(error), (label, str(error))
            else:
                raise AssertionError(label + " accepted invalid input")
            assert not target.exists(), label + " mutated staged output before validating inputs"

        payload = runtime / "embedded-addons/overlay" / android_ci.COMPAT_FILES[0]
        original = payload.read_bytes()
        payload.write_bytes(original + b"\n# unreviewed\n")
        rejected("bad-payload", "payload hash mismatch")
        payload.write_bytes(original)

        wrong = copy.deepcopy(manifest)
        wrong["before"][android_ci.COMPAT_FILES[0]] = "0" * 64
        manifest_path.write_text(json.dumps(wrong))
        rejected("bad-apk-preimage", "source/APK preimage mismatch")
        manifest_path.write_text(json.dumps(manifest))

        wrong = json.loads(classification)
        wrong["scripts"][0]["sha256"] = "0" * 64
        classification_path.write_text(json.dumps(wrong))
        rejected("bad-native-association", "classification/postimage mismatch")
        classification_path.write_text(classification)

        native_contract = contract.read_bytes()
        contract.write_bytes(native_contract + b"\n// unreviewed\n")
        rejected("bad-native-contract-source", "contract source hash mismatch")
        contract.write_bytes(native_contract)

        native_manifest_path = native_folder / "manifest.json"
        native_manifest = native_manifest_path.read_text()
        wrong_native_contract = native_contract.replace(manifest["after"][android_ci.COMPAT_FILES[0]].encode(), b"0" * 64)
        contract.write_bytes(wrong_native_contract)
        wrong_native_manifest = json.loads(native_manifest)
        wrong_native_manifest["after"][contract_name] = hashlib.sha256(wrong_native_contract).hexdigest()
        native_manifest_path.write_text(json.dumps(wrong_native_manifest))
        rejected("bad-native-contract-pin", "compiled contract/compatibility postimage mismatch")
        contract.write_bytes(native_contract)
        native_manifest_path.write_text(native_manifest)

        wrong = copy.deepcopy(manifest)
        wrong["changed"].append("service.infinity.compat/addon.xml")
        manifest_path.write_text(json.dumps(wrong))
        rejected("scope-expanded", "exceeds the reviewed")
        manifest_path.write_text(json.dumps(manifest))

        bad_apk = root / "wrong.apk"
        bad_apk.write_bytes(b"not the preservation APK")
        rejected("wrong-parent", "Wrong preservation APK", bad_apk)

        try:
            android_ci.stage_compat_assets(args.base, assets, root / "repeat.json", runtime)
        except ValueError as error:
            assert "fresh target paths" in str(error)
        else:
            raise AssertionError("preexisting target accepted")
        assert marker.read_bytes() == b"frozen-participant-untouched"
    print("PASS compatibility asset staging: actual APK association, exact payload, native hashes, expanded scope, wrong parent and existing-target rejection")


if __name__ == "__main__":
    main()
