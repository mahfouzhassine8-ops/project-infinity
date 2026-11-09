"""Official prepared69-based experimental pair: proposals and checks only.

Reuses original authority transition/evidence, component and APK member gates.
No authority/ref mutation, signing, key access, build, or application execution.
The root-owned actual core-check clearance is mandatory; absent pins fail closed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUEST = HERE / 'PREPARED-PAIR-REQUEST.json'
WORKFLOW = '.github/workflows/infinity-combined-release.yml'
TARGETS = ['INFINITY', 'CHOOSER_SHELL']
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def command(*args):
    return subprocess.check_output(list(map(str, args)), text=True, timeout=60).strip()


def api(path):
    return json.loads(command('gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path))


def preparation():
    # Authenticate this task's producer before importing it. It in turn verifies
    # every immutable original executable dependency before importing them.
    request = load(HERE / 'MODULE-REQUEST.json')
    path = HERE / 'prepare_tracking_release.py'
    require(request['source_bindings'][path.relative_to(ROOT).as_posix()] == sha(path), 'REVIEWED_PREPARATION_TOOL_BEFORE_IMPORT')
    spec = importlib.util.spec_from_file_location('reviewed_tracking_preparation', path)
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    tools = prep.load_tools()
    import release_authority
    require(Path(release_authority.__file__).resolve() == prep.ISO / 'release_authority.py', 'ORIGINAL_AUTHORITY_IMPORT_ORIGIN')
    return prep, tools, release_authority


def request_data(path):
    require(path.resolve().parent == HERE, 'COMMITTED_TASK_PREPARED_REQUEST_REQUIRED')
    data = load(path)
    require(type(data['run_id']) is int and data['run_id'] > 0 and
            re.fullmatch('[0-9a-f]{40}', data['source_commit']) and
            set(data['artifacts']) == {'2103474', '2103475'} and
            re.fullmatch('[0-9a-f]{64}', data['module_audit_sha256']), 'FROZEN_OFFICIAL_FORWARD_PAIR')
    for row in data['artifacts'].values():
        require(set(row) == {'id', 'name', 'digest', 'size_in_bytes'} and type(row['id']) is int and row['id'] > 0 and
                re.fullmatch('sha256:[0-9a-f]{64}', row['digest']) and row['size_in_bytes'] > 0,
                'EXACT_PREPARED_ARTIFACT_DESCRIPTOR')
    return data


def bindings(prep, producer, module_producer, request):
    selected = load(HERE / 'MODULE-REQUEST.json')
    result = dict(selected['source_bindings'])
    own = Path(__file__).resolve().relative_to(ROOT).as_posix()
    require(own in result and prep.SOURCE_FREEZE.relative_to(ROOT).as_posix() in result, 'PREPARATION_BOUND_REGISTRATION_AND_SOURCE_PROOF')
    result[(HERE / 'MODULE-REQUEST.json').relative_to(ROOT).as_posix()] = sha(HERE / 'MODULE-REQUEST.json')
    require(prep.digest(prep.git('show', module_producer + ':' + WORKFLOW)) == selected['workflow_sha256'],
            'IMMUTABLE_ORIGINAL_MODULE_PRODUCER_WORKFLOW')
    for name, wanted in result.items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts and sha(ROOT / path) == wanted and
                (ROOT / path).read_bytes() == prep.git('show', producer + ':' + name) == prep.git('show', module_producer + ':' + name),
                'UNCHANGED_MODULE_AND_APK_PREPARATION_SOURCE:' + name)
    require((ROOT / WORKFLOW).read_bytes() == prep.git('show', producer + ':' + WORKFLOW), 'EXACT_OFFICIAL_APK_PREPARATION_WORKFLOW')
    result[WORKFLOW] = sha(ROOT / WORKFLOW)
    result[request.relative_to(ROOT).as_posix()] = sha(request)
    return result


def clearance(prep, proof, pins):
    return prep.core_clearance(proof, pins)


def official(prepared, version, audit, request):
    prep, tools, authority = preparation()
    require(version in (2103474, 2103475), 'EXACT_EXPERIMENTAL74_75_PAIR')
    frozen = request_data(request)
    producer, run_id = frozen['source_commit'], frozen['run_id']
    run = api('actions/runs/' + str(run_id))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == producer and
            run['head_branch'] == 'work/infinity-tracking-integration-20261108' and run['workflow_id'] == 397702717 and
            run['path'] == WORKFLOW, 'ORIGINAL_SOLE_OWNER_OFFICIAL_PREPARATION')
    wanted = frozen['artifacts'][str(version)]
    artifact = api('actions/artifacts/' + str(wanted['id']))
    require(not artifact['expired'] and artifact['workflow_run']['id'] == run_id and
            all(artifact[k] == v for k, v in wanted.items()), 'EXACT_OFFICIAL_PREPARED_ARTIFACT')
    archive = prepared.parent / (str(artifact['id']) + '.zip')
    require(archive.is_file() and sha(archive) == artifact['digest'].removeprefix('sha256:') and
            archive.stat().st_size == artifact['size_in_bytes'], 'WHOLE_PREPARED_ARCHIVE_DIGEST_AND_SIZE')
    with ZipFile(archive) as zipped:
        names = {n for n in tools.validate_names(zipped) if not n.endswith('/')}
        require(names == {p.relative_to(prepared).as_posix() for p in prepared.rglob('*') if p.is_file()}, 'EXACT_OFFICIAL_PREPARED_MEMBER_VECTOR')
        for name in names:
            with zipped.open(name) as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == sha(prepared / name), 'OFFICIAL_PREPARED_MEMBER:' + name)
    proof = load(prepared / 'PREPARATION.json')
    recovery = version == 2103475
    cc = '0.3.5.73' if recovery else '0.3.5.72'
    source, current = prep.source_inputs()
    require(proof['status'] == 'PREPARED_UNSIGNED_69_TRACKING_EXPERIMENTAL_PAIR' and
            proof['source'] == producer and proof['run_id'] == run_id and proof['versionCode'] == version and
            proof['production_source'] == source['production_source'] and proof['baseline_sha256'] == prep.BASE_APK and
            proof['native_sha256'] == prep.BASE_NATIVE and proof['module_source_count'] == 80 and proof['CC'] == cc and
            proof['Trakt'] == '1.2.8.1' and proof['recovery'] is recovery and proof['recovery_functional_base'] == 2103469 and proof['recovery_service_only_loading_guard'] is recovery and
            proof['public_release'] is False and proof['registry_mutated'] is False and proof['added_members'] == [],
            'EXACT69_NATIVE_SOURCE_AND_COMPLETE80_PREPARATION')
    audit_result = load(audit)
    selected = load(HERE / 'CURRENT-INPUT-FIXTURE.json')['selected_installer_cases']
    require(sha(audit) == frozen['module_audit_sha256'] == proof['module_audit_sha256'] and
            audit_result['status'] == 'PASS_FOUR_REAL_JAVA_CURRENT80_GENERATION_CASES' and
            [r['case'] for r in audit_result['cases']] == selected and len(selected) == 4 and
            audit_result['original_installer_changed'] is False and audit_result['complete80_signatures_verified'] is True and
            audit_result['source_pins_sha256'] == proof['source_pins_sha256'], 'EXACT_NEW_GENERATION_ORIGINAL_JAVA_AUDIT')
    catalog = load(prepared / 'components/catalog.json')
    require(catalog['source'] == producer, 'OFFICIAL_COMPONENT_SOURCE')
    components = {o: tools.read_bundle(prepared / 'components' / r['file'], r) for o, r in catalog['bundles'].items()}
    baseline = json.loads(prep.git('show', prep.BASE_SOURCE + ':' + prep.AUTHORITY))
    payload = {k: v for meta in components.values() for k, v in meta['payload'].items()}
    allowed = {'member:' + n for n in prep.allowed_members(recovery) if n != 'AndroidManifest.xml'}
    require(set(payload) == set(baseline['payload']) and
            all(payload[k] == v for k, v in baseline['payload'].items() if k not in allowed),
            'ALL_UNDECLARED_NATIVE_DEX_COBRA_SKIN_TRAKT_PROVIDER_BYTES_IDENTICAL69')
    changed = {k.removeprefix('member:') for k in payload if payload[k] != baseline['payload'][k]}
    require(set(proof['changed_members']) == changed | {'AndroidManifest.xml'}, 'EXACT_DECLARED_FULL_MEMBER_CHANGES')
    for owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        require(catalog['bundles'][owner] == baseline['bundle_catalog']['bundles'][owner], 'BYTE_IDENTICAL_PROTECTED_BUNDLE:' + owner)
    for owner, component in components.items():
        with ZipFile(prepared / 'components' / catalog['bundles'][owner]['file']) as zipped:
            for name in component['members']:
                raw = zipped.read('payload/' + name)
                normalized = tools.normalize_manifest(raw)[0] if name == 'AndroidManifest.xml' else raw
                require(component['payload']['member:' + name]['sha256'] == prep.digest(normalized), 'FULL_COMPONENT_PAYLOAD_HASH:' + name)
                if name in proof['changed_members']:
                    actual = tools.set_version(raw, version) if name == 'AndroidManifest.xml' else raw
                    require(prep.digest(actual) == proof['changed_members'][name], 'FROZEN_PREPARATION_MEMBER_HASH:' + name)
    with tempfile.TemporaryDirectory() as temporary:
        modules = Path(temporary) / 'modules'
        with ZipFile(prepared / 'components' / catalog['bundles']['INFINITY']['file']) as zipped:
            for name in components['INFINITY']['members']:
                if any(name.startswith('assets/addons/' + aid + '/') for aid in tools.module_bundle.IDS):
                    target = modules / name.removeprefix('assets/addons/')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zipped.read('payload/' + name))
        manifest, files = tools.module_bundle.build(modules)
        require(len(files) == 80 and prep.digest(manifest) == proof['module_manifest_sha256'] and
                manifest == (modules / prep.CC / prep.MANIFEST).read_bytes(), 'OFFICIAL_COMPLETE80_MANIFEST')
        prep.verify_signature(modules)
        require(prep.hashes(modules) == audit_result['signed_inputs'][str(version)]['source_sha256'], 'EXACT_ACTUALLY_TESTED_SIGNED80_INPUTS')
        expected = {n: prep.digest(files[prep.CC + '/' + n]) for n in prep.PYTHON}
        wanted_map = {n: prep.digest(prep.recovery_source(n)) for n in prep.PYTHON} if recovery else current
        require(expected == wanted_map, 'EXACT_CANDIDATE_OR_ORIGINAL69_RECOVERY_SOURCE3')
    module_pin_path = HERE / 'TRACKING-MODULE-FIXTURE-PIN.json'
    module_pin = load(module_pin_path)
    require(proof['signed_module_artifact'] == module_pin and proof['module_producer_source'] == module_pin['source'] and
            proof['source_pins_sha256'] == module_pin['source_pins_sha256'], 'UNCHANGED_SIGNED_MODULE_PRODUCER_PROVENANCE')
    module_run = api('actions/runs/' + str(module_pin['run']))
    module_artifact = api('actions/artifacts/' + str(module_pin['id']))
    require(module_run['head_sha'] == module_pin['source'] and module_run['workflow_id'] == 397702717 and
            module_run['status'] == 'completed' and module_run['conclusion'] == 'success' and
            not module_artifact['expired'] and module_artifact['workflow_run']['id'] == module_pin['run'] and
            all(module_artifact[k] == module_pin[k] for k in ('id', 'name', 'digest', 'size_in_bytes')),
            'ACTUAL_ORIGINAL_SIGNED80_PRODUCER_AND_ARTIFACT')
    sources = bindings(prep, producer, module_pin['source'], request)
    sources[module_pin_path.relative_to(ROOT).as_posix()] = sha(module_pin_path)
    clear, clearance_sources = clearance(prep, proof, current)
    sources.update(clearance_sources)
    return prep, tools, authority, frozen, artifact, proof, catalog, components, sources, clear


def proposed(prepared, version, audit, request=REQUEST, previous=None):
    prep, tools, authority, frozen, artifact, proof, catalog, components, sources, clear = official(prepared, version, audit, request)
    previous = previous if previous is not None else load(ROOT / prep.AUTHORITY)
    canonical = json.loads(prep.git('show', prep.BASE_SOURCE + ':' + prep.AUTHORITY))
    if version == 2103474:
        require(previous == canonical, 'EXACT_CANONICAL69_AUTHORITY_PREDECESSOR')
    else:
        require(previous['candidate_versionCode'] == 2103474 and previous['generation'] == 57 and
                previous['previous_authority_sha256'] == prep.digest(tools.canonical(canonical)) and
                previous['owner_update_evidence']['producer_source'] == frozen['source_commit'] and
                previous['owner_update_evidence']['artifact'] == frozen['artifacts']['2103474'], 'EXACT_SAME_PAIR74_AUTHORITY_PREDECESSOR')
    for name, wanted in previous['source_files'].items():
        require(sha(ROOT / name) == wanted, 'UNCHANGED_ORIGINAL_RELEASE_IMPLEMENTATION:' + name)
    result = copy.deepcopy(previous)
    result.update(generation=previous['generation'] + 1, last_issued_versionCode=previous['candidate_versionCode'],
        candidate_versionCode=version, previous_authority_sha256=prep.digest(tools.canonical(previous)),
        target_owners=TARGETS, update_kind='owner_update',
        payload={k: v for meta in components.values() for k, v in meta['payload'].items()}, bundle_catalog=catalog,
        experience_version_labels={'INFINITY': version, 'COBRA': 2103445}, workflow_sha256=sha(ROOT / WORKFLOW))
    for owner in TARGETS:
        result['components'][owner] = {k: components[owner][k] for k in ('version', 'digest', 'approved_source', 'settings_schema')}
        result['components'][owner]['revision'] = previous['components'][owner]['revision'] + 1
        result['bundle_sources'][owner] = dict(run_id=frozen['run_id'], build_source=frozen['source_commit'], artifact=artifact['name'], path='components/' + owner + '.zip')
    result['owner_update_evidence'] = dict(owner='INFINITY_TRACKING_EXPERIMENTAL' if version == 2103474 else 'INFINITY_TRACKING_FORWARD_RECOVERY_TO69',
        producer_run=frozen['run_id'], producer_source=frozen['source_commit'], source_files=sources,
        artifact={k: artifact[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
        preparation_sha256=sha(prepared / 'PREPARATION.json'), native_sha256=prep.BASE_NATIVE,
        module_upgrade_recovery_sha256=sha(audit), module_manifest_sha256=proof['module_manifest_sha256'], module_source_count=80,
        source_pins_sha256=proof['source_pins_sha256'], immutable_functional_base=2103469,
        production_source=proof['production_source'], experimental=True, engineering_QA_only=True,
        remaining_unverified=clear['remaining_unverified'], core_checks=clear['core_checks'],
        signed_APK_install_forward_recovery='PENDING_POST_SIGN_OWNER_DELIVERY', owner_delivery_cleared=False,
        publication=False, public_release=False, accepted_pointer_updated=False, physical_Fold='PENDING_ONE_FINAL_OWNER_ACCEPTANCE',
        verification_toolchain=previous['owner_update_evidence']['verification_toolchain'])
    # These original gates are intentionally unmodified, including formal
    # release_blockers==[]; disclosures never turn a rejected gate into PASS.
    authority.transition(previous, result, TARGETS)
    authority.verify_evidence(result, lambda name: (ROOT / name).read_bytes())
    return result


def check_registered(prepared, version, audit, out, request=REQUEST):
    prep, _, _ = preparation()
    current = load(ROOT / prep.AUTHORITY)
    changed = command('git', '-C', ROOT, 'log', '-1', '--format=%H', '--', prep.AUTHORITY)
    previous = json.loads(prep.git('show', changed + '^:' + prep.AUTHORITY))
    require(proposed(prepared, version, audit, request, previous) == current, 'EXACT_REGISTERED_OFFICIAL_EXPERIMENTAL_PAIR')
    save(out, dict(status='EXACT_REGISTERED_OFFICIAL_EXPERIMENTAL_PAYLOAD', versionCode=version,
        publication=False, accepted_pointer_updated=False))


def compare(parent, candidate, prepared, out, sdk=None):
    prep, _, _ = preparation()
    result = prep.compare(parent, candidate, prepared / 'PREPARATION.json')
    out.mkdir(parents=True, exist_ok=True)
    if sdk:
        certificate = command(sdk / 'apksigner', 'verify', '--verbose', '--print-certs', candidate)
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', certificate) == [CERT], 'ONE_ORIGINAL_PERMANENT_CERTIFICATE')
        save(out / 'CERTIFICATE.json', dict(status='VERIFIED_ORIGINAL_CERTIFICATE', output=certificate))
    save(out / 'APK-PRESERVATION.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='operation', required=True)
    for name in ('propose', 'check_registered'):
        mode = modes.add_parser(name)
        for field in ('prepared', 'audit', 'out'):
            mode.add_argument('--' + field, type=Path, required=True)
        mode.add_argument('--version', type=int, required=True)
        mode.add_argument('--request', type=Path, default=REQUEST)
        if name == 'propose':
            mode.add_argument('--previous', type=Path)
    mode = modes.add_parser('compare')
    for field in ('parent', 'candidate', 'prepared', 'out'):
        mode.add_argument('--' + field, type=Path, required=True)
    mode.add_argument('--sdk', type=Path)
    args = vars(parser.parse_args())
    operation = args.pop('operation')
    if operation == 'propose':
        output, previous = args.pop('out'), args.pop('previous')
        save(output, proposed(previous=load(previous) if previous else None, **args))
    else:
        globals()[operation](**args)
