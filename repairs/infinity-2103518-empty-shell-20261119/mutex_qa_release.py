"""Prepare one 2103518-derived diagnostic through the existing owner gate."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "repairs/infinity-2103514-targeted-20261118"))
sys.path.insert(0, str(ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/release"))

import common_release as release
from prepare_authority import owner_bundle, ref_blob
from stage_qa import copy_member, file_sha, load, require

AUTHORITY = Path(release.AUTHORITY)
WORKFLOW = Path(release.WORKFLOW)
BASE_SOURCE = "41dcaca27396fca320097b6a53d1ba5f3d7dfee6"
BASE_APK = "9bfb4c87bc2536a2b806fa995866fd719345fcd575c180aeba93eb02c4303f54"
BASE_ENGINE = "c0c5e871380a5c4d7bf2842ffcfa84614068a8a68c4b15d31e2b87ab0ad5dc20"
NATIVE = "lib/arm64-v8a/libkodi.so"
MANIFEST = "AndroidManifest.xml"
LABELS = "assets/experience-component-updates.properties"
ALLOWLIST = {NATIVE, MANIFEST, LABELS}
OWNERS = ("INFINITY", "CHOOSER_SHELL")
PREPARED = ROOT / "mutex-qa-prepared"
SIGNED = ROOT / "mutex-qa-original-signed"
REQUEST = HERE / "MUTEX-RELEASE-REQUEST.json"


def context():
    release.context(canonical=True)
    require(os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch", "Manual release request required")
    lock = release.git("ls-remote", "origin", "refs/heads/lock/infinity-2103514-user-approved-baseline-20261117")
    require(lock.split()[0].decode() == "3f79964746c37310e4baeb4f7ea6bae87f0a4380",
            "Protected 2103514 baseline moved")
    row = load(REQUEST)
    require(row["operation"] == "original_sign_one_2103518_based_persistence_mutex_diagnostic"
            and row["owner_acceptance"] is False, "Wrong owner-authorized diagnostic")
    for path, digest in row["inputs"].items():
        require(file_sha(ROOT / path) == digest, "Verified diagnostic input differs: " + path)
    return row


def apk_baseline(row):
    path = release.unique(release.obtain(row["signed518_artifact"], "mutex-signed518"),
                          "Infinity-2103518-Combined-Original-Signer.apk")
    require(file_sha(path) == BASE_APK, "Wrong signed 2103518 bytes")
    release.signature(path)
    return path


def members(apk, inventory):
    return {name: row["sha256"] for name, row in inventory.apk_members(apk).items()
            if name not in inventory.SIGNATURE}


def member_delta(old, new):
    require(set(old) == set(new), "APK entry inventory differs")
    return {name: dict(before=digest, after=new[name]) for name, digest in old.items() if new[name] != digest}


def prepare():
    row = context()
    require(file_sha(ROOT / AUTHORITY) == row["registry_before_sha256"] and "prepared_artifact" not in row,
            "Registry changed since diagnostic authorization")
    inventory, bundles, authority, guard, _ = release.tools()
    previous = load(ROOT / AUTHORITY)
    baseline = json.loads(ref_blob(BASE_SOURCE, AUTHORITY))
    version = max(previous["candidate_versionCode"], previous["last_issued_versionCode"]) + 1
    source, run_id = os.environ["GITHUB_SHA"], int(os.environ["GITHUB_RUN_ID"])
    original = apk_baseline(row)
    natives = release.obtain(row["native_artifact"], "scoped-mutex-engine")
    arm = load(natives / "MUTEX-ARM64.json")
    abi = load(natives / "ABI-514.json")
    frozen = load(natives / "MUTEX-SOURCE-PRESERVATION.json")
    engine = natives / "libkodi.so"
    require(arm == dict(status="PASS_FULL_ARM64_LINK_AND_EXACT_2103518_ABI",
                        engine_sha256=file_sha(engine), baseline_engine_sha256=BASE_ENGINE,
                        source=row["native_artifact"]["source"], native_source_count=9419,
                        full_arm64_link=True, diagnostic_only=True) and
            frozen["source"] == arm["source"] and frozen["unchanged_sources"] == 9414 and
            frozen["native_delta"] == load(HERE / "MUTEX-NATIVE-REQUEST.json")["source_allowlist"] and
            not abi["added"] and not abi["removed"] and abi["needed_before"] == abi["needed_after"] and
            abi["versions_before"] == abi["versions_after"] and
            abi["startup_storage_before"] == abi["startup_storage_after"],
            "Missing exact ARM64 link, ABI or scoped native receipt")
    owners = release.obtain(row["owner518_artifact"], "signed518-owners") / "candidate/components"
    catalog = load(owners / "catalog.json")
    require(catalog == baseline["bundle_catalog"], "Original signed 2103518 owner catalog differs")

    PREPARED.mkdir()
    apk = PREPARED / f"Infinity-{version}-UNSIGNED.apk"
    with ZipFile(original) as before, ZipFile(apk, "w", allowZip64=True) as out:
        require(set(inventory.validate_names(before)) == set(before.namelist()), "Wrong baseline entry inventory")
        original_labels = before.read(LABELS)
        require(original_labels == b"infinity.last_updated_in=2103518\ncobra.last_updated_in=2103445\n",
                "Wrong signed owner version labels")
        replacements = {
            MANIFEST: bundles.set_version(before.read(MANIFEST), version),
            NATIVE: engine,
            LABELS: original_labels.replace(b"2103518", str(version).encode()),
        }
        for info in before.infolist():
            if info.filename not in inventory.SIGNATURE:
                copy_member(before, out, info, replacements.get(info.filename))
    changes = member_delta(members(original, inventory), members(apk, inventory))
    require(set(changes) == ALLOWLIST and changes[NATIVE] ==
            dict(before=BASE_ENGINE, after=arm["engine_sha256"]), "Unexpected APK member delta")

    work = ROOT / "mutex-qa-component-inspection"
    actual, observed_version = guard.inspect_candidate(apk, release.jars(), work)
    require(observed_version == version and set(actual) == set(baseline["payload"]),
            "Package identity or entry set changed")
    payload = {key: dict(baseline["payload"][key], sha256=digest) for key, digest in actual.items()}
    require({key for key in payload if payload[key] != baseline["payload"][key]} ==
            {"member:" + NATIVE, "member:" + LABELS}, "Protected APK payload changed")

    catalog.update(source=source, release_approved=False)
    root = PREPARED / "components"
    root.mkdir()
    proposal = deepcopy(previous)
    for owner, desc in catalog["bundles"].items():
        target = root / desc["file"]
        if owner in OWNERS:
            meta = owner_bundle(owners / desc["file"], target, apk, owner, desc, payload, version,
                                source, bundles, inventory)
            desc.update(sha256=file_sha(target), **{key: meta[key] for key in ("version", "digest", "approved_source")})
            proposal["components"][owner] = {key: meta[key] for key in
                                            ("version", "digest", "approved_source", "settings_schema")}
            proposal["components"][owner]["revision"] = previous["components"][owner]["revision"] + 1
            proposal["bundle_sources"][owner] = dict(
                run_id=run_id, build_source=source, artifact=f"Infinity518-Mutex-Prepared-{run_id}",
                path=f"components/{owner}.zip")
        else:
            shutil.copyfile(owners / desc["file"], target)
        bundles.read_bundle(target, desc)
    (root / "catalog.json").write_bytes(inventory.canonical(catalog))
    proposal.update(generation=previous["generation"] + 1, candidate_versionCode=version,
                    last_issued_versionCode=previous["candidate_versionCode"],
                    previous_authority_sha256=inventory.digest(inventory.canonical(previous)),
                    target_owners=list(OWNERS), update_kind="owner_update", payload=payload, bundle_catalog=catalog,
                    experience_version_labels={"INFINITY": version, "COBRA": 2103445},
                    workflow_sha256=file_sha(ROOT / WORKFLOW))
    proposal["owner_update_evidence"] = dict(
        owner="INFINITY_518_PERSISTENCE_MUTEX_DIAGNOSTIC_ONLY", producer_run=run_id,
        producer_source=source, baseline_APK_sha256=BASE_APK, unsigned_sha256=file_sha(apk),
        Fold="PENDING_OWNER", accepted_pointer_updated=False, public_release=False,
        verification_toolchain=dict(previous["owner_update_evidence"]["verification_toolchain"],
                                    unchanged_original_DEX=True, content_baseline_APK_sha256=BASE_APK))
    authority.transition(previous, proposal, OWNERS)
    authority.verify_evidence(proposal, lambda path: (ROOT / path).read_bytes())
    authority.verify(proposal, actual, version, proposal["generation"])
    guard.validate_runtime_ownership(proposal, work)
    (PREPARED / "AUTHORITY-PROPOSAL.json").write_bytes(inventory.canonical(proposal))
    inventory.save(PREPARED / "PRESERVATION.json", dict(
        result="PASS_EXACT_SIGNED_2103518_MEMBER_DELTA", source=source, versionCode=version,
        unsigned_sha256=file_sha(apk), baseline_apk_sha256=BASE_APK, changes=changes,
        unchanged=len(members(original, inventory)) - len(changes),
        diagnostic_only=True, APK_signing=False))


def selected():
    row = context()
    root = release.obtain(row["prepared_artifact"], "registered-mutex-qa")
    proposal = load(ROOT / AUTHORITY)
    require((root / "AUTHORITY-PROPOSAL.json").read_bytes() == (ROOT / AUTHORITY).read_bytes(),
            "Registry does not bind the exact prepared proposal")
    report = load(root / "PRESERVATION.json")
    require(report["result"] == "PASS_EXACT_SIGNED_2103518_MEMBER_DELTA" and
            report["diagnostic_only"] is True and set(report["changes"]) == ALLOWLIST and
            report["baseline_apk_sha256"] == BASE_APK, "Wrong package verification scope")
    apk = release.unique(root, f"Infinity-{proposal['candidate_versionCode']}-UNSIGNED.apk")
    require(file_sha(apk) == report["unsigned_sha256"] == proposal["owner_update_evidence"]["unsigned_sha256"],
            "Staged input changed")
    release.jars()
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
        stream.write(f"apk={apk}\ngeneration={proposal['generation']}\n")


def verify_signed():
    row = context()
    authority = load(ROOT / AUTHORITY)
    version = authority["candidate_versionCode"]
    product = release.unique(SIGNED, f"Infinity-{version}-Combined-Original-Signer.apk")
    cert = release.signature(product)
    receipt = load(SIGNED / "BUILD-RECEIPT.json")
    require(file_sha(product) == receipt["signed_apk_sha256"], "Signed APK bytes changed")
    original = apk_baseline(row)
    inventory, *_ = release.tools()
    delta = member_delta(members(original, inventory), members(product, inventory))
    root = release.obtain(row["prepared_artifact"], "registered-mutex-qa")
    report = load(root / "PRESERVATION.json")
    require(set(delta) == ALLOWLIST and delta == report["changes"] and report["versionCode"] == version,
            "Signed APK differs from the scoped candidate")
    report.update(signed_apk_sha256=file_sha(product), certificate_sha256=release.CERT,
                  APK_signing=True, unchanged=len(members(original, inventory)) - len(delta),
                  Fold="PENDING_OWNER", accepted_pointer_updated=False)
    inventory.save(SIGNED / "PRESERVATION.json", report)
    (SIGNED / "SIGNATURE.txt").write_text(cert)
    shutil.copyfile(ROOT / AUTHORITY, SIGNED / "release-authority.json")


if __name__ == "__main__":
    {"prepare": prepare, "select": selected, "verify-signed": verify_signed}[sys.argv[1]]()
