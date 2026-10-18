#!/usr/bin/env python3
"""Build an additive Android Version Check correction from the exact signed APK.

No native observer exception, service disable, APK mutation or profile access.
The original import probes a Linux distribution on Android before run() checks
settings. Android must take its existing non-APT version-check path directly.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import zipfile

APK_SHA = '342587d9079f7e51b61ef525c04ae9b62adb6d128791164acbd99ec691fbac87'
ADDON = 'service.xbmc.versioncheck'
VERSION = '0.5.28+infinity.1'
ORIGINAL_VERSION = '0.5.27+matrix.1'
SERVICE = 'resources/lib/version_check/service.py'
SERVICE_SHA = '166a1f5974fd2f7c297f801dd36040b4e7d6ccf6655e2edfa335803f3bbc58d5'
MANIFEST_SHA = 'f1a3d4cc5e4339f385752038b1f655fdb03834d2ef2077ad9c62818ee9c13c4d'
ARCHIVE = ADDON + '-' + VERSION + '-Android-TEST.zip'
ARCHIVE_SHA = '58d8869b16f2c6f409887de1e6c05b86908d3d314c439d780a294e8ccb88fb88'
CANDIDATE_SERVICE_SHA = '6eb8ed9dd5d4712aacb44d55c3e006b1da5198c6bee076315579927c437bcfc1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, detail):
    if not ok:
        raise ValueError('Version Check Android candidate rejected: ' + detail)


def patch_service(data):
    require(sha(data) == SERVICE_SHA, 'unverified original service.py')
    old = b"if sys.platform.startswith('linux'):\r\n"
    new = (b"# Android uses the existing non-APT version-check path; do not launch\r\n"
           b"# desktop Linux distribution probes while importing this service.\r\n"
           b"if xbmc.getCondVisibility('System.Platform.Android'):\r\n"
           b"    DISTRIBUTION = 'android'\r\n"
           b"elif sys.platform.startswith('linux'):\r\n")
    require(data.count(old) == 1, 'ambiguous platform branch')
    return data.replace(old, new, 1)


def source_files(apk):
    apk = Path(apk)
    require(sha(apk.read_bytes()) == APK_SHA, 'different signed APK input')
    prefix = 'assets/addons/' + ADDON + '/'
    with zipfile.ZipFile(apk) as z:
        names = [n for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')]
        require(len(names) == len(set(names)) == 103, 'incomplete or duplicate add-on')
        files = {}
        for name in names:
            rel = name[len(prefix):]
            require(not PurePosixPath(rel).is_absolute() and '..' not in PurePosixPath(rel).parts
                    and '\\' not in rel, 'unsafe source path')
            files[rel] = z.read(name)
    require(sha(files[SERVICE]) == SERVICE_SHA, 'source service hash mismatch')
    require(sha(files['addon.xml']) == MANIFEST_SHA, 'source manifest hash mismatch')
    return files


def candidate_files(apk):
    original = source_files(apk)
    files = dict(original)
    files[SERVICE] = patch_service(files[SERVICE])
    old = ('version="' + ORIGINAL_VERSION + '"').encode()
    require(files['addon.xml'].count(old) == 1, 'ambiguous source version')
    files['addon.xml'] = files['addon.xml'].replace(old, ('version="' + VERSION + '"').encode(), 1)
    return original, files


def build(apk, out):
    original, files = candidate_files(apk)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    archive = out / ARCHIVE
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(ADDON + '/' + name, (2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, content)
    proof = {
        'addon': ADDON, 'version': VERSION, 'archive': ARCHIVE,
        'archive_sha256': sha(archive.read_bytes()), 'source_apk_sha256': APK_SHA,
        'source_service_sha256': SERVICE_SHA, 'service_sha256': sha(files[SERVICE]),
        'source_files': {n: sha(b) for n, b in sorted(original.items())},
        'candidate_files': {n: sha(b) for n, b in sorted(files.items())},
        'files_modified': [n for n in sorted(files) if files[n] != original[n]],
        'native_changes': False, 'apk_changes': False, 'settings_changes': False,
        'service_disabled': False, 'durability_exemption_added': False,
        'physical_fold_accepted': False, 'shutdown_verified': False,
    }
    require(proof['files_modified'] == ['addon.xml', SERVICE], 'unexpected asset changes')
    require(proof['archive_sha256'] == ARCHIVE_SHA and
            proof['service_sha256'] == CANDIDATE_SERVICE_SHA, 'non-reproducible candidate')
    (out / 'BUILD-VERSIONCHECK-ANDROID.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def stage(archive, destination):
    """Install only a verified package in disposable CI staging, never a profile."""
    archive, destination = Path(archive), Path(destination)
    proof = json.loads((archive.parent / 'BUILD-VERSIONCHECK-ANDROID.json').read_text())
    require(proof['addon'] == ADDON and proof['version'] == VERSION
            and proof['source_apk_sha256'] == APK_SHA
            and proof['source_service_sha256'] == SERVICE_SHA,
            'package source proof mismatch')
    require(sha(archive.read_bytes()) == proof['archive_sha256'] == ARCHIVE_SHA
            and proof['service_sha256'] == CANDIDATE_SERVICE_SHA, 'package hash mismatch')
    target = destination / ADDON
    require(not target.exists() and not target.is_symlink(),
            'refuse to overwrite an existing staged add-on')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        expected = {ADDON + '/' + n: digest for n, digest in proof['candidate_files'].items()}
        require(len(names) == len(expected) == 103 and set(names) == set(expected), 'package inventory mismatch')
        for name in names:
            require('..' not in PurePosixPath(name).parts and '\\' not in name
                    and not PurePosixPath(name).is_absolute(), 'unsafe package entry')
            require(sha(z.read(name)) == expected[name], 'modified package entry')
        manifest = ET.fromstring(z.read(ADDON + '/addon.xml'))
        require(manifest.get('id') == ADDON and manifest.get('version') == VERSION,
                'candidate manifest mismatch')
        z.extractall(destination)
    return {k: proof[k] for k in ('addon', 'version', 'archive_sha256', 'source_apk_sha256',
                                 'source_service_sha256', 'service_sha256', 'files_modified')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.apk, args.out)
    print(json.dumps({k: result[k] for k in ('archive', 'archive_sha256', 'service_sha256', 'files_modified')}))
