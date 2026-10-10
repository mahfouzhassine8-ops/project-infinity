#!/usr/bin/env python3
"""Build the deterministic, code-only Command Center participation asset."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
FILES = {"common.py", "default.py", "experience.py", "plugin.py", "resume_hub.py",
         "service.py", "checkpoint_runtime.py", "persistence_participant.py"}


def build():
    root = HERE / "runtime" / "commandcenter"
    delta = json.loads((root / "manifest.json").read_text())
    if set(delta["changed"]) != FILES:
        raise ValueError("Unexpected participant source scope")
    if delta["before"]["addon.xml"] != delta["after"]["addon.xml"]:
        raise ValueError("Participant overlay may not change add-on identity")
    manifest = {"schema": 1, "addon_id": "script.infinity.commandcenter",
                "addon_version": "0.3.5.19", "addon_xml_sha256": delta["before"]["addon.xml"],
                "files": [{"path": name, "before": delta["before"].get(name),
                           "after": delta["after"][name]} for name in sorted(FILES)]}
    green = json.loads((HERE / "resume-speed/GREEN-2103362.json").read_text())
    for entry in manifest['files']:
        entry['previous'] = green['commandcenter19'][entry['path']]
    entries = {"manifest.json": (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()}
    for name in sorted(FILES):
        data = (root / "overlay" / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != delta["after"][name]:
            raise ValueError("Participant payload hash mismatch: " + name)
        entries["payload/" + name] = data
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(entries.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--android-source", type=Path,
                        help="Verify the runtime installer pins the exact generated asset")
    args = parser.parse_args()
    data = build()
    digest = hashlib.sha256(data).hexdigest()
    if args.android_source:
        installer = args.android_source / "tools/android/packaging/xbmc/src/InfinityCheckpointAddonInstaller.java.in"
        if 'ASSET_SHA256 = "' + digest + '"' not in installer.read_text():
            raise ValueError("Installer/participant asset association mismatch")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(json.dumps({"asset": str(args.output), "sha256": digest, "bytes": len(data),
                      "user_data_included": False, "skin_changed": False}))


if __name__ == "__main__":
    main()
