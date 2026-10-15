"""Read installed code into an evidence archive; never import add-on code."""
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

CODE = {".py", ".pyi", ".pyx", ".pxd", ".c", ".cpp", ".h", ".hpp", ".js", ".sh"}
OPAQUE = {".so", ".pyd", ".dll", ".dylib", ".pyc", ".pyo", ".zip"}
EXCLUDED = {"userdata", "addon_data", "profile", "profiles", "cache", "database",
            "databases", "logs", ".git", "__pycache__"}
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 300 * 1024 * 1024


def safe_id(value):
    return bool(value) and all(c.isalnum() or c in "._-" for c in value)


def digest_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(addons, output, progress=None):
    report = {"schema": 1, "purpose": "installed add-on source evidence; no persistence acceptance",
              "device_accepted": False, "sources_stable": True, "addons": [], "errors": [],
              "excluded_directory_names": sorted(EXCLUDED), "contains_user_databases": False}
    total = 0
    verify = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, item in enumerate(addons):
            addon_id = item["id"]
            if progress:
                progress(index, len(addons), addon_id)
            if not safe_id(addon_id):
                report["errors"].append({"id": addon_id, "reason": "invalid_addon_id"})
                continue
            root = Path(item["path"])
            owner = {"id": addon_id, "version": item.get("version", "unknown"),
                     "files": [], "opaque_code": [], "dependencies": [], "excluded_links": []}
            report["addons"].append(owner)
            try:
                if root.is_symlink() or not root.is_dir():
                    raise ValueError("addon_root_unavailable_or_linked")
                manifest = root / "addon.xml"
                if manifest.is_symlink():
                    raise ValueError("linked_addon_manifest")
                metadata = ET.parse(manifest).getroot()
                if metadata.get("id") != addon_id:
                    raise ValueError("resolved_addon_identity_mismatch")
                owner["version"] = metadata.get("version", "unknown")
                owner["dependencies"] = [{"id": node.get("addon"), "minimum_version": node.get("version"),
                                           "optional": node.get("optional") == "true"}
                                          for node in metadata.findall("./requires/import")]
                for directory, dirs, names in os.walk(root, followlinks=False):
                    parent = Path(directory)
                    keep = []
                    for name in sorted(dirs):
                        path = parent / name
                        if path.is_symlink():
                            owner["excluded_links"].append(path.relative_to(root).as_posix())
                        elif name.lower() not in EXCLUDED:
                            keep.append(name)
                    dirs[:] = keep
                    for name in sorted(names):
                        path = parent / name
                        relative = path.relative_to(root).as_posix()
                        if path.is_symlink():
                            owner["excluded_links"].append(relative)
                            continue
                        code = path.suffix.lower() in CODE or relative == "addon.xml"
                        opaque = path.suffix.lower() in OPAQUE
                        if not (code or opaque):
                            continue
                        if path.stat().st_size > MAX_FILE:
                            report["errors"].append({"id": addon_id, "file": relative, "reason": "file_size_limit"})
                            continue
                        digest = digest_file(path)
                        if opaque:
                            owner["opaque_code"].append({"file": relative, "sha256": digest,
                                                         "source_not_exported": True})
                            verify.append((addon_id, relative, path, digest))
                            continue
                        data = path.read_bytes()
                        if hashlib.sha256(data).hexdigest() != digest:
                            raise ValueError("source_changed_during_read")
                        total += len(data)
                        if total > MAX_TOTAL:
                            raise ValueError("total_source_size_limit")
                        archive.writestr("addons/" + addon_id + "/" + relative, data)
                        owner["files"].append({"file": relative, "sha256": digest, "bytes": len(data)})
                        verify.append((addon_id, relative, path, digest))
            except (OSError, ValueError, ET.ParseError) as error:
                report["errors"].append({"id": addon_id, "reason": type(error).__name__,
                                         "detail": str(error) if isinstance(error, ValueError) else "source_read_failed"})
        for addon_id, relative, path, digest in verify:
            try:
                stable = not path.is_symlink() and digest_file(path) == digest
            except OSError:
                stable = False
            if not stable:
                report["sources_stable"] = False
                report["errors"].append({"id": addon_id, "file": relative, "reason": "source_changed_during_export"})
        report["exported_source_bytes"] = total
        archive.writestr("SOURCE-MANIFEST.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
