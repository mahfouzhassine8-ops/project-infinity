#!/usr/bin/env python3
"""Propose one exact 2103482 original-key INTERNAL QA authority transition.

This job is key-free/read-only: it cannot register, sign, install, reset, accept,
or waive fail-closed shutdown protection. Every proposed payload comes from
authenticated complete owner bundles already built in GitHub Actions.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "repairs/dual-experience-isolation-2103420"))
import component_bundles as cb
import release_authority as ra
from inventory import canonical, digest, file_sha, validate_names

REPO = "mahfouzhassine8-ops/project-infinity"
CANONICAL = "work/infinity-2103460-nine-corrections-20261106"
AUTHORITY = ROOT / ra.AUTHORITY_PATH
VERSION = 2103482
GENERATION = 66
BASE_APK = "9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2"
NATIVE = "503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437"
NATIVE_COMMIT = "5e26af40222bc521638bd184a2bfb0d5dce337f1"
ASSEMBLY_COMMIT = "a7a5ca31a8353c6f6d42b9cc521146f811f5c8c9"
ARTIFACT_ID = 13833695178
ARTIFACT_RUN = 42970204230
ARTIFACT_NAME = "Infinity2103482-Shutdown-UNSIGNED-Owner-Prepared-42970204230-NOT-INSTALLABLE"
ARTIFACT_ARCHIVE_DIGEST = "3f5221e00605d7c05bc371dafdae8c2fb14a8058caed798a5a1ec7e3df4eb9b9"
OWNER_NAMES = ("INFINITY", "CHOOSER_SHELL")
NATIVE_MEMBER = "lib/arm64-v8a/libkodi.so"
LABEL_MEMBER = "assets/experience-component-updates.properties"

def must(condition, reason):
    if not condition:
        raise RuntimeError(reason)

def api(path):
    proc = subprocess.run(
        ["gh", "api", "repos/" + REPO + "/" + path],
        capture_output=True, text=True, check=True, timeout=45)
    return json.loads(proc.stdout)

def sha_path(path):
    return file_sha(path)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def validate_routing():
    must(os.environ.get("GITHUB_REPOSITORY") == REPO, "WRONG_REPOSITORY")
    must(os.environ.get("GITHUB_REF") == "refs/heads/" + CANONICAL, "WRONG_SIGNING_BRANCH")
    must(git("rev-parse", "HEAD") == os.environ.get("GITHUB_SHA"), "HEAD_RACE")
    must(not git("status", "--porcelain", "--untracked-files=no"),
         "MODIFIED_REVIEWED_PRODUCTION_SOURCE")
    must(Path(".github/workflows/infinity-combined-release.yml").exists(), "SIGNER_MISSING")
    # Sole signer remains the same workflow ID and retains its permanent key policy.
    policy = json.loads((ROOT / "repairs/dual-experience-isolation-2103420/signer-policy.json").read_text())
    must(policy["sole_original_key_workflow_id"] == 397702717, "ORIGINAL_KEY_OWNER_CHANGED")
    run = api("actions/runs/" + str(ARTIFACT_RUN))
    must(run["head_sha"] == ASSEMBLY_COMMIT and run["conclusion"] == "success",
         "NOT_COMPLETED_UNSIGNED_PRODUCER")
    must(run["workflow_id"] != policy["sole_original_key_workflow_id"],
         "UNSIGNED_JOB_MUST_NOT_HANDLE_SIGNING_KEYS")
    artifact = api("actions/artifacts/" + str(ARTIFACT_ID))
    must(artifact["name"] == ARTIFACT_NAME and artifact["workflow_run"]["id"] == ARTIFACT_RUN and
         artifact["digest"] == "sha256:" + ARTIFACT_ARCHIVE_DIGEST and not artifact["expired"],
         "UNVERIFIED_OR_EXPIRED_QA_ARTIFACT")
    native_run = api("actions/runs/42959455792")
    must(native_run["head_sha"] == NATIVE_COMMIT and native_run["conclusion"] == "success",
         "NATIVE_PRODUCER_NOT_GREEN")
    prior_signed = api("actions/runs/42832461653")
    must(prior_signed["conclusion"] == "success" and
         prior_signed["workflow_id"] == policy["sole_original_key_workflow_id"],
         "PREVIOUS_2103481_ISSUANCE_NOT_ORIGINAL_KEY")

def proposal(prepared, out):
    validate_routing()
    receipt_path = prepared / "UNSIGNED-QA-PRESERVATION.json"
    receipt = json.loads(receipt_path.read_text())
    must(receipt["status"] == "PASS_UNSIGNED_OWNER_BUNDLE_AND_APK_MEMBER_PRESERVATION",
         "UNSIGNED_QA_MEMBER_PROOF_FAILED")
    must(receipt["baseline_apk_sha256"] == BASE_APK and
         receipt["native_engine_sha256"] == NATIVE and
         receipt["native_engine_commit"] == NATIVE_COMMIT and
         receipt["packaging_commit"] == ASSEMBLY_COMMIT, "WRONG_QA_PROVENANCE")
    must(receipt["qa_version_provisional_unreserved"] == VERSION and
         receipt["source_files_unchanged"] == 9410, "WRONG_CANDIDATE_SOURCE")
    must(receipt["signed_apk_sha256"] is None and receipt["original_key_used"] is False and
         receipt["release_authority_registered"] is False and
         receipt["Android_shutdown"] == "NOT_RUN", "UNVERIFIED_QA_MISLABELED")
    must(receipt["source_service_patched_in_apk"] is False and
         receipt["native_writer_unknown_effect"].startswith("FAIL_CLOSED"), "UNKNOWN_WRITER_SAFETY_WEAKENED")
    changed = set(receipt["changed_member_sha256"])
    must(changed == {NATIVE_MEMBER, LABEL_MEMBER, "AndroidManifest.xml"},
         "UNRELATED_APK_MEMBER_CHANGED")
    must(receipt["changed_member_sha256"][NATIVE_MEMBER]["after"] == NATIVE, "NATIVE_CHANGED")
    unsigned = next(prepared.glob("Infinity-2103482-Shutdown-UNSIGNED-NOT-INSTALLABLE.apk"), None)
    must(unsigned and sha_path(unsigned) == receipt["unsigned_sha256"], "UNSIGNED_APK_HASH_MISMATCH")
    with ZipFile(unsigned) as z:
        validate_names(z)
        must("classes.dex" in z.namelist(), "DEX_MISSING")
        must(z.read(LABEL_MEMBER) == b"infinity.last_updated_in=2103482\ncobra.last_updated_in=2103445\n",
             "CROSS_OWNER_LABEL_CHANGED")

    owner_folder = prepared / "components"
    catalog = json.loads((owner_folder / "catalog.json").read_text())
    must(catalog["schema"] == 1 and set(catalog["bundles"]) == set(cb.OWNED) and
         catalog["release_approved"] is False and catalog["source"] == ASSEMBLY_COMMIT,
         "BUNDLE_CATALOG_CHANGED")
    meta = {}
    for owner in cb.OWNED:
        row = catalog["bundles"][owner]
        meta[owner] = cb.read_bundle(owner_folder / row["file"], row)
        must(row["digest"] == meta[owner]["digest"], "COMPONENT_DIGEST_MISMATCH:" + owner)
        if owner in OWNER_NAMES:
            must(row["approved_source"] == ASSEMBLY_COMMIT and
                 str(VERSION) in row["version"], "OWNER_SOURCE_VERSION_UNBOUND:" + owner)
    before = json.loads(AUTHORITY.read_text())
    must(before["generation"] == GENERATION - 1 and before["candidate_versionCode"] == 2103481,
         "LIVE_RELEASE_GENERATION_ADVANCED")
    must(before["last_issued_versionCode"] == 2103480 and
         before["guard_schema"] == 2 and before["accepted_pointer_updated"] is False,
         "LIVE_AUTHORITY_NOT_EXPECTED")
    must(before["components"]["COBRA"]["version"] == "2103445.cobra.1" and
         before["experience_version_labels"]["COBRA"] == 2103445, "COBRA_CHANGE_NOT_ALLOWED")
    for owner in ("COBRA", "MINIMAL_ANDROID_CONTRACT"):
        must(catalog["bundles"][owner] == before["bundle_catalog"]["bundles"][owner] and
             cb.component_digest(meta[owner]["payload"], owner) == before["components"][owner]["digest"],
             "UNRELATED_OWNER_COMPONENT_CHANGED:" + owner)
    payload = {k:v for owner in cb.OWNED for k,v in meta[owner]["payload"].items()}
    must(len(payload) == sum(len(meta[o]["payload"]) for o in cb.OWNED),
         "DUPLICATE_PAYLOAD_KEYS")
    must(payload["member:" + NATIVE_MEMBER] == {"owner":"INFINITY","sha256":NATIVE},
         "SHUTDOWN_NATIVE_OWNER_WRONG")
    must(payload["member:" + LABEL_MEMBER] ==
         {"owner":"CHOOSER_SHELL",
          "sha256":digest(b"infinity.last_updated_in=2103482\ncobra.last_updated_in=2103445\n")},
         "LAST_UPDATED_LABEL_NOT_AUTHENTIC")
    result = copy.deepcopy(before)
    result.update(
        generation=GENERATION, candidate_versionCode=VERSION, last_issued_versionCode=2103481,
        previous_authority_sha256=digest(canonical(before)),
        target_owners=list(OWNER_NAMES), update_kind="owner_update",
        payload=payload, bundle_catalog=catalog,
        experience_version_labels={"INFINITY":VERSION, "COBRA":2103445},
        workflow_sha256=sha_path(ROOT / ".github/workflows/infinity-combined-release.yml"),
    )
    for owner in OWNER_NAMES:
        m = meta[owner]
        result["components"][owner] = {k:m[k] for k in
            ("version", "digest", "approved_source", "settings_schema")}
        result["components"][owner]["revision"] = before["components"][owner]["revision"] + 1
        result["bundle_sources"][owner] = {
            "run_id": ARTIFACT_RUN, "build_source": ASSEMBLY_COMMIT,
            "artifact": ARTIFACT_NAME, "path": "components/" + owner + ".zip"
        }
    task_path = Path(__file__).resolve()
    script_path = task_path.relative_to(ROOT).as_posix()
    result["owner_update_evidence"] = dict(
        owner="INFINITY_SHUTDOWN82_INTERNAL_QA_NOT_ACCEPTED",
        producer_run=ARTIFACT_RUN, producer_source=ASSEMBLY_COMMIT,
        artifact={"id":ARTIFACT_ID,"name":ARTIFACT_NAME,
                  "digest":"sha256:"+ARTIFACT_ARCHIVE_DIGEST},
        source_files={script_path:sha_path(task_path),
                      'repairs/infinity-close-startup-2103480-20261110/build_candidate/sign_shutdown82.py':
                      sha_path(ROOT / 'repairs/infinity-close-startup-2103480-20261110/build_candidate/sign_shutdown82.py')},
        preparation_sha256=sha_path(receipt_path),
        immutable_functional_base=2103480,
        baseline_APK_sha256=BASE_APK, native_sha256=NATIVE, native_build_commit=NATIVE_COMMIT,
        Cobra_changes=False, networking_inputs=False, experimental=True,
        engineering_QA_only=True, publication=False, public_release=False,
        owner_delivery_cleared=False, accepted_pointer_updated=False,
        Android="NOT_RUN", physical_Fold="PENDING_OWNER",
        original_key_signing="PENDING_EXACT_SOURCE_REGISTERED_IN_SAME_SIGNER",
        native_writer_unknown_effect="UNPROVEN_FAIL_CLOSED",
        recovery="SIGNED2103480_BASELINE_PRESERVED_NOT_APPLIED",
        verification_toolchain=before["owner_update_evidence"]["verification_toolchain"],
    )
    # The old accepted pointer and protected class contracts cannot be modified.
    ra.transition(before, result, OWNER_NAMES)
    ra.verify_evidence(result, lambda name:(ROOT / name).read_bytes())
    ra.verify(result, {k:v["sha256"] for k,v in payload.items()}, VERSION, GENERATION)
    must(result["components"]["COBRA"] == before["components"]["COBRA"] and
         result["protected_contract"] == before["protected_contract"] and
         result["accepted_registry_sha256"] == before["accepted_registry_sha256"],
         "PROTECTED_BASELINE_CHANGED")
    out.mkdir(parents=True, exist_ok=False)
    (out / "AUTHORITY-PROPOSAL.json").write_text(
         json.dumps(result, sort_keys=True, indent=2) + "\n")
    (out / "ADMISSION-RESULT.json").write_text(json.dumps({
        "status":"PASS_EXACT_AUTHORITY66_TRANSITION_AND_PROTECTED_COMPONENTS",
        "source_commit":git("rev-parse","HEAD"), "candidate_version":VERSION,
        "generation":GENERATION, "source_archive":ARTIFACT_ID,
        "payload_entries":len(payload), "changed_owners":list(OWNER_NAMES),
        "previous_authority_sha256":digest(canonical(before)),
        "proposed_authority_sha256":digest(canonical(result)),
        "original_signer_workflow":397702717,
        "signed_apk_available":False, "Android_shutdown":"NOT_RUN",
        "native_opaque_writer":"UNPROVEN_STILL_FAIL_CLOSED",
    }, sort_keys=True, indent=2)+"\n")
    print("PASS EXACT AUTHORITY 66 QA PROPOSAL; NO KEY OR SIGNING", flush=True)
    # Text chunks for read-only review; uploader also retains complete JSON.
    packed=json.dumps(result,sort_keys=True,separators=(",",":"))
    for i in range(0,len(packed),3000):
        print("AUTHORITY82_JSON_PART_%05d:%s" % (i//3000,packed[i:i+3000]), flush=True)
    print("AUTHORITY82_JSON_END:%d:%s" % (len(packed),digest(canonical(result))), flush=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prepared",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    proposal(a.prepared,a.out)
