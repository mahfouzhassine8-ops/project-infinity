"""Prepare the scoped owner bundles and unsigned authority proposals for QA."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from stage_qa import ROOT, copy_member, file_sha, load, require

REPOSITORY = "mahfouzhassine8-ops/project-infinity"
CANONICAL = "work/infinity-2103460-nine-corrections-20261106"
BASE_COMMIT = "a70aaaec062eac447556d22325affef9d8d496ec"
DIAGNOSTIC_COMMIT = "45289ee8235b19d6d49d9144241b1988fbc3754f"
AUTHORITY = Path("repairs/dual-experience-isolation-2103420/release-authority.json")
WORKFLOW = Path(".github/workflows/infinity-combined-release.yml")
TARGETS = ("INFINITY", "CHOOSER_SHELL")
APK_KINDS = ("candidate", "forward-recovery")


def ref_blob(commit, path):
    return subprocess.check_output(["git", "-C", ROOT, "show", f"{commit}:{path}"])


def owner_bundle(source, destination, apk, owner, expected, payload, version, head, bundles, inventory):
    original = bundles.read_bundle(source, expected)
    proposed = deepcopy(original)
    proposed["payload"] = {name: row for name, row in payload.items() if row["owner"] == owner}
    require(set(original["payload"]) == set(proposed["payload"]), "Owner member inventory changed")
    replacements = {}
    with ZipFile(source) as before, ZipFile(apk) as candidate:
        for name, desc in proposed["members"].items():
            key = "member:" + name
            require(key in proposed["payload"], "Member outside approved owner")
            value = proposed["payload"][key]["sha256"]
            if value != original["payload"][key]["sha256"]:
                replacements["payload/" + name] = candidate.read(name)
                require(inventory.digest(replacements["payload/" + name]) == value, "Owner member hash differs")
                desc["sha256"] = value
        proposed.update(version=f"{version}.{owner.lower()}.startup514.1", approved_source=head,
                        digest=bundles.component_digest(proposed["payload"], owner))
        replacements["component.json"] = inventory.canonical(proposed)
        with ZipFile(destination, "w", allowZip64=True) as result:
            for info in before.infolist():
                copy_member(before, result, info, replacements.get(info.filename))
    return proposed


def prepare(args):
    require(os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("GITHUB_REPOSITORY") == REPOSITORY
            and os.environ.get("GITHUB_REF") == "refs/heads/" + CANONICAL
            and ref_blob(os.environ["GITHUB_SHA"], AUTHORITY) == (ROOT / AUTHORITY).read_bytes(),
            "Exact canonical pre-signing checkout required")
    remote = subprocess.check_output(["git", "-C", ROOT, "ls-remote", "origin",
                                      "refs/heads/" + CANONICAL], text=True).split()
    require(remote and remote[0] == os.environ["GITHUB_SHA"], "Canonical release state changed")
    sys.path.insert(0, str(ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/release"))
    from common_release import jars, tools

    inventory, bundles, authority, guard, _ = tools()
    baseline = json.loads(ref_blob(BASE_COMMIT, AUTHORITY))
    diagnostics = json.loads(ref_blob(DIAGNOSTIC_COMMIT, AUTHORITY))
    require(diagnostics["candidate_versionCode"] == 2103516, "Wrong diagnostic source authority")
    previous = load(ROOT / AUTHORITY)
    staged = load(args.staged / "STAGING.json")
    require(staged["release_registry_sha256"] == file_sha(ROOT / AUTHORITY) and
            staged["registration"] is False and staged["apk_signing"] is False,
            "Staged package is not bound to the unchanged registry")
    verified_catalog = load(args.original_owners / "catalog.json")
    require(verified_catalog == baseline["bundle_catalog"] and
            verified_catalog["certificate_sha256"] == inventory.CERT_SHA,
            "Original signed 2103514 owner catalog differs")
    require(set(staged["releases"]) == set(APK_KINDS) and staged["changed_DEX"] == [],
            "Only the scoped candidate and recovery may be prepared")
    source, run_id = os.environ["GITHUB_SHA"], int(os.environ["GITHUB_RUN_ID"])
    jar_folder = jars()
    args.out.mkdir()
    for kind in APK_KINDS:
        receipt = staged["releases"][kind]
        version = receipt["versionCode"]
        apk = args.staged / f"Infinity-{version}-UNSIGNED-NOT-INSTALLABLE.apk"
        require(file_sha(apk) == receipt["unsigned_apk_sha256"], "Staged package changed")
        product = args.out / kind
        components = product / "components"
        components.mkdir(parents=True)
        target_apk = product / f"Infinity-{version}-UNSIGNED.apk"
        shutil.copyfile(apk, target_apk)
        work = args.out.parent / f"inspect-514-{kind}"
        actual, observed_version = guard.inspect_candidate(target_apk, jar_folder, work)
        require(observed_version == version and set(actual) == set(baseline["payload"]),
                "Original payload keys, package or version differ")
        expected_delta = {"member:" + n for n in receipt["changes"]} - {"member:AndroidManifest.xml"}
        changed = {n for n in actual if actual[n] != baseline["payload"][n]["sha256"]}
        require(changed == expected_delta, "Original class or APK member changed outside the scope")
        payload = {n: dict(baseline["payload"][n], sha256=digest) for n, digest in actual.items()}
        if kind == "candidate":
            expected_qa_delta = {"member:assets/experience-component-updates.properties"} | {
                "member:assets/addons/script.infinity.commandcenter/" + name
                for name in ("plugin.py", "INFINITY-MODULES.v1", "INFINITY-MODULES.v1.sig", "addon.xml")
            }
            retained = diagnostics["payload"]
            require(set(payload) == set(retained) and
                    {n for n in payload if payload[n] != retained[n]} == expected_qa_delta,
                    "The candidate must preserve the 2103516 diagnostics and all other reviewed members")

        catalog = deepcopy(verified_catalog)
        catalog.update(source=source, release_approved=False)
        metas = {}
        for owner, row in catalog["bundles"].items():
            original = args.original_owners / row["file"]
            target = components / row["file"]
            if owner in TARGETS:
                meta = owner_bundle(original, target, target_apk, owner, row, payload,
                                    version, source, bundles, inventory)
                row.update(sha256=file_sha(target), **{k: meta[k] for k in ("version", "digest", "approved_source")})
                metas[owner] = meta
            else:
                shutil.copyfile(original, target)
            bundles.read_bundle(target, row)
        (components / "catalog.json").write_bytes(inventory.canonical(catalog))
        proposal = deepcopy(previous)
        proposal.update(generation=previous["generation"] + 1, candidate_versionCode=version,
                        last_issued_versionCode=previous["candidate_versionCode"],
                        previous_authority_sha256=inventory.digest(inventory.canonical(previous)),
                        target_owners=list(TARGETS), update_kind="owner_update",
                        payload=payload, bundle_catalog=catalog,
                        experience_version_labels={"INFINITY": version, "COBRA": 2103445},
                        workflow_sha256=file_sha(ROOT / WORKFLOW))
        for owner in TARGETS:
            proposal["components"][owner] = {key: metas[owner][key] for key in
                                             ("version", "digest", "approved_source", "settings_schema")}
            proposal["components"][owner]["revision"] = previous["components"][owner]["revision"] + 1
            proposal["bundle_sources"][owner] = dict(
                run_id=run_id, build_source=source, artifact=f"Infinity514-Prepared-{run_id}",
                path=f"{kind}/components/{owner}.zip")
        proposal["owner_update_evidence"] = dict(
            owner=f"INFINITY_514_STARTUP_CONTINUE_{kind.upper()}", producer_run=run_id,
            producer_source=source, baseline_APK_sha256=staged["baseline"]["apk_sha256"],
            unsigned_sha256=receipt["unsigned_apk_sha256"], Fold="PENDING_OWNER",
            accepted_pointer_updated=False, public_release=False,
            verification_toolchain=dict(previous["owner_update_evidence"]["verification_toolchain"],
                                        unchanged_original_DEX=True,
                                        content_baseline_APK_sha256=staged["baseline"]["apk_sha256"]))
        authority.transition(previous, proposal, proposal["target_owners"])
        authority.verify_evidence(proposal, lambda path: (ROOT / path).read_bytes())
        authority.verify(proposal, actual, version, proposal["generation"])
        guard.validate_runtime_ownership(proposal, work)
        (product / "AUTHORITY-PROPOSAL.json").write_bytes(inventory.canonical(proposal))
        inventory.save(product / "PRESERVATION.json", receipt)
        previous = proposal
    inventory.save(args.out / "PREPARATION.json",
                   dict(status="PASS_UNSIGNED_514_OWNER_PREPARATION",
                        baseline=staged["baseline"], staged_sha256=file_sha(args.staged / "STAGING.json"),
                        source=source, registry_updated=False, signing=False, physical_acceptance=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("staged", "original-owners", "out"):
        parser.add_argument("--" + flag, type=Path, required=True)
    prepare(parser.parse_args())
