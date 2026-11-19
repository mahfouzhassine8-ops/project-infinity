"""Resolve the exact original-signed pair for the selected Android verification."""
import os
from pathlib import Path
import shutil
import sys

from stage_qa import HERE, ROOT, file_sha, load, require

sys.path.insert(0, str(ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/release"))
import common_release as release


def main():
    require(os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ.get("GITHUB_REPOSITORY") == release.REPO and
            os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch",
            "Selected feature execution only in official CI")
    request_path = HERE / "ANDROID-REQUEST.json"
    require(file_sha(request_path) == os.environ["SELECTED_AUTHORIZATION"],
            "Manual dispatch does not identify the exact selected test")
    request = load(request_path)
    require(request["operation"] == "signed_514_pair_install_over_and_startup" and
            request["shutdown"] is False and request["data_reset"] is False and
            request["Fold_acceptance"] is False and
            set(request["inputs"]) == {"baseline", "candidate", "recovery"} and
            file_sha(HERE / "verify_android.py") == request["driver_sha256"],
            "Unrecognized corrective feature request")
    expected = load(HERE / "BASE-RELEASE-INPUTS.json")["baseline"]
    require(all(request["inputs"]["baseline"][key] == value for key, value in expected.items()),
            "Exact protected original 2103514 baseline artifact required")
    out = ROOT / "infinity514-verified-android-input"
    out.mkdir()
    for kind, row in request["inputs"].items():
        require(row["workflow_id"] == 397702717, "Only the original signing route is accepted")
        product = release.obtain(row, "514-install-" + kind)
        apk = release.unique(product, f"Infinity-{row['versionCode']}-Combined-Original-Signer.apk")
        require(file_sha(apk) == row["APK_sha256"], "Signer evidence package hash differs")
        release.signature(apk)
        (out / f"{kind}.apk").symlink_to(apk)
        if kind != "baseline":
            proof = load(release.unique(product, "PRESERVATION.json"))
            require(proof["signed_apk_sha256"] == row["APK_sha256"] and
                    proof["versionCode"] == row["versionCode"], "Signed preservation receipt differs")
            shutil.copyfile(release.unique(product, "PRESERVATION.json"), out / f"{kind}.json")


if __name__ == "__main__":
    main()
