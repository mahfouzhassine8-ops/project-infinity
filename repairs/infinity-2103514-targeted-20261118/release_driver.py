"""Drive the 2103514 QA pair under the existing original-key workflow."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from zipfile import ZipFile

from prepare_authority import APK_KINDS, AUTHORITY, BASE_COMMIT, CANONICAL, REPOSITORY, prepare, ref_blob
from prepare_modules import CC, MANIFEST, PREFIX, stage
from stage_qa import HERE, ROOT, build, file_sha, load, require, validate_engine

sys.path.insert(0, str(ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/release"))
import common_release as release

BASELINE = load(HERE / "SCOPE.json")["baseline"]
FIRST_PARTY = ROOT / "repairs/infinity-final-closure-2103407"
PUBLIC_KEY = FIRST_PARTY / "ORIGINAL-INFINITY-PUBLIC-KEY.pem"
REQUEST_PATH = HERE / "RELEASE-REQUEST.json"
CONTEXT = ROOT / "infinity514-release-inputs.json"
PRODUCTS = ROOT / "infinity514-unsigned-preparation"
SIGNED = ROOT / "infinity514-original-signed"
TASK_PATH = HERE.relative_to(ROOT)


def request():
    require(os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
            os.environ.get("GITHUB_REPOSITORY") == REPOSITORY and
            os.environ.get("GITHUB_REF") == "refs/heads/" + CANONICAL,
            "Canonical original-key release job required")
    head = os.environ["GITHUB_SHA"]
    require(subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip() == head,
            "Canonical source checkout changed")
    require(subprocess.check_output(["git", "-C", ROOT, "ls-remote", "origin",
            "refs/heads/" + CANONICAL], text=True).split()[0] == head, "Canonical authorization changed")
    row = load(REQUEST_PATH)
    require(row["operation"] == "prepare_and_sign_514_scoped_qa_pair" and
            row["baseline"] == BASELINE and row["owner_accepted"] is False,
            "Scope or protected baseline differs")
    required = {"SCOPE.json", "CONTINUE-SCOPE.json", "CONTINUE-HOST.json", "MODULE-PRESERVATION.json",
                "continue-navigation.patch", "STARTUP-ABI-HOST.json", "STARTUP-ABI-SCOPE.json",
                "prepare_modules.py", "stage_qa.py", "prepare_authority.py", "release_driver.py"}
    require(set(row["source_inputs"]) == required, "Incomplete scope approval")
    for member, expected in row["source_inputs"].items():
        path = HERE / member
        require(file_sha(path) == expected and path.read_bytes() ==
                ref_blob(row["reviewed_source_commit"], TASK_PATH / member), "Reviewed source differs: " + member)
    require((FIRST_PARTY / "SignInfinityModules.java").read_bytes() ==
            ref_blob(BASE_COMMIT, (FIRST_PARTY / "SignInfinityModules.java").relative_to(ROOT)),
            "Original Java module signer changed")
    return row


def baseline(row):
    path = release.unique(release.obtain(row["baseline_artifact"], "514-release-base"),
                          "Infinity-2103514-Combined-Original-Signer.apk")
    require(file_sha(path) == BASELINE["apk_sha256"], "Wrong signed 2103514 package")
    release.signature(path)
    return path


def preflight():
    row = request()
    require(file_sha(ROOT / AUTHORITY) == row["preparation_registry_sha256"], "Release registry changed")
    original = baseline(row)
    engine = release.obtain(row["native_artifact"], "514-verified-engine")
    validate_engine(engine, BASELINE, row["native_artifact"]["source"])
    input_owners = release.obtain(row["owner_artifact"], "514-original-owners") / "candidate/components"
    preserve_catalog = json.loads(ref_blob(BASE_COMMIT, AUTHORITY))["bundle_catalog"]
    require(load(input_owners / "catalog.json") == preserve_catalog, "Wrong 2103514 owner roots")
    inventory, *_ = release.tools()
    baseline_modules = ROOT / "infinity514-baseline-modules"
    baseline_modules.mkdir()
    addons = {CC, "script.infinity.rails", "script.infinity.uirepair", "script.infinity.watchedbridge"}
    with ZipFile(original) as archive:
        for name in inventory.validate_names(archive):
            if name.startswith(PREFIX) and not name.endswith("/") and name.removeprefix(PREFIX).split("/")[0] in addons:
                output = baseline_modules / name
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(archive.read(name))
    modules = ROOT / "infinity514-module-stage"
    stage(baseline_modules, modules, PUBLIC_KEY)
    require(load(modules / "MODULE-PRESERVATION.json") == load(HERE / "MODULE-PRESERVATION.json"),
            "Prepared module hashes differ from source verification")
    inventory.save(CONTEXT, dict(baseline=str(original), native=str(engine),
        native_source=row["native_artifact"]["source"], owners=str(input_owners),
        modules=str(modules), manifest_binding=file_sha(modules / "MODULE-PRESERVATION.json"),
        request_sha256=file_sha(REQUEST_PATH), workflow_commit=os.environ["GITHUB_SHA"]))


def sign_modules():
    request()
    inputs = load(CONTEXT)
    modules = Path(inputs["modules"])
    require(inputs["workflow_commit"] == os.environ["GITHUB_SHA"] and
            inputs["request_sha256"] == file_sha(REQUEST_PATH) and
            inputs["manifest_binding"] == file_sha(modules / "MODULE-PRESERVATION.json") and
            load(modules / "MODULE-PRESERVATION.json") == load(HERE / "MODULE-PRESERVATION.json"),
            "Verified module signing context changed")
    expected = load(HERE / "MODULE-PRESERVATION.json")
    manifests = {kind: modules / kind / PREFIX / MANIFEST for kind in APK_KINDS}
    for kind, manifest in manifests.items():
        require(file_sha(manifest) == expected[kind]["manifest_sha256"] and
                not manifest.with_suffix(".v1.sig").exists(), "Wrong signing payload or duplicate signature")
    with tempfile.TemporaryDirectory(prefix="infinity514-original-module-sign-") as temporary:
        local = Path(temporary)
        classes = local / "classes"
        classes.mkdir()
        subprocess.run(["javac", "--release", "8", "-d", classes, FIRST_PARTY / "SignInfinityModules.java"], check=True)
        key = local / "original.jks"
        key.touch(mode=0o600)
        key.write_bytes(base64.b64decode(os.environ["INFINITY_KEYSTORE_B64"], validate=True))
        env = {name: os.environ[name] for name in ("PATH", "JAVA_HOME", "INFINITY_KEY_ALIAS",
                                                   "INFINITY_STORE_PASSWORD", "INFINITY_KEY_PASSWORD")}
        for manifest in manifests.values():
            subprocess.run(["java", "-cp", classes, "SignInfinityModules", key, manifest],
                           env=env, check=True)
            subprocess.run(["openssl", "dgst", "-sha256", "-verify", PUBLIC_KEY,
                            "-signature", manifest.with_suffix(".v1.sig"), manifest], check=True)
    signatures = ROOT / "infinity514-module-signatures"
    for kind, manifest in manifests.items():
        target = signatures / kind / (MANIFEST + ".sig")
        target.parent.mkdir(parents=True)
        shutil.copyfile(manifest.with_suffix(".v1.sig"), target)


def owner_prepare():
    row = request()
    inputs = load(CONTEXT)
    require(file_sha(ROOT / AUTHORITY) == row["preparation_registry_sha256"], "Release registry changed")
    staged = ROOT / "infinity514-unsigned-apks"
    build(SimpleNamespace(baseline=Path(inputs["baseline"]), engine=Path(inputs["native"]),
                         engine_source=inputs["native_source"], registry=ROOT / AUTHORITY,
                         module_signatures=ROOT / "infinity514-module-signatures", out=staged))
    prepare(SimpleNamespace(staged=staged, original_owners=Path(inputs["owners"]), out=PRODUCTS))


def selected():
    row = request()
    kind = row["selected_kind"]
    require(kind in APK_KINDS, "Explicit registered candidate or recovery required")
    root = release.obtain(row["prepared_artifact"], "514-registered-owner-preparation")
    require(load(root / "PREPARATION.json")["status"] == "PASS_UNSIGNED_514_OWNER_PREPARATION",
            "Missing completed owner preparation receipt")
    authority = load(ROOT / AUTHORITY)
    require((root / kind / "AUTHORITY-PROPOSAL.json").read_bytes() == (ROOT / AUTHORITY).read_bytes(),
            "Actual registered authority does not match the verified proposal")
    apk = release.unique(root / kind, f"Infinity-{authority['candidate_versionCode']}-UNSIGNED.apk")
    require(file_sha(apk) == authority["owner_update_evidence"]["unsigned_sha256"],
            "Registered unsigned bytes differ")
    release.jars()
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
        stream.write(f"apk={apk}\ngeneration={authority['generation']}\n")


def post_sign():
    row = request()
    authority = load(ROOT / AUTHORITY)
    kind = row["selected_kind"]
    proof = load(SIGNED / "BUILD-RECEIPT.json")
    version = authority["candidate_versionCode"]
    product = release.unique(SIGNED, f"Infinity-{version}-Combined-Original-Signer.apk")
    release.signature(product)
    require(proof["signed_apk_sha256"] == file_sha(product), "Signed APK changed after protected signing")
    original = baseline(row)
    inventory, *_ = release.tools()
    old, new = (inventory.apk_members(path) for path in (original, product))
    for data in (old, new):
        for name in inventory.SIGNATURE:
            data.pop(name, None)
    require(set(old) == set(new), "Signed APK added or removed a baseline member")
    staged = release.obtain(row["prepared_artifact"], "514-registered-owner-preparation")
    preservation = load(staged / kind / "PRESERVATION.json")
    changes = {name: {"before": data["sha256"], "after": new[name]["sha256"]}
               for name, data in old.items() if data["sha256"] != new[name]["sha256"]}
    require(changes == preservation["changes"] and preservation["versionCode"] == version,
            "Original-key signed member delta differs from verified staging")
    inventory.save(SIGNED / "PRESERVATION.json", dict(
        versionCode=version, signed_apk_sha256=file_sha(product), changes=changes,
        unchanged=len(old)-len(changes), bridge="ORIGINAL_APK_AND_MODULE_SIGNATURES",
        Fold="PENDING_OWNER", accepted_pointer_updated=False))
    shutil.copyfile(ROOT / AUTHORITY, SIGNED / "release-authority.json")


if __name__ == "__main__":
    methods = {"preflight": preflight, "sign-modules": sign_modules, "prepare": owner_prepare,
               "select": selected, "post-sign": post_sign}
    methods[sys.argv[1]]()
