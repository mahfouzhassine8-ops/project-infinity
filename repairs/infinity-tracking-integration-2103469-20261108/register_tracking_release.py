"""Official prepared69-based experimental pair: proposals and checks only.

Reuses original authority transition/evidence, component and APK member gates.
No authority/ref mutation, signing, key access, build, or application execution.
A root-owned, source-bound experimental disposition is mandatory; absent pins
fail closed. Unexecuted behavior remains explicit and blocks acceptance claims.
"""
import argparse
import ast
import os
import stat
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_TASK = Path('repairs/infinity-tracking-integration-2103469-20261108')
if HERE.relative_to(ROOT) != SOURCE_TASK:
    raise RuntimeError('REGISTRATION_HELPER_MUST_USE_IMMUTABLE_PRODUCER_TASK_PATH')
REQUEST = HERE / 'PREPARED-PAIR-REQUEST.json'
WORKFLOW = '.github/workflows/infinity-combined-release.yml'
TARGETS = ['INFINITY', 'CHOOSER_SHELL']
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE_APK = '804eebc57af2e4ef4e5418b56994bda64eb7fd7e7f2c0653b5c6e2a9f7833058'
PREPARED_PRODUCER = '0245abf5e4a10d490bd38677b118e873c01e5504'
REGISTERED74 = 'ae0a6c205eb948b240872613220f38309165e7da'
REGISTERED74_SHA256 = '86dafbd9923adcc82b3c66075d3236a9f65b436dd15e8edbca5a7ea7a42fb670'
CORRECTION = HERE / 'PACKAGING-PATH-CORRECTION-REVIEW.json'


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
    request = load(HERE / 'APK-PREPARE-REQUEST.json')
    require(request['enabled'] is True and request['operation'] == 'prepare-tracking-experimental74-75', 'ROOT_REVIEWED_APK_PREPARATION_ENABLED')
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


def packaging_correction(prep):
    """Two reviewed packaging-only exceptions; frozen payload inputs stay exact."""
    require(CORRECTION.is_file(), 'REVIEWED_POSTPRODUCER_PACKAGING_CORRECTION_REQUIRED')
    review = load(CORRECTION)
    require(review['status'] == 'ROOT_ASTRA_REVIEWED_PACKAGING_PATH_CORRECTION_ONLY' and
            review['producer_source'] == PREPARED_PRODUCER and review['registration74_commit'] == REGISTERED74 and
            review['registration74_sha256'] == REGISTERED74_SHA256, 'EXACT_PACKAGING_CORRECTION_SCOPE')
    own = Path(__file__).resolve().relative_to(ROOT).as_posix()
    request = (HERE / 'APK-PREPARE-REQUEST.json').relative_to(ROOT).as_posix()
    expected_old = {own: 'c321719d20dd7984f4f3d5ceabc984a9087a29d5da71c1fc6b8cb57d852092c8',
                    WORKFLOW: '5a95562b576315c43585b43af76d4c4afe227c8920b0f7de46c42b902f6bd159'}
    require(review['historical_sha256'] == expected_old and set(review['reviewed_sha256']) == set(expected_old) and
            review['producer_request_sha256'] == '4b46e83b9163d709fa8c3d073949b47c64ea3f78e612db2a40533dae8d391d7b',
            'ONLY_EXACT_HELPER_AND_WORKFLOW_CORRECTION')
    for name, wanted in expected_old.items():
        require(prep.digest(prep.git('show', PREPARED_PRODUCER + ':' + name)) == wanted and
                sha(ROOT / name) == review['reviewed_sha256'][name], 'EXACT_REVIEWED_PACKAGING_BYTES:' + name)
    require(sha(ROOT / request) == review['producer_request_sha256'] ==
            prep.digest(prep.git('show', PREPARED_PRODUCER + ':' + request)), 'IMMUTABLE_PRODUCER_REQUEST')
    old = prep.git('show', PREPARED_PRODUCER + ':' + WORKFLOW)
    before = b'generation={2103474:57,2103475:58}[version]'
    after = b'generation={2103474:58,2103475:59}[version]'
    require(old.count(before) == 1 and (ROOT / WORKFLOW).read_bytes() == old.replace(before, after, 1),
            'ONLY_REVIEWED_GENERATION_LITERAL_WORKFLOW_CHANGE')
    return review


