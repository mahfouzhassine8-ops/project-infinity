#!/usr/bin/env python3
"""Strict, read-only verification for ONLY Infinity #1-6, #9, #10 and #12.

This checker does not sign, install or modify an APK. It checks an already
assembled candidate against the exact previous APK and refuses any extra
component, deleted file, changed native/Java payload or protected service.
Full Samsung Fold/Android 17 functional acceptance remains independent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPAIR_NUMBERS = (1, 2, 3, 4, 5, 6, 9, 10, 12)
SKIPPED = (7, 8, 11)
LOCKED_APK_SHA256 = "b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af"
SIGNER_SHA256 = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
VERSIONS = {
    "skin.infinity.diggz": "1.0.5.228",
    "script.infinity.uirepair": "0.1.2",
    "script.infinity.rails": "0.2.7",
    "script.infinity.watchedbridge": "1.0.1",
}
ADDON_BASE = "assets/addons/"
# Existing approved, hash-pinned requirements of the .225-derived Infinity skin;
# these are not new features. Existing parent bytes must never be overwritten.
DEPENDENCIES = {
    "script.infinity.commandcenter": "0.3.5.20",
    # Locked 2103384 already embeds 0.7.2. External .8.2 staging is NOT an
    # authorized service upgrade, and reviewed skin .228 doesn't require it.
    "service.infinity.compat": None,
    "script.skinshortcuts": None,
    "resource.images.studios.white": None,
    "resource.images.recordlabels.white": None,
}
PRESERVED_COMPAT_VERSION = "0.7.2"
MANIFEST = "assets/system/addon-manifest.xml"
ENGINE = "lib/arm64-v8a/libkodi.so"
CRASH = "lib/arm64-v8a/libinfinitycrash.so"
SIGNATURE = re.compile(r"META-INF/[^/]+\.(?:RSA|DSA|EC|SF|MF)$", re.I)


def require(ok, message):
    if not ok:
        raise ValueError("Infinity exact-scope gate failed: " + message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version(source: Path):
    root = ET.fromstring(source.read_bytes())
    return root.attrib.get("id"), root.attrib.get("version")


def check_sources(root: Path = ROOT):
    # All source files are read-only. There is NO modification of #7, #8 or #11.
    declared = {
        "script.infinity.uirepair": root / "repairs/four-repair-20261018/addon/addon.xml",
        "script.infinity.watchedbridge": root / "repairs/watched-bridge-20261017/addon/addon.xml",
    }
    for aid, source in declared.items():
        require(source.is_file() and version(source) == (aid, VERSIONS[aid]),
                "Unexpected source ID/version: " + aid)
    runtime = (root / "repairs/four-repair-20261018/addon/runtime.py").read_text()
    guard = "return xbmcaddon.Addon('script.infinity.rails').getAddonInfo('version') in ('0.2.6', '0.2.7')"
    require(runtime.count(guard) == 1, "Reviewed #4/#6 version predicate missing")
    require("RunScript(script.infinity.rails,add," in runtime, "Original Add to Rails action missing")
    require("Addons.SetAddonEnabled" in runtime and "enabled=False" in runtime,
            "Original confirmed Disable behavior missing")
    native = (root / "repairs/four-repair-20261018/native_patch.py").read_text()
    require(native.count("INFINITY_VIDEO_SOURCES_IDENTITY_V1") == 1 and
            "token != item->GetProperty(\"Addon.ID\").asString()" in native,
            "#3 exact opt-in identity guard not present")
    require("('xbmc/input/InputManager.cpp', 'xbmc/guilib/GUIBaseContainer.cpp'," in native,
            "Unreviewed native delta inventory")
    rails = (root / "repairs/item6-rails-20261018/build.py").read_text()
    require("version=\"0.2.7\"" in rails and "InfinityRailsOptions.xml" in rails and
            "resources/skins/Default/720p/" in rails,
            "#6 approved script-owned Mocha XML change absent")
    rotate = (root / "repairs/four-repair-20261018/item1_rotate_cyan_228.py").read_text()
    require("VERSION = '1.0.5.228'" in rotate and "PARENT_SHA256 =" in rotate,
            "#1 approved Rotate candidate missing")
    lock = json.loads((root / "repairs/locked-baselines/INFINITY-2103384-SHUTDOWN-LOCK.json").read_text())
    require(lock["product"]["sha256"] == LOCKED_APK_SHA256 and
            lock["product"]["signing_certificate_sha256"] == SIGNER_SHA256,
            "Locked #10 baseline modified")
    return {"source_contract": "PASS", "scope": list(REPAIR_NUMBERS),
            "excluded_new_work": list(SKIPPED),
            "expected_updated_addons": VERSIONS, "locked_shutdown_unchanged": True,
            "physical_fold_verified": False, "crash_fixed": False}


def read_archive(path: Path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(z.testzip() is None and len(names) == len(set(names)), "Corrupt/duplicate APK entries")
        return {name: z.read(name) for name in names if not SIGNATURE.fullmatch(name)}


def manifest_members(payload: bytes):
    xml = ET.fromstring(payload)
    require(xml.tag == "addons", "System addon manifest root mismatch")
    names = [a.text for a in xml.findall("addon")]
    require(len(names) == len(set(names)), "Duplicate system add-on")
    return set(names)


def check_apks(previous: Path, candidate: Path):
    """Byte-check EVERY preexisting APK member, not just named Cobra files."""
    old, new = read_archive(previous), read_archive(candidate)
    require(MANIFEST in old and MANIFEST in new, "System manifest missing")
    require(ENGINE in old and ENGINE in new, "Native engine missing")
    require(CRASH in old and CRASH in new and old[CRASH] == new[CRASH],
            "Existing in-app #12 native crash recorder changed or missing")
    require(not (set(old) - set(new)), "An original APK member was deleted")

    allowed_files = {"AndroidManifest.xml", MANIFEST, ENGINE}
    allowed_prefix = tuple(ADDON_BASE + aid + "/" for aid in VERSIONS)
    static_prefix = tuple(ADDON_BASE + aid + "/" for aid in DEPENDENCIES)
    additions = set(new) - set(old)
    changed = {name for name in old if old[name] != new[name]}
    extra = [name for name in additions | changed
             if name not in allowed_files and
             not name.startswith(allowed_prefix) and
             not (name in additions and name.startswith(static_prefix))]
    require(not extra, "Unapproved APK payload changed/added: " + repr(sorted(extra)[:15]))
    require(all(name not in additions for name in old),
            "Unapproved duplicate input")
    require(old.get("classes.dex") == new.get("classes.dex"),
            "Native Java/DEX app code changed outside this exact integration")

    prior_ids = manifest_members(old[MANIFEST])
    after_ids = manifest_members(new[MANIFEST])
    require(after_ids - prior_ids <= set(VERSIONS) | set(DEPENDENCIES) and
            prior_ids <= after_ids, "Unapproved new or removed bundled addon")
    require(set(VERSIONS) | set(DEPENDENCIES) <= after_ids,
            "Required updated addon or approved existing dependency not registered")

    for aid, expected in VERSIONS.items():
        xmlpath = ADDON_BASE + aid + "/addon.xml"
        require(xmlpath in new, "Required component absent: " + aid)
        info = ET.fromstring(new[xmlpath])
        require(info.attrib.get("id") == aid and info.attrib.get("version") == expected,
                "Wrong updated component ID/version: " + aid)

    for aid, expected in DEPENDENCIES.items():
        path = ADDON_BASE + aid + "/addon.xml"
        require(path in new, "Approved production dependency missing: " + aid)
        row = ET.fromstring(new[path])
        require(row.attrib.get("id") == aid and
                (expected is None or row.attrib.get("version") == expected),
                "Production dependency identity/version mismatch: " + aid)
        if aid == "service.infinity.compat":
            require(path in old and row.attrib.get("version") == PRESERVED_COMPAT_VERSION,
                    "Original locked Compatibility 0.7.2 ID/version must be preserved")
        prefix = ADDON_BASE + aid + "/"
        original_members = {name for name in old if name.startswith(prefix)}
        candidate_members = {name for name in new if name.startswith(prefix)}
        if original_members:
            require(original_members == candidate_members,
                    "Existing protected dependency acquired unapproved new files: " + aid)
        require(all(old[name] == new[name] for name in original_members),
                "Existing production dependency was overwritten: " + aid)

    # Never silently add recovery from skipped #7, or alter the versioncheck
    # service or other #11 files, preexisting Cobra or any locked shutdown code.
    for aid in ("script.infinity.addonrecovery", "service.xbmc.versioncheck"):
        prefix = ADDON_BASE + aid + "/"
        before = {name:body for name,body in old.items() if name.startswith(prefix)}
        after = {name:body for name,body in new.items() if name.startswith(prefix)}
        require(before == after, "Skipped/preserved add-on changed: " + aid)

    native_libs = {name for name in old if name.startswith("lib/") and name != ENGINE}
    require(all(old[name] == new[name] for name in native_libs),
            "Protected native library changed")
    cobra = {name for name in old if "cobra" in name.lower()}
    require(all(old[name] == new[name] for name in cobra),
            "Protected Cobra member changed")

    return {
        "source_parent_sha256": sha(previous.read_bytes()),
        "candidate_sha256": sha(candidate.read_bytes()),
        "new_or_updated_addons": VERSIONS,
        "unchanged_dependency_identities": DEPENDENCIES,
        "scope": list(REPAIR_NUMBERS),
        "added_files": sorted(additions),
        "changed_files": sorted(changed),
        "removed_files": [],
        "legacy_compat_service_preserved": True,
        "versioncheck_unchanged": True,
        "cobra_named_members_unchanged": True,
        "original_native_crash_recorder_preserved": True,
        "android17_full_runtime_verified": False,
        "physical_fold_verified": False,
        "original_crash_fixed": False,
        "final_lock_approved": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--previous", type=Path)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    results = check_sources()
    if args.previous or args.candidate:
        require(args.previous and args.candidate, "Both APKs required for binary audit")
        results["apk_delta"] = check_apks(args.previous, args.candidate)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
