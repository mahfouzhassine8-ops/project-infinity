#!/usr/bin/env python3
"""Pin the proven manual recorder helper to the actual signed correction APK."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "repairs/fold-anr-20261017"
ADDON = "script.infinity.foldcapture"
TEST4_NATIVE = "2f1597ecc4f8a0ee09f24e399aa738b96a876c7760eaec0ee0ad1a18bafd6929"


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Capture source preimage changed: " + old[:80])
    return text.replace(old, new, 1)


def build(apk, preservation, output):
    proof = json.loads(preservation.read_text())
    item = next(value for value in proof["artifacts"] if not value["rollback"])
    assert proof["native_source_commit"] == "0c9b933c7916cce7d5e0f47a195751827fc41c28"
    assert item["signer_sha256"] == "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
    assert hashlib.sha256(apk.read_bytes()).hexdigest() == item["sha256"]
    assert item["version_code"] == 2103380 and not proof["final_lock_authorized"]
    with zipfile.ZipFile(apk) as archive:
        native = hashlib.sha256(archive.read("lib/arm64-v8a/libkodi.so")).hexdigest()
        spec = importlib.util.spec_from_file_location("capture_manifest_check", ROOT / "repairs/critical-preview-2103376/manifest_patch.py")
        manifest_check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manifest_check)
        manifest_check.PARENT_CODE = manifest_check.CODE = 2103380
        manifest_check.PARENT_NAME = manifest_check.NAME = "1.0.9-Fold-Deadlock-Repair-TEST1"
        raw = archive.read("AndroidManifest.xml")
        assert manifest_check.patch(raw)[0] == raw
    assert native == item["native_packaged_sha256"]
    source = BASE / "helper" / ADDON
    files = {name: (source / name).read_text() for name in ("addon.xml", "capture.py", "default.py", "README.txt")}
    capture = once(files["capture.py"], TEST4_NATIVE, native)
    capture = capture.replace("locked 2103377 TEST4 engine", "2103380 Fold Deadlock TEST1 engine")
    capture = capture.replace("identity differs from TEST4", "identity differs from TEST4-derived 2103380 TEST1")
    capture = once(capture, '"helper_version": "1.0.0"', '"helper_version": "1.0.1"')
    capture = once(capture, '"expected_test4_native_sha256"', '"expected_native_sha256"')
    capture = once(capture, "def collect(destination, temp_dir, versions=None):",
                   "def collect(destination, temp_dir, versions=None, allow_empty=False, metadata=None):")
    capture = once(capture, "    files = {}\n", "    if metadata is not None:\n        manifest['validation'] = metadata\n    files = {}\n")
    capture = once(capture, '    if not any(info["probe_rows"] for info in manifest["files"].values()):',
                   '    observed = any(info["probe_rows"] for info in manifest["files"].values())\n'
                   '    manifest["capture_status"] = "STALL_SNAPSHOTS_PRESENT" if observed else "NO_STALL_SNAPSHOTS_OBSERVED; NOT A PASS CERTIFICATE"\n'
                   '    if not observed and not allow_empty:')
    files["capture.py"] = capture
    default = once(files["default.py"], "import xbmcaddon\n", "import xbmc\nimport json\nimport capture_session\nimport xbmcaddon\n")
    default = once(default, "            capture.arm_exact_library(capture.find_exact_native())",
                   '            receipt = capture.arm_exact_library(capture.find_exact_native())\n'
                   '            capture_session.save_arm(xbmcvfs.translatePath("special://temp/"), receipt)')
    default = once(default, '            capture.collect(target, xbmcvfs.translatePath("special://temp/"), versions)',
                   '''            temp = xbmcvfs.translatePath("special://temp/")
            def enabled(addon_id):
                value = json.loads(xbmc.executeJSONRPC(json.dumps({"jsonrpc": "2.0", "id": 1,
                    "method": "Addons.GetAddonDetails", "params": {"addonid": addon_id, "properties": ["enabled"]}})))
                return value.get("result", {}).get("addon", {}).get("enabled")
            inventory = capture_session.installed(xbmcvfs.translatePath("special://home/addons/"), enabled)
            versions.update({key: row["version"] for key, row in inventory.items()})
            loaded = {"verified": False}
            try:
                loaded = {"verified": True, "native_sha256": capture.sha256_file(capture.find_exact_native())}
            except (OSError, RuntimeError):
                loaded["reason"] = "Current engine does not match this candidate helper"
            capture.collect(target, temp, versions, allow_empty=True,
                            metadata={"armed_session": capture_session.arm_record(temp),
                                      "export_engine": loaded, "installed": inventory})''')
    files["default.py"] = default
    xml = ET.fromstring(files["addon.xml"])
    xml.set("version", "1.0.1")
    xml.find("./extension[@point='xbmc.addon.metadata']/summary").text = "Manually capture Fold return-test evidence for 2103380 TEST1."
    xml.find("./extension[@point='xbmc.addon.metadata']/description").text = "Exact candidate engine pin, two-hour bounded recorder, arm-session correlation and read-only add-on code identities. No service or provider/settings/database changes. Empty stall logs are not a pass certificate."
    files["addon.xml"] = ET.tostring(xml, encoding="unicode")
    files["capture_session.py"] = (HERE / "capture_session.py").read_text()
    files["README.txt"] = """Infinity Fold Capture 1.0.1 — 2103380 Fold Deadlock TEST1 only.
Install from ZIP, run from Program Add-ons, and arm before background testing.
This helper is observational and has no background service. It cannot repair
or certify stability. Export after a return test or after reopening from a
freeze. The export includes the arm PID/hash, the current engine identity and
whitelisted add-on code hashes/versions, never provider settings or databases.
No stall snapshots means none were captured, not proof that every test passed.
Keep the normal Android diagnostic ZIP from a failing attempt too.
The older 1.0.0 helper remains the matching helper for original TEST4.
"""
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        file = folder / "capture.py"
        file.write_text(capture)
        spec = importlib.util.spec_from_file_location("correction_capture", file)
        candidate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(candidate)
        spec = importlib.util.spec_from_file_location("original_capture_checks", BASE / "test_capture.py")
        checks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checks)
        checks.capture = candidate  # Unmodified original tests, run against generated candidate code.
        result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(checks))
        assert result.wasSuccessful() and result.testsRun == 10
        data = candidate.collect(folder / "no-stall.zip", folder, allow_empty=True,
                                 metadata={"test": "empty export is not an acceptance result"})
        assert data["capture_status"].startswith("NO_STALL") and data["is_repair"] is False
        files["PACKAGE-IDENTITY.json"] = json.dumps(dict(version="1.0.1", native_sha256=native,
            candidate_apk_sha256=item["sha256"], inherited_host_checks=10, empty_evidence_semantics_checked=True,
            background_service=False, physical_fold_verified=False), indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(files.items()):
            if name.endswith(".py"):
                compile(value, name, "exec")
            info = zipfile.ZipInfo(ADDON + "/" + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, value.encode())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    return dict(file=output.name, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                version="1.0.1", native_sha256=native, original_host_checks_passed=10,
                physical_fold_verified=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("apk", "preservation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.apk, args.preservation, args.output), indent=2))
