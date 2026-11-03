"""Kodi452 physical-test candidate through the unchanged sole original signer.

Android execution remains blocked/pending. No runtime PASS, accepted-pointer
update, native rebuild or Unknown-ledger exemption is introduced here.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ISO = REPO / 'repairs/dual-experience-isolation-2103420'
sys.path.insert(0, str(ISO))
from inventory import canonical, digest, file_sha, load, save, CERT_SHA, SIGNATURE, validate_names
from component_bundles import read_bundle, record, combine
from release_gate import normalize_manifest, require, component_digest
from release_authority import transition, verify_evidence

BASE = '7bcc698d5b89f1cfe9d020bafc89b85a78f94c7c'
BRANCH = 'work/infinity-kodi-2103451-checkpoint-anr-20261103'
AUTH = ISO / 'release-authority.json'
VERSION = 2103452
GENERATION = 38
APK_SHA = 'd77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399'
NATIVE = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
NATIVE_SHA = 'f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674'
NATIVE_SOURCE = '765b92bc8af1452ffc2bbb19a03a3de229a90255'
NATIVE_RUN = 41729462691
NATIVE_ARTIFACT = 13276398254
RUNTIME = 'BLOCKED_NO_AUTHORIZED_COMPATIBLE_TARGET'
TARGETS = ['INFINITY', 'CHOOSER_SHELL']
OWNER = 'INFINITY_KODI_P0_NATIVE'
ALLOWED = {NATIVE, LABEL, 'AndroidManifest.xml'}
ASSETS = {
    'baseline': (13200361701, 41568721264, 'Infinity-Combined-Original-Signer-41568721264', 328005311,
                 '7e2eb67204ecc24e1a9d27007e90050b40683f0442bd8c32aec9b3bac32a9c41'),
    'components': (13200925524, 41568721264, 'Infinity-Combined-Owner-Components-41568721264', 319074381,
                   'e5f3017e5154625561103580c86020eab0176cc4d1f6ca033f0c1bb8726baedd'),
    'native': (NATIVE_ARTIFACT, NATIVE_RUN, 'Infinity-Kodi451-P0-ARM64-Native-41729462691-INTERNAL-NOT-APK',
               184610295, 'cac2281741679eaebbdf167969afdbeccdd0a8e1a1f4e2e5fd7eb529807571e0'),
}
FROZEN_NATIVE_SCRIPTS = ('stage_lifecycle_repair.py', 'stage_watched_repair.py',
                         'test_lifecycle_repair.py', 'test_watched_repair.py')
CONTROL_PATHS = {'.github/workflows/infinity-combined-release.yml',
    'repairs/dual-experience-isolation-2103420/release_gate.py',
    'repairs/dual-experience-isolation-2103420/signer-policy.json',
    'repairs/dual-experience-isolation-2103420/release-authority.json'}


def cmd(*args):
    return subprocess.check_output(list(map(str, args)), text=True)


def previous():
    return json.loads(cmd('git', 'show', BASE + ':' + str(AUTH.relative_to(REPO))))


def head_check():
    require(os.environ.get('GITHUB_WORKFLOW') == 'Infinity combined release | owner gate before original signing',
            'SOLE_ORIGINAL_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'EXACT_P0_BRANCH')
    head = os.environ['GITHUB_SHA']
    require(cmd('git', 'rev-parse', 'HEAD').strip() == head, 'SOURCE_HEAD')
    require(cmd('git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == head, 'REMOTE_HEAD_RACE')
    require(not cmd('git', 'status', '--porcelain', '--untracked-files=no').strip(), 'DIRTY_SOURCE')
    changed = cmd('git', 'diff', '--name-only', BASE, 'HEAD').splitlines()
    require(changed and all(n.startswith('repairs/infinity-kodi-2103451-checkpoint-anr/') or n in CONTROL_PATHS
                            for n in changed), 'UNRELATED_SOURCE_CHANGED')
    for name in FROZEN_NATIVE_SCRIPTS:
        path = str((HERE / name).relative_to(REPO))
        require((HERE / name).read_bytes() == subprocess.check_output(['git', 'show', BASE + ':' + path]),
                'TESTED_NATIVE_REPAIR_CHANGED:' + name)
    return head


def validate_metadata(row, identity):
    ident, run, name, size, sha = identity
    require(row.get('id') == ident and row.get('workflow_run', {}).get('id') == run and
            row.get('name') == name and row.get('size_in_bytes') == size and
            row.get('digest') == 'sha256:' + sha and row.get('expired') is False, 'ARTIFACT_IDENTITY_OR_DIGEST')
    return {k: row[k] for k in ('id', 'name', 'size_in_bytes', 'digest')}


def input_metadata(out):
    head_check()
    report = {}
    for name, asset in ASSETS.items():
        row = json.loads(cmd('gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/' + str(asset[0])))
        report[name] = validate_metadata(row, asset)
    save(out, report)


def certificate(apk, sdk):
    result = cmd(sdk / 'apksigner', 'verify', '--verbose', '--print-certs', apk)
    require(re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]{64})', result) == [CERT_SHA],
            'ORIGINAL_CERTIFICATE')
    return result


def verify_native(root):
    libs = list(root.rglob('libkodi.so'))
    require(len(libs) == 1, 'ONE_COMPILED_NATIVE_INPUT')
    library = libs[0]; parent = library.parent
    require(file_sha(library) == NATIVE_SHA, 'EXACT_COMPILED_NATIVE_BYTES')
    proof = load(parent / 'ENGINE-PROOF.json')
    require(proof['source_commit'] == NATIVE_SOURCE and proof['native_sha256'] == NATIVE_SHA and
            proof['complete_native_engine_compiled'] is True and proof['reviewed_file_count'] == 9411 and
            proof['changed_or_missing_reviewed'] == [], 'COMPLETE_SOURCE_BOUND_NATIVE_BUILD')
    pin = load(HERE / 'evidence/NATIVE-BUILD-RESULT.json')['source_map_file_sha256']
    require(file_sha(parent / 'NATIVE-SOURCE-MAP.json') == pin, 'COMPLETE_NATIVE_SOURCE_MAP')
    mapping = load(parent / 'NATIVE-SOURCE-MAP.json')
    reviewed = load(HERE / 'evidence/NATIVE-INTEGRATION-RESTORED.json')
    require(len(mapping) == 9411 and all(mapping[n] == sha for n, sha in reviewed['after'].items()),
            'FIVE_REVIEWED_NATIVE_EDITS')
    abi = (parent / 'NATIVE-MODULE-ABI.txt').read_text()
    require('InfinityCommandCenterIdentityV1' in abi and 'ELF64' in abi and 'AArch64' in abi,
            'PROTECTED_NATIVE_MODULE_ABI')
    for name, count in [('LIFECYCLE-HOST-VERIFICATION.json', 7), ('WATCHED-ACTUAL-NATIVE-SUPPORT.json', 15)]:
        evidence = load(HERE / 'evidence' / name)
        require(len(evidence['cases']) == count and all(c['status'] == 'HOST_PASS' for c in evidence['cases']),
                'PRESERVED_HOST_EVIDENCE:' + name)
    return library


def compare(baseline, candidate, out, sdk=None):
    require(file_sha(baseline) == APK_SHA, 'EXACT_SIGNED451_APK')
    changes = {}; members = {}
    with ZipFile(baseline) as old, ZipFile(candidate) as new:
        names = set(validate_names(old)) - SIGNATURE
        require(names == set(validate_names(new)) - SIGNATURE, 'EXACT_APK_MEMBER_SET')
        for name in sorted(names):
            with old.open(name) as stream: a = hashlib.file_digest(stream, 'sha256').hexdigest()
            with new.open(name) as stream: b = hashlib.file_digest(stream, 'sha256').hexdigest()
            members[name] = {'before': a, 'after': b}
            if a != b: changes[name] = members[name]
        require(set(changes) == ALLOWED, 'UNEXPECTED_APK_MEMBER_DELTA:' + str(set(changes) ^ ALLOWED))
        require(changes[NATIVE]['after'] == NATIVE_SHA, 'EXACT_NATIVE_ARTIFACT')
        require(normalize_manifest(new.read('AndroidManifest.xml')) ==
                (normalize_manifest(old.read('AndroidManifest.xml'))[0], VERSION), 'VERSION_ONLY_MANIFEST')
        require(new.read(LABEL) == b'infinity.last_updated_in=2103452\ncobra.last_updated_in=2103445\n',
                'TRUTHFUL_VERSION_METADATA_ONLY')
    out.mkdir(parents=True, exist_ok=True)
    result = dict(status='PASS_EXACT_SIGNED451_KODI_P0_PRESERVATION', baseline_sha256=APK_SHA,
        candidate_sha256=file_sha(candidate), changed_members=changes, added=[], removed=[],
        unchanged_members=len(names)-3,
        unchanged_dex_members=sum(re.fullmatch(r'classes[0-9]*\.dex', n) is not None for n in names),
        unchanged_native_libraries=sum(n.startswith('lib/') and n.endswith('.so') and n != NATIVE for n in names),
        Android=RUNTIME, physical_Fold='PENDING', accepted_pointer_updated=False)
    save(out / 'APK-PRESERVATION.json', result)
    save(out / 'ALL-APK-MEMBER-HASHES.json', members)
    if sdk is not None:
        (out / 'SIGNATURE.txt').write_text(certificate(candidate, sdk))
    return result


def repack(owner, bundles, dest, row, source, library):
    old = read_bundle(bundles / row['file'], row)
    meta = copy.deepcopy(old)
    meta.update(version=str(VERSION) + '.' + owner.lower() + '.1', approved_source=source)
    name = NATIVE if owner == 'INFINITY' else LABEL
    raw = library.read_bytes() if owner == 'INFINITY' else b'infinity.last_updated_in=2103452\ncobra.last_updated_in=2103445\n'
    require(name in old['members'] and old['payload']['member:' + name]['owner'] == owner, 'EXISTING_OWNED_MEMBER')
    meta['members'][name]['sha256'] = digest(raw)
    meta['payload']['member:' + name]['sha256'] = digest(raw)
    meta['digest'] = component_digest(meta['payload'], owner)
    path = dest / row['file']
    with ZipFile(bundles / row['file']) as z, ZipFile(path, 'w') as target:
        for n in z.namelist():
            if n != 'component.json': target.writestr(record(n), raw if n == 'payload/' + name else z.read(n))
        target.writestr(record('component.json'), canonical(meta))
    result = dict(file=path.name, sha256=file_sha(path), **{k: meta[k] for k in ('version','digest','approved_source','settings_schema')})
    verified = read_bundle(path, result)
    require(verified['dex'] == old['dex'], 'ALL_DEX_FROZEN')
    require({k:v for k,v in verified['payload'].items() if k != 'member:' + name} ==
            {k:v for k,v in old['payload'].items() if k != 'member:' + name}, 'UNRELATED_OWNER_MEMBER')
    return result


def selected_sources():
    return [HERE / n for n in FROZEN_NATIVE_SCRIPTS] + [HERE / n for n in
        ('release452.py', 'test_release452.py', 'FOLD-CANDIDATE-AUTHORIZATION.md',
         'evidence/LIFECYCLE-HOST-VERIFICATION.json', 'evidence/WATCHED-ACTUAL-NATIVE-SUPPORT.json',
         'evidence/NATIVE-BUILD-RESULT.json', 'evidence/NATIVE-INTEGRATION-RESTORED.json')]


def prepare(bundles, baseline, native, sdk, out):
    source = head_check(); prior = previous()
    require(prior['candidate_versionCode'] == 2103451 and prior['generation'] == 37, 'EXACT451_PREDECESSOR')
    require(load(bundles / 'catalog.json') == prior['bundle_catalog'], 'EXACT451_CATALOG')
    require(file_sha(baseline) == APK_SHA, 'EXACT_SIGNED451_APK')
    out.mkdir(exist_ok=False)
    (out / 'BASELINE-SIGNATURE.txt').write_text(certificate(baseline, sdk))
    library = verify_native(native)
    catalog = copy.deepcopy(prior['bundle_catalog']); catalog['source'] = source
    dest = out / 'components'; dest.mkdir()
    for frozen in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        row = catalog['bundles'][frozen]; read_bundle(bundles / row['file'], row)
        shutil.copyfile(bundles / row['file'], dest / row['file'])
    for owner in TARGETS:
        catalog['bundles'][owner] = repack(owner, bundles, dest, catalog['bundles'][owner], source, library)
    save(dest / 'catalog.json', catalog)
    source_paths = selected_sources()
    proof = dict(status='PASS_NATIVE_P0_PACKAGING_RUNTIME_PENDING', source=source, run_id=int(os.environ['GITHUB_RUN_ID']),
        baseline=BASE, baseline_apk_sha256=APK_SHA, native_sha256=NATIVE_SHA, native_build_source=NATIVE_SOURCE,
        native_build_run=NATIVE_RUN, native_build_artifact=NATIVE_ARTIFACT,
        source_files={str(p.relative_to(REPO)): file_sha(p) for p in source_paths}, Android=RUNTIME,
        historical_watched_route='UNKNOWN', unknown_obligations='REMAIN_BLOCKING',
        physical_Fold='PENDING', accepted_pointer_updated=False)
    save(out / 'PREPARATION.json', proof)
    combine(dest, catalog, out / 'combined-unsigned.apk', VERSION)
    compare(baseline, out / 'combined-unsigned.apk', out / 'preservation')
    head_check()
    publish = out / 'publish'; publish.mkdir()
    shutil.copytree(dest, publish / 'components'); shutil.copytree(out / 'preservation', publish / 'preservation')
    shutil.copyfile(out / 'PREPARATION.json', publish / 'PREPARATION.json')
    print('PASS exact native/metadata owner preparation; Android BLOCKED, Fold PENDING; unsigned only')


def official(prepared, run_id, archive=None):
    proof = load(prepared / 'PREPARATION.json')
    run = json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/' + str(run_id)))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == proof['source'] and
            run['head_branch'] == BRANCH and run['path'] == '.github/workflows/infinity-combined-release.yml', 'OFFICIAL_PRODUCER')
    require(proof['run_id'] == run_id and proof['status'] == 'PASS_NATIVE_P0_PACKAGING_RUNTIME_PENDING' and
            proof['baseline'] == BASE and proof['baseline_apk_sha256'] == APK_SHA and
            proof['native_sha256'] == NATIVE_SHA and proof['native_build_source'] == NATIVE_SOURCE and
            proof['native_build_run'] == NATIVE_RUN and proof['native_build_artifact'] == NATIVE_ARTIFACT and
            proof['Android'] == RUNTIME and proof['physical_Fold'] == 'PENDING' and
            proof['historical_watched_route'] == 'UNKNOWN' and proof['unknown_obligations'] == 'REMAIN_BLOCKING' and
            proof['accepted_pointer_updated'] is False, 'EXACT_PHYSICAL_TEST_CANDIDATE_SCOPE')
    rows = json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/' + str(run_id) + '/artifacts?per_page=100'))['artifacts']
    rows = [r for r in rows if r['name'] == 'Infinity452-Prepared-' + str(run_id) and not r['expired']]
    require(len(rows) == 1, 'ONE_OFFICIAL_PREPARATION')
    row = {k: rows[0][k] for k in ('id','name','digest','size_in_bytes')}
    require(re.fullmatch('sha256:[a-f0-9]{64}', row['digest']) is not None, 'OFFICIAL_ARCHIVE_DIGEST')
    if archive is None:
        cache = Path('/tmp/kodi452-official'); cache.mkdir(exist_ok=True)
        archive = cache / (str(row['id']) + '.zip')
        if not archive.exists():
            with archive.open('wb') as stream:
                subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/' + str(row['id']) + '/zip'], stdout=stream, check=True)
    require(file_sha(archive) == row['digest'][7:], 'OFFICIAL_ARCHIVE_BYTES')
    with ZipFile(archive) as z:
        names = set(validate_names(z)); names = {n for n in names if not n.endswith('/')}
        require(names == {str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()}, 'OFFICIAL_FILE_SET')
        for n in names:
            with z.open(n) as stream: require(hashlib.file_digest(stream,'sha256').hexdigest() == file_sha(prepared/n), 'OFFICIAL_FILE:' + n)
    require(set(proof['source_files']) == {str(p.relative_to(REPO)) for p in selected_sources()}, 'EXACT_SOURCE_BINDING_SET')
    for n, pin in proof['source_files'].items():
        require(file_sha(REPO/n) == pin and digest(subprocess.check_output(['git','show',proof['source']+':'+n])) == pin,
                'TESTED_SOURCE_CHANGED:' + n)
    return row


def proposed(prepared, run_id, archive=None):
    artifact = official(prepared, run_id, archive); proof = load(prepared / 'PREPARATION.json'); prior = previous()
    catalog = load(prepared / 'components/catalog.json')
    metas = {o: read_bundle(prepared / 'components' / row['file'], row) for o, row in catalog['bundles'].items()}
    authority = copy.deepcopy(prior)
    authority.update(generation=GENERATION, last_issued_versionCode=2103451, candidate_versionCode=VERSION,
        target_owners=TARGETS, update_kind='owner_update', previous_authority_sha256=digest(canonical(prior)),
        payload={k:v for m in metas.values() for k,v in m['payload'].items()}, bundle_catalog=catalog,
        experience_version_labels={'INFINITY':VERSION,'COBRA':2103445})
    for owner in TARGETS:
        authority['components'][owner] = {k: metas[owner][k] for k in ('version','digest','approved_source','settings_schema')}
        authority['components'][owner]['revision'] = prior['components'][owner]['revision'] + 1
        authority['bundle_sources'][owner] = dict(run_id=run_id, build_source=proof['source'],
            artifact='Infinity452-Prepared-' + str(run_id), path='components/' + owner + '.zip')
    authority['source_files'] = {n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256'] = file_sha(REPO / '.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence'] = dict(owner=OWNER, producer_run=run_id, producer_source=proof['source'],
        source_files=proof['source_files'], artifact=artifact, preparation_sha256=file_sha(prepared/'PREPARATION.json'),
        native_sha256=NATIVE_SHA, native_build_source=NATIVE_SOURCE, native_build_run=NATIVE_RUN,
        Android=RUNTIME, physical_Fold='PENDING', historical_watched_route='UNKNOWN',
        unknown_obligations='REMAIN_BLOCKING', frozen_owners=['COBRA','MINIMAL_ANDROID_CONTRACT'], accepted_pointer_updated=False)
    transition(prior, authority, TARGETS)
    verify_evidence(authority, lambda n:(REPO/n).read_bytes())
    return authority


def register(prepared, run_id, archive=None):
    candidate = proposed(prepared, run_id, archive)
    require(load(AUTH) == previous(), 'AUTHORITY_PREDECESSOR')
    save(AUTH, candidate)


def check_registered(prepared, run_id, out, archive=None):
    head_check()
    require(proposed(prepared, run_id, archive) == load(AUTH), 'REGISTERED_EXACT_OFFICIAL_PREPARATION')
    save(out, dict(status='PASS_EXACT_NATIVE_P0_PREPARATION_RUNTIME_PENDING', run_id=run_id,
                   Android=RUNTIME, physical_Fold='PENDING'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='op', required=True)
    a = sub.add_parser('metadata'); a.add_argument('--out', type=Path, required=True)
    a = sub.add_parser('prepare')
    for n in ('bundles','baseline','native','sdk','out'): a.add_argument('--'+n, type=Path, required=True)
    a = sub.add_parser('compare')
    for n in ('baseline','candidate','out'): a.add_argument('--'+n, type=Path, required=True)
    a.add_argument('--sdk', type=Path)
    for name in ('register','check_registered'):
        a = sub.add_parser(name); a.add_argument('--prepared', type=Path, required=True)
        a.add_argument('--run-id', type=int, required=True); a.add_argument('--archive', type=Path)
        if name == 'check_registered': a.add_argument('--out', type=Path, required=True)
    args = vars(p.parse_args()); op = args.pop('op')
    {'metadata':input_metadata, 'prepare':prepare, 'compare':compare, 'register':register,
     'check_registered':check_registered}[op](**args)
