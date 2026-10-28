"""Verify final signed APK against actual baseline and selected owner ZIP bytes.

Packaging only: no device launch, user data access or behavioral shutdown test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from prepare_release import REPO, ISOLATION, command, load, require, sha
HERE = Path(__file__).resolve().parent
from inventory import file_sha, canonical, digest, SIGNATURE, save, validate_names, CERT_SHA
from release_gate import normalize_manifest
from component_bundles import read_bundle


def verify(baseline, signed, bundles, sdk):
    permission = load(HERE / 'RELEASE-AUTHORIZATION.json')
    scope = load(HERE / 'SCOPE.json')
    receipt = load(signed / 'BUILD-RECEIPT.json')
    authority = load(signed / 'release-authority.json')
    require(authority == load(ISOLATION / 'release-authority.json'), 'EXACT_AUTHORITY')
    require(receipt['registry_sha256'] == digest(canonical(authority)), 'AUTHORITY_BINDING')
    require(receipt['versionCode'] == 2103427 and receipt['source'] == os.environ.get('GITHUB_SHA', receipt['source']), 'SOURCE_VERSION')
    require(file_sha(baseline) == scope['input_apk_sha256'], 'EXACT_BASELINE')
    apk = signed / 'Infinity-2103427-Combined-Original-Signer.apk'
    require(file_sha(apk) == receipt['signed_apk_sha256'], 'SIGNED_HASH')
    signature = command([sdk / 'apksigner', 'verify', '--verbose', '--print-certs', apk])
    require(re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT_SHA], 'ORIGINAL_CERTIFICATE')
    for scheme in ('v1', 'v2', 'v3'):
        require(re.search('Verified using ' + scheme + r' scheme.*: true', signature) is not None, 'SIGNATURE:' + scheme)
    command([sdk / 'zipalign', '-c', '-P', '16', '4', apk])
    plan = load(HERE / 'SOURCE-PLAN.json')
    changes = set(plan) | {'assets/addons/script.infinity.commandcenter/INFINITY-MODULES.v1.sig', permission['metadata_member']}
    observed, native, dex = set(), {}, {}
    with ZipFile(baseline) as old, ZipFile(apk) as new:
        require(set(validate_names(old)) - SIGNATURE == set(validate_names(new)) - SIGNATURE, 'EXACT_APK_MEMBER_SET')
        old_manifest, old_version = normalize_manifest(old.read('AndroidManifest.xml'))
        require(normalize_manifest(new.read('AndroidManifest.xml')) == (old_manifest, 2103427) and old_version == 2103426, 'MANIFEST_VERSION_ONLY')
        for name in sorted(set(new.namelist()) - SIGNATURE - {'AndroidManifest.xml'}):
            with old.open(name) as before, new.open(name) as after:
                a, b = hashlib.file_digest(before, 'sha256').hexdigest(), hashlib.file_digest(after, 'sha256').hexdigest()
            if a != b:
                require(name in changes, 'FROZEN_APK_MEMBER:' + name)
                observed.add(name)
            if name.endswith('.so'): native[name] = b
            if re.fullmatch(r'classes\d*\.dex', name): dex[name] = b
        require(observed == changes, 'EXACT_CHANGED_MEMBER_SET')
        for name, row in plan.items():
            require(sha(new.read(name)) == row['after'] and sha(old.read(name)) == row['before'], 'EXACT_PRODUCTION_SOURCE:' + name)
        require(new.read(permission['metadata_member']) == permission['metadata_after'].encode(), 'EXACT_METADATA_EXCEPTION')
        catalog = authority['bundle_catalog']
        bundle_dex, component_sha = set(), {}
        for owner, row in catalog['bundles'].items():
            meta = read_bundle(bundles / row['file'], row)
            component_sha[row['file']] = row['sha256']
            with ZipFile(bundles / row['file']) as bundle:
                for name in meta['members']:
                    a, b = bundle.read('payload/' + name), new.read(name)
                    if name == 'AndroidManifest.xml': a, b = normalize_manifest(a)[0], normalize_manifest(b)[0]
                    require(a == b, 'COMPONENT_APK_MISMATCH:' + name)
                bundle_dex.update(meta['dex'].values())
        require(set(dex.values()) == bundle_dex and len(dex) == len(bundle_dex), 'EXACT_COMPONENT_DEX')
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            for leaf in ('INFINITY-MODULES.v1', 'INFINITY-MODULES.v1.sig'):
                (temp / leaf).write_bytes(new.read('assets/addons/script.infinity.commandcenter/' + leaf))
            require(file_sha(temp / 'INFINITY-MODULES.v1') == permission['module_manifest_sha256'], 'EXACT_SIGNED_SOURCE_MANIFEST')
            command(['openssl', 'dgst', '-sha256', '-verify',
                     REPO / 'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                     '-signature', temp / 'INFINITY-MODULES.v1.sig', temp / 'INFINITY-MODULES.v1'])
    original = json.loads(subprocess.check_output(['git', 'show', load(HERE.parent / 'SCOPE.json')['baseline_source'] + ':repairs/dual-experience-isolation-2103420/release-authority.json']))
    for owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        require(authority['bundle_catalog']['bundles'][owner] == original['bundle_catalog']['bundles'][owner], 'FROZEN_OWNER_ZIP:' + owner)
    require(authority['protected_contract'] == original['protected_contract'], 'FROZEN_PROTECTED_CONTRACT')
    report = dict(status='SIGNED_INSTALL_OVER_CANDIDATE_VERIFIED', versionCode=2103427,
        source=receipt['source'], build_run=os.environ.get('GITHUB_RUN_ID'),
        package='com.projectinfinity.kodi', certificate_sha256=CERT_SHA,
        signature_schemes=['v1', 'v2', 'v3'], apk_sha256=file_sha(apk), apk_bytes=apk.stat().st_size,
        component_sha256=component_sha, changed_APK_members=sorted(observed),
        manifest_change='versionCode only', unchanged_native_libraries=len(native), unchanged_DEX_files=len(dex),
        Cobra='EXACT_ORIGINAL_COMPONENT_ZIP', shared_contract='EXACT_ORIGINAL_COMPONENT_ZIP',
        chooser='EXACT_CODE_RESOURCES_ONLY_AUTHORIZED_METADATA_DIFF',
        shutdown_sources_and_binaries='BYTE_IDENTICAL', shutdown_tests='NOT_RUN',
        actual_device_install='NOT_RUN', physical_Fold='USER_ACCEPTANCE_PENDING', accepted_pointer_updated=False)
    save(signed / 'DELIVERY-VERIFICATION.json', report)
    (bundles / 'SHA256SUMS').write_text(''.join(pin + '  ' + name + '\n' for name, pin in sorted(component_sha.items())))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('baseline', 'signed', 'bundles', 'sdk'): p.add_argument('--' + name, type=Path, required=True)
    verify(**vars(p.parse_args()))
