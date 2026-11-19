"""Assemble only the scoped 2103514 QA payloads, using verified build outputs."""
import argparse
from copy import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

from prepare_modules import CC, MANIFEST, PREFIX, require, sha, stage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NATIVE = "lib/arm64-v8a/libkodi.so"
LABELS = "assets/experience-component-updates.properties"


def file_sha(path):
    with path.open("rb") as blob:
        return hashlib.file_digest(blob, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def digest(archive, name):
    with archive.open(name) as blob:
        return hashlib.file_digest(blob, "sha256").hexdigest()


def copy_member(source, target, info, replacement):
    with target.open(copy(info), "w", force_zip64=info.file_size >= 2**31) as out:
        if replacement is not None:
            if isinstance(replacement, Path):
                with replacement.open("rb") as src:
                    shutil.copyfileobj(src, out)
            else:
                out.write(replacement)
        else:
            with source.open(info) as src:
                shutil.copyfileobj(src, out)


def validate_engine(engine, baseline_scope, source):
    scope = load(HERE / "STARTUP-ABI-SCOPE.json")
    abi = load(engine / "ABI-514.json")
    build = load(engine / "ARM64-514.json")
    preservation = load(engine / "SOURCE-PRESERVATION-514.json")
    require(build["status"] == "PASS_FULL_ARM64_LINK_AND_EXACT_2103514_ABI" and
            build["source_commit"] == source and build["complete_native_engine_compiled"] is True and
            build["changed_or_missing_reviewed"] == [] and build["reviewed_file_count"] == 9418,
            "Missing exact native link and ABI receipt")
    require(preservation["baseline"] == baseline_scope and preservation["build_source"] == source and
            preservation["changes"] == scope["source_allowlist"] and preservation["unchanged_files"] == 9415,
            "Native preservation receipt differs from the reviewed three-source overlay")
    require(not abi["removed"] and not abi["added"] and abi["needed_before"] == abi["needed_after"] and
            abi["versions_before"] == abi["versions_after"] and
            abi["startup_storage_before"] == abi["startup_storage_after"],
            "Native ABI incompatibility")
    library = engine / "libkodi.so"
    require(file_sha(library) == build["native_sha256"], "Native file or link receipt mismatch")
    return library


def build(args):
    # Load the existing package helpers and verify that no signing/gate
    # implementation was replaced by code from this task.
    import sys
    sys.path.insert(0, str(ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/release"))
    from common_release import signature, tools

    inventory, bundles, *_ = tools()
    baseline_scope = load(HERE / "SCOPE.json")["baseline"]
    key = ROOT / "repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem"
    require(file_sha(args.baseline) == baseline_scope["apk_sha256"], "Wrong signed 2103514 APK")
    signature(args.baseline)
    library = validate_engine(args.engine, baseline_scope, args.engine_source)
    registry = load(args.registry)
    floor = max(registry["candidate_versionCode"], registry["last_issued_versionCode"])
    versions = {"candidate": floor + 1, "forward-recovery": floor + 2}
    module_ids = {CC, "script.infinity.rails", "script.infinity.uirepair", "script.infinity.watchedbridge"}

    args.out.mkdir()
    with tempfile.TemporaryDirectory(prefix="infinity514-stage-") as work, ZipFile(args.baseline) as original:
        root = Path(work)
        names = inventory.validate_names(original)
        preserved_names = set(names) - inventory.SIGNATURE
        require(digest(original, NATIVE) == baseline_scope["engine_sha256"], "Wrong signed engine member")
        for name in names:
            if name.startswith(PREFIX) and not name.endswith("/") and name.removeprefix(PREFIX).split("/")[0] in module_ids:
                target = root / "baseline" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(original.read(name))
        expected_products = root / "modules"
        stage(root / "baseline", expected_products, key)
        module_receipt = load(expected_products / "MODULE-PRESERVATION.json")
        require(module_receipt == load(HERE / "MODULE-PRESERVATION.json"), "Original-signed module source map differs")
        baseline_members = {name: digest(original, name) for name in preserved_names}

        result = {}
        for kind, version in versions.items():
            manifest = expected_products / kind / PREFIX / MANIFEST
            detached = args.module_signatures / kind / (CC + "/INFINITY-MODULES.v1.sig")
            subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(key), "-signature",
                            str(detached), str(manifest)], check=True)
            replacements = {}
            for name in module_receipt[kind]["changes"]:
                replacements[PREFIX + name] = expected_products / kind / PREFIX / name
            replacements[PREFIX + MANIFEST + ".sig"] = detached
            replacements["AndroidManifest.xml"] = bundles.set_version(original.read("AndroidManifest.xml"), version)
            replacements[LABELS] = f"infinity.last_updated_in={version}\ncobra.last_updated_in=2103445\n".encode()
            if kind == "candidate":
                replacements[NATIVE] = library
            require(set(replacements) <= preserved_names, "Unexpected APK member addition")
            output = args.out / f"Infinity-{version}-UNSIGNED-NOT-INSTALLABLE.apk"
            with ZipFile(output, "w", allowZip64=True) as candidate:
                for info in original.infolist():
                    if info.filename in preserved_names:
                        copy_member(original, candidate, info, replacements.get(info.filename))
            with ZipFile(output) as candidate:
                require(set(inventory.validate_names(candidate)) == preserved_names, "Unexpected APK member set")
                after = {name: digest(candidate, name) for name in preserved_names}
            changes = {name: {"before": old, "after": after[name]} for name, old in baseline_members.items()
                       if old != after[name]}
            require(set(changes) == set(replacements), "Unexpected APK byte delta")
            for name, value in replacements.items():
                require(after[name] == (file_sha(value) if isinstance(value, Path) else sha(value)),
                        "Staged member changed after verification: " + name)
            result[kind] = dict(versionCode=version, unsigned_apk_sha256=file_sha(output),
                                changes=changes, unchanged=len(preserved_names)-len(changes))

    report = dict(baseline=baseline_scope, engine_source=args.engine_source, releases=result,
                  release_registry_sha256=file_sha(args.registry), registration=False,
                  apk_signing=False, android_execution=False, Cobra="BYTE_IDENTICAL",
                  changed_DEX=[], stored_profile_changes=False)
    (args.out / "STAGING.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("baseline", "engine", "module-signatures", "registry", "out"):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--engine-source", required=True)
    build(parser.parse_args())
