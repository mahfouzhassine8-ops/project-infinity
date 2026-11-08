"""Read-only official Watchlist pair review and original-authority proposals.

No registry/ref mutation or signing. The unchanged transition, verify_evidence,
owner-bundle gate and existing APK signer retain their authority.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ISO = ROOT / 'repairs/dual-experience-isolation-2103420'
sys.path[:0] = [str(HERE), str(ISO)]
import prepare_release as prep
from inventory import canonical, digest, file_sha, load, save, validate_names
from component_bundles import read_bundle, set_version
from release_gate import require
from release_authority import AUTHORITY_PATH, transition, verify_evidence

REQUEST = HERE / 'PREPARED-PAIR-REQUEST.json'
TARGETS = ['INFINITY', 'CHOOSER_SHELL']
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD_HELPER = ROOT / 'repairs/infinity-three-corrections-20261108/release_three.py'
OLD_HELPER_SHA = digest(prep.git('show', prep.BASE + ':' + OLD_HELPER.relative_to(ROOT).as_posix()))
EVIDENCE_NAMES = ('RUNTIME-SOURCE-PINS.json', 'VERSION-ADMISSION.json', 'NATIVE-INPUT-REQUEST.json',
                  'HOST-INTEGRATION-RESULT.json', 'NATIVE-HOST-RESULT.json', 'NATIVE-REVIEW.json',
                  'PYTHON-TARGETED-REVIEW.json', 'PYTHON-PRESERVATION.json', 'PHASE-B-PRESERVATION.json',
                  'CURRENT-EMITTER-PINS.json', 'RUNTIME-CONTRACT.md', 'OWNER-PHASE-B-AUTHORIZATION.md',
                  'OWNER-SCOPE-EXTENSION.md', 'MODULE-TEST-SELECTION.md', 'HOST-TEST-SELECTION.md')


def command(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def gh(path):
    return json.loads(command('gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path))


def request_data(path):
    require(path.is_relative_to(ROOT), 'COMMITTED_TASK_REQUEST_PATH_REQUIRED')
    request = load(path)
    require(type(request['run_id']) is int and request['run_id'] > 0 and
            re.fullmatch('[0-9a-f]{40}', request['source_commit']) is not None, 'FROZEN_PREPARATION_PRODUCER')
    require(set(request['artifacts']) == {'2103468', '2103469'}, 'EXACT_FORWARD_PREPARED_PAIR')
    for row in request['artifacts'].values():
        require(set(row) == {'id', 'name', 'digest', 'size_in_bytes'} and type(row['id']) is int and
                re.fullmatch('sha256:[0-9a-f]{64}', row['digest']) is not None and row['size_in_bytes'] > 0,
                'COMPLETE_IMMUTABLE_ARTIFACT_REQUEST')
    require(re.fullmatch('[0-9a-f]{64}', request['module_audit_sha256']) is not None, 'FROZEN_MODULE_AUDIT')
    return request


def bindings(producer, request):
    require(file_sha(OLD_HELPER) == OLD_HELPER_SHA, 'UNCHANGED_REFERENCE_REGISTRATION_HELPER')
    prep.tool_pins()
    paths = sorted(HERE.glob('*.py')) + [HERE / name for name in EVIDENCE_NAMES]
    paths += [HERE / 'native' / name for name in sorted(prep.NATIVE_SOURCES)]
    paths += [HERE / 'overlay' / prep.CC / name for name in sorted(prep.PYTHON | {prep.HELPER})]
    paths += prep.TOOLS + [prep.FIRST / 'module_dex.py', OLD_HELPER]
    result = {}
    for p in paths:
        name = p.relative_to(ROOT).as_posix()
        if p == Path(__file__).resolve():
            review = load(HERE / 'REGISTER-TOOL-REVIEW.json')
            require(producer == review['producer_source'] == 'a56ef7d9e96146a167afe84e5a8a6fcf904f40cb' and
                    review['producer_tool_sha256'] == digest(prep.git('show', producer + ':' + name)) ==
                    '904286f2ff03ba1b322c45c9a16d514aab547a18c6d4ac35d1de7e58030affc9' and
                    review['reviewed_tool_sha256'] == file_sha(p), 'EXACT_REGISTRATION_ONLY_TOOL_CORRECTION')
        else:
            require(p.read_bytes() == prep.git('show', producer + ':' + name), 'UNCHANGED_OFFICIAL_PREPARATION_SOURCE:' + name)
        result[name] = file_sha(p)
    result[(HERE / 'REGISTER-TOOL-REVIEW.json').relative_to(ROOT).as_posix()] = file_sha(HERE / 'REGISTER-TOOL-REVIEW.json')
    result[request.relative_to(ROOT).as_posix()] = file_sha(request)
    return result


def official(prepared, version, audit, request):
    request = request.resolve()
    frozen = request_data(request)
    require(version in (2103468, 2103469), 'EXACT_SELECTED_WATCHLIST_PAIR')
    producer, run_id = frozen['source_commit'], frozen['run_id']
    run = gh('actions/runs/' + str(run_id))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == producer and
            run['head_branch'] == 'work/infinity-watchlist-phase-b-20261108' and run['workflow_id'] == 397702717 and
            run['path'] == '.github/workflows/infinity-combined-release.yml', 'OFFICIAL_SOLE_OWNER_WORKFLOW_PREPARATION')
    expected = frozen['artifacts'][str(version)]
    row = gh('actions/artifacts/' + str(expected['id']))
    require(not row['expired'] and row['workflow_run']['id'] == run_id and all(row[k] == v for k, v in expected.items()), 'EXACT_OFFICIAL_PREPARED_ARTIFACT')
    archive = prepared.parent / (str(row['id']) + '.zip')
    require(archive.is_file() and file_sha(archive) == row['digest'].removeprefix('sha256:') and
            archive.stat().st_size == row['size_in_bytes'], 'OFFICIAL_ARTIFACT_ARCHIVE_DIGEST_AND_SIZE')
    with ZipFile(archive) as z:
        names = {n for n in validate_names(z) if not n.endswith('/')}
        require(names == {p.relative_to(prepared).as_posix() for p in prepared.rglob('*') if p.is_file()}, 'EXACT_PREPARED_FILE_SET')
        for name in names:
            with z.open(name) as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == file_sha(prepared / name), 'OFFICIAL_PREPARED_MEMBER:' + name)
    proof = load(prepared / 'PREPARATION.json')
    native_request = load(HERE / 'NATIVE-INPUT-REQUEST.json')
    wanted_native = native_request['native_sha256'] if version == 2103468 else prep.BASE_NATIVE
    require(proof['status'] == 'PASS_PREPARED_UNSIGNED_EXACT466_WATCHLIST_OR_FORWARD_RECOVERY' and
            proof['source'] == producer and proof['run_id'] == run_id and proof['versionCode'] == version and
            proof['baseline_sha256'] == prep.BASE_APK and proof['native_sha256'] == wanted_native,
            'OFFICIAL466_NATIVE_AND_SOURCE_BOUND_PREPARATION')
    require(proof['module_source_count'] == 80 and proof['Trakt'] == '1.2.8.1' and
            proof['CC'] == ('0.3.5.66' if version == 2103468 else '0.3.5.67') and
            proof['public_release'] is False and proof['registry_mutated'] is False, 'COMPLETE80_ENGINEERING_QA_ONLY')
    check = load(audit)
    require(file_sha(audit) == frozen['module_audit_sha256'] and
            check['status'] == 'PASS_THIRTEEN_REAL_JAVA80_FILE_UPGRADE_AND_FORWARD_RECOVERY_CASES' and
            len(check['cases']) == 13 and check['original_installer_changed'] is False and
            check['source_pins_sha256'] == proof['source_pins_sha256'] and check['original_signatures_verified'] is True,
            'EXACT_NEW80_REAL_UNCHANGED_INSTALLER_EVIDENCE')
    pins = load(HERE / 'RUNTIME-SOURCE-PINS.json')
    require(pins['native'] == {name: file_sha(HERE / 'native' / name) for name in prep.NATIVE_SOURCES} and
            pins['python'] == prep.hashes(HERE / 'overlay' / prep.CC), 'CURRENT_FROZEN_RUNTIME_SOURCE_PINS')
    for name, sha in pins['native'].items():
        require(digest(prep.git('show', native_request['source_commit'] + ':' + (HERE / 'native' / name).relative_to(ROOT).as_posix())) == sha,
                'COMPILED_SIX_SOURCE_BINDING:' + name)
    host = load(HERE / 'HOST-INTEGRATION-RESULT.json')
    native_host = load(HERE / 'NATIVE-HOST-RESULT.json')
    require(host['result'] == 'PASS' and host['unique_focused_host_cases'] == 28 and native_host['status'] == 'PASS' and
            native_host['source_sha256'] == pins['native'], 'SOURCE_BOUND_HOST_EVIDENCE')
    for name, sha in host['source_binding'].items():
        require(file_sha(HERE / name) == sha, 'PYTHON_HOST_SOURCE_BINDING:' + name)
    review = load(HERE / 'NATIVE-REVIEW.json')
    python_review = load(HERE / 'PYTHON-TARGETED-REVIEW.json')
    require(not review['findings'] and review['source_sha256'] == pins['native'] and
            python_review['source_sha256'] == pins['python'] and python_review['producer_pins_match_reviewed_map'], 'CLOSED_SOURCE_BOUND_REVIEWS')
    catalog = load(prepared / 'components/catalog.json')
    require(catalog['source'] == producer, 'OFFICIAL_COMPONENT_SOURCE')
    metas = {o: read_bundle(prepared / 'components' / r['file'], r) for o, r in catalog['bundles'].items()}
    baseline = json.loads(prep.git('show', prep.BASE + ':' + AUTHORITY_PATH))
    full = {key: value for meta in metas.values() for key, value in meta['payload'].items()}
    cc_prefix = 'member:assets/addons/' + prep.CC + '/'
    allowed = {'member:' + prep.LABEL, cc_prefix + 'addon.xml', cc_prefix + prep.module_bundle.MANIFEST,
               cc_prefix + prep.module_bundle.MANIFEST + '.sig', cc_prefix + prep.HELPER}
    if version == 2103468:
        allowed |= {'member:' + prep.NATIVE} | {cc_prefix + name for name in prep.PYTHON}
    require(set(full) - set(baseline['payload']) == {cc_prefix + prep.HELPER} and not set(baseline['payload']) - set(full), 'ONE_ADDED_HELPER_FULL_PAYLOAD_MAP')
    require(all(full[key] == value for key, value in baseline['payload'].items() if key not in allowed), 'ALL_UNDECLARED_NATIVE_CC_SEARCH_TRAKT_SKIN_DEX_PAYLOAD_IDENTICAL466')
    require(full['member:' + prep.NATIVE]['sha256'] == wanted_native, 'EXACT_MATCHED_CANDIDATE_OR_NATIVE466_RECOVERY')
    changed = {key.removeprefix('member:') for key in full if key.startswith('member:') and full[key] != baseline['payload'].get(key)}
    require(set(proof['changed_members']) == changed | {'AndroidManifest.xml'}, 'EXACT_DECLARED_FULL_MEMBER_CHANGES')
    for owner, meta in metas.items():
        with ZipFile(prepared / 'components' / catalog['bundles'][owner]['file']) as z:
            for name, member_row in meta['members'].items():
                raw = z.read('payload/' + name)
                normalized = prep.normalize_manifest(raw)[0] if name == 'AndroidManifest.xml' else raw
                require(meta['payload']['member:' + name]['sha256'] == digest(normalized), 'COMPLETE_COMPONENT_RAW_PAYLOAD_BINDING:' + name)
                if name in proof['changed_members']:
                    actual = set_version(raw, version) if name == 'AndroidManifest.xml' else raw
                    require(digest(actual) == proof['changed_members'][name], 'FROZEN_PREPARATION_MEMBER_HASH:' + name)
    with tempfile.TemporaryDirectory() as temp:
        modules = Path(temp) / 'modules'
        modules.mkdir()
        with ZipFile(prepared / 'components' / catalog['bundles']['INFINITY']['file']) as z:
            for name in metas['INFINITY']['members']:
                if any(name.startswith('assets/addons/' + aid + '/') for aid in prep.module_bundle.IDS):
                    target = modules / name.removeprefix('assets/addons/')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read('payload/' + name))
        payload, files = prep.module_bundle.build(modules)
        require(len(files) == 80 and digest(payload) == proof['module_manifest_sha256'] and
                payload == (modules / prep.CC / prep.module_bundle.MANIFEST).read_bytes(), 'COMPLETE_OFFICIAL80_MODULE_MANIFEST')
        prep.verify_signature(modules)
        require(prep.hashes(modules) == check['signed_inputs'][str(version)]['source_sha256'], 'EXACT_ACTUAL_JAVA_TESTED_SIGNED80_INPUTS')
        require(files[prep.CC + '/' + prep.HELPER] == (HERE / 'overlay' / prep.CC / prep.HELPER).read_bytes(), 'ONE_SAME_AUTHENTICATED_HELPER')
        if version == 2103468:
            require(all(digest(files[prep.CC + '/' + name]) == pins['python'][name] for name in prep.PYTHON), 'EXACT_FROZEN_CANDIDATE_PYTHON')
    source_bindings = bindings(producer, request)
    return frozen, row, proof, catalog, metas, check, source_bindings


def proposed(prepared, version, audit, request=REQUEST, previous=None):
    frozen, row, proof, catalog, metas, check, source_bindings = official(prepared, version, audit, request)
    previous = previous if previous is not None else load(ROOT / AUTHORITY_PATH)
    require(previous['candidate_versionCode'] == version - 1 and previous['generation'] == (54 if version == 2103468 else 55), 'EXACT_CURRENT_AUTHORITY_PREDECESSOR')
    canonical_previous = json.loads(prep.git('show', prep.AUTHORITY_SOURCE + ':' + AUTHORITY_PATH))
    if version == 2103468:
        require(previous == canonical_previous, 'EXACT_CANONICAL67_AUTHORITY_REQUIRED')
    else:
        require(previous['previous_authority_sha256'] == digest(canonical(canonical_previous)) and
                previous['owner_update_evidence']['producer_source'] == frozen['source_commit'] and
                previous['owner_update_evidence']['artifact'] == frozen['artifacts']['2103468'], 'EXACT_SAME_PAIR68_PREDECESSOR')
    for owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        require(catalog['bundles'][owner] == previous['bundle_catalog']['bundles'][owner], 'PROTECTED_OWNER_BUNDLE:' + owner)
    for name, wanted in previous['source_files'].items():
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
        a['bundle_sources'][owner] = dict(run_id=frozen['run_id'], build_source=frozen['source_commit'], artifact=row['name'], path='components/' + owner + '.zip')
    a['source_files'] = {name: file_sha(ROOT / name) for name in previous['source_files']}
    a['owner_update_evidence'] = dict(owner='INFINITY_WATCHLIST_SUCCESSOR' if version == 2103468 else 'INFINITY_WATCHLIST_FORWARD_RECOVERY_TO466',
        producer_run=frozen['run_id'], producer_source=frozen['source_commit'], source_files=source_bindings,
        artifact={k: row[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
        preparation_sha256=file_sha(prepared / 'PREPARATION.json'), native_sha256=proof['native_sha256'],
        module_upgrade_recovery_sha256=file_sha(audit), module_manifest_sha256=proof['module_manifest_sha256'], module_source_count=80,
        runtime_source_pins_sha256=file_sha(HERE / 'RUNTIME-SOURCE-PINS.json'), source_pins_sha256=proof['source_pins_sha256'],
        immutable_functional_base=2103466, engineering_QA_only=True, publication=False, public_release=False,
        Android='PENDING_SELECTED_WATCHLIST_AV_RESTART_INSTALL_OVER_AND_RECOVERY', physical_Fold='PENDING_ONE_FINAL_OWNER_ACCEPTANCE',
        accepted_pointer_updated=False,
        verification_toolchain=previous['owner_update_evidence'].get('verification_toolchain', dict(java_major=21, unchanged_original_DEX=True)))
    transition(previous, a, TARGETS)
    verify_evidence(a, lambda name: (ROOT / name).read_bytes())
    return a


def check_registered(prepared, version, audit, out, request=REQUEST):
    release_request = load(HERE / 'RELEASE-REQUEST.json')
    require(release_request['version'] == version and release_request['publication'] is False, 'ENGINEERING_QA_REQUEST_ONLY')
    current = load(ROOT / AUTHORITY_PATH)
    changed_at = command('git', '-C', ROOT, 'log', '-1', '--format=%H', '--', AUTHORITY_PATH)
    previous = json.loads(prep.git('show', changed_at + '^:' + AUTHORITY_PATH))
    require(proposed(prepared, version, audit, request, previous) == current, 'EXACT_REVIEWED_REGISTERED_WATCHLIST_PAIR_PAYLOAD')
    save(out, dict(status='PASS_EXACT_OFFICIAL_REGISTERED_WATCHLIST_ENGINEERING_QA_PAYLOAD', versionCode=version,
                   source=command('git', '-C', ROOT, 'rev-parse', 'HEAD'), publication=False, public_release=False, accepted_pointer_updated=False))


def compare(parent, candidate, prepared, out, sdk=None):
    out.mkdir(parents=True, exist_ok=True)
    result = prep.compare(parent, candidate, prepared / 'PREPARATION.json')
    result.update(publication=False, public_release=False, accepted_pointer_updated=False, engineering_QA_only=True)
    if sdk:
        signature = command(sdk / 'apksigner', 'verify', '--verbose', '--print-certs', candidate)
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT], 'ONE_ORIGINAL_PERMANENT_CERTIFICATE')
        (out / 'SIGNATURE.txt').write_text(signature + '\n')
        result['signing'] = 'VERIFIED_ONE_ORIGINAL_PERMANENT_CERTIFICATE'
    save(out / 'APK-PRESERVATION.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    for name in ('propose', 'check_registered'):
        p = commands.add_parser(name)
        for key in ('prepared', 'audit', 'out'):
            p.add_argument('--' + key, type=Path, required=True)
        p.add_argument('--version', type=int, required=True)
        p.add_argument('--request', type=Path, default=REQUEST)
        if name == 'propose':
            p.add_argument('--previous', type=Path)
    p = commands.add_parser('compare')
    for key in ('parent', 'candidate', 'prepared', 'out'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--sdk', type=Path)
    args = vars(parser.parse_args())
    operation = args.pop('operation')
    if operation == 'propose':
        output = args.pop('out')
        prior = args.pop('previous')
        save(output, proposed(previous=load(prior) if prior else None, **args))
    else:
        globals()[operation](**args)