def preserved_module_generator(prep, module_producer):
    path = HERE / 'prepare_tracking_release.py'
    old = prep.git('show', module_producer + ':' + path.relative_to(ROOT).as_posix())
    def payload_nodes(raw):
        return [ast.dump(n, include_attributes=False) for n in ast.parse(raw).body
                if not (isinstance(n, ast.FunctionDef) and n.name == 'core_clearance')]
    require(payload_nodes(old) == payload_nodes(path.read_bytes()), 'ONLY_NEW_EXPERIMENTAL_DISPOSITION_MAY_CHANGE_AFTER_MODULE_PREPARATION')
    historical_path = (HERE / 'MODULE-REQUEST.json').relative_to(ROOT).as_posix()
    historical = json.loads(prep.git('show', module_producer + ':' + historical_path))
    for name, wanted in historical['source_bindings'].items():
        require(prep.digest(prep.git('show', module_producer + ':' + name)) == wanted,
                'IMMUTABLE_HISTORICAL_MODULE_PREPARATION_INPUT:' + name)
    require(prep.digest(prep.git('show', module_producer + ':' + WORKFLOW)) == historical['workflow_sha256'],
            'IMMUTABLE_MODULE_PRODUCER_WORKFLOW')
    return historical


def apk_request(prep):
    path = HERE / 'APK-PREPARE-REQUEST.json'
    request = load(path)
    require(request['operation'] == 'prepare-tracking-experimental74-75' and request['enabled'] is True and
            request['candidate_versionCode'] == 2103474 and request['recovery_versionCode'] == 2103475 and
            request['APK_signing'] is False and request['registry_mutation'] is False and request['publication'] is False,
            'EXACT_REVIEWED_UNSIGNED_EXPERIMENTAL_PREPARATION_REQUEST')
    module_pin = load(HERE / 'TRACKING-MODULE-FIXTURE-PIN.json')
    historical = preserved_module_generator(prep, module_pin['source'])
    expected = set(historical['source_bindings']) | {
        (HERE / n).relative_to(ROOT).as_posix() for n in ('TRACKING-MODULE-FIXTURE-PIN.json',
            'EXPERIMENTAL-RELEASE-CLEARANCE.json', 'MODULE-REQUEST.json',
            'evidence/signed-c1-fixture-42602243785/MODULE-UPGRADE-RECOVERY.json',
            'evidence/signed-c1-fixture-42602243785/SOURCE-PINS.json',
            'evidence/signed-c1-fixture-42602243785/MODULE-FIXTURE.json',
            'EXPERIMENTAL-ADMISSION-GUARDS.json', 'OBSERVED-SCHEMA2-COMPATIBILITY.json',
            'OBSERVED-SCHEMA2-COMPATIBILITY-SELECTION.json')}
    require(set(request['source_bindings']) == expected, 'EXACT_APK_PREPARATION_INPUT_BINDINGS')
    for name, wanted in request['source_bindings'].items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'REVIEWED_APK_PREPARATION_PATH')
        if name == Path(__file__).resolve().relative_to(ROOT).as_posix() and sha(ROOT / relative) != wanted:
            require(packaging_correction(prep)['historical_sha256'][name] == wanted, 'EXACT_REGISTRATION_ONLY_CORRECTION')
        else:
            require(sha(ROOT / relative) == wanted, 'REVIEWED_APK_PREPARATION_INPUT:' + name)
    if sha(ROOT / WORKFLOW) != request['workflow_sha256']:
        require(packaging_correction(prep)['historical_sha256'][WORKFLOW] == request['workflow_sha256'],
                'EXACT_POSTPRODUCER_WORKFLOW_CORRECTION')
    return request


