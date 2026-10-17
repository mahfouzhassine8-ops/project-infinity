#!/usr/bin/env python3
"""Reproducible standalone Kodi helper package; no APK or skin changes."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ADDON_ID = "script.infinity.foldcapture"


def build(output):
    source = HERE / "helper" / ADDON_ID
    names = ("addon.xml", "capture.py", "default.py", "README.txt")
    manifest = ET.parse(source / "addon.xml").getroot()
    assert manifest.get("id") == ADDON_ID and manifest.get("version") == "1.0.0"
    assert not manifest.findall("./extension[@point='xbmc.service']")
    data = {name: (source / name).read_bytes() for name in names}
    for name in ("capture.py", "default.py"):
        compile(data[name], name, "exec")
    identity = {"schema": 1, "addon_id": ADDON_ID, "version": "1.0.0",
                "sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in data.items()},
                "native_apk_changed": False, "skin_changed": False,
                "background_service_added": False, "android_fold_verified": False}
    data["PACKAGE-IDENTITY.json"] = (json.dumps(identity, indent=2) + "\n").encode()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(data.items()):
            info = zipfile.ZipInfo(ADDON_ID + "/" + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(data)
        assert all(archive.read(ADDON_ID + "/" + name) == raw for name, raw in data.items())
    return {"file": output.name, "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "addon_id": ADDON_ID, "version": "1.0.0", "zip_crc": "PASS",
            "scope": "EXPERIMENTAL_DIAGNOSTIC_HELPER_ONLY", "is_anr_fix": False,
            "native_apk_changed": False, "skin_changed": False, "physical_fold_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = build(args.output)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
