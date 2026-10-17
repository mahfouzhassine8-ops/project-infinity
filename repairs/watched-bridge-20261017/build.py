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
    assert manifest.get("id") == "script.infinity.watchedbridge" and manifest.get("version") == "1.0.0"
    assert manifest.find("./extension[@point='xbmc.service']").get("library") == "service.py"
    expected = json.loads((HERE.parent / "android-checkpoint-shutdown/installed/manifest.json").read_text())["script.infinity.commandcenter"]["after"]
    assert json.loads((source / "CONTROLLER-PREIMAGES.json").read_text()) == expected
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.iterdir()):
            if path.suffix not in (".py", ".json", ".xml"):
                continue
            data = path.read_bytes()
            if path.suffix == ".py":
                compile(data, path.name, "exec")
            info = zipfile.ZipInfo(manifest.get("id") + "/" + path.name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    return dict(file=output.name, bytes=output.stat().st_size, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                controller_replacement=False, profile_or_database_replacement=False,
                background_service="read-only, abort-aware, one-second metadata stat", physical_fold_verified=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
