#!/usr/bin/env python3
"""Experimental 2103387 over EXACT signed 2103386: Version Check + version only.

No native engine, bytecode, player, persistence, WriteAdmission, skin, helper,
or crash-recorder change. Preserve every other original APK entry byte-for-byte.
Generate a matching add-on ZIP for explicit in-place addon upgrades if Kodi
does not automatically select the bundled newer version. NEVER claim Close
or the physical crash is fixed by signing an APK.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import zipfile

import versioncheck_android as service

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT_SHA = '342587d9079f7e51b61ef525c04ae9b62adb6d128791164acbd99ec691fbac87'
PARENT_CODE = 2103386
CODE = 2103387
PARENT_NAME = '1.0.9-UI-Restoration-Fold-TEST02'
NAME = '1.0.9-UI-Restoration-Fold-TEST03'
FILENAME = 'Infinity-2103387-UI-Restoration-TEST3.apk'
ENGINE = 'lib/arm64-v8a/libkodi.so'
ENGINE_SHA = '4b61414f05d67eb6df1f8a32f46d6b96c4991f91674401727d6ea4987f0d01af'
SOURCE_SERVICE_SHA = service.SERVICE_SHA
CANDIDATE_SERVICE_SHA = service.CANDIDATE_SERVICE_SHA
ADDON = service.ADDON
PREFIX = 'assets/addons/' + ADDON + '/'
MANIFEST = 'AndroidManifest.xml'
EXPECTED_DELTA = sorted((MANIFEST, PREFIX + 'addon.xml', PREFIX + service.SERVICE))


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    item = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(item)
    return item


signer = module('infinity_2103387_signer', ROOT / 'repairs/full-system-20261017/package_2103384_vfs.py')
patch = module('infinity_2103387_manifest', ROOT / 'repairs/critical-preview-2103376/manifest_patch.py')


def verify_archive(parent, candidate, patched_files, *, source_certified=False):
    with zipfile.ZipFile(parent) as original, zipfile.ZipFile(candidate) as built:
        original_unsigned = {n for n in original.namelist() if not signer.SIGNATURE.fullmatch(n)}
        built_unsigned = {n for n in built.namelist() if not signer.SIGNATURE.fullmatch(n)}
        assert len(original.namelist()) == len(set(original.namelist()))
        assert len(built.namelist()) == len(set(built.namelist()))
        assert original_unsigned == built_unsigned, 'Lost/additional APK payload entry'
        assert built.testzip() is None, 'Corrupted APK'
        changes = []
        for name in sorted(original_unsigned):
            if original.read(name) != built.read(name):
                changes.append(name)
            if name in patched_files:
                assert built.read(name) == patched_files[name], 'Patched file bytes do not match pinned candidate'
            elif name != MANIFEST:
                assert original.read(name) == built.read(name), 'Unreviewed byte change: ' + name
        assert changes == EXPECTED_DELTA, 'Unexpected APK change: ' + repr(changes)
        assert hashlib.sha256(built.read(ENGINE)).hexdigest() == ENGINE_SHA
        assert built.read('classes.dex') == original.read('classes.dex'), 'Java bytecode mutated'
        return changes


def build(parent, out, sign=False):
    parent = Path(parent)
    out = Path(out)
    assert not out.exists(), 'Refuse to reuse a stale output directory'
    assert digest(parent) == PARENT_SHA, 'Different signed APK 2103386 input'
    assert len(NAME) == len(PARENT_NAME), 'Manifest versionName must fit exactly'
    original_files, changed_files = service.candidate_files(parent)
    assert len(original_files) == len(changed_files) == 103
    assert sorted(n for n in original_files if original_files[n] != changed_files[n]) == [
        'addon.xml', service.SERVICE
    ], 'Unexpected Version Check change'
    assert hashlib.sha256(changed_files[service.SERVICE]).hexdigest() == CANDIDATE_SERVICE_SHA
    out.mkdir(parents=True)
    companion_proof = service.build(parent, out / 'versioncheck-companion')
    assert companion_proof['archive_sha256'] == service.ARCHIVE_SHA

    patch.PARENT_CODE = PARENT_CODE
    patch.CODE = CODE
    patch.PARENT_NAME = PARENT_NAME
    patch.NAME = NAME
    with zipfile.ZipFile(parent) as original:
        assert original.testzip() is None, 'Corrupted signed parent'
        assert hashlib.sha256(original.read(ENGINE)).hexdigest() == ENGINE_SHA
        binary_manifest, manifest_edits = patch.patch(original.read(MANIFEST))
        assert {e['field'] for e in manifest_edits} == {'versionCode', 'versionName'}
        patched = {MANIFEST: binary_manifest}
        for name in ('addon.xml', service.SERVICE):
            patched[PREFIX + name] = changed_files[name]
        unsigned = out / ('unsigned-' + FILENAME)
        with zipfile.ZipFile(unsigned, 'w') as target:
            for info in original.infolist():
                if signer.SIGNATURE.fullmatch(info.filename):
                    continue
                value = patched.get(info.filename)
                target.writestr(copy.copy(info),
                                value if value is not None else original.read(info))

    preflight_delta = verify_archive(parent, unsigned, patched)
    candidate = unsigned
    signing_receipt = None
    if sign:
        for key in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD',
                    'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
            assert os.environ.get(key), 'Permanent signing identity required: ' + key
        bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
        signer.verify_signed(parent, bt)
        candidate = out / FILENAME
        subprocess.run(['bash', str(ROOT / 'scripts/sign-infinity71.sh'),
                        str(unsigned), str(candidate)], check=True)
        signer.verify_signed(candidate, bt)
        signer.output(bt / 'zipalign', '-c', '-p', '4', candidate)
        badge = signer.output(bt / 'aapt', 'dump', 'badging', candidate)
        assert "package: name='com.projectinfinity.kodi' versionCode='2103387'" in badge
        assert "versionName='1.0.9-UI-Restoration-Fold-TEST03'" in badge
        assert 'application-debuggable' not in badge
        assert verify_archive(parent, candidate, patched) == preflight_delta
        unsigned.unlink()
        signing_receipt = signer.CERT

    receipt = {
        'file': candidate.name, 'sha256': digest(candidate),
        'parent_version_code': PARENT_CODE, 'parent_sha256': PARENT_SHA,
        'version_code': CODE, 'version_name': NAME,
        'permanently_signed': bool(sign), 'signer_sha256': signing_receipt,
        'changed_unsigned_payload': preflight_delta,
        'native_engine_sha256': ENGINE_SHA, 'native_engine_unchanged': True,
        'classes_dex_unchanged': True, 'native_close_policy_unchanged': True,
        'crash_recorder_unchanged': True,
        'service_id': ADDON, 'bundled_service_version': service.VERSION,
        'bundled_service_sha256': CANDIDATE_SERVICE_SHA,
        'companion_addon_archive': service.ARCHIVE,
        'companion_addon_sha256': service.ARCHIVE_SHA,
        'existing_user_addon_override_requires_runtime_check': True,
        'automatic_existing_addon_upgrade_proven': False,
        'skin_and_helper_unchanged': True,
        'shutdown_verified': False, 'physical_fold_verified': False,
        'crash_fixed': False, 'locked': False, 'test_candidate_only': True,
    }
    (out / ('SIGNED-2103387.json' if sign else 'UNSIGNED-2103387.json')).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + '\n'
    )
    print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sign', action='store_true')
    args = parser.parse_args()
    build(args.parent, args.out, args.sign)
