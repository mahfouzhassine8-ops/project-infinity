#!/usr/bin/env python3
"""Key-free reviewed workflow inventory evidence-refresh: 2103482 generation 66 -> 67.

Do not change the candidate payload, owner/source revision, user data,
protected contracts, or the accepted APK. No credentials or APK signing here.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import argparse

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
import release_authority as ra
from inventory import canonical, digest

EXPECTED_PREVIOUS_POLICY="668be3057893450fb53c2c3d506723de16de45abe46c0034a0ba81234c1fc06b"
NATIVE="503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437"
SIGN_SCRIPT="repairs/infinity-close-startup-2103480-20261110/build_candidate/sign_shutdown82.py"
POLICY="repairs/dual-experience-isolation-2103420/signer-policy.json"
WORKFLOW=".github/workflows/infinity-combined-release.yml"

def require(value, reason):
    if not value:
        raise RuntimeError(reason)

def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    require(os.environ.get("GITHUB_REPOSITORY")=="mahfouzhassine8-ops/project-infinity","WRONG_REPO")
    require(os.environ.get("GITHUB_REF")=="refs/heads/work/infinity-2103460-nine-corrections-20261106","WRONG_BRANCH")
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    require(head==os.environ.get("GITHUB_SHA"),"HEAD_RACE")
    require(not subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=ROOT),"DIRTY_SOURCE")
    previous=json.loads((ROOT/ra.AUTHORITY_PATH).read_text())
    ra.validate(previous)
    require(previous["generation"]==66 and previous["candidate_versionCode"]==2103482,"NOT_REGISTERED_66")
    require(previous["update_kind"]=="owner_update" and previous["target_owners"]==["INFINITY","CHOOSER_SHELL"],"OWNER_PROOF_LOST")
    require(previous["source_files"][POLICY]==EXPECTED_PREVIOUS_POLICY,"POLICY_PREIMAGE_CHANGED")
    require(previous["accepted_pointer_updated"] is False and previous["owner_update_evidence"]["Android"]=="NOT_RUN","UNVERIFIED_ANDROID_ACCEPTANCE")
    require(previous["owner_update_evidence"]["native_writer_unknown_effect"]=="UNPROVEN_FAIL_CLOSED","UNSAFE_NATIVE_WRITER_APPROVAL")
    require(previous["payload"]["member:lib/arm64-v8a/libkodi.so"]=={"owner":"INFINITY","sha256":NATIVE},"NATIVE_PAYLOAD_CHANGED")
    require(previous["experience_version_labels"]=={"INFINITY":2103482,"COBRA":2103445},"CROSS_OWNER_VERSION_CHANGED")

    policy=json.loads((ROOT/POLICY).read_text())
    require(policy["sole_original_key_workflow_id"]==397702717,"ORIGINAL_KEY_ROUTE_CHANGED")
    expected={414096338,414251549,414031428}
    require(expected <= set(policy["reviewed_workflow_ids"]),"THREE_REVIEWED_SHUTDOWN_WORKFLOWS_NOT_REGISTERED")
    extras={e["id"]:e for e in policy["additional_unsigned_owner_workflows"]}
    require(expected <= set(extras) and all(extras[i]["original_key_access"] is False for i in expected),"REVIEWED_NO_KEY_EVIDENCE_MISSING")
    for i in expected:
        require(extras[i]["workflow_sha256"] and extras[i]["path"].startswith(".github/workflows/"),
                "REVIEWED_SHA_MISSING")
    result=copy.deepcopy(previous)
    result["generation"]=67
    result["previous_authority_sha256"]=digest(canonical(previous))
    result["update_kind"]="evidence_refresh"
    result["target_owners"]=[]
    result["source_files"][POLICY]=sha(ROOT/POLICY)
    result["workflow_sha256"]=sha(ROOT/WORKFLOW)
    result["owner_update_evidence"]["source_files"][SIGN_SCRIPT]=sha(ROOT/SIGN_SCRIPT)
    reviewer=Path(__file__).relative_to(ROOT).as_posix()
    result["owner_update_evidence"]["source_files"][reviewer]=sha(Path(__file__))
    result["owner_update_evidence"]["signing_generation"]=67
    result["owner_update_evidence"]["signer_workflow_policy"]="EXACT_THREE_REVIEWED_READONLY_SHUTDOWN_JOBS"
    require(result["accepted_registry_sha256"]==previous["accepted_registry_sha256"],"ACCEPTED_POINTER_CHANGED")
    require(result["payload"]==previous["payload"],"PAYLOAD_CHANGED")
    require(result["components"]==previous["components"],"COMPONENT_CHANGED")
    require(result["bundle_catalog"]==previous["bundle_catalog"],"OWNER_BUNDLE_CHANGED")
    require(result["protected_contract"]==previous["protected_contract"],"PROTECTED_LIFECYCLE_CHANGED")
    require(result["candidate_versionCode"]==previous["candidate_versionCode"],"RELEASE_VERSION_CHANGED")
    require(result["last_issued_versionCode"]==previous["last_issued_versionCode"],"ISSUANCE_CHANGED")
    ra.transition(previous,result,[])
    ra.verify_evidence(result,lambda name:(ROOT/name).read_bytes())
    ra.verify(result,{k:v["sha256"] for k,v in result["payload"].items()},2103482,67)
    args.out.mkdir(exist_ok=False,parents=True)
    (args.out/"GEN67-REVIEW.json").write_text(json.dumps({
        "status":"PASS_EXACT_SIGNED_QA_EVIDENCE_REFRESH_67_NO_KEYS",
        "source":head,"previous_authority_sha256":digest(canonical(previous)),
        "reviewed_new_workflow_ids":sorted(expected),"original_signer_workflow_id":397702717,
        "proposed_authority_sha256":digest(canonical(result)),
        "payload_changed":False,"Cobra_changed":False,"protected_contract_changed":False,
        "native_writer":"UNPROVEN_FAIL_CLOSED",
        "signed_apk":"NOT_ISSUED","Android_shutdown":"NOT_RUN"
    },indent=2,sort_keys=True)+"\n")
    packed=json.dumps(result,sort_keys=True,separators=(",",":"))
    for i in range(0,len(packed),3000):
        print("AUTHORITY67_JSON_PART_%05d:%s"%(i//3000,packed[i:i+3000]),flush=True)
    print("AUTHORITY67_JSON_END:%d:%s"%(len(packed),digest(canonical(result))),flush=True)
    print("PASS exact evidence refresh G67; signing keys not accessed",flush=True)

if __name__=="__main__":
    main()
