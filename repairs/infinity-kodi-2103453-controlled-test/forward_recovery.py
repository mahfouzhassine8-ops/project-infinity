"""Unsigned forward-recovery rehearsal. No signing, installation or data access."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile

from inventory import SIGNATURE, canonical, digest, file_sha, save, validate_names
from component_bundles import record, set_version
from release_gate import component_digest, normalize_manifest, require
from release_authority import transition, verify

NATIVE = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
PARENT_NATIVE = 'f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674'


def labels(version):
    return f'infinity.last_updated_in={version}\ncobra.last_updated_in=2103445\n'.encode()


def forward_authority(prior, payload, version, source, components=None):
    require(version > prior['candidate_versionCode'], 'RECOVERY_MUST_ADVANCE_VERSION')
    result = copy.deepcopy(prior)
    result.update(generation=prior['generation'] + 1,
                  last_issued_versionCode=prior['candidate_versionCode'], candidate_versionCode=version,
                  target_owners=['INFINITY','CHOOSER_SHELL'], update_kind='owner_update',
                  previous_authority_sha256=digest(canonical(prior)), payload=payload,
                  experience_version_labels={'INFINITY':version, 'COBRA':2103445})
    for owner in ('INFINITY','CHOOSER_SHELL'):
        row = result['components'][owner]
        row.update(revision=prior['components'][owner]['revision'] + 1,
                   version=f'{version}.{owner.lower()}.recovery-rehearsal',
                   digest=component_digest(payload, owner), approved_source=source)
        if components:
            row.update({k:components[owner][k] for k in ('version','digest','approved_source','settings_schema')})
    transition(prior, result, ['INFINITY','CHOOSER_SHELL'])
    verify(result, {k:v['sha256'] for k,v in payload.items()}, version, result['generation'])
    return result


def build_unsigned_recovery(baseline, out, version, installed_version):
    require(version > installed_version, 'RECOVERY_MUST_ADVANCE_VERSION')
    require(not out.exists(), 'FRESH_RECOVERY_OUTPUT')
    with ZipFile(baseline) as src, ZipFile(out, 'w') as dst:
        for name in sorted(set(validate_names(src)) - SIGNATURE):
            info = src.getinfo(name)
            entry = record(name)
            entry.compress_type, entry.external_attr = info.compress_type, info.external_attr
            with dst.open(entry, 'w', force_zip64=info.file_size >= 2**31) as target:
                if name == 'AndroidManifest.xml': target.write(set_version(src.read(name), version))
                elif name == LABEL: target.write(labels(version))
                else:
                    with src.open(name) as original: shutil.copyfileobj(original, target, 4*1024*1024)


def verify_recovery(baseline, candidate, prior, catalog, bundles, source, out):
    out.mkdir(exist_ok=False)
    version = 2103454  # Rehearsal only; recheck the next unused version before future signing.
    recovery = out / 'UNSIGNED-RECOVERY-REHEARSAL.apk'
    build_unsigned_recovery(baseline, recovery, version, 2103453)
    comparisons = {}
    with ZipFile(baseline) as old, ZipFile(candidate) as test, ZipFile(recovery) as new:
        names = set(validate_names(old)) - SIGNATURE
        require(names == set(validate_names(new)) - SIGNATURE, 'RECOVERY_EXACT_MEMBER_SET')
        require(normalize_manifest(new.read('AndroidManifest.xml')) ==
                (normalize_manifest(old.read('AndroidManifest.xml'))[0], version), 'RECOVERY_VERSION_ONLY_MANIFEST')
        require(normalize_manifest(test.read('AndroidManifest.xml'))[1] == 2103453, 'EXACT_TEST_VERSION')
        require(new.read(LABEL) == labels(version), 'RECOVERY_TRUTHFUL_METADATA')
        for name in sorted(names):
            with old.open(name) as stream: a = hashlib.file_digest(stream,'sha256').hexdigest()
            with new.open(name) as stream: b = hashlib.file_digest(stream,'sha256').hexdigest()
            comparisons[name] = {'before452':a,'recovery':b}
        differences = {n for n,r in comparisons.items() if r['before452'] != r['recovery']}
        require(differences == {'AndroidManifest.xml',LABEL}, 'RECOVERY_RESTORES_EXACT452_PAYLOAD')
        require(comparisons[NATIVE]['recovery'] == PARENT_NATIVE, 'RECOVERY_EXACT452_ENGINE')
        require(new.testzip() is None, 'RECOVERY_ZIP_CRC')

    metas = {}
    for owner, row in catalog['bundles'].items():
        with ZipFile(bundles / row['file']) as z: metas[owner] = json.loads(z.read('component.json'))
    current_payload = {k:v for m in metas.values() for k,v in m['payload'].items()}
    current = forward_authority(prior, current_payload, 2103453, source, metas)
    restored = copy.deepcopy(prior['payload'])
    restored['member:' + LABEL]['sha256'] = digest(labels(version))
    proposed = forward_authority(current, restored, version, source)
    require(proposed['protected_contract'] == prior['protected_contract'] and
            proposed['accepted_registry_sha256'] == prior['accepted_registry_sha256'] and
            proposed['accepted_pointer_updated'] is False, 'RECOVERY_PROTECTIONS_UNCHANGED')
    require(all(proposed['components'][o]['settings_schema'] == prior['components'][o]['settings_schema']
                for o in proposed['components']), 'RECOVERY_DATA_SCHEMA_CHANGED')
    save(out / 'ALL-RECOVERY-MEMBER-HASHES.json', comparisons)
    result = dict(status='PASS_UNSIGNED_FORWARD_RECOVERY_REHEARSAL',
        baseline_apk_sha256=file_sha(baseline), candidate_unsigned_sha256=file_sha(candidate),
        recovery_unsigned_sha256=file_sha(recovery), recovery_version_rehearsed=version,
        installed_candidate_version=2103453, restored_native_sha256=PARENT_NATIVE,
        changed_members_from452=sorted(differences), preserved_payload_members=len(names)-2,
        data_schema_unchanged=True, actual_original_authority_transition_passed=True,
        source=source, accepted_pointer_updated=False, signed_recovery_available=False,
        signed_or_installed=False, user_data_accessed=False, Android_tested=False,
        future_signing='Separate explicit recovery authorization; recheck next unused higher version, official preparation, owner/source gates and original signer.',
        limits='Unsigned package/authority rehearsal only. Cannot recover unsaved in-memory writes. Never install during unresolved persistence or force termination.')
    save(out / 'FORWARD-RECOVERY-VERIFIED.json', result)
    recovery.unlink()  # Keep receipts, not an unsigned APK that could be mistaken for a deliverable.
    return dict(status=result['status'], evidence_sha256=file_sha(out/'FORWARD-RECOVERY-VERIFIED.json'),
                data_schema_unchanged=True, signed_recovery_available=False,
                recovery_version_rehearsed=version, restored_native_sha256=PARENT_NATIVE)
