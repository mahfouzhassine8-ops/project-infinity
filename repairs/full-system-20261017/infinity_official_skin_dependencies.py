#!/usr/bin/env python3
"""Stage official Kodi Omega *skin dependencies* for the real Infinity APK.

The products under test remain the permanently signed Infinity Android APK,
the exact full skin.infinity.diggz 1.0.5.225 ZIP, and Rails helper 0.2.6.
These packages are dependency data, NOT a replacement stock Kodi app.
Official repository packages are not proof of the user's exact Fold addon
versions or full Diggz environment.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

REQUIRED = {
    "script.skinshortcuts": "2.0.3",
    "resource.images.studios.white": "0.0.34",
    "resource.images.recordlabels.white": "0.0.7",
}
BASE = "https://mirrors.kodi.tv/addons/omega"
MAX_PACKAGE_BYTES = 36 * 1024 * 1024
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_EXTRACTED_BYTES = 350 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError("Infinity skin dependency rejected: " + message)


def hashfile(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as src:
        for piece in iter(lambda: src.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def validate_manifest(directory, ident, version):
    manifest = Path(directory) / "addon.xml"
    require(manifest.is_file(), "Missing actual addon.xml: " + ident)
    root = ET.parse(manifest).getroot()
    require(root.tag == "addon" and root.get("id") == ident and
            root.get("version") == version, "Unexpected manifest identity: " + ident)
    return hashfile(manifest)


def package(addon, version, destination):
    path = destination / addon
    if path.exists():
        require(path.is_dir() and not path.is_symlink(),
                "Preexisting skin dependency is not an addon directory: " + addon)
        manifest_hash = validate_manifest(path, addon, version)
        return {"id": addon, "version": version, "origin": "authenticated provided bundle",
                "manifest_sha256": manifest_hash, "addon_zip_sha256": None,
                "exact_fold_installation_verified": False}

    url = f"{BASE}/{addon}/{addon}-{version}.zip"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Infinity-Android-CI/1.0"}),
        timeout=75
    ) as stream:
        raw = stream.read(MAX_PACKAGE_BYTES + 1)
    require(0 < len(raw) <= MAX_PACKAGE_BYTES, "Missing or oversized official dependency " + addon)
    digest = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        require(infos and archive.testzip() is None, "Corrupt official dependency ZIP")
        require(len(infos) == len({v.filename for v in infos}), "Duplicate entries")
        total = 0
        for entry in infos:
            name = entry.filename
            parts = PurePosixPath(name).parts
            require(bool(parts) and parts[0] == addon and
                    not name.startswith("/") and "\\" not in name and
                    ".." not in parts, "Wrong or unsafe ZIP root: " + name)
            require(not stat.S_ISLNK((entry.external_attr >> 16) & 0xffff),
                    "Symbolic link in add-on ZIP")
            require(entry.file_size < MAX_FILE_BYTES, "Oversized dependency member")
            total += entry.file_size
            require(total <= MAX_EXTRACTED_BYTES, "Dependency decompression size exceeded")
        path.mkdir()
        for entry in infos:
            if entry.is_dir():
                continue
            parts = PurePosixPath(entry.filename).parts
            f = destination.joinpath(*parts)
            require(f.resolve().is_relative_to(path.resolve()), "ZIP traversal")
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(archive.read(entry))
    manifest_hash = validate_manifest(path, addon, version)
    return {"id": addon, "version": version, "origin": url,
            "source": "official Kodi Omega addon mirror, only as Infinity skin dependency",
            "addon_zip_sha256": digest, "manifest_sha256": manifest_hash,
            "exact_fold_installation_verified": False}


def stage(additional, output):
    additional = Path(additional)
    additional.mkdir(parents=True, exist_ok=True)
    record = {
        "product_under_test": "Infinity",
        "stock_kodi_application_installed": False,
        "dependency_sources_are_not_full_diggz_or_fold_proof": True,
        "addons": {}
    }
    for addon, version in REQUIRED.items():
        record["addons"][addon] = package(addon, version, additional)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--additional", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    stage(args.additional, args.out)
