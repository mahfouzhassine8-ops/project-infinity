#!/usr/bin/env python3
"""EXPERIMENTAL integrated Infinity 2103390: exactly repairs #1-6/#9/#10/#12.

Input parent must be a freshly compiled, permanently signed 2103385 #3 native
candidate derived ONLY from signed locked 2103384. Output remains experimental,
unapproved for user install until exact Android17/Fold acceptance. No changes
to Cobra, shutdown, Android Version Check, original crash recorder or user data.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import zipfile
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_CODE, CODE = 2103385, 2103390
BASE_NAME = "1.0.9-UI-Restoration-Fold-TEST01"
NAME = "1.0.9-UI-Restoration-Fold-TEST06"
FILENAME = "Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk"
SKIN_HASH = "39f8f041376748fbe209868a33ef51e1cfd59082ee6ebb8ad095e6f85336bdef"
RAILS_HASH = "e3b8614bc024d25159b64721ec5efe2b26b8c1bf0589dc03a0a33e7a9f02eddf"
WATCHED_HASH = "dbc913459c148052ce46b30241d77c4a2c7d29bea45fddcad82496ebe9ad0029"
SOURCE_FIRST_PARTY = "eb61ddf66a01f434978c9ea070131311360ad76c536dd704355738db9179c1a5"
DISTRIBUTION = {
    "skin.infinity.diggz": "skin",
    "script.infinity.uirepair": "helper",
    "script.infinity.rails": "rails",
    "script.infinity.watchedbridge": "watched",
}
SIGNATURE = re.compile(r"META-INF/[^/]+\.(?:RSA|DSA|EC|SF|MF)$", re.I)

spec = importlib.util.spec_from_file_location("nine_scope", HERE / "scope_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
spec = importlib.util.spec_from_file_location(
    "manifest_native", ROOT / "repairs/critical-preview-2103376/manifest_patch.py")
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)
spec = importlib.util.spec_from_file_location(
    "original_infinity_signer", ROOT / "repairs/full-system-20261017/package_2103384_vfs.py")
signer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signer)


def require(ok, reason):
    if not ok:
        raise ValueError("INFINITY 2103390 BLOCKED: " + reason)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def unzip_component(archive: Path, addon: str, known_sha=None):
    require(archive.is_file(), "Required approved ZIP unavailable: " + addon)
    actual_hash = digest(archive)
    if known_sha:
        require(actual_hash == known_sha, "Source ZIP digest differs: " + addon)
    result = {}
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        require(z.testzip() is None and len(names) == len(set(names)), "Invalid ZIP: " + addon)
        for info in z.infolist():
            name = info.filename
            parts = PurePosixPath(name).parts
            require(parts and parts[0] == addon and len(parts) >= 2 and
                    not name.startswith("/") and ".." not in parts and
                    "\\" not in name and not stat.S_ISLNK((info.external_attr >> 16) & 0xffff),
                    "Unsafe ZIP member: " + name)
            if info.is_dir():
                continue
            result["assets/addons/" + name] = z.read(info)
    key = "assets/addons/" + addon + "/addon.xml"
    require(key in result, "Missing add-on manifest for " + addon)
    xml = ET.fromstring(result[key])
    require(xml.get("id") == addon and xml.get("version") == gate.VERSIONS[addon],
            "Wrong approved add-on identity/version for " + addon)
    require(bool(result), "Empty ZIP: " + addon)
    return result, actual_hash


def helper_source_identity(contents):
    base = ROOT / "repairs/four-repair-20261018"
    source = base / "addon"
    expected = {}
    for item in source.rglob("*"):
        if item.is_file() and "__pycache__" not in item.parts:
            expected["assets/addons/script.infinity.uirepair/" +
                     item.relative_to(source).as_posix()] = item.read_bytes()
    expected["assets/addons/script.infinity.uirepair/resources/skins/Default/1080i/InfinityItemOptions.xml"] = (
        base / "InfinityItemOptions.xml").read_bytes()
    require(set(contents) == set(expected), "UI helper archive membership differs from reviewed source")
    require(all(contents[k] == expected[k] for k in expected),
            "UI helper archive does not contain current reviewed .1.2 + .027 guard")
    return True


def original_dependency_sources(folder: Path, proof: Path):
    require(folder.is_dir() and proof.is_file(), "No exact original production dependencies")
    report = json.loads(proof.read_text())
    require(report.get("approved_first_party_source_tree_sha256") == SOURCE_FIRST_PARTY
            and report.get("full_production_skin_dependencies_satisfied") is True
            and report.get("no_addon_xml_rewritten") is True,
            "Original locked production dependency proof missing")
    original = report.get("addons", {})
    require(set(gate.DEPENDENCIES) <= set(original),
            "Some original production dependencies have no source proof")
    contents = {}
    inventory = {}
    for aid, version in sorted(gate.DEPENDENCIES.items()):
        addon_dir = folder / aid
        require(addon_dir.is_dir() and not addon_dir.is_symlink(),
                "Dependency directory not found: " + aid)
        xml = ET.parse(addon_dir / "addon.xml").getroot()
        require(xml.get("id") == aid and
                (version is None or xml.get("version") == version),
                "Dependency manifest mismatch: " + aid)
        require(gate.sha((addon_dir / "addon.xml").read_bytes()) ==
                original[aid].get("addon_xml_sha256"),
                "Dependency source manifest differs from accepted input: " + aid)
        count = 0
        for path in sorted(addon_dir.rglob("*")):
            require(not path.is_symlink(), "Dependency symlink: " + aid)
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            relative = path.relative_to(addon_dir)
            require(".." not in relative.parts and "\\" not in relative.as_posix(),
                    "Unsafe dependency filename")
            contents["assets/addons/" + aid + "/" + relative.as_posix()] = path.read_bytes()
            count += 1
        require(count > 0, "Empty dependency: " + aid)
        inventory[aid] = dict(version=xml.get("version"), file_count=count)
    return contents, inventory


def verify_native_parent(parent: Path, locked: Path, signed_proof: Path, expected_native_sha: str):
    require(digest(locked) == gate.LOCKED_APK_SHA256,
            "Locked user-approved 2103384 SHA mismatch")
    report = json.loads(signed_proof.read_text())
    require(report.get("parent_sha256") == gate.LOCKED_APK_SHA256
            and report.get("signer_sha256") == gate.SIGNER_SHA256
            and report.get("only_input_native_delta") is True
            and report.get("source_commit") == expected_native_sha,
            "Native parent is not the reviewed new #3 correction from locked 2103384")
    released = [a for a in report.get("artifacts", [])
                if a.get("native_restored_2103384") is False]
    require(len(released) == 1 and released[0]["file"] == parent.name
            and released[0]["sha256"] == digest(parent)
            and released[0]["changed_unsigned_payload"] == ["AndroidManifest.xml",
                                                               "lib/arm64-v8a/libkodi.so"],
            "Signed native parent lineage or file inventory mismatch")
    with zipfile.ZipFile(locked) as old, zipfile.ZipFile(parent) as source:
        require(old.testzip() is None and source.testzip() is None, "Bad locked/native APK")
        a = {n:old.read(n) for n in old.namelist() if not SIGNATURE.fullmatch(n)}
        b = {n:source.read(n) for n in source.namelist() if not SIGNATURE.fullmatch(n)}
        require(set(a) == set(b), "Native parent added or dropped APK files")
        edits = {n for n in a if a[n] != b[n]}
        require(edits == {"AndroidManifest.xml", gate.ENGINE},
                "Unexpected differences to original native parent: " + repr(sorted(edits)[:12]))
        require(gate.CRASH in a and a[gate.CRASH] == b[gate.CRASH],
                "Original in-app crash recorder is absent or replaced")
        require(gate.sha(a[gate.ENGINE]) ==
                "f47c6f3473a45438a533ecfa57dd196bac6d794227b16c4fb7888636e8f4408d",
                "Original verified shutdown/deadlock engine not selected")
    return report


def revised_manifest(original: bytes):
    xml = ET.fromstring(original)
    require(xml.tag == "addons", "Unexpected original system add-on manifest")
    names = [c.text for c in xml.findall("addon")]
    require(len(names) == len(set(names)), "Original duplicate add-on registration")
    require(original.endswith(b"</addons>\n"), "Unexpected original system manifest trailer")
    missing = sorted((set(gate.VERSIONS) | set(gate.DEPENDENCIES)) - set(names))
    appendix = b"".join(("  <addon>" + aid + "</addon>\n").encode() for aid in missing)
    updated = original[:-len(b"</addons>\n")] + appendix + b"</addons>\n"
    require(gate.manifest_members(updated) == set(names) | set(missing),
            "System manifest additions did not match exact dependency contract")
    return updated


def create_unsigned(parent: Path, approved: dict, destination: Path):
    manifest.PARENT_CODE = BASE_CODE
    manifest.CODE = CODE
    manifest.PARENT_NAME = BASE_NAME
    manifest.NAME = NAME
    with zipfile.ZipFile(parent) as original:
        require(original.testzip() is None, "Corrupt signed native parent")
        new_manifest, edits = manifest.patch(original.read("AndroidManifest.xml"))
        require({x["field"] for x in edits} == {"versionCode", "versionName"},
                "Unreviewed AndroidManifest changes")
        targets = dict(approved)
        targets["AndroidManifest.xml"] = new_manifest
        targets[gate.MANIFEST] = revised_manifest(original.read(gate.MANIFEST))
        members = set(original.namelist())
        for name in approved:
            # Original static dependencies stay byte-for-byte identical.
            if name in members and name.startswith(tuple(
                    "assets/addons/" + aid + "/" for aid in gate.DEPENDENCIES)):
                require(original.read(name) == approved[name],
                        "Refusing to overwrite existing production dependency: " + name)
        with zipfile.ZipFile(destination, "w", allowZip64=True) as z:
            for info in original.infolist():
                if SIGNATURE.fullmatch(info.filename):
                    continue
                z.writestr(copy.copy(info),
                           targets[info.filename] if info.filename in targets else original.read(info))
            for name in sorted(set(targets) - members):
                entry = zipfile.ZipInfo(name, (2026, 10, 18, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = (stat.S_IFREG | 0o644) << 16
                z.writestr(entry, targets[name])
    return gate.check_apks(parent, destination)


def run(args):
    gate.check_sources()
    require(not args.out.exists(), "Destination already exists; do not overwrite artifacts")
    for key in ("skin", "helper", "rails", "watched", "native_parent",
                "locked", "signed_parent_proof", "static", "static_proof"):
        require(getattr(args, key).exists(), "Required exact source not found: " + key)
    prior = verify_native_parent(args.native_parent, args.locked,
                                 args.signed_parent_proof, args.native_source_commit)
    inputs = {}
    hashes = {}
    for addon, arg, sha in (("skin.infinity.diggz", "skin", SKIN_HASH),
                            ("script.infinity.uirepair", "helper", None),
                            ("script.infinity.rails", "rails", RAILS_HASH),
                            ("script.infinity.watchedbridge", "watched", WATCHED_HASH)):
        group, fingerprint = unzip_component(getattr(args, arg), addon, sha)
        if addon == "script.infinity.uirepair":
            helper_source_identity(group)
        inputs.update(group)
        hashes[addon] = fingerprint
    original, dependencies = original_dependency_sources(args.static, args.static_proof)
    require(not (set(inputs) & set(original)), "Original dependency collides with new approved correction")
    inputs.update(original)
    args.out.mkdir(parents=True)
    intermediate = args.out / ("unsigned-" + FILENAME)
    scope = create_unsigned(args.native_parent, inputs, intermediate)
    signed = False
    candidate = intermediate
    if args.sign:
        for key in ("INFINITY_KEYSTORE_B64", "INFINITY_STORE_PASSWORD",
                    "INFINITY_KEY_PASSWORD", "INFINITY_KEY_ALIAS"):
            require(bool(os.environ.get(key)), "Permanent signing secret missing: " + key)
        require("ANDROID_HOME" in os.environ, "Android build tools path not specified")
        bt = Path(os.environ["ANDROID_HOME"]) / "build-tools" / "34.0.0"
        signer.verify_signed(args.native_parent, bt)
        candidate = args.out / FILENAME
        subprocess.run(["bash", str(ROOT / "scripts/sign-infinity71.sh"),
                        str(intermediate), str(candidate)], check=True)
        signer.verify_signed(candidate, bt)
        signer.output(bt / "zipalign", "-c", "-p", "4", candidate)
        badge = signer.output(bt / "aapt", "dump", "badging", candidate)
        require("package: name='com.projectinfinity.kodi' versionCode='2103390'" in badge
                and "versionName='" + NAME + "'" in badge
                and "application-debuggable" not in badge,
                "Permanent-signed APK identity invalid")
        signed_scope = gate.check_apks(args.native_parent, candidate)
        require({k:v for k,v in scope.items()
                 if k not in ("candidate_sha256", "source_parent_sha256")} ==
                {k:v for k,v in signed_scope.items()
                 if k not in ("candidate_sha256", "source_parent_sha256")},
                "Signed payload changed outside verified source")
        intermediate.unlink()
        signed = True
    receipt = dict(
        format="EXPERIMENTAL_UNAPPROVED",
        version_code=CODE, name=NAME, parent_code=BASE_CODE,
        component_hashes=hashes, static_dependency_inventory=dependencies,
        exact_native_source_commit=args.native_source_commit,
        parent_apk_sha256=digest(args.native_parent),
        source_locked_apk_sha256=gate.LOCKED_APK_SHA256,
        candidate_sha256=digest(candidate),
        artifact=candidate.name, signed_permanently=signed,
        signer_sha256=gate.SIGNER_SHA256 if signed else None,
        approved_items=list(gate.REPAIR_NUMBERS),
        explicitly_excluded_new_work=list(gate.SKIPPED),
        original_essential_first_shutdown_unchanged=True,
        original_crash_recorder_unchanged=True, crash_root_cause_resolved=False,
        cobra_changed=False, versioncheck_changed=False,
        new_addon_recovery_included=False, all_original_apk_members_preserved=True,
        android17_api37_full_runtime_qualified=False, physical_fold_accepted=False,
        user_data_install_over_tested=False, final_binding_audit_passed=False,
        user_final_lock_approved=False, package_scope=scope,
    )
    (args.out / "INTEGRATION-2103390-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:receipt[k] for k in ("version_code", "artifact",
                                           "candidate_sha256", "signed_permanently",
                                           "component_hashes", "approved_items")}, indent=2))
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for key in ("native-parent", "locked", "signed-parent-proof", "skin",
                "helper", "rails", "watched", "static", "static-proof", "out"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--native-source-commit", required=True)
    p.add_argument("--sign", action="store_true")
    run(p.parse_args())