def bindings(prep, producer, module_producer, request):
    request = request.resolve()
    selected = apk_request(prep)
    result = dict(selected['source_bindings'])
    for name, wanted in result.items():
        original = prep.git('show', producer + ':' + name)
        if name == Path(__file__).resolve().relative_to(ROOT).as_posix() and (ROOT / name).read_bytes() != original:
            review = packaging_correction(prep)
            require(producer == PREPARED_PRODUCER and prep.digest(original) == review['historical_sha256'][name],
                    'EXACT_POSTPRODUCER_REGISTRATION_HELPER')
            result[name] = sha(ROOT / name)
        else:
            require((ROOT / name).read_bytes() == original, 'OFFICIAL_APK_PRODUCER_SOURCE:' + name)
    prepare_request = HERE / 'APK-PREPARE-REQUEST.json'
    require(prepare_request.read_bytes() == prep.git('show', producer + ':' + prepare_request.relative_to(ROOT).as_posix()),
            'OFFICIAL_APK_PREPARATION_REQUEST')
    if (ROOT / WORKFLOW).read_bytes() != prep.git('show', producer + ':' + WORKFLOW):
        require(producer == PREPARED_PRODUCER, 'EXACT_CORRECTED_PRODUCER')
        packaging_correction(prep)
        result[CORRECTION.relative_to(ROOT).as_posix()] = sha(CORRECTION)
    result[prepare_request.relative_to(ROOT).as_posix()] = sha(prepare_request)
    result[WORKFLOW] = sha(ROOT / WORKFLOW)
    result[request.relative_to(ROOT).as_posix()] = sha(request)
    return result


def clearance(prep, proof, pins):
    return prep.core_clearance(proof, pins)


def observed_compatibility(observation, baseline_apk, out):
    """One selected actual TV/Watchlist semantic case; no movie progress claim."""
    selection_path = HERE / 'OBSERVED-SCHEMA2-COMPATIBILITY-SELECTION.json'
    selection = load(selection_path)
    require(selection['selected_before_execution'] is True and selection['observation_sha256'] == sha(observation) and
            selection['scope'] == 'OBSERVED_TV_SOURCE_PARENT_AND_BOTH_QUERY_WATCHLISTS_ONLY' and
            not out.exists() and sha(baseline_apk) == BASE_APK, 'EXACT_SELECTED_ACTUAL_OBSERVATION_AND_SIGNED69')
    data = load(observation)['data']
    require(data['schema'] == 2 and isinstance(data['items'], dict) and
            not any(row.get('media') == 'movie' for row in data['items'].values()), 'NO_OBSERVED_MOVIE_PROGRESS_IN_THIS_CASE')
    require(any(row.get('media') == 'tv' and row.get('position', 0) > 0 and row.get('source_parent')
                for row in data['items'].values()) and
            {'tv', 'movie'} <= {row.get('media') for row in data['watchlist'].values()} and
            any('?' in row.get('source', '') for row in data['watchlist'].values()), 'ACTUAL_TV_PROGRESS_AND_QUERY_WATCHLISTS_REQUIRED')
    with ZipFile(baseline_apk) as zipped:
        raw = zipped.read('assets/addons/script.infinity.commandcenter/resume_hub.py')
    require(raw == (HERE / 'reference/script.infinity.commandcenter/resume_hub.py').read_bytes(), 'EXACT_ORIGINAL69_HUB_SOURCE')
    names = {'_dict', '_normalize', 'load', '_now', 'save'}
    nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == names, 'EXACT_SELECTED_ORIGINAL69_READ_SAVE_FUNCTIONS')
    env = dict(Path=Path, time=time, SCHEMA=2, CONTINUE_FILE='continue-watching.json',
               KEY_RE=re.compile(r'^[a-f0-9]{64}$'), _view_lock=threading.RLock(), _view_cache=None,
               read_json=lambda path, default: json.loads(path.read_text()),
               atomic_json=lambda path, value: path.write_text(json.dumps(value, sort_keys=True) + '\n'))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'signed69/resume_hub.py', 'exec'), env)
    semantic = lambda value: {k: v for k, v in value.items() if k not in ('revision', 'updated')}
    with tempfile.TemporaryDirectory() as temporary:
        profile = Path(temporary)
        (profile / env['CONTINUE_FILE']).write_text(json.dumps(data))
        before = env['load'](profile)
        require(semantic(before) == semantic(data), 'ORIGINAL69_READ_RETAINS_ACTUAL_OBSERVED_DATA')
        env['save'](profile, before)
        after = env['load'](profile)
        require(semantic(after) == semantic(data), 'ORIGINAL69_SAVE_RETAINS_ACTUAL_RECORDS_POSITIONS_PARENT_MEMBERSHIPS')
    report = dict(status='PASS_OBSERVED_TV_AND_WATCHLIST_ONLY', observation_sha256=sha(observation),
        observation_path=observation.resolve().relative_to(ROOT).as_posix(), source_run=42593220047,
        original69_APK_sha256=BASE_APK, original69_hub_sha256=hashlib.sha256(raw).hexdigest(),
        selection_sha256=sha(selection_path), movie_progress='NOT_OBSERVED',
        TV_positions_source_parent_and_watchlist_memberships_preserved=True,
        semantic_data_sha256=hashlib.sha256(json.dumps(semantic(data), sort_keys=True).encode()).hexdigest(),
        host_JSON_transport_only=True, runtime='NOT_RUN', checkpoint_durability='NOT_RUN',
        C1_playback_or_service_survival='NOT_RUN_NATIVE_CONSTRUCTOR_BLOCK', Android_recovery='NOT_RUN',
        display='Original69 display/classification differences unverified', owner_data_modified=False)
    save(out, report)
    return report


