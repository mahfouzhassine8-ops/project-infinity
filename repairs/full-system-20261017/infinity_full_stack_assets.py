#!/usr/bin/env python3
"""Prepare EXACT full Infinity skin + Rails with approved first-party add-ons.

This is not a Kodi/Estuary fixture. No addon.xml is rewritten, no dependencies
are suppressed, and missing signed product inputs are fatal. Only use the
staging output on a disposable Android emulator, never on a user's device.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

SKIN = ("skin.infinity.diggz", "1.0.5.225",
        "8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235", 3071)
RAILS = ("script.infinity.rails", "0.2.6",
         "5e4ff64592d6f8660d17db1077ed85a368c02f4eb14442760797b1d133c08179", 14)
PINNED_FIRST_PARTY = {"script.infinity.commandcenter": "0.3.5.20",
                      "service.infinity.compat": "0.8.2"}
FIRST_PARTY_TREE_SHA = "eb61ddf66a01f434978c9ea070131311360ad76c536dd704355738db9179c1a5"
NATIVE_ADDONS = {"xbmc.gui", "xbmc.python"}
EXPERIMENTAL = ("script.infinity.watchedbridge", "script.infinity.addonrecovery")


def verify(ok, message):
    if not ok:
        raise ValueError("INFINITY FULL STACK BLOCKED: " + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def addon_info(directory):
    path = Path(directory) / "addon.xml"
    verify(path.is_file(), "Missing real add-on manifest: " + str(path))
    root = ET.parse(path).getroot()
    verify(root.tag == "addon", "Non-Kodi add-on manifest: " + str(path))
    ident, version = root.get("id"), root.get("version")
    verify(bool(ident and version), "Unknown add-on ID/version")
    requirements = [(x.get("addon"), x.get("version", "0"))
                    for x in root.findall("./requires/import")]
    return dict(id=ident, version=version, requirements=requirements,
                addon_xml_sha256=digest(path))


def archive_to_stage(path, spec, stage):
    addon, expected_version, expected_sha, expected_entries = spec
    path = Path(path)
    verify(path.is_file(), "Exact FULL ZIP unavailable: " + str(path))
    verify(digest(path) == expected_sha, "Wrong/full ZIP hash: " + addon)
    with zipfile.ZipFile(path) as pack:
        entries = pack.infolist()
        verify(len(entries) == expected_entries, "Incomplete or substituted ZIP: " + addon)
        verify(pack.testzip() is None, "Corrupt ZIP: " + addon)
        verify(len({e.filename for e in entries}) == len(entries), "Duplicate ZIP entry")
        folder = addon + "/"
        destination = stage / addon
        destination.mkdir(parents=True, exist_ok=False)
        for entry in entries:
            name = entry.filename
            parts = PurePosixPath(name).parts
            verify(bool(parts) and parts[0] == addon, "Wrong ZIP root: " + name)
            verify(not name.startswith("/") and "\\" not in name and ".." not in parts,
                   "Unsafe ZIP entry: " + name)
            verify(not stat.S_ISLNK((entry.external_attr >> 16) & 0xffff),
                   "Symlinks forbidden in full ZIP: " + name)
            if name.endswith("/"):
                continue
            verify(len(parts) >= 2, "Unexpected ZIP root file")
            out = stage.joinpath(*parts)
            verify(out.resolve().is_relative_to(destination.resolve()), "ZIP traversal")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(pack.read(entry))
    info = addon_info(stage / addon)
    verify(info["id"] == addon and info["version"] == expected_version,
           "Wrong production addon ID/version for " + addon)
    return dict(**info, source_zip_sha256=expected_sha, source_zip_entries=len(entries),
                production_manifest_modified=False)


def copy_addon(src, dst, ident, version=None):
    src = Path(src)
    verify(src.is_dir() and not src.is_symlink(), "Missing dependency: " + ident)
    verify(not dst.exists(), "Dependency collision: " + ident)
    for item in src.rglob("*"):
        verify(not item.is_symlink(), "Symlink in dependency: " + ident)
    data = addon_info(src)
    verify(data["id"] == ident, "Source/addon mismatch: " + ident)
    if version is not None:
        verify(data["version"] == version, "Wrong dependency version: " + ident)
    shutil.copytree(src, dst)
    return data


def approve_first_party(directory):
    root = Path(directory)
    verify(root.is_dir(), "Approved First Party source missing")
    inventory = {}
    for addon in PINNED_FIRST_PARTY:
        directory = root / addon
        verify(directory.is_dir(), "Missing essential first-party add-on: " + addon)
        proof = {}
        for path in directory.rglob("*"):
            if path.is_file() and not path.name.endswith(".pyc") and "__pycache__" not in path.parts:
                proof[path.relative_to(directory).as_posix()] = digest(path)
        inventory[addon] = proof
    manifest = {k + "/" + rel: value for k, group in inventory.items() for rel, value in group.items()}
    check = sha(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
    verify(check == FIRST_PARTY_TREE_SHA, "First-party source differs from accepted signed-APK evidence")
    return check


def prepare(skin, rails, first_party, additional, work, include_helpers=False):
    stage = Path(work) / "addons"
    verify(not stage.exists(), "Use a fresh isolated staging directory")
    stage.mkdir(parents=True)
    approved_source_sha = approve_first_party(first_party)
    verified = {}
    for zipfile_path, spec in ((skin, SKIN), (rails, RAILS)):
        verified[spec[0]] = archive_to_stage(zipfile_path, spec, stage)
    for addon, version in PINNED_FIRST_PARTY.items():
        verified[addon] = copy_addon(Path(first_party) / addon, stage / addon, addon, version)
    if include_helpers:
        root = Path(__file__).resolve().parents[1]
        for addon, location in (("script.infinity.watchedbridge", "watched-bridge-20261017"),
                                ("script.infinity.addonrecovery", "addon-recovery-20261017")):
            verified[addon] = copy_addon(root / location / "addon", stage / addon, addon, "1.0.0")
    for item in Path(additional).iterdir() if additional else []:
        if not item.is_dir():
            continue
        info = addon_info(item)
        verify(info["id"] == item.name, "Additional addon folder ID does not match")
        verify(info["id"] not in verified, "Additional addon overwrites approved component")
        verified[info["id"]] = copy_addon(item, stage / info["id"], info["id"])

    # Full production skin dependencies MUST be resolvable without removing,
    # rewriting or lying about imports. Kodi's built-in requirements are native.
    mandatory = verified[SKIN[0]]["requirements"]
    for addon, required in mandatory:
        if addon in NATIVE_ADDONS:
            continue
        verify(addon in verified, "Required complete skin dependency missing: " + addon)
        # Require at least declared version using dotted numeric tuple, if comparable.
        v = verified[addon]["version"]
        def compare(s):
            verify(re.fullmatch(r"\d+(?:\.\d+)*", s) is not None, "Bad addon version: " + s)
            return tuple(int(x) for x in s.split("."))
        one, two = compare(v), compare(required)
        length = max(len(one), len(two))
        verify(one + (0,) * (length - len(one)) >= two + (0,) * (length - len(two)),
               "Installed version below full skin requirement: " + addon)

    report = {
        "scope": "Exact complete Infinity APK companion packages, no fixture manifests",
        "approved_first_party_source_tree_sha256": approved_source_sha,
        "skin_sha256": SKIN[2], "rails_sha256": RAILS[2],
        "addons": verified, "addon_count": len(verified),
        "full_production_skin_dependencies_satisfied": True,
        "no_addon_xml_rewritten": True, "fixture_dependencies_removed": False,
        "full_stack_android_run_passed": False,
        "physical_fold_accepted": False, "final_lock_authorized": False
    }
    (Path(work) / "FULL-STACK-INPUTS.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skin", type=Path, required=True)
    p.add_argument("--rails", type=Path, required=True)
    p.add_argument("--first-party", type=Path, required=True)
    p.add_argument("--additional", type=Path)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--include-helpers", action="store_true")
    a = p.parse_args()
    result = prepare(a.skin, a.rails, a.first_party, a.additional, a.work, a.include_helpers)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
