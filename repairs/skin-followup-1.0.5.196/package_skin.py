#!/usr/bin/env python3
"""Build and verify a separately versioned skin 196 from exact locked skin 195.

Requires the complete original ZIP; CI fixture checks are not full package or
device acceptance. No APK is built and no installed configuration is touched.
"""
import argparse
from copy import deepcopy
import difflib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from delta import AFTER, BEFORE, BASELINE_ZIP_SHA256, HERE, repair, require, sha

ADDON = "skin.infinity.diggz"
VERSION = "1.0.5.196"
METADATA = {"addon.xml", "infinity-skin.json", "Infinity-Protected-Manifest.json"}
ROOT = HERE.parents[1]


def dump(data):
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()


def archive_files(path):
    files = {}
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, "ZIP CRC failed")
        for info in archive.infolist():
            name = PurePosixPath(info.filename)
            require(not name.is_absolute() and ".." not in name.parts and "\\" not in info.filename,
                    "Unsafe ZIP member")
            require(name.parts and name.parts[0] == ADDON, "Unexpected add-on root")
            require(not stat.S_ISLNK(info.external_attr >> 16), "Symlink ZIP member")
            if info.is_dir():
                continue
            relative = str(PurePosixPath(*name.parts[1:]))
            require(relative not in files, "Duplicate ZIP member")
            files[relative] = archive.read(info)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    require(sha(args.baseline.read_bytes()) == BASELINE_ZIP_SHA256, "Locked 195 ZIP SHA mismatch")
    original = archive_files(args.baseline)
    require(ET.fromstring(original["addon.xml"]).get("version") == "1.0.5.195", "Wrong baseline version")
    previous_manifest = json.loads(original["Infinity-Protected-Manifest.json"])
    for name, digest in previous_manifest["protected_files"].items():
        require(sha(original[name]) == digest, "Stale baseline protected-file hash: " + name)

    candidate = repair(original)
    release = {
        "version": VERSION, "title": "Drawer Follow-up RC1",
        "baseline": "exact locked 1.0.5.195 / APK 2103304",
        "requires_apk": 2103305, "command_center": "0.3.5.20",
        "profiles": ["unified"], "native_responsive_marker_enabled": False,
        "runtime_tested": False, "physical_device_verified": False,
        "status": "package/source verified; physical acceptance pending",
        "scope": ["Power-ended initial drawer viewport", "outline-only hamburger focus",
                  "unique UI Theme control ID and focus marker"],
        "repair_xml": {n: {"before": BEFORE[n], "after": AFTER[n]} for n in BEFORE},
        "locked_baseline_zip_sha256": BASELINE_ZIP_SHA256,
        "deferred_movie_video_framing_changed": False,
        "open_runtime_gates": ["native graceful-exit completion", "Umbrella source/resolver sizing and Back freeze",
                               "idle screensaver takeover ownership", "physical fold/orientation/theme/touch matrix"],
    }
    addon = original["addon.xml"].decode("utf-8")
    require(addon.count('version="1.0.5.195"') == 1, "Ambiguous baseline version")
    addon = addon.replace('version="1.0.5.195"', 'version="' + VERSION + '"', 1)
    description = ("Infinity 1.0.5.196 Drawer Follow-up RC1. Guarded drawer edits over exact locked "
                   "skin 1.0.5.195: Power-ended initial viewport, outline-only hamburger focus and "
                   "a unique UI Theme control ID, separate from Performance and refresh. "
                   "All player, artwork, provider and responsive-profile files preserved. "
                   "Matched APK 2103305 for Power-route installation; Command Center 0.3.5.20 unchanged. "
                   "Source/package checks are not physical acceptance. Native shutdown, idle takeover and "
                   "Umbrella source/resolver Back freeze remain runtime investigation gates.")
    addon, count = re.subn(r'(<description lang="en_GB">).*?(</description>)',
                          lambda m: m[1] + description + m[2], addon, flags=re.S)
    require(count == 1, "Missing or ambiguous description")
    candidate["addon.xml"] = addon.encode("utf-8")
    metadata = json.loads(original["infinity-skin.json"])
    metadata["delivery_196_previous_release"] = deepcopy(metadata["current_release"])
    metadata.update(candidate=196, candidate_name=release["title"], skin_version=VERSION,
                    version=VERSION, release=release["title"], current_release=release,
                    requires_apk=2103305, candidate_locked=False, physical_device_verified=False)
    candidate["infinity-skin.json"] = dump(metadata)
    manifest = deepcopy(previous_manifest)
    manifest["delivery_196_previous_release"] = deepcopy(manifest["current_release"])
    manifest.update(candidate=196, candidate_version=VERSION, skin_version=VERSION,
                    current_release=release, candidate_locked=False)
    for name in manifest["protected_files"]:
        require(name != "Infinity-Protected-Manifest.json", "Self-referential manifest")
        manifest["protected_files"][name] = sha(candidate[name])
    candidate["Infinity-Protected-Manifest.json"] = dump(manifest)

    require(set(candidate) == set(original), "File set changed")
    changed = {n for n in original if original[n] != candidate[n]}
    require(changed == set(BEFORE) | METADATA, "Unexpected package delta")
    require(set(manifest["protected_files"]) == set(previous_manifest["protected_files"]),
            "Protected-file set changed")
    xml_count = 0
    for name, payload in candidate.items():
        if name.endswith(".xml"):
            ET.fromstring(payload)
            xml_count += 1
    profiles = ET.fromstring(candidate["addon.xml"]).findall('./extension[@point="xbmc.gui.skin"]/res')
    old_profiles = ET.fromstring(original["addon.xml"]).findall('./extension[@point="xbmc.gui.skin"]/res')
    require([p.attrib for p in profiles] == [p.attrib for p in old_profiles], "Profile architecture changed")
    require([p.get("folder") for p in profiles] == ["unified"], "Unexpected active profile")

    spec = importlib.util.spec_from_file_location("drawer196", HERE / "test_delta.py")
    new_tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(new_tests)
    new_tests.ORIGINAL = original
    new_tests.CANDIDATE = candidate
    # Hash fixture tests intentionally continue to verify the three audited XML
    # fixtures, while bundle tests verify all 2,892 source files independently.
    new_tests.ORIGINAL = {n: original[n] for n in new_tests.FIXTURE_SHA256}
    new_tests.CANDIDATE = {n: candidate[n] for n in new_tests.FIXTURE_SHA256}
    suite = unittest.defaultTestLoader.loadTestsFromModule(new_tests)
    with tempfile.TemporaryDirectory(prefix="infinity-skin196-") as tmp:
        skin = Path(tmp) / ADDON
        for name, payload in candidate.items():
            target = skin / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        parent_spec = importlib.util.spec_from_file_location(
            "skin195_contracts", HERE / "test_preserved_contracts.py")
        parent_tests = importlib.util.module_from_spec(parent_spec)
        parent_spec.loader.exec_module(parent_tests)
        parent_tests.SKIN = skin
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(parent_tests))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        require(result.wasSuccessful(), "Skin contracts failed")
        # Validate actual alpha, not just the name of a purported transparent
        # asset. Do not change the approved image resources to satisfy this test.
        from PIL import Image
        transparent = Image.open(skin / "media/infinity_reference/slider_transparent.png").convert("RGBA")
        rim = Image.open(skin / "media/infinity_polish/focus_rim.png").convert("RGBA")
        require(transparent.getchannel("A").getextrema() == (0, 0), "Resting texture is not transparent")
        require(rim.getpixel((rim.width // 2, rim.height // 2))[3] == 0, "Focus rim contains a center fill")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / (ADDON + "-" + VERSION + "-Drawer-Follow-up-RC1.zip")
    require(not output.exists(), "Refusing to overwrite an existing deliverable")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(candidate.items()):
            info = zipfile.ZipInfo(ADDON + "/" + name, (2026, 10, 4, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload, compresslevel=9)
    readback = archive_files(output)
    require(readback == candidate, "Candidate byte-for-byte archive readback failed")
    addon_identity = ET.fromstring(readback["addon.xml"])
    require(addon_identity.get("id") == ADDON and addon_identity.get("version") == VERSION,
            "Candidate identity mismatch")
    for name, digest in manifest["protected_files"].items():
        require(sha(readback[name]) == digest, "Candidate protected hash mismatch: " + name)
    patch = "".join("".join(difflib.unified_diff(original[n].decode().splitlines(True),
                    candidate[n].decode().splitlines(True), fromfile="a/" + ADDON + "/" + n,
                    tofile="b/" + ADDON + "/" + n)) for n in sorted(BEFORE))
    (args.output_dir / "skin-195-drawer.patch").write_text(patch)
    proof = {
        "schema": 1, "file": output.name, "sha256": sha(output.read_bytes()),
        "size_bytes": output.stat().st_size, "skin_id": ADDON, "version": VERSION,
        "requires_apk": 2103305, "apk_modified": False, "installable_apk": False,
        "baseline_zip_sha256": BASELINE_ZIP_SHA256, "files": len(candidate),
        "changed": {n: {"before": sha(original[n]), "after": sha(candidate[n])} for n in sorted(changed)},
        "byte_identical_files": len(candidate) - len(changed),
        "media_files_identical": sum(n.startswith("media/") for n in candidate),
        "python_files_identical": sum(n.endswith(".py") for n in candidate),
        "protected_files_verified": len(manifest["protected_files"]),
        "all_xml_files_parsed": xml_count, "source_geometry_contract_tests_passed": result.testsRun,
        "exact_archive_readback_passed": True, "crc_passed": True,
        "fixture_workflow_is_full_archive_validation": False,
        "skin_profile_architecture_unchanged": True, "player_files_identical": True,
        "weather_and_provider_configuration_changed": False, "native_changed": False,
        "deferred_movie_video_framing_changed": False, "physical_device_verified": False,
        "patch_sha256": sha(patch.encode()), "open_runtime_gates": release["open_runtime_gates"],
    }
    (args.output_dir / "package-proof.json").write_bytes(dump(proof))
    print(json.dumps({k: proof[k] for k in ["file", "sha256", "size_bytes", "files", "byte_identical_files",
                     "source_geometry_contract_tests_passed", "all_xml_files_parsed", "physical_device_verified"]}, indent=2))


if __name__ == "__main__":
    main()