def prepare_official(out, sdk):
    """Selected original workflow's unsigned APK preparation; no credentials."""
    prep, tools, _ = preparation()
    selected = apk_request(prep)
    head = prep.git('rev-parse', 'HEAD').decode().strip()
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-tracking-integration-20261108' and
            os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and os.environ.get('GITHUB_SHA') == head and
            not prep.git('status', '--porcelain', '--untracked-files=no').strip(), 'CLEAN_EXACT_SELECTED_APK_PRODUCER')
    this = api('actions/runs/' + os.environ['GITHUB_RUN_ID'])
    require(this['head_sha'] == head and this['workflow_id'] == 397702717 and this['path'] == WORKFLOW,
            'SOLE_ORIGINAL_WORKFLOW_UNSIGNED_PREPARATION')
    for ref in ('work/infinity-2103460-nine-corrections-20261106', 'locks/infinity-2103469-protected-recovery-20261108'):
        require(api('git/ref/heads/' + ref)['object']['sha'] == prep.BASE_SOURCE, 'UNCHANGED69_AUTHORITY_AND_PROTECTED_REF')
    module_pin = load(HERE / 'TRACKING-MODULE-FIXTURE-PIN.json')
    clearance(prep, dict(production_source=prep.source_inputs()[0]['production_source'],
                        source_pins_sha256=module_pin['source_pins_sha256']), prep.source_inputs()[1])
    # Preserve every prior job, including the exact original module signer.
    old = prep.git('show', module_pin['source'] + ':' + WORKFLOW).decode()
    expected = old.replace('prepare-tracking-modules]', 'prepare-tracking-modules, prepare-tracking-release, sign-tracking]', 1)
    current = (ROOT / WORKFLOW).read_text()
    require(current.startswith(expected.rstrip() + '\n') and
            re.findall(r'^  ([A-Za-z0-9_-]+):', current[len(expected.rstrip()):], re.M) ==
            ['prepare-tracking-release', 'sign-tracking'], 'ALL_EXISTING_ORIGINAL_WORKFLOW_JOBS_UNCHANGED')
    fixture_path = HERE / 'tracking_module_fixture.py'
    historical = preserved_module_generator(prep, module_pin['source'])
    require(sha(fixture_path) == historical['source_bindings'][fixture_path.relative_to(ROOT).as_posix()],
            'ORIGINAL_REVIEWED_MODULE_DOWNLOAD_ADAPTER')
    spec = importlib.util.spec_from_file_location('original_tracking_fixture_download', fixture_path)
    fixture_tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture_tool)
    require(not out.exists(), 'FRESH_OFFICIAL_UNSIGNED_PREPARATION')
    out.mkdir(parents=True)
    baseline = fixture_tool.download(fixture_tool.SIGNED, out / 'signed69')
    prepared = fixture_tool.download(fixture_tool.PREPARED, out / 'prepared69')
    fixture = fixture_tool.download(module_pin, out / 'signed80')
    apk = baseline / 'Infinity-2103469-Combined-Original-Signer.apk'
    cert = command(sdk / 'apksigner', 'verify', '--verbose', '--print-certs', apk)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', cert) == [CERT], 'EXACT_ORIGINAL69_CERTIFICATE')
    (out / 'ORIGINAL69-SIGNATURE.txt').write_text(cert + '\n')
    audit = fixture / 'module-audit/MODULE-UPGRADE-RECOVERY.json'
    prep.finish(apk, prepared, fixture / 'pair/VERSION-ADMISSION.json', fixture,
                HERE / 'TRACKING-MODULE-FIXTURE-PIN.json', out / 'pair', audit)
    for version in (2103474, 2103475):
        publish = out / 'pair' / str(version) / 'publish'
        # These are exact copies; no signed-module SOURCE-PINS rewrite occurs.
        for source, name in ((fixture / 'pair/SOURCE-PINS.json', 'MODULE-SOURCE-PINS.json'),
                             (audit, 'MODULE-UPGRADE-RECOVERY.json'),
                             (HERE / 'EXPERIMENTAL-RELEASE-CLEARANCE.json', 'EXPERIMENTAL-RELEASE-CLEARANCE.json')):
            (publish / name).write_bytes(source.read_bytes())
    save(out / 'APK-PREPARATION-ADMISSION.json', dict(status='ORIGINAL69_UNSIGNED_EXPERIMENTAL_PAIR_PREPARED',
        source=head, module_producer_source=module_pin['source'], module_source_pins_sha256=module_pin['source_pins_sha256'],
        request_sha256=sha(HERE / 'APK-PREPARE-REQUEST.json'), APK_signing=False,
        registry_mutated=False, publication=False, owner_delivery_cleared=False))


