#!/usr/bin/env python3
"""Single-APK experimental 2103388: bundle COMPLETE verified UI add-on code.

This package is an installable APK, NOT permission to change an installed user
skin or profile. Fresh and in-place device runtime selection gates MUST pass
before release. Preserve the locked user-passed 2103384 and exact 2103387
native engine. Crash and Essential-First Close still require independent proof.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT_SHA = "c517d02e09fa0bfcca38a24a387b78b0d06e86ae1892207b2558792bd3ea2b97"
CODE = 2103389
PARENT_NAME = "1.0.9-UI-Restoration-Fold-TEST03"
NAME = "1.0.9-UI-Restoration-Fold-TEST05"
FILENAME = "Infinity-2103389-All-In-One-TEST5.apk"
ENGINE = "lib/arm64-v8a/libkodi.so"
ENGINE_SHA = "4b61414f05d67eb6df1f8a32f46d6b96c4991f91674401727d6ea4987f0d01af"
SYSTEM_MANIFEST = "assets/system/addon-manifest.xml"
IN_SCOPE = {
    "skin.infinity.diggz": "1.0.5.227",
    "script.infinity.uirepair": "0.1.0",
    "script.infinity.commandcenter": "0.3.5.20",
    "script.infinity.rails": "0.2.6",
    "service.infinity.compat": "0.8.2",
    "script.infinity.watchedbridge": "1.0.0",
    "script.infinity.addonrecovery": "1.0.0",
    "script.skinshortcuts": None,
    "resource.images.studios.white": None,
    "resource.images.recordlabels.white": None,
}
PINNED_SKIN_ZIP_SHA = "cc07fe41ccef2b9eca52b8b273ac5ad9a6c1f498a008d64ac0526a7e62dbe699"
PINNED_HELPER_ZIP_SHA = "792154bc91f3a2839dec29b6c560c854105913df6d78a79d39cb253207f947d7"


def require(ok, why):
    if not ok:
        raise RuntimeError("Single-APK packaging rejected: " + why)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(file):
    h = hashlib.sha256()
    with Path(file).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


signer = load_module("infinity2103388signer", ROOT / "repairs/full-system-20261017/package_2103384_vfs.py")
manifest_patch = load_module("infinity2103388manifest", ROOT / "repairs/critical-preview-2103376/manifest_patch.py")


def collect(addons, proof):
    """No profile/addon_data, test fixtures, symlinks, stale .pyc or unknown add-ons."""
    data = json.loads(Path(proof).read_text())
    ui = data["ui_candidate"]
    require(ui["skin_version"] == "1.0.5.227" and
            ui["skin_sha256"] == PINNED_SKIN_ZIP_SHA and
            ui["helper_sha256"] == PINNED_HELPER_ZIP_SHA,
            "UI ZIP provenance differs from the exact tested skin/helper")
    require(data["full_production_skin_dependencies_satisfied"] is True and
            data["no_addon_xml_rewritten"] is True,
            "Full original Diggz/Infinity dependency proof missing")
    require(set(IN_SCOPE).issubset(set(data.get("addons", {})) |
                                 {"skin.infinity.diggz", "script.infinity.uirepair"}),
            "Required first-party skin/dependency source missing")
    files, inventory = {}, {}
    for addon_id, version in sorted(IN_SCOPE.items()):
        folder = Path(addons) / addon_id
        require(folder.is_dir() and not folder.is_symlink(), "No verified source for " + addon_id)
        xml = ET.parse(folder / "addon.xml").getroot()
        require(xml.tag == "addon" and xml.get("id") == addon_id,
                "Addon ID mismatch " + addon_id)
        if version is not None:
            require(xml.get("version") == version, "Addon version mismatch " + addon_id)
        n = 0
        for path in sorted(folder.rglob("*")):
            require(not path.is_symlink(), "Symlink forbidden " + str(path))
            if not path.is_file():
                continue
            relative = path.relative_to(folder)
            if "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            rel = relative.as_posix()
            parts = PurePosixPath(rel).parts
            require(parts and ".." not in parts and "\\" not in rel and rel[0] != "/",
                    "Unsafe source filename " + rel)
            expected = ui["source_files"].get(addon_id + "/" + rel)
            payload = path.read_bytes()
            require(expected == sha_bytes(payload), "Unreviewed source bytes " + addon_id + "/" + rel)
            target = "assets/addons/" + addon_id + "/" + rel
            require(target not in files, "Duplicate packaged file " + target)
            files[target] = payload
            n += 1
        require(n > 0, "Empty add-on: " + addon_id)
        inventory[addon_id] = {"version": xml.get("version"), "files": n,
                               "addon_xml_sha256": sha_bytes(files["assets/addons/" + addon_id + "/addon.xml"])}
    return files, inventory


def system_manifest(previous):
    root = ET.fromstring(previous)
    require(root.tag == "addons", "Unexpected system addon-manifest")
    installed = {x.text for x in root.findall("addon")}
    require(not installed.intersection(IN_SCOPE),
            "Already registered bundled addon; inspect current source before modifying")
    require(previous.endswith(b"</addons>\n"), "Unexpected system manifest trailer")
    addition = b"".join(("  <addon>" + name + "</addon>\n").encode()
                        for name in sorted(IN_SCOPE))
    result = previous[:-len(b"</addons>\n")] + addition + b"</addons>\n"
    parsed = ET.fromstring(result)
    require(len(parsed.findall("addon")) == len(root.findall("addon")) + len(IN_SCOPE),
            "Incomplete system addon manifest")
    return result


def verify(parent, candidate, additions, targets, expected_manifest):
    with zipfile.ZipFile(parent) as before, zipfile.ZipFile(candidate) as after:
        require(after.testzip() is None, "ZIP integrity failure")
        require(len(after.namelist()) == len(set(after.namelist())), "APK duplicate entries")
        old = {n for n in before.namelist() if not signer.SIGNATURE.fullmatch(n)}
        now = {n for n in after.namelist() if not signer.SIGNATURE.fullmatch(n)}
        permitted = {"AndroidManifest.xml", SYSTEM_MANIFEST} | set(additions)
        permitted |= {x for x in old if x.startswith("assets/addons/service.infinity.compat/")}
        require(now - old <= permitted, "Unapproved new APK member")
        require(not (old - now), "Any removed APK payload member violates the preservation contract")
        for n in old & now:
            if n in targets:
                require(after.read(n) == targets[n], "Payload mismatch " + n)
            else:
                require(after.read(n) == before.read(n), "Unapproved parent change " + n)
        for n in now - old:
            require(after.read(n) == targets[n], "Added payload mismatch " + n)
        require(after.read(SYSTEM_MANIFEST) == expected_manifest, "Manifest modification missing")
        require(sha_bytes(after.read(ENGINE)) == ENGINE_SHA and
                after.read("classes.dex") == before.read("classes.dex"),
                "Native/Dex engine changed")
        return sorted(n for n in now - old), sorted(n for n in old - now), sorted(
            n for n in now & old if before.read(n) != after.read(n))


def build(parent, addons, proof, out, sign=False):
    parent, out = Path(parent), Path(out)
    require(not out.exists(), "Stale output destination")
    require(sha_file(parent) == PARENT_SHA, "Signed parent 2103387 mismatch")
    require(len(NAME) == len(PARENT_NAME), "Version name length mismatch")
    targets, inventory = collect(addons, proof)
    out.mkdir(parents=True)
    manifest_patch.PARENT_CODE = 2103387
    manifest_patch.CODE = CODE
    manifest_patch.PARENT_NAME = PARENT_NAME
    manifest_patch.NAME = NAME
    with zipfile.ZipFile(parent) as src:
        require(src.testzip() is None and
                sha_bytes(src.read(ENGINE)) == ENGINE_SHA, "Bad parent native identity")
        m, edits = manifest_patch.patch(src.read("AndroidManifest.xml"))
        require({e["field"] for e in edits} == {"versionCode", "versionName"},
                "Unexpected Android manifest mutation")
        targets["AndroidManifest.xml"] = m
        revised_system = system_manifest(src.read(SYSTEM_MANIFEST))
        targets[SYSTEM_MANIFEST] = revised_system
        unsigned = out / ("unsigned-" + FILENAME)
        with zipfile.ZipFile(unsigned, "w", allowZip64=True) as dst:
            for old_info in src.infolist():
                n = old_info.filename
                if signer.SIGNATURE.fullmatch(n):
                    continue
                dst.writestr(copy.copy(old_info),
                             targets[n] if n in targets else src.read(old_info))
            for n in sorted(set(targets) - set(src.namelist())):
                info = zipfile.ZipInfo(n, (2026, 10, 18, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                dst.writestr(info, targets[n])
    added, removed, changed = verify(parent, unsigned, targets, targets, revised_system)
    output = unsigned
    if sign:
        for key in ("INFINITY_KEYSTORE_B64", "INFINITY_STORE_PASSWORD",
                    "INFINITY_KEY_PASSWORD", "INFINITY_KEY_ALIAS"):
            require(bool(os.environ.get(key)), "Stable signing secret missing: " + key)
        bt = Path(os.environ["ANDROID_HOME"]) / "build-tools/34.0.0"
        signer.verify_signed(parent, bt)
        output = out / FILENAME
        subprocess.run(["bash", str(ROOT / "scripts/sign-infinity71.sh"),
                        str(unsigned), str(output)], check=True)
        signer.verify_signed(output, bt)
        signer.output(bt / "zipalign", "-c", "-p", "4", output)
        badge = signer.output(bt / "aapt", "dump", "badging", output)
        require("package: name='com.projectinfinity.kodi' versionCode='2103389'" in badge,
                "Incorrect signed APK version")
        require("versionName='" + NAME + "'" in badge and
                "application-debuggable" not in badge, "Bad signed APK identity")
        require(verify(parent, output, targets, targets, revised_system) ==
                (added, removed, changed), "Signed output differs from verified preimage")
        unsigned.unlink()
    receipt = {
        "file": output.name, "sha256": sha_file(output), "version_code": CODE,
        "parent_sha256": PARENT_SHA, "signed_permanently": bool(sign),
        "release_signer_sha256": signer.CERT if sign else None,
        "component_inventory": inventory, "component_count": len(inventory),
        "added_paths": added, "removed_paths": removed, "changed_paths": changed,
        "native_engine_unchanged": True, "native_engine_sha256": ENGINE_SHA,
        "java_bytecode_unchanged": True, "preserves_all_user_profiles": True,
        "no_uninstall_or_data_clear": True,
        "no_prior_apk_members_removed": True,
        "legacy_compat_resources_retained_but_runtime_parity_requires_proof": True,
        "fresh_runtime_activation_proven": False,
        "existing_install_upgrade_activation_proven": False,
        "essential_first_close_verified": False,
        "original_crash_fixed": False, "physical_fold_accepted": False,
        "user_final_lock_approved": False,
    }
    (out / ("SIGNED-2103389.json" if sign else "UNSIGNED-2103389.json")).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: receipt[k] for k in ("file", "sha256", "version_code",
                        "component_inventory", "native_engine_unchanged",
                        "existing_install_upgrade_activation_proven")}, indent=2))
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--addons", type=Path, required=True)
    p.add_argument("--proof", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--sign", action="store_true")
    a = p.parse_args()
    build(a.parent, a.addons, a.proof, a.out, a.sign)
