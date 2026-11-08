"""Read-only official-input review and existing owner-authority proposals.

The original release_gate and assemble.sign remain the only APK signer path.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ISO = ROOT / 'repairs/dual-experience-isolation-2103420'
sys.path[:0] = [str(ISO), str(HERE)]
from inventory import canonical, digest, file_sha, load, save, SIGNATURE, validate_names
from component_bundles import read_bundle
from release_gate import require, normalize_manifest
from release_authority import AUTHORITY_PATH, transition, verify_evidence
from prepare_three import BASE_APK, NEW_NATIVE, BASE_NATIVE, CC, TRAKT

RUN = 42460784588
PRODUCER = 'ec4d011e1dfd0bec7949e8b442dbde5ee42deabf'
ARTIFACTS = {
    2103466: dict(id=13609546660, digest='sha256:9c27d2cf7a7a9e75f047a2d3204b327b7e024fa7df4f4d2523ee81d1f63d908f', size_in_bytes=320620369),
    2103467: dict(id=13608819053, digest='sha256:62e6344da6e3903d36ee665b7ec841aad66b4721dd101cbc279381b577749b9b', size_in_bytes=320613005),
}
TARGETS = ['INFINITY', 'CHOOSER_SHELL']
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def command(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def gh(path):
    return json.loads(command('gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path))


def bindings():
    paths = list(HERE.glob('*.py')) + [HERE / n for n in ('PACKAGING-SCOPE.json', 'INSTALLED-SOURCE-CHECKS.json', 'RELEASE-REQUEST.json',
                                                       'evidence/DEVICE-SOURCE-VERIFICATION.json', 'evidence/MODULE-UPGRADE-RECOVERY.json',
                                                       'evidence/ARM64-LINK-VERIFIED.json', 'inputs/Infinity_Source_Exports_For_Work.zip')]
    paths += [ROOT / 'repairs/infinity-final-closure-2103407' / n for n in ('SignInfinityModules.java', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem', 'module_bundle.py', 'module_dex.py', 'InfinityInstalledModules.java.in')]
    return {p.relative_to(ROOT).as_posix(): file_sha(p) for p in paths}


def official(prepared, version):
    require(version in ARTIFACTS, 'EXACT_SELECTED_FORWARD_PAIR')
    run = gh('actions/runs/' + str(RUN))
    require(run['conclusion'] == 'success' and run['status'] == 'completed' and run['head_sha'] == PRODUCER and
            run['head_branch'] == 'work/infinity-three-corrections-20261108' and run['workflow_id'] == 397702717, 'OFFICIAL_ORIGINAL_WORKFLOW_PREPARATION')
    row = next(r for r in gh('actions/runs/' + str(RUN) + '/artifacts?per_page=100')['artifacts'] if r['id'] == ARTIFACTS[version]['id'])
    require(not row['expired'] and all(row[k] == v for k, v in ARTIFACTS[version].items()), 'EXACT_PREPARED_ARTIFACT')
    archive = prepared.parent / (str(row['id']) + '.zip')
    require(archive.is_file() and file_sha(archive) == row['digest'].removeprefix('sha256:'), 'PREPARED_ARCHIVE_DIGEST')
    with ZipFile(archive) as z:
        names = {n for n in validate_names(z) if not n.endswith('/')}
        require(names == {p.relative_to(prepared).as_posix() for p in prepared.rglob('*') if p.is_file()}, 'EXACT_PREPARED_FILE_SET')
        for name in names:
            with z.open(name) as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == file_sha(prepared / name), 'PREPARED_MEMBER:' + name)
    proof = load(prepared / 'PREPARATION.json')
    require(proof['source'] == PRODUCER and proof['run_id'] == RUN and proof['versionCode'] == version and proof['baseline_sha256'] == BASE_APK, 'PREPARED_SOURCE_BINDING')
    require(proof['status'] == 'PASS_EXACT464_THREE_CORRECTIONS_OR_FORWARD_RECOVERY' and proof['native_sha256'] == (NEW_NATIVE if version == 2103466 else BASE_NATIVE), 'PREPARED_NATIVE_AND_SOURCE_PASS')
    for name in ('prepare_three.py', 'verify_device_sources.py', 'verify_module_pair.py', 'PACKAGING-SCOPE.json'):
        path = (HERE / name).relative_to(ROOT).as_posix()
        require((ROOT / path).read_bytes() == subprocess.check_output(['git', 'show', PRODUCER + ':' + path]), 'UNCHANGED_OFFICIAL_PRODUCER:' + name)
    return row


def proposed(prepared, version, audit, previous=None):
    row = official(prepared, version)
    proof = load(prepared / 'PREPARATION.json')
    previous = previous or load(ROOT / AUTHORITY_PATH)
    require(previous['candidate_versionCode'] == version - 1 and previous['generation'] == (52 if version == 2103466 else 53), 'EXACT_AUTHORITY_PREDECESSOR')
    check = load(audit)
    require(check['status'] == 'PASS_TEN_REAL_JAVA79_FILE_UPGRADE_AND_FORWARD_RECOVERY_CASES' and len(check['cases']) == 10 and check['original_installer_changed'] is False, 'REAL_UNCHANGED_INSTALLER_PASS_REQUIRED')
    catalog = load(prepared / 'components/catalog.json')
    metas = {o: read_bundle(prepared / 'components' / r['file'], r) for o, r in catalog['bundles'].items()}
    for owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        require(catalog['bundles'][owner] == previous['bundle_catalog']['bundles'][owner], 'PROTECTED_OWNER:' + owner)
    for name, wanted in previous['source_files'].items():
        if name == 'repairs/dual-experience-isolation-2103420/signer-policy.json':
            wanted = '668be3057893450fb53c2c3d506723de16de45abe46c0034a0ba81234c1fc06b'
        require(file_sha(ROOT / name) == wanted, 'UNCHANGED_RELEASE_IMPLEMENTATION:' + name)
    a = copy.deepcopy(previous)
    a.update(generation=previous['generation'] + 1, last_issued_versionCode=version - 1, candidate_versionCode=version,
             previous_authority_sha256=digest(canonical(previous)), target_owners=TARGETS, update_kind='owner_update',
             payload={k: v for meta in metas.values() for k, v in meta['payload'].items()}, bundle_catalog=catalog,
             experience_version_labels={'INFINITY': version, 'COBRA': 2103445},
             workflow_sha256=file_sha(ROOT / '.github/workflows/infinity-combined-release.yml'))
    for owner in TARGETS:
        a['components'][owner] = {k: metas[owner][k] for k in ('version', 'digest', 'approved_source', 'settings_schema')}
        a['components'][owner]['revision'] = previous['components'][owner]['revision'] + 1
        a['bundle_sources'][owner] = dict(run_id=RUN, build_source=PRODUCER, artifact=row['name'], path='components/' + owner + '.zip')
    a['source_files'] = {name: file_sha(ROOT / name) for name in previous['source_files']}
    a['owner_update_evidence'] = dict(owner='INFINITY_THREE_SCOPED_CORRECTIONS' if version == 2103466 else 'INFINITY_THREE_CORRECTIONS_FORWARD_RECOVERY',
        producer_run=RUN, producer_source=PRODUCER, source_files=bindings(), artifact={k: row[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
        preparation_sha256=file_sha(prepared / 'PREPARATION.json'), native_sha256=proof['native_sha256'], module_upgrade_recovery_sha256=file_sha(audit),
        Android='PENDING_SELECTED_SEARCH_TRAKT_INSTALL_OVER_AND_RECOVERY', physical_Fold='PENDING_ONE_FINAL_OWNER_ACCEPTANCE',
        public_release='BLOCKED_UNTIL_SELECTED_ANDROID_GATES_PASS', accepted_pointer_updated=False,
        installed_source_evidence_sha256='e14b1e9c8441e78ce5c930dea8c7a5885053011d531df9ec51377fcb18298b65',
        verification_toolchain=previous['owner_update_evidence']['verification_toolchain'] if 'verification_toolchain' in previous['owner_update_evidence'] else dict(java_major=21, unchanged_original_DEX=True))
    transition(previous, a, TARGETS)
    verify_evidence(a, lambda name: (ROOT / name).read_bytes())
    return a


def check_registered(prepared, version, audit, out):
    request = load(HERE / 'RELEASE-REQUEST.json')
    require(request['version'] == version and request['publication'] is False, 'INTERNAL_QA_REQUEST_ONLY')
    current = load(ROOT / AUTHORITY_PATH)
    changed_at = command('git', 'log', '-1', '--format=%H', '--', AUTHORITY_PATH)
    previous = json.loads(command('git', 'show', changed_at + '^:' + AUTHORITY_PATH))
    require(proposed(prepared, version, audit, previous) == current, 'EXACT_REVIEWED_REGISTERED_THREE_SCOPE_PAYLOAD')
    save(out, dict(status='PASS_EXACT_OFFICIAL_REGISTERED_THREE_SCOPE_PAYLOAD', versionCode=version,
                   source=command('git', 'rev-parse', 'HEAD'), accepted_pointer_updated=False, public_release=False))


def compare(parent, candidate, prepared, out, sdk=None):
    require(file_sha(parent) == BASE_APK, 'EXACT_SIGNED464_PARENT')
    proof = load(prepared / 'PREPARATION.json')
    differences = {}
    with ZipFile(parent) as a, ZipFile(candidate) as b:
        old = set(validate_names(a)) - SIGNATURE
        names = set(validate_names(b)) - SIGNATURE
        require(names == old | set(proof['added_members']), 'EXACT_DECLARED_APK_MEMBER_SET')
        for name in sorted(names):
            before, after = a.read(name) if name in old else None, b.read(name)
            if before == after:
                continue
            require(name in proof['changed_members'] and digest(after) == proof['changed_members'][name], 'UNAPPROVED_APK_MEMBER:' + name)
            if name == 'AndroidManifest.xml':
                require(normalize_manifest(after) == (normalize_manifest(before)[0], proof['versionCode']), 'ANDROID_VERSION_METADATA_ONLY')
            differences[name] = digest(after)
    require(differences == proof['changed_members'], 'EXACT_FROZEN_CORRECTION_BYTES')
    out.mkdir(parents=True, exist_ok=True)
    if sdk:
        signature = command(sdk / 'apksigner', 'verify', '--verbose', '--print-certs', candidate)
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT], 'ONE_ORIGINAL_PERMANENT_CERTIFICATE')
        (out / 'SIGNATURE.txt').write_text(signature + '\n')
    report = dict(status='PASS_SIGNED464_EXACT_THREE_SCOPE_MEMBER_PRESERVATION', baseline_sha256=BASE_APK,
        versionCode=proof['versionCode'], candidate_sha256=file_sha(candidate), changed_members=differences,
        existing_unchanged_members=len(old) - len(set(differences) & old), new_source_members=len(proof['added_members']),
        all_DEX_byte_identical=True, Cobra_bundle_byte_identical=True, skin_byte_identical=True, account_or_profile_migration=False,
        Android='NOT_RUN_BY_PACKAGING', Fold='NOT_RUN', public_release=False, accepted_pointer_updated=False)
    save(out / 'APK-PRESERVATION.json', report)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    commands = p.add_subparsers(dest='operation', required=True)
    for name in ('propose', 'check_registered'):
        a = commands.add_parser(name)
        for key in ('prepared', 'audit', 'out'):
            a.add_argument('--' + key, type=Path, required=True)
        a.add_argument('--version', type=int, required=True)
    a = commands.add_parser('compare')
    for key in ('parent', 'candidate', 'prepared', 'out'):
        a.add_argument('--' + key, type=Path, required=True)
    a.add_argument('--sdk', type=Path)
    args = vars(p.parse_args())
    operation = args.pop('operation')
    if operation == 'propose':
        output = args.pop('out')
        save(output, proposed(**args))
    else:
        globals()[operation](**args)
