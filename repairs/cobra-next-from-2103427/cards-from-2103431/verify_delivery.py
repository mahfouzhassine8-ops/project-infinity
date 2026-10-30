"""Verify one original-key 432 install-over APK and its exact owner ZIPs.

No application execution, installation, acceptance update or shutdown test.
ZIP page alignment is checked separately from frozen native ELF compatibility.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ISO = REPO / 'repairs/dual-experience-isolation-2103420'
sys.path.insert(0, str(ISO))
from inventory import CERT_SHA, PACKAGE, SIGNATURE, canonical, digest, file_sha, load, save, validate_names
from component_bundles import read_bundle
from release_gate import normalize_manifest, require
from release_authority import launcher_icon_guard, transition
from register_release import BASE_SOURCE, FROZEN, GENERATION, METADATA, TARGETS, VERSION, validate_payload


def run(args):
    return subprocess.check_output(list(map(str, args)), text=True)


def member_sha(archive, name):
    with archive.open(name) as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(baseline, signed, bundles, sdk):
    recovery = load(HERE / 'BASELINE.json')
    authority = load(signed / 'release-authority.json')
    receipt = load(signed / 'BUILD-RECEIPT.json')
    previous = json.loads(run(['git', '-C', REPO, 'show', BASE_SOURCE +
        ':repairs/dual-experience-isolation-2103420/release-authority.json']))
    require(authority == load(ISO / 'release-authority.json'), 'EXACT_CURRENT_AUTHORITY')
    require(authority['generation'] == GENERATION and authority['candidate_versionCode'] == VERSION and
            set(authority['target_owners']) == set(TARGETS), 'EXACT432_OWNER_AUTHORITY')
    transition(previous, authority, TARGETS)
    require(receipt['registry_sha256'] == digest(canonical(authority)), 'AUTHORITY_RECEIPT_BINDING')
    require(receipt['versionCode'] == VERSION and receipt['source'] == os.environ.get('GITHUB_SHA', receipt['source']),
            'SIGNING_SOURCE_AND_VERSION')
    require(receipt['accepted_pointer_updated'] is False, 'NO_AUTOMATIC_ACCEPTANCE')
    require(file_sha(baseline) == recovery['APK_sha256'] and baseline.stat().st_size == recovery['APK_bytes'],
            'EXACT_ACCEPTED431_APK')
    apk = signed / ('Infinity-' + str(VERSION) + '-Combined-Original-Signer.apk')
    require(file_sha(apk) == receipt['signed_apk_sha256'], 'SIGNED_APK_HASH')
    for path, leaf in ((baseline, 'ACCEPTED431-ORIGINAL-SIGNATURE.txt'), (apk, 'ORIGINAL-SIGNATURE.txt')):
        signature = run([sdk / 'apksigner', 'verify', '--verbose', '--print-certs', path])
        (signed / leaf).write_text(signature)
        require(re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT_SHA],
                'ORIGINAL_CERTIFICATE:' + path.name)
        for scheme in ('v1', 'v2', 'v3'):
            require(re.search('Verified using ' + scheme + r' scheme.*: true', signature) is not None,
                    'SIGNATURE_SCHEME:' + scheme)
    run([sdk / 'zipalign', '-c', '-P', '16', '4', apk])
    catalog = load(bundles / 'catalog.json')
    require(catalog == authority['bundle_catalog'], 'EXACT_MATCHING_COMPONENT_CATALOG')
    payload, metas, changed_payload, added_payload = validate_payload(previous, catalog, bundles)
    require(payload == authority['payload'], 'EXACT_AUTHORITY_COMPONENT_PAYLOAD')
    for owner in FROZEN:
        row = catalog['bundles'][owner]
        require(row['sha256'] == recovery['component_sha256'][row['file']], 'EXACT431_FROZEN_ZIP:' + owner)
    component_sha = {row['file']: file_sha(bundles / row['file']) for row in catalog['bundles'].values()}
    expected_members, expected_dex = {}, {}
    dex_index = 0
    for owner in ('CHOOSER_SHELL', 'MINIMAL_ANDROID_CONTRACT', 'INFINITY', 'COBRA'):
        meta = metas[owner]
        for name in meta['members']:
            require(name not in expected_members, 'DUPLICATE_COMPONENT_MEMBER')
            expected_members[name] = owner
        for name, pin in sorted(meta['dex'].items()):
            dex_index += 1
            expected_dex['classes' + (str(dex_index) if dex_index > 1 else '') + '.dex'] = (owner, pin)
    changed_members, native = set(), {}
    with ZipFile(baseline) as old, ZipFile(apk) as new:
        old_names = set(validate_names(old)) - SIGNATURE
        new_names = set(validate_names(new)) - SIGNATURE
        require(new_names == set(expected_members) | set(expected_dex), 'EXACT_DECLARED_APK_MEMBER_SET')
        require(old_names - {n for n in old_names if re.fullmatch(r'classes\d*\.dex', n)} == set(expected_members),
                'NO_RESOURCE_OR_NATIVE_MEMBER_ADDITION_REMOVAL')
        normalized, old_version = normalize_manifest(old.read('AndroidManifest.xml'))
        require(old_version == 2103431 and normalize_manifest(new.read('AndroidManifest.xml')) == (normalized, VERSION),
                'MANIFEST_TYPED_VERSION_ONLY')
        for name in sorted(new_names - {'AndroidManifest.xml'}):
            after = member_sha(new, name)
            if name in expected_dex:
                owner, pin = expected_dex[name]
                require(after == pin, 'COMPONENT_APK_DEX_MISMATCH:' + name)
                if owner != 'COBRA':
                    require(name in old_names and member_sha(old, name) == after, 'FROZEN_OWNER_APK_DEX:' + owner)
            elif name == METADATA:
                require(new.read(name) == b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103432\n',
                        'GENUINE_COMPONENT_LABELS')
            else:
                require(name in old_names and member_sha(old, name) == after, 'FROZEN_APK_MEMBER:' + name)
            if name not in old_names or member_sha(old, name) != after:
                changed_members.add(name)
            if name.endswith('.so'):
                native[name] = after
        require(METADATA in changed_members and any(expected_dex.get(n, (None,))[0] == 'COBRA'
                for n in changed_members), 'CARDS_OWNER_AND_VERSION_BOTH_PRESENT')
        for owner, meta in metas.items():
            with ZipFile(bundles / catalog['bundles'][owner]['file']) as bundle:
                for name in meta['members']:
                    a, b = bundle.read('payload/' + name), new.read(name)
                    if name == 'AndroidManifest.xml':
                        a, b = normalize_manifest(a)[0], normalize_manifest(b)[0]
                    require(a == b, 'COMPONENT_APK_MEMBER_MISMATCH:' + name)
        # Preserve authenticated first-party Infinity bytes and verify the same
        # detached original-key module signature independently of APK signing.
        with tempfile.TemporaryDirectory(prefix='infinity432-module-verification-') as temporary:
            temp = Path(temporary)
            for leaf in ('INFINITY-MODULES.v1', 'INFINITY-MODULES.v1.sig'):
                name = 'assets/addons/script.infinity.commandcenter/' + leaf
                require(old.read(name) == new.read(name), 'FROZEN_AUTHENTICATED_INFINITY')
                (temp / leaf).write_bytes(new.read(name))
            run(['openssl', 'dgst', '-sha256', '-verify',
                REPO / 'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                '-signature', temp / 'INFINITY-MODULES.v1.sig', temp / 'INFINITY-MODULES.v1'])
    icon_proof = launcher_icon_guard().verify_actual_apk(apk, authority)
    require(authority['launcher_icon_exception'] == previous['launcher_icon_exception'], 'FROZEN_APPROVED_ICON_EXCEPTION')
    require(authority['protected_contract'] == previous['protected_contract'], 'FROZEN_PROTECTED_CONTRACT')
    report = dict(status='SIGNED432_INSTALL_OVER_OWNER_COMPONENTS_VERIFIED', versionCode=VERSION,
        signing_source=receipt['source'], producer_source=authority['owner_update_evidence']['producer_source'],
        producer_run=authority['owner_update_evidence']['producer_run'], build_run=os.environ.get('GITHUB_RUN_ID'),
        package=PACKAGE, certificate_sha256=CERT_SHA, signature_schemes=['v1', 'v2', 'v3'],
        apk_sha256=file_sha(apk), apk_bytes=apk.stat().st_size, component_sha256=component_sha,
        recovery_versionCode=2103431, recovery_source=BASE_SOURCE, recovery_APK_sha256=recovery['APK_sha256'],
        changed_APK_members=sorted(changed_members), changed_existing_payload=sorted(changed_payload),
        added_Cobra_helpers=sorted(added_payload), manifest_change='Typed versionCode only',
        Infinity='EXACT_ACCEPTED431_ZIP; Infinity implementation remains2103427',
        minimal_Android_native_and_icons='EXACT_ACCEPTED431_ZIP', chooser='EXACT431_DEX_UI; Cobra last-updated metadata only',
        unchanged_native_libraries=len(native), launcher_icons=icon_proof,
        zip_alignment='PASS zipalign -P16; does not establish ELF segment compatibility',
        native_ELF_compatibility='UNCHANGED431; no native patch or new ELF compatibility claim',
        protected_contract='EXACT431', shutdown_tests='NOT_RUN', actual_device_install='NOT_RUN',
        physical_Fold='USER_ACCEPTANCE_PENDING', accepted_pointer_updated=False, lock_promoted=False)
    save(signed / 'DELIVERY-VERIFICATION.json', report)
    (signed / 'SHA256SUMS').write_text(file_sha(apk) + '  ' + apk.name + '\n')
    (bundles / 'SHA256SUMS').write_text(''.join(pin + '  ' + name + '\n' for name, pin in sorted(component_sha.items())))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'signed', 'bundles', 'sdk'):
        parser.add_argument('--' + name, type=Path, required=True)
    verify(**vars(parser.parse_args()))
