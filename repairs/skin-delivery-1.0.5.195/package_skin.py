#!/usr/bin/env python3
"""Package the existing seven-file repair with a distinct Kodi upgrade identity.

Does not change the APK, native engine, locked baseline, or repair XML. Output
verification is a package/source check, not installed-device acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPAIR = ROOT / "repairs/mobile-regressions-2103304"
ADDON = "skin.infinity.diggz"
VERSION = "1.0.5.195"
METADATA = {"addon.xml", "infinity-skin.json", "Infinity-Protected-Manifest.json"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    proof = json.loads((REPAIR / "skin-delta-proof.json").read_text())
    baseline_hash = sha(args.baseline.read_bytes())
    require(baseline_hash == proof["baseline_zip_sha256"], "Locked baseline SHA mismatch")
    with zipfile.ZipFile(args.baseline) as archive:
        require(archive.testzip() is None, "Baseline CRC failed")
        original = {}
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            require(not path.is_absolute() and ".." not in path.parts, "Unsafe ZIP path")
            require(path.parts[0] == ADDON, "Unexpected baseline root")
            if not member.is_dir():
                name = str(PurePosixPath(*path.parts[1:]))
                require(name not in original, "Duplicate baseline member")
                original[name] = archive.read(member)
    old_manifest = json.loads(original["Infinity-Protected-Manifest.json"])
    old_hash_errors = sorted(name for name, digest in old_manifest["protected_files"].items()
                             if sha(original[name]) != digest)
    with tempfile.TemporaryDirectory(prefix="infinity-skin195-") as temporary:
        stage = Path(temporary)
        skin = stage / "addons" / ADDON
        for name, data in original.items():
            target = skin / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        patch = REPAIR / "skin-194-repair.patch"
        subprocess.run(["git", "apply", "--check", str(patch)], cwd=stage, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=stage, check=True)
        changed = {p.relative_to(skin).as_posix() for p in skin.rglob("*")
                   if p.is_file() and p.read_bytes() != original[p.relative_to(skin).as_posix()]}
        require(changed == set(proof["changed"]), "Repair delta changed")
        for name, hashes in proof["changed"].items():
            require(sha(original[name]) == hashes["before"], "Wrong XML preimage: " + name)
            require(sha((skin / name).read_bytes()) == hashes["after"], "Wrong repaired XML: " + name)

        addon = original["addon.xml"].decode()
        require('version="1.0.5.194"' in addon, "Wrong baseline version")
        addon = addon.replace('version="1.0.5.194"', 'version="' + VERSION + '"', 1)
        description = ("Infinity 1.0.5.195 Responsive Repair RC1. Packages the existing "
                       "seven-file mobile repair over locked skin 1.0.5.194 with a distinct "
                       "installation version. Matched APK 2103304 and Command Center 0.3.5.20. "
                       "Package/source checks passed; physical device acceptance pending. "
                       "Umbrella source-window sizing and Back freeze remain unresolved.")
        addon, replacements = re.subn(r'(<description lang="en_GB">).*?(</description>)',
                                      lambda m: m[1] + description + m[2], addon, flags=re.S)
        require(replacements == 1, "Missing description")
        (skin / "addon.xml").write_bytes(addon.encode())
        release = {
            "version": VERSION, "title": "Responsive Repair RC1",
            "baseline": "1.0.5.194 / APK 2103303", "requires_apk": 2103304,
            "command_center": "0.3.5.20", "profiles": ["unified"],
            "native_responsive_marker_enabled": False, "runtime_tested": False,
            "status": "package/source verified; physical acceptance pending",
            "repair_xml": proof["changed"],
            "locked_baseline_zip_sha256": baseline_hash,
            "deferred_movie_video_framing_changed": False,
        }
        data = json.loads(original["infinity-skin.json"])
        data["delivery_195_previous_release"] = data["current_release"]
        data.update(candidate=195, candidate_name=release["title"], skin_version=VERSION,
                    version=VERSION, release=release["title"], current_release=release,
                    requires_apk=2103304, candidate_locked=False, physical_device_verified=False)
        (skin / "infinity-skin.json").write_bytes(dump(data))
        manifest = json.loads(original["Infinity-Protected-Manifest.json"])
        manifest["delivery_195_previous_release"] = manifest["current_release"]
        manifest.update(candidate=195, candidate_version=VERSION, skin_version=VERSION,
                        current_release=release, candidate_locked=False)
        # Retain the entire protected-file set; correct hashes to verified bytes.
        # Some baseline194 hash entries were already stale. No code is changed
        # to match them and none of these integrity checks is removed.
        for name in manifest["protected_files"]:
            require(name != "Infinity-Protected-Manifest.json", "Self-referential manifest")
            manifest["protected_files"][name] = sha((skin / name).read_bytes())
        (skin / "Infinity-Protected-Manifest.json").write_bytes(dump(manifest))

        spec = importlib.util.spec_from_file_location("skin_contracts", REPAIR / "test_skin.py")
        tests = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tests)
        tests.SKIN = skin
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        require(result.wasSuccessful(), "Skin contracts failed")

        expected = {p.relative_to(skin).as_posix(): p.read_bytes() for p in skin.rglob("*") if p.is_file()}
        require(set(expected) == set(original), "Unexpected file addition/removal")
        changed = sorted(name for name in expected if expected[name] != original[name])
        require(set(changed) == set(proof["changed"]) | METADATA, "Unexpected package delta")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output = args.output_dir / (ADDON + "-" + VERSION + "-Responsive-Repair-RC1.zip")
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, payload in sorted(expected.items()):
                info = zipfile.ZipInfo(ADDON + "/" + name, (2026, 10, 4, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, payload, compresslevel=9)
        with zipfile.ZipFile(output) as archive:
            require(archive.testzip() is None, "Candidate CRC failed")
            require(len(archive.infolist()) == len(expected), "Candidate member mismatch")
            for name, payload in expected.items():
                require(archive.read(ADDON + "/" + name) == payload, "Candidate byte mismatch: " + name)
            metadata = ET.fromstring(archive.read(ADDON + "/addon.xml"))
            require(metadata.get("id") == ADDON and metadata.get("version") == VERSION, "Candidate identity mismatch")
            profiles = metadata.findall('./extension[@point="xbmc.gui.skin"]/res')
            require([p.get("folder") for p in profiles] == ["unified"], "Unexpected profile change")
        receipt = {
            "schema": 1, "file": output.name, "sha256": sha(output.read_bytes()),
            "size_bytes": output.stat().st_size, "files": len(expected),
            "skin_id": ADDON, "version": VERSION, "requires_apk": 2103304,
            "baseline_zip_sha256": baseline_hash,
            "patch_sha256": sha(patch.read_bytes()),
            "changed": {name: {"before": sha(original[name]), "after": sha(expected[name])} for name in changed},
            "byte_identical_files": len(expected) - len(changed),
            "media_files_identical": sum(name.startswith("media/") for name in expected),
            "protected_files_verified": len(manifest["protected_files"]),
            "inherited_stale_manifest_entries_corrected": old_hash_errors,
            "host_contract_tests_passed": result.testsRun,
            "exact_archive_readback_passed": True, "crc_passed": True,
            "device_verified": False, "apk_modified": False,
            "deferred_movie_video_framing_changed": False,
        }
        (args.output_dir / "package-proof.json").write_bytes(dump(receipt))
        print(json.dumps({k: receipt[k] for k in ["file", "sha256", "size_bytes", "files", "byte_identical_files", "host_contract_tests_passed", "device_verified"]}, indent=2))


if __name__ == "__main__":
    main()
