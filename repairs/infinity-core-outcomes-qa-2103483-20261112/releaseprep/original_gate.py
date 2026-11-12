"""Original-owner diagnostic QA admission; no signing or key handling.

Frozen request: ORIGINAL-QA-REQUEST.json beside this file, enabled only after
actual ARM64, native-injection Android and unsigned preparation artifacts exist.
Modes propose/admit/inputs/presign/post retain original authority/owner gates.
An injection experiment never establishes APK install-over or Fold acceptance.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE_DIR = Path('repairs/infinity-core-outcomes-qa-2103483-20261112/releaseprep')
if HERE.relative_to(ROOT) != SOURCE_DIR:
    raise RuntimeError('ORIGINAL_GATE_SOURCE_DIRECTORY_MUST_NOT_BE_RELOCATED')
CORE = ROOT / 'repairs/dual-experience-isolation-2103420'
REQUEST = HERE / 'ORIGINAL-QA-REQUEST.json'
BASE = '3d9709bb1226a2ffa3a474cf04b3d3842b084611'
AUTHORITY = 'repairs/dual-experience-isolation-2103420/release-authority.json'
REPO = 'mahfouzhassine8-ops/project-infinity'
CANONICAL = 'work/infinity-2103460-nine-corrections-20261106'
WORKFLOW = '.github/workflows/infinity-combined-release.yml'
VERSION, GENERATION = 2103484, 69  # Provisional; this helper never reserves them.
APK83 = '0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236'
ENGINE83 = 'f14ff78865158337eb6fd19dfe549912d57f2a6a912e5b3440ed28880ee0cb0c'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
LIB = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
MEMBERS = {LIB, LABEL, 'AndroidManifest.xml'}
OWNERS = ['INFINITY', 'CHOOSER_SHELL']
OWNER = 'INFINITY_CORE_OUTCOMES_NATIVE_OBSERVATION_INTERNAL_QA_NOT_ACCEPTED'
PREPARED = ROOT / 'core-outcomes-qa-prepared'
ARCHIVE = ROOT / 'core-outcomes-qa-prepared.zip'
UNSIGNED = 'Infinity-2103484-Core-Outcomes-UNSIGNED-NOT-INSTALLABLE.apk'


def require(value, label):
    if not value:
        raise RuntimeError(label)


def load(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=60)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], timeout=45))


def member_sha(archive, name):
    with archive.open(name) as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def policy_extension(before, after, additions, workflow_ids):
    """Only exact reviewed key-free Native/Stage inventory additions are allowed."""
    require(len(before['retired_original_key_workflows']) == 351 and before['sole_original_key_workflow_id'] == 397702717 and
            len(additions) <= 2 and len({r['id'] for r in additions}) == len(additions), 'EXACT_ORIGINAL_SIGNER_POLICY')
    fixed = set(before) - {'additional_unsigned_owner_workflows', 'reviewed_workflow_ids', 'audit_workflows'}
    require(set(after) == set(before) and all(after[k] == before[k] for k in fixed), 'NO_SIGNER_RETIREMENT_OR_POLICY_RELAXATION')
    old = {r['id']: r for r in before['additional_unsigned_owner_workflows']}
    retired = {r['id'] for r in before['retired_original_key_workflows']}
    extra = {}
    for row in additions:
        require(type(row['id']) is int and row['id'] in workflow_ids and row['id'] not in old and
                row['id'] not in retired and row['id'] != 397702717 and row['original_key_access'] is False and
                re.fullmatch('[0-9a-f]{40}', row['source']) and
                row['path'].startswith('.github/workflows/') and '..' not in Path(row['path']).parts,
                'ONLY_NEW_KEYFREE_NATIVE_OR_STAGE_WORKFLOW')
        extra[row['id']] = row
    require({r['id']: r for r in after['additional_unsigned_owner_workflows']} == old | extra and
            len(after['additional_unsigned_owner_workflows']) == len(old) + len(extra) and
            set(after['reviewed_workflow_ids']) == set(before['reviewed_workflow_ids']) | set(extra) and
            len(after['reviewed_workflow_ids']) == len(set(after['reviewed_workflow_ids'])) and
            after['audit_workflows'] == before['audit_workflows'] + len(extra), 'EXACT_REVIEWED_UNSIGNED_INVENTORY_EXTENSION')


def toolkit(r):
    base = json.loads(git('show', BASE + ':' + AUTHORITY))
    policy_path = CORE / 'signer-policy.json'
    old_policy = json.loads(git('show', BASE + ':' + policy_path.relative_to(ROOT).as_posix()))
    current_policy = load(policy_path)
    policy_extension(old_policy, current_policy, r['unsigned_workflow_additions'],
                     {r['native_producer']['workflow_id'], r['prepared_producer']['workflow_id']})
    require(sha(policy_path) == r['signer_policy_sha256'], 'REVIEWED_SIGNER_POLICY_INVENTORY_HASH')
    for name, wanted in base['source_files'].items():
        if name == policy_path.relative_to(ROOT).as_posix():
            continue  # Validated exact data-only extension above; no executable exception.
        require(sha(ROOT / name) == wanted, 'ORIGINAL_TOOL_CHANGED_BEFORE_IMPORT:' + name)
    sys.path.insert(0, str(CORE))
    import component_bundles as cb
    import release_authority as ra
    import release_gate as gate
    import inventory
    for module in (cb, ra, gate, inventory):
        require(Path(module.__file__).resolve() == CORE / (module.__name__ + '.py'), 'ORIGINAL_TOOL_IMPORT_ORIGIN')
    return SimpleNamespace(cb=cb, ra=ra, gate=gate, inventory=inventory, base=base)


def producer(row, expected_id=None):
    require(all(type(row[k]) is int and row[k] > 0 for k in ('run', 'workflow_id', 'id', 'size_in_bytes')) and
            re.fullmatch('[0-9a-f]{40}', row['source']) and re.fullmatch('sha256:[0-9a-f]{64}', row['digest']),
            'COMPLETE_FROZEN_PRODUCER_DESCRIPTOR')
    require(expected_id is None or row['workflow_id'] == expected_id, 'EXACT_WORKFLOW_ROLE')
    run = api('actions/runs/' + str(row['run']))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == row['source'] and
            run['workflow_id'] == row['workflow_id'], 'ACTUAL_SUCCESSFUL_EXACT_PRODUCER')
    artifact = api('actions/artifacts/' + str(row['id']))
    require(not artifact['expired'] and artifact['workflow_run']['id'] == row['run'] and
            all(artifact[k] == row[k] for k in ('id', 'name', 'digest', 'size_in_bytes')), 'EXACT_LIVE_PRODUCER_ARTIFACT')


def request():
    require(REQUEST.is_file(), 'DISABLED_UNTIL_FROZEN_ORIGINAL_QA_REQUEST_EXISTS')
    r = load(REQUEST)
    require(r['enabled'] is True and r['operation'] == 'original-owner-core-outcomes-native-observation-internal-QA' and
            r['sign_operation'] == 'sign-core-outcomes-qa' and r['versionCode'] == VERSION and r['generation'] == GENERATION and
            r['original_signer_workflow_id'] == 397702717 and r['baseline_source'] == BASE and r['baseline_APK_sha256'] == APK83,
            'EXACT_ENABLED_ORIGINAL_OWNER_QA_REQUEST')
    require(r['Core_path_or_source_patch'] is False and r['Fold_cause_established'] is False and
            r['owner_delivery'] is False and r['publication'] is False and r['accepted_pointer_updated'] is False,
            'NO_UNRELATED_PATCH_OR_FALSE_ACCEPTANCE')
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REPOSITORY') == REPO and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + CANONICAL and
            git('rev-parse', 'HEAD').decode().strip() == os.environ.get('GITHUB_SHA') and
            not git('status', '--porcelain', '--untracked-files=no').strip(), 'CLEAN_EXACT_CANONICAL_OWNER_SOURCE')
    require(api('git/ref/heads/' + CANONICAL)['object']['sha'] == os.environ['GITHUB_SHA'], 'LIVE_CANONICAL_HEAD_RACE')
    this = api('actions/runs/' + os.environ['GITHUB_RUN_ID'])
    require(this['workflow_id'] == 397702717 and this['path'] == WORKFLOW and this['head_sha'] == os.environ['GITHUB_SHA'],
            'SOLE_ORIGINAL_OWNER_WORKFLOW_CONTEXT')
    require(sha(ROOT / WORKFLOW) == r['workflow_sha256'], 'REVIEWED_ORIGINAL_WORKFLOW')
    stage_request = Path(r['stage_request'])
    required = {Path(__file__).resolve().relative_to(ROOT).as_posix(),
                (HERE / 'stage.py').relative_to(ROOT).as_posix(), (HERE / 'BASELINE83.json').relative_to(ROOT).as_posix(),
                stage_request.as_posix()}
    require(set(r['source_bindings']) == required and stage_request.parent == HERE.relative_to(ROOT), 'EXACT_TASK_TOOL_AND_STAGE_INPUT_BINDINGS')
    for name, wanted in r['source_bindings'].items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts and sha(ROOT / path) == wanted,
                'REVIEWED_QA_ADMISSION_SOURCE:' + name)
    require(REQUEST.read_bytes() == git('show', os.environ['GITHUB_SHA'] + ':' + REQUEST.relative_to(ROOT).as_posix()),
            'FROZEN_COMMITTED_ORIGINAL_QA_REQUEST')
    for key in ('native_producer', 'prepared_producer', 'android_producer'):
        require(r[key]['workflow_id'] != 397702717, 'NATIVE_ANDROID_STAGE_HAVE_NO_ORIGINAL_SIGNER_ROLE')
        producer(r[key])
    role_sources = {r[k]['workflow_id']: r[k]['source'] for k in ('native_producer', 'prepared_producer')}
    for row in r['unsigned_workflow_additions']:
        meta = api('actions/workflows/' + str(row['id']))
        require(row['id'] in role_sources and row['source'] == role_sources[row['id']] and
                meta['path'] == row['path'] and meta['state'] == 'active' and row['original_key_access'] is False,
                'ACTUAL_REVIEWED_KEYFREE_WORKFLOW_IDENTITY')
    issued = api('actions/runs/43119348510')
    require(issued['status'] == 'completed' and issued['conclusion'] == 'success' and issued['head_sha'] == BASE and
            issued['workflow_id'] == 397702717, 'ACTUAL_ORIGINAL83_ISSUANCE_REQUIRED')
    return r


def compare(baseline, candidate, native_sha, t):
    require(sha(baseline) == APK83, 'EXACT_ORIGINAL_SIGNED83_BYTES')
    with ZipFile(baseline) as old, ZipFile(candidate) as new:
        names = set(t.inventory.validate_names(old)) - set(t.inventory.SIGNATURE)
        require(set(t.inventory.validate_names(new)) - set(t.inventory.SIGNATURE) == names, 'APK_MEMBER_SET_CHANGED')
        changed = {name for name in names if member_sha(old, name) != member_sha(new, name)}
        require(changed == MEMBERS and member_sha(old, LIB) == ENGINE83 and member_sha(new, LIB) == native_sha,
                'EXACT_NATIVE_AND_ONLY_THREE_MEMBER_DELTA')
        before, bv = t.cb.normalize_manifest(old.read('AndroidManifest.xml'))
        after, av = t.cb.normalize_manifest(new.read('AndroidManifest.xml'))
        require(bv == 2103483 and av == VERSION and before == after, 'MANIFEST_VERSION_ONLY')
        require(new.read(LABEL) == b'infinity.last_updated_in=2103484\ncobra.last_updated_in=2103445\n', 'EXACT_OWNER_VERSION_LABELS')
        return len(names) - len(changed)


def prepared_inputs(r, baseline, t):
    row = r['prepared_producer']
    require('sha256:' + sha(ARCHIVE) == row['digest'] and ARCHIVE.stat().st_size == row['size_in_bytes'], 'WHOLE_PREPARED_ARCHIVE_DIGEST')
    consumed = {'UNSIGNED-QA-PRESERVATION.json', 'ORIGINAL83-SIGNATURE.txt', 'components/catalog.json', UNSIGNED}
    consumed |= {'components/' + owner + '.zip' for owner in t.cb.OWNED}
    with ZipFile(ARCHIVE) as archive:
        names = set(t.inventory.validate_names(archive))
        require(consumed <= names, 'COMPLETE_PREPARED_ORIGINAL_OWNER_INPUTS')
        for name in consumed:
            require(member_sha(archive, name) == sha(PREPARED / name), 'PREPARED_FILE_NOT_FROM_OFFICIAL_ARCHIVE:' + name)
    proof = load(PREPARED / 'UNSIGNED-QA-PRESERVATION.json')
    require(proof['status'] == 'PASS_KEY_FREE_UNSIGNED83_NATIVE_OBSERVATION_THREE_MEMBER_PRESERVATION' and
            proof['source'] == row['source'] and proof['baseline_version'] == 2103483 and proof['baseline_APK_sha256'] == APK83 and
            proof['authority_source'] == BASE and proof['versionCode'] == VERSION and proof['version_reserved'] is False and
            proof['native_sha256'] == r['native_sha256'] and proof['native_producer'] == r['native_producer'] and
            proof['Android_producer'] == r['android_producer'] and proof['Android_proof_sha256'] == r['Android_proof_sha256'] and
            proof['Android_native_injection'] == 'PASS_SELECTED_SCOPE_ONLY_NOT_APK_INSTALL_ACCEPTANCE' and
            proof['Core_path_or_source_patch'] is False and proof['signed'] is False and proof['original_key_used'] is False and
            proof['owner_delivery'] is False and proof['Fold'] == 'NOT_RUN', 'EXACT_ACTUAL_STAGE_AND_ANDROID_INJECTION_PROVENANCE')
    stage_path = HERE / 'stage.py'
    require(proof['stage_tool_sha256'] == sha(stage_path) and proof['baseline_metadata_sha256'] == sha(HERE / 'BASELINE83.json') and
            proof['request_sha256'] == sha(ROOT / r['stage_request']), 'EXACT_FROZEN_STAGE_TOOL_AND_REQUEST')
    for path in (stage_path, HERE / 'BASELINE83.json', ROOT / r['stage_request']):
        require(path.read_bytes() == git('show', row['source'] + ':' + path.relative_to(ROOT).as_posix()), 'UNCHANGED_ACTUAL_PREPARATION_SOURCE')
    stage = load(ROOT / r['stage_request'])
    require(stage['native_producer'] == r['native_producer'] and stage['native_sha256'] == r['native_sha256'] and
            stage['android_producer'] == r['android_producer'] and stage['android_proof']['sha256'] == r['Android_proof_sha256'],
            'FROZEN_NATIVE_AND_ANDROID_CONTRACT_CHAIN')
    require(sha(PREPARED / UNSIGNED) == r['unsigned_sha256'] == proof['unsigned_sha256'] and set(proof['changed_members']) == MEMBERS,
            'EXACT_UNSIGNED_QA_APK')
    return proof, compare(baseline, PREPARED / UNSIGNED, r['native_sha256'], t)


def download():
    r = request()
    t = toolkit(r)
    require(not ARCHIVE.exists() and not PREPARED.exists(), 'NO_OVERWRITE_OF_PRIOR_PREPARATION')
    row = r['prepared_producer']
    with ARCHIVE.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/' + REPO + '/actions/artifacts/' + str(row['id']) + '/zip'], stdout=stream, check=True, timeout=600)
    require('sha256:' + sha(ARCHIVE) == row['digest'] and ARCHIVE.stat().st_size == row['size_in_bytes'], 'ACTUAL_PREPARATION_ZIP')
    with ZipFile(ARCHIVE) as archive:
        names = t.inventory.validate_names(archive)
        require(0 < len(names) <= 100000 and sum(i.file_size for i in archive.infolist()) <= 8 * 1024**3 and
                all(not stat.S_ISLNK(i.external_attr >> 16) and not i.flag_bits & 1 for i in archive.infolist()), 'BOUNDED_SAFE_PREPARATION_ZIP')
        PREPARED.mkdir()
        archive.extractall(PREPARED)


def propose(out, baseline):
    r = request()
    t = toolkit(r)
    proof, retained = prepared_inputs(r, baseline, t)
    before = load(ROOT / AUTHORITY)
    require(before == t.base and before['generation'] == 68 and before['candidate_versionCode'] == 2103483,
            'ACTUAL83_AUTHORITY_ADVANCED_RECONCILE_FIRST')
    catalog = load(PREPARED / 'components/catalog.json')
    require(catalog['source'] == r['prepared_producer']['source'] and catalog['release_approved'] is False and
            set(catalog['bundles']) == set(t.cb.OWNED) and
            all(row['file'] == owner + '.zip' for owner, row in catalog['bundles'].items()), 'COMPLETE_REVIEWED_OWNER_CATALOG')
    meta = {o: t.cb.read_bundle(PREPARED / 'components' / catalog['bundles'][o]['file'], catalog['bundles'][o]) for o in t.cb.OWNED}
    for owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        require(catalog['bundles'][owner] == before['bundle_catalog']['bundles'][owner], 'PROTECTED83_OWNER_CATALOG_CHANGED')
    payload = {k: v for m in meta.values() for k, v in m['payload'].items()}
    require(len(payload) == sum(len(m['payload']) for m in meta.values()) and set(payload) == set(before['payload']), 'EXACT_FULL_PAYLOAD_VECTOR')
    allowed = {'member:' + LIB, 'member:' + LABEL}
    require(all(payload[k] == v for k, v in before['payload'].items() if k not in allowed), 'ALL_UNDECLARED_CLASSES_AND_MEMBERS_IDENTICAL83')
    require(payload['member:' + LIB] == {'owner': 'INFINITY', 'sha256': r['native_sha256']} and
            payload['member:' + LABEL] == {'owner': 'CHOOSER_SHELL',
                'sha256': digest(b'infinity.last_updated_in=2103484\ncobra.last_updated_in=2103445\n')},
            'EXACT_DECLARED_NATIVE_AND_LABEL_OWNER_PAYLOAD')
    result = copy.deepcopy(before)
    result.update(generation=GENERATION, candidate_versionCode=VERSION, last_issued_versionCode=2103483,
        previous_authority_sha256=t.inventory.digest(t.inventory.canonical(before)), target_owners=OWNERS, update_kind='owner_update',
        payload=payload, bundle_catalog=catalog, experience_version_labels={'INFINITY': VERSION, 'COBRA': 2103445},
        workflow_sha256=sha(ROOT / WORKFLOW))
    for owner in OWNERS:
        require(meta[owner]['approved_source'] == r['prepared_producer']['source'], 'EXACT_OWNER_PRODUCER_SOURCE')
        result['components'][owner] = {k: meta[owner][k] for k in ('version', 'digest', 'approved_source', 'settings_schema')}
        result['components'][owner]['revision'] = before['components'][owner]['revision'] + 1
        result['bundle_sources'][owner] = dict(run_id=r['prepared_producer']['run'], build_source=r['prepared_producer']['source'],
            artifact=r['prepared_producer']['name'], path='components/' + owner + '.zip')
    result['source_files'][(CORE / 'signer-policy.json').relative_to(ROOT).as_posix()] = r['signer_policy_sha256']
    files = dict(r['source_bindings'])
    files[REQUEST.relative_to(ROOT).as_posix()] = sha(REQUEST)
    result['owner_update_evidence'] = dict(owner=OWNER, producer_run=r['prepared_producer']['run'], producer_source=r['prepared_producer']['source'],
        artifact={k: r['prepared_producer'][k] for k in ('id', 'name', 'digest', 'size_in_bytes')}, source_files=files,
        preparation_sha256=sha(PREPARED / 'UNSIGNED-QA-PRESERVATION.json'), baseline_APK_sha256=APK83, native_sha256=r['native_sha256'],
        native_producer=r['native_producer'], Android_producer=r['android_producer'], Android_proof_sha256=r['Android_proof_sha256'],
        immutable_functional_base=2103483, Core_path_or_source_patch=False,
        Android='PASS_SELECTED_NATIVE_INJECTION_ONLY_NOT_APK_INSTALL_ACCEPTANCE',
        APK_installation='NOT_RUN_REQUIRES_ORIGINAL_SIGNATURE', Fold_cause_established=False, physical_Fold='NOT_RUN',
        engineering_QA_only=True, experimental=True, publication=False, public_release=False, owner_delivery_cleared=False,
        accepted_pointer_updated=False, shutdown_or_Core_outcome_repair='UNPROVEN',
        verification_toolchain=before['owner_update_evidence']['verification_toolchain'])
    t.ra.transition(before, result, OWNERS)
    t.ra.verify_evidence(result, lambda name: (ROOT / name).read_bytes())
    t.ra.verify(result, {k: v['sha256'] for k, v in payload.items()}, VERSION, GENERATION)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'AUTHORITY-PROPOSAL.json').write_bytes(t.inventory.canonical(result))
    (out / 'ADMISSION-RESULT.json').write_bytes(t.inventory.canonical(dict(status='PASS_KEYFREE_ORIGINAL_QA_PROPOSAL_ONLY',
        versionCode=VERSION, generation=GENERATION, native_sha256=r['native_sha256'], unsigned_sha256=r['unsigned_sha256'],
        unchanged_APK_members=retained, signed=False, version_reserved=False, registry_mutated=False, owner_delivery=False)))


def admit():
    r = request()
    t = toolkit(r)
    value = load(ROOT / AUTHORITY)
    require(value['generation'] == GENERATION and value['candidate_versionCode'] == VERSION and value['last_issued_versionCode'] == 2103483 and
            value['target_owners'] == OWNERS and value['update_kind'] == 'owner_update', 'UNREGISTERED_EXACT_DIAGNOSTIC_QA_PAYLOAD')
    evidence = value['owner_update_evidence']
    require(evidence['owner'] == OWNER and evidence['producer_run'] == r['prepared_producer']['run'] and
            evidence['artifact']['id'] == r['prepared_producer']['id'] and evidence['native_sha256'] == r['native_sha256'] and
            evidence['baseline_APK_sha256'] == APK83 and evidence['Core_path_or_source_patch'] is False and
            evidence['owner_delivery_cleared'] is False and evidence['publication'] is False and value['accepted_pointer_updated'] is False,
            'EXACT_REGISTERED_PREPARATION_AND_NO_FALSE_ACCEPTANCE')
    for name, wanted in evidence['source_files'].items():
        require(sha(ROOT / name) == wanted, 'REGISTERED_QA_SOURCE_CHANGED:' + name)
    require(value['components']['COBRA'] == t.base['components']['COBRA'] and
            value['protected_contract'] == t.base['protected_contract'] and
            value['payload']['member:' + LIB] == {'owner': 'INFINITY', 'sha256': r['native_sha256']}, 'PROTECTED_OWNER_OR_NATIVE_IDENTITY_CHANGED')
    t.ra.validate(value)
    t.ra.verify_evidence(value, lambda name: (ROOT / name).read_bytes())
    return r, t


def inputs(baseline):
    r, t = admit()
    prepared_inputs(r, baseline, t)


def presign(baseline, jars, work, out):
    r, t = admit()
    prepared_inputs(r, baseline, t)
    decision = t.gate.pre_sign(PREPARED / UNSIGNED, jars, work, ROOT, os.environ['GITHUB_SHA'], GENERATION)
    require(decision['versionCode'] == VERSION and decision['unsigned_apk_sha256'] == r['unsigned_sha256'], 'ORIGINAL_PRESIGN_DECISION_MISMATCH')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(t.inventory.canonical(decision))


def post(baseline, signed, sdk):
    r, t = admit()
    apk = signed / ('Infinity-' + str(VERSION) + '-Combined-Original-Signer.apk')
    build = load(signed / 'BUILD-RECEIPT.json')
    require(build['versionCode'] == VERSION and build['signed_apk_sha256'] == sha(apk) and build['certificate_sha256'] == CERT,
            'ACTUAL_ORIGINAL_SIGNED_BUILD_IDENTITY')
    verify = subprocess.check_output([str(sdk / 'apksigner'), 'verify', '--verbose', '--print-certs', str(apk)], text=True, timeout=90)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', verify) == [CERT], 'ACTUAL_PERMANENT_ORIGINAL_CERTIFICATE')
    for scheme in ('v1', 'v2', 'v3'):
        require(any(line.startswith('Verified using ' + scheme + ' scheme') and line.endswith(': true') for line in verify.splitlines()),
                'ACTUAL_SIGNATURE_SCHEME_MISSING:' + scheme)
    retained = compare(baseline, apk, r['native_sha256'], t)
    receipt = dict(status='PASS_ORIGINAL_SIGNED_DIAGNOSTIC_QA_THREE_MEMBER_PRESERVATION', versionCode=VERSION,
        source=os.environ['GITHUB_SHA'], signed_apk_sha256=sha(apk), certificate_sha256=CERT, native_sha256=r['native_sha256'],
        baseline_APK_sha256=APK83, changed_members=sorted(MEMBERS), unchanged_payload_members=retained,
        original83_preserved=True, Cobra_changed=False, Core_path_or_source_patch=False,
        Android='SELECTED_INJECTED_NATIVE_ONLY', actual_APK_installation='NOT_RUN', owner_delivery=False,
        shutdown_or_Core_outcome_repair='UNPROVEN', Fold='NOT_RUN', Fold_cause_established=False, public_release=False)
    (signed / 'QA-PRESERVATION.json').write_bytes(t.inventory.canonical(receipt))
    (signed / 'QA-SIGNATURE.txt').write_text(verify)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['download', 'propose', 'admit', 'inputs', 'presign', 'post'])
    parser.add_argument('--baseline', type=Path, default=ROOT / 'signed83/Infinity-2103483-Combined-Original-Signer.apk')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--jars', type=Path)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--signed', type=Path, default=ROOT / 'core-outcomes-qa-original-signed')
    parser.add_argument('--sdk', type=Path)
    args = parser.parse_args()
    if args.mode == 'download':
        download()
    elif args.mode == 'admit':
        admit()
    elif args.mode == 'inputs':
        inputs(args.baseline)
    elif args.mode == 'propose':
        require(args.out is not None, 'PROPOSAL_OUTPUT_REQUIRED')
        propose(args.out, args.baseline)
    elif args.mode == 'presign':
        require(args.out and args.jars and args.work, 'ORIGINAL_GATE_INPUTS_REQUIRED')
        presign(args.baseline, args.jars, args.work, args.out)
    else:
        require(args.sdk is not None, 'ACTUAL_SIGNATURE_VERIFIER_REQUIRED')
        post(args.baseline, args.signed, args.sdk)