def download_prepared(out, version, request=REQUEST):
    """Original artifact digest/member intake before the original APK gate."""
    prep, tools, _ = preparation()
    frozen = request_data(request)
    require(version in (2103474, 2103475) and not out.exists(), 'EXACT_FRESH_PREPARED_PAIR_DOWNLOAD')
    run = api('actions/runs/' + str(frozen['run_id']))
    require(run['workflow_id'] == 397702717 and run['path'] == WORKFLOW and
            run['head_branch'] == 'work/infinity-tracking-integration-20261108' and
            run['head_sha'] == frozen['source_commit'] and run['status'] == 'completed' and run['conclusion'] == 'success',
            'EXACT_OFFICIAL_APK_PREPARATION_PRODUCER')
    row = frozen['artifacts'][str(version)]
    actual = api('actions/artifacts/' + str(row['id']))
    require(not actual['expired'] and actual['workflow_run']['id'] == frozen['run_id'] and
            all(actual[k] == value for k, value in row.items()), 'EXACT_LIVE_PREPARED_ARTIFACT')
    out.mkdir(parents=True)
    archive = out / (str(row['id']) + '.zip')
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/' + str(row['id']) + '/zip'],
                       check=True, stdout=stream, timeout=600)
    require(sha(archive) == row['digest'].removeprefix('sha256:') and archive.stat().st_size == row['size_in_bytes'],
            'EXACT_WHOLE_PREPARED_ARCHIVE')
    dest = out / str(version)
    with ZipFile(archive) as zipped:
        names = tools.validate_names(zipped)
        require(0 < len(names) <= 100000 and sum(i.file_size for i in zipped.infolist()) <= 8 * 1024**3 and
                all(not stat.S_ISLNK(i.external_attr >> 16) and not i.flag_bits & 1 for i in zipped.infolist()),
                'BOUNDED_SAFE_OFFICIAL_PREPARED_ARCHIVE')
        dest.mkdir()
        zipped.extractall(dest)
    return dest


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


def original_registration74(prep):
    raw = prep.git('show', REGISTERED74 + ':' + prep.AUTHORITY)
    require(prep.digest(raw) == REGISTERED74_SHA256, 'EXACT_ACTUAL_REGISTERED74_AUTHORITY')
    value = json.loads(raw)
    require(value['generation'] == 57 and value['candidate_versionCode'] == 2103474 and
            value['last_issued_versionCode'] == 2103469 and value['update_kind'] == 'owner_update',
            'REGISTERED74_UNISSUED_VERSION_STATE')
    return value


