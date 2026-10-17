#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent


def build(output):
    source = HERE / "addon"
    manifest = ET.parse(source / "addon.xml").getroot()
    assert manifest.get("id") == "script.infinity.addonrecovery"
    assert not manifest.findall("./extension[@point='xbmc.service']")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("addon.xml", "default.py", "recovery.py"):
            data = (source / name).read_bytes()
            if name.endswith(".py"):
                compile(data, name, "exec")
            info = zipfile.ZipInfo("script.infinity.addonrecovery/" + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    return dict(file=output.name, bytes=output.stat().st_size,
                sha256=hashlib.sha256(output.read_bytes()).hexdigest(), addon_id=manifest.get("id"),
                version=manifest.get("version"), background_service=False, physical_fold_verified=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
