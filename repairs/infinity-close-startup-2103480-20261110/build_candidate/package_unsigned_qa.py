#!/usr/bin/env python3
"""Source-authenticated, UNSIGNED original-owner shutdown QA assembly.

Only stages a candidate for independent original-key signer admission. It never
signs, installs, registers, locks, publishes a release, or changes user data.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "repairs/dual-experience-isolation-2103420"))
import component_bundles as cb
from inventory import SIGNATURE, canonical, digest, file_sha, validate_names

BRANCH = "work/infinity-2103480-shutdown-qa-package-20261111"
PARENT = "5e26af40222bc521638bd184a2bfb0d5dce337f1"
VERSION = 2103482  # PROVISIONAL, not issued/reserved or a release approval.
BASE_APK = "9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2"
BASE_NATIVE = "ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794"
NEW_NATIVE = "503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437"
SOURCE_AFTER = "2273becee60a25e81b2c5844f052fe32eaa8d03335311672cd67b66bc3738648"
LIB = "lib/arm64-v8a/libkodi.so"
LABEL = "assets/experience-component-updates.properties"
ALLOWED = {LIB, LABEL, "AndroidManifest.xml"}
OWNERS = ("INFINITY", "CHOOSER_SHELL")
DELTA = {
    "INFINITY": {"payload/" + LIB},
    "CHOOSER_SHELL": {"payload/" + LABEL},
}
FILES = {
    "repairs/infinity-close-startup-2103480-20261110/build_candidate/package_unsigned_qa.py",
    ".github/workflows/infinity-2103480-shutdown-qa-assembly.yml",
    "repairs/infinity-close-startup-2103480-20261110/build_candidate/ORIGINAL-KEY-SIGNING-HANDOFF.md",
}


def hash_stream(handle):
    h = hashlib.sha256()
    for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def zip_digest(z, name):
    with z.open(name) as handle:
        return hash_stream(handle)


def must(cond, reason):
    if not cond:
        raise ValueError(reason)


def require_scope():
    must(os.environ.get("GITHUB_REPOSITORY") == "mahfouzhassine8-ops/project-infinity", "WRONG_REPOSITORY")
    must(os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH, "WRONG_BRANCH")
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    must(current == os.environ.get("GITHUB_SHA"), "HEAD_CHANGED")
    changes = set(subprocess.check_output(["git", "diff", "--name-only", PARENT, "HEAD"],
                                          cwd=ROOT, text=True).splitlines())
    must(changes == FILES, "OUT_OF_SCOPE_SOURCE_CHANGES:" + repr(sorted(changes ^ FILES)))
    must(re.fullmatch(r"[0-9a-f]{40}", current) is not None, "NOT_GIT_COMMIT")
    return current


def copy_entry(source, target, name, replacement=None):
    info = source.getinfo(name)
    fresh = ZipInfo(name, info.date_time)
    fresh.compress_type = info.compress_type
    fresh.external_attr = info.external_attr
    fresh.create_system = info.create_system
    fresh.comment = info.comment
    with target.open(fresh, "w", force_zip64=info.file_size >= (1 << 31)) as output:
        if replacement is None:
            with source.open(name) as original:
                shutil.copyfileobj(original, output, 4 * 1024 * 1024)
        elif isinstance(replacement, (bytes, bytearray)):
            output.write(replacement)
        else:
            with Path(replacement).open("rb") as new_content:
                shutil.copyfileobj(new_content, output, 4 * 1024 * 1024)


def rebuild_owner(src_path, dest_path, owner, source_commit, changes):
    with ZipFile(src_path) as z:
        validate_names(z)
        original = json.loads(z.read("component.json"))
        must(original["owner"] == owner, "OWNER_MISMATCH")
        must(set(changes) == DELTA[owner], "OWNER_CHANGE_SCOPE")
        updated = json.loads(json.dumps(original))
        updated["approved_source"] = source_commit
        updated["version"] = str(VERSION) + "." + owner.lower() + ".shutdownqa.1"
        for entry, new_value in changes.items():
            member = entry.removeprefix("payload/")
            must(entry == "payload/" + member and member in updated["members"], "NOT_OWNED:" + member)
            sha = (hashlib.sha256(new_value).hexdigest() if isinstance(new_value, bytes)
                   else file_sha(Path(new_value)))
            updated["members"][member]["sha256"] = sha
            updated["payload"]["member:" + member]["sha256"] = sha
        updated["digest"] = cb.component_digest(updated["payload"], owner)
        with ZipFile(dest_path, "w", allowZip64=True) as out:
            for entry in z.namelist():
                content = canonical(updated) if entry == "component.json" else changes.get(entry)
                copy_entry(z, out, entry, content)
    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--signed80", type=Path, required=True)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--native-proof", type=Path, required=True)
    parser.add_argument("--source-proof", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    commit = require_scope()
    must(not args.out.exists(), "NO_OVERWRITE_OF_PREVIOUS_CANDIDATE")
    must(file_sha(args.signed80) == BASE_APK, "SIGNED80_APK_IDENTITY")
    must(file_sha(args.native) == NEW_NATIVE, "NEW_NATIVE_ARTIFACT_IDENTITY")
    engine = json.loads(args.native_proof.read_text())
    source = json.loads(args.source_proof.read_text())
    must(engine["status"] == "PASS_FULL_ARM64_ENGINE_AND_BASELINE_ABI", "NATIVE_BUILD_NOT_PASS")
    must(engine["source_commit"] == PARENT and engine["native_sha256"] == NEW_NATIVE, "WRONG_ENGINE")
    must(source["status"] == "PASS_SIGNED80_EXACT_9411_SOURCES_PLUS_ONE_REVIEWED_DELTA", "NOT_EXACT_SOURCE")
    must(source["after_sha256"] == SOURCE_AFTER and source["unchanged_production_native_files"] == 9410,
         "OTHER_NATIVE_SOURCE_CHANGED")
    must(source["baseline_apk_sha256"] == BASE_APK, "WRONG_SIGNED_PARENT")
    must(source["signed"] is False and source["Android_Close"] == "NOT_RUN", "MISLABELED_QA")
    must(json.loads((args.official.parent / "PREPARATION.json").read_text())["versionCode"] == 2103480,
         "WRONG_OFFICIAL_COMPONENT_GENERATION")
    catalog = json.loads((args.official / "catalog.json").read_text())
    must(set(catalog["bundles"]) == set(cb.OWNED), "INCOMPLETE_OWNER_CATALOG")
    must(catalog["release_approved"] is False, "REVIEW_ONLY_OFFICIAL_INPUT")
    must(catalog["bundles"]["COBRA"]["version"] == "2103445.cobra.1",
         "CANNOT_MODIFY_COBRA")
    before = {owner: cb.read_bundle(args.official / catalog["bundles"][owner]["file"],
                                    catalog["bundles"][owner])
              for owner in cb.OWNED}
    with ZipFile(args.signed80) as signed:
        validate_names(signed)
        must(zip_digest(signed, LIB) == BASE_NATIVE, "PARENT_NATIVE_SHA_MISMATCH")
        must(signed.read(LABEL) == b"infinity.last_updated_in=2103480\ncobra.last_updated_in=2103445\n",
             "ORIGINAL_LABEL_CONTENT_MISMATCH")
    args.out.mkdir()
    owners = args.out / "components"
    owners.mkdir()
    new_label = b"infinity.last_updated_in=2103482\ncobra.last_updated_in=2103445\n"
    new_catalog = json.loads(json.dumps(catalog))
    new_catalog.update(source=commit, release_approved=False)
    for owner in cb.OWNED:
        old_row = catalog["bundles"][owner]
        src_path = args.official / old_row["file"]
        dest_path = owners / old_row["file"]
        if owner == "INFINITY":
            updated = rebuild_owner(src_path, dest_path, owner, commit,
                                    {"payload/" + LIB: args.native})
        elif owner == "CHOOSER_SHELL":
            updated = rebuild_owner(src_path, dest_path, owner, commit,
                                    {"payload/" + LABEL: new_label})
        else:
            shutil.copyfile(src_path, dest_path)
            updated = before[owner]
            must(file_sha(src_path) == file_sha(dest_path), "UNRELATED_OWNER_BUNDLE_CHANGED")
        row = new_catalog["bundles"][owner]
        row.update(sha256=file_sha(dest_path), version=updated["version"],
                   digest=updated["digest"], approved_source=updated["approved_source"])
        actual = cb.read_bundle(dest_path, row)
        must(actual == updated, "REBUILT_OWNER_CONTRACT_MISMATCH")
    (owners / "catalog.json").write_bytes(canonical(new_catalog))
    unsigned = args.out / ("Infinity-" + str(VERSION) + "-Shutdown-UNSIGNED-NOT-INSTALLABLE.apk")
    proof = cb.combine(owners, new_catalog, unsigned, VERSION)
    must(proof["signed"] is False and proof["versionCode"] == VERSION, "UNSIGNED_QA_MISLABELED")
    with ZipFile(args.signed80) as old, ZipFile(unsigned) as new:
        old_names = set(validate_names(old)) - set(SIGNATURE)
        new_names = set(validate_names(new))
        must(new_names == old_names, "CHANGED_APK_MEMBER_INVENTORY")
        changed = {}
        for name in sorted(new_names):
            old_sha = zip_digest(old, name)
            new_sha = zip_digest(new, name)
            if old_sha != new_sha:
                must(name in ALLOWED, "UNAUTHORIZED_APK_MEMBER_CHANGE:" + name)
                changed[name] = dict(before=old_sha, after=new_sha)
        must(set(changed) == ALLOWED, "UNEXPECTED_CHANGED_MEMBER_SET:" + repr(sorted(changed)))
        must(changed[LIB]["after"] == NEW_NATIVE, "FINAL_NATIVE_CHANGED")
        must(new.read(LABEL) == new_label, "CHOOSER_VERSION_LABEL_CHANGED")
        old_manifest, old_version = cb.normalize_manifest(old.read("AndroidManifest.xml"))
        new_manifest, new_version = cb.normalize_manifest(new.read("AndroidManifest.xml"))
        must(old_version == 2103480 and new_version == VERSION and old_manifest == new_manifest,
             "ANDROID_MANIFEST_CHANGED_BEYOND_VERSION")
    receipt = {
        "status": "PASS_UNSIGNED_OWNER_BUNDLE_AND_APK_MEMBER_PRESERVATION",
        "baseline_apk_version": 2103480, "qa_version_provisional_unreserved": VERSION,
        "baseline_apk_sha256": BASE_APK, "native_engine_sha256": NEW_NATIVE,
        "native_engine_commit": PARENT, "packaging_commit": commit,
        "changed_member_sha256": changed, "modified_owners": list(OWNERS),
        "unchanged_owner_zip_sha256": {o: file_sha(owners / catalog["bundles"][o]["file"])
                                       for o in ("COBRA", "MINIMAL_ANDROID_CONTRACT")},
        "source_files_unchanged": 9410, "original_dex_and_provider_payloads_preserved": True,
        "installer": "UNSIGNED_NOT_INSTALLABLE", "original_key_used": False,
        "signed_apk_sha256": None, "release_authority_registered": False,
        "native_writer_unknown_effect": "FAIL_CLOSED_REMAINS_UNPROVEN",
        "Android_shutdown": "NOT_RUN", "Fold_acceptance": "NOT_RUN",
        "source_service_patched_in_apk": False,
        "signed_baseline_modified": False,
        "unsigned_sha256": file_sha(unsigned),
    }
    (args.out / "UNSIGNED-QA-PRESERVATION.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("PASS exact original owner-bundle assembly; three member changes only, unsigned QA", flush=True)


if __name__ == "__main__":
    main()