def refreshed_authority(prep, tools, authority, previous, sources):
    packaging_correction(prep)
    require(previous == original_registration74(prep), 'EXACT_GEN57_REFRESH_PREDECESSOR')
    result = copy.deepcopy(previous)
    result.update(generation=58, update_kind='evidence_refresh', target_owners=[],
                  previous_authority_sha256=prep.digest(tools.canonical(previous)), workflow_sha256=sha(ROOT / WORKFLOW))
    result['owner_update_evidence']['source_files'] = sources
    result['owner_update_evidence']['packaging_correction_review_sha256'] = sha(CORRECTION)
    # No payload/component/version/reservation/contract field is reconstructed
    # or advanced. The unchanged original transition admits evidence only.
    authority.transition(previous, result, [])
    authority.verify_evidence(result, lambda name: (ROOT / name).read_bytes())
    return result


def refresh_proposal(prepared, version, audit, request=REQUEST, previous=None):
    require(version == 2103474, 'EVIDENCE_REFRESH_ONLY_REGISTERED74')
    prep, tools, authority, _, _, _, _, _, sources, _ = official(prepared, version, audit, request)
    previous = previous if previous is not None else load(ROOT / prep.AUTHORITY)
    return refreshed_authority(prep, tools, authority, previous, sources)


def proposed(prepared, version, audit, request=REQUEST, previous=None):
    prep, tools, authority, frozen, artifact, proof, catalog, components, sources, clear = official(prepared, version, audit, request)
    previous = previous if previous is not None else load(ROOT / prep.AUTHORITY)
    canonical = json.loads(prep.git('show', prep.BASE_SOURCE + ':' + prep.AUTHORITY))
    if version == 2103474:
        require(previous == canonical, 'EXACT_CANONICAL69_AUTHORITY_PREDECESSOR')
    else:
        require(previous == refreshed_authority(prep, tools, authority, original_registration74(prep), sources) and
                previous['candidate_versionCode'] == 2103474 and previous['generation'] == 58 and
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
        runtime_disposition=clear['status'],
        schema2_compatibility_disposition=clear['core_checks'].get('actual_schema2_recovery_read_save', 'NOT_RUN'),
        available_schema2_preservation=clear.get('available_schema2_preservation'),
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
    expected = (refresh_proposal(prepared, version, audit, request, previous)
                if current.get('update_kind') == 'evidence_refresh' else proposed(prepared, version, audit, request, previous))
    require(expected == current, 'EXACT_REGISTERED_OFFICIAL_EXPERIMENTAL_PAIR')
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
    mode = modes.add_parser('observed_compatibility')
    for field in ('observation', 'baseline-apk', 'out'):
        mode.add_argument('--' + field, type=Path, required=True)
    mode = modes.add_parser('prepare_official')
    mode.add_argument('--out', type=Path, required=True)
    mode.add_argument('--sdk', type=Path, required=True)
    mode = modes.add_parser('download_prepared')
    mode.add_argument('--out', type=Path, required=True)
    mode.add_argument('--version', type=int, required=True)
    mode.add_argument('--request', type=Path, default=REQUEST)
    for name in ('propose', 'refresh', 'check_registered'):
        mode = modes.add_parser(name)
        for field in ('prepared', 'audit', 'out'):
            mode.add_argument('--' + field, type=Path, required=True)
        mode.add_argument('--version', type=int, required=True)
        mode.add_argument('--request', type=Path, default=REQUEST)
        if name in ('propose', 'refresh'):
            mode.add_argument('--previous', type=Path)
    mode = modes.add_parser('compare')
    for field in ('parent', 'candidate', 'prepared', 'out'):
        mode.add_argument('--' + field, type=Path, required=True)
    mode.add_argument('--sdk', type=Path)
    args = vars(parser.parse_args())
    operation = args.pop('operation')
    if operation in ('propose', 'refresh'):
        output, previous = args.pop('out'), args.pop('previous')
        proposal = refresh_proposal if operation == 'refresh' else proposed
        save(output, proposal(previous=load(previous) if previous else None, **args))
    else:
        globals()[operation](**args)
