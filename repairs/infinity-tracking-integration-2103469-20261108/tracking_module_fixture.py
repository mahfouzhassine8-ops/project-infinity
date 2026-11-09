"""Original-key module fixture admission for disposable Android engineering.

Never builds/signs an APK, changes release authority, or opens a private key.
The sole original owner workflow performs the existing Java signing call.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = 'mahfouzhassine8-ops/project-infinity'
BRANCH = 'work/infinity-tracking-integration-20261108'
AUTHORITY = 'a76e29b84996304241e6b309d56a31e6659ad190'
WORKFLOW = '.github/workflows/infinity-combined-release.yml'
CC = 'script.infinity.commandcenter'
REQUEST = HERE / 'MODULE-REQUEST.json'
SOURCES = ('plugin.py', 'resume_hub.py', 'service.py')
REVIEWED = '2e52b7befd0228a09449f79eaf9774a3946dfa1c'
BRIDGE_SOURCE = 'e410f30ba9e38182e4e77810e5237e5442cbd31a'
PRIOR_FIXTURE_SOURCE = 'ce88dc9dd16aad4d0bdd2e4f9ce1bcbb9f203cd4'
PRIOR_FIXTURE_RUN = 42588102830
SELECTION = ('signed69_to_tracking_complete80_and_data', 'same_candidate_idempotent_noop',
             'forward_recovery_restores69_with_loading_guard_and_data',
             'older_candidate_retains_authenticated_recovery')
SIGNED = dict(run=42514440156, source=AUTHORITY, id=13631340281,
    name='Infinity-Watchlist-Original-Signed-2103469-42514440156-INTERNAL-QA',
    digest='sha256:f9d054ee500326b77ee2bf4ce8673af2bd54c54115831899d374d931a98dff43', size_in_bytes=329126132)
PREPARED = dict(run=42512905724, source='a56ef7d9e96146a167afe84e5a8a6fcf904f40cb', id=13630122222,
    name='Infinity2103469-Watchlist-Recovery-Prepared-42512905724-INTERNAL',
    digest='sha256:65d743e48eda62a04f9d887c2fdd65b3a11a932886bf65b1f5f14a75e47eed4d', size_in_bytes=320586755)


def require(ok, label):
    if not ok:
        raise RuntimeError(label)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=30)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], timeout=30))


def check_fresh_runs(runs, current_run):
    require(any(r['id'] == current_run for r in runs) and
            all(r['id'] == current_run or r['id'] <= PRIOR_FIXTURE_RUN for r in runs),
            'NO_UNREVIEWED_LATER_ORIGINAL_SIGNING_RUN')


def check_sources():
    request = load(REQUEST)
    require(request['operation'] == 'prepare-authenticated-tracking80-internal-android-fixture' and
            request['APK_build'] is False and request['publication'] is False and request['registry_mutation'] is False,
            'MODULE_FIXTURE_ONLY')
    freeze_path = HERE / 'SERVICE-SURVIVAL-SOURCE-PROOF.json'
    require(freeze_path.is_file(), 'SERVICE_SURVIVAL_SOURCE_FREEZE_REQUIRED')
    freeze = load(freeze_path)
    receipt_names = set()
    for key in ('host_receipt', 'independent_review', 'delta_proof'):
        path = Path(freeze[key]['path'])
        require(not path.is_absolute() and '..' not in path.parts and (ROOT / path).parent == HERE, 'EXACT_TASK_CORRECTION_RECEIPT')
        receipt_names.add(path.name)
    required_names = {'prepare_tracking_release.py', 'verify_tracking_modules.py', 'tracking_module_fixture.py',
        'MODULE-TEST-SELECTION.md', 'RELEASE-INPUT-SELECTION.json', 'VERSION-ADMISSION.json',
        'SCOPE.json', 'PROJECTION-HOST-RESULT.json', 'ACTUAL-SOURCE-HOST-RESULT.json',
        'INTEGRATION-SOURCE-PROOF.json', 'evidence/api36-startup-pass-42542862696/EVIDENCE.json',
        'CURRENT-INPUT-FIXTURE.json', 'CURRENT-SOURCE-PROOF.json', 'register_tracking_release.py',
        'SERVICE-SURVIVAL-SOURCE-PROOF.json', 'RECOVERY-SERVICE-PRESERVATION.json', 'RECOVERY-SERVICE-REVIEW.json',
        'EXPERIMENTAL-RELEASE-AUTHORIZATION.json',
        'TV-IDENTITY-SAFETY-BRIDGE-HOST-RESULT.json', 'TV-IDENTITY-SAFETY-BRIDGE-REVIEW.json',
        'evidence/signed-tracking80-42555855742/MODULE-UPGRADE-RECOVERY.json',
        'evidence/signed-e410-origin-fixture-42588102830/MODULE-UPGRADE-RECOVERY.json'}
    required_names |= receipt_names | {'overlay/' + CC + '/' + name for name in SOURCES}
    require(set(request['source_bindings']) == {HERE.relative_to(ROOT).as_posix() + '/' + name for name in required_names},
            'EXACT_MANDATORY_SOURCE_BINDING_SET')
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REPOSITORY') == REPO and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'EXACT_AUTHORIZED_INTERNAL_BRANCH')
    head = git('rev-parse', 'HEAD').decode().strip()
    require(head == os.environ['GITHUB_SHA'] and not git('status', '--porcelain', '--untracked-files=no').strip(),
            'CLEAN_EXACT_COMMITTED_SOURCE')
    this = api('actions/runs/' + os.environ['GITHUB_RUN_ID'])
    require(this['head_sha'] == head and this['workflow_id'] == 397702717 and this['path'] == WORKFLOW,
            'EXISTING_SOLE_ORIGINAL_SIGNING_WORKFLOW')
    for name, expected in request['source_bindings'].items():
        p = Path(name)
        require(not p.is_absolute() and '..' not in p.parts and sha(ROOT / p) == expected, 'FROZEN_REVIEWED_INPUT:' + name)
    require(sha(ROOT / WORKFLOW) == request['workflow_sha256'], 'SOURCE_BOUND_ORIGINAL_WORKFLOW_ADDITION')
    for name in ['SCOPE.json',
                 'PROJECTION-HOST-RESULT.json', 'ACTUAL-SOURCE-HOST-RESULT.json', 'INTEGRATION-SOURCE-PROOF.json']:
        path = HERE / name
        require(path.read_bytes() == git('show', REVIEWED + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_REVIEWED_TRACKING_SOURCE_OR_EVIDENCE:' + name)
    for name in ['CURRENT-SOURCE-PROOF.json',
                 'TV-IDENTITY-SAFETY-BRIDGE-HOST-RESULT.json', 'TV-IDENTITY-SAFETY-BRIDGE-REVIEW.json']:
        path = HERE / name
        require(path.read_bytes() == git('show', BRIDGE_SOURCE + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_E410_REVIEWED_BRIDGE_SOURCE_OR_EVIDENCE:' + name)
    selection = load(HERE / 'CURRENT-INPUT-FIXTURE.json')
    require(selection['production_source'] == freeze['production_source'] and tuple(selection['selected_installer_cases']) == SELECTION and
            selection['APK_build'] is False and selection['reserved'] is False, 'EXACT_FOUR_CASE_INTERNAL_FIXTURE_SELECTION')
    prep = prep_module()
    prep.source_inputs()  # exact new3/C1 receipts; no APK or signing
    recovery_proof = load(HERE / 'RECOVERY-SERVICE-PRESERVATION.json')
    require(hashlib.sha256(prep.recovery_source('service.py')).hexdigest() == recovery_proof['recovery_service_sha256'],
            'EXACT_REVIEWED_RECOVERY_LOADING_GUARD')
    recovery_review = load(HERE / 'RECOVERY-SERVICE-REVIEW.json')
    require(recovery_review['status'] == 'ACCEPTED_SOURCE_PRESERVATION_ORIGINAL69_PLUS_EXACT_REVIEWED_LOADING_GUARD_ONLY' and
            recovery_review['concrete_blockers'] == [] and
            recovery_review['recovery_service_sha256'] == recovery_proof['recovery_service_sha256'] and
            recovery_review['preservation_receipt_sha256'] == sha(HERE / 'RECOVERY-SERVICE-PRESERVATION.json'),
            'INDEPENDENT_REVIEWED_RECOVERY_SOURCE_VARIANT')
    prior = HERE / 'evidence/signed-tracking80-42555855742/MODULE-UPGRADE-RECOVERY.json'
    require(prior.read_bytes() == git('show', BRIDGE_SOURCE + ':' + prior.relative_to(ROOT).as_posix()) and
            sha(prior) == selection['retained_tracking13_receipt_sha256'], 'RETAINED_TRACKING13_RECEIPT')
    prior4 = HERE / 'evidence/signed-e410-origin-fixture-42588102830/MODULE-UPGRADE-RECOVERY.json'
    require(prior4.read_bytes() == git('show', freeze['production_source'] + ':' + prior4.relative_to(ROOT).as_posix()) and
            sha(prior4) == selection['retained_tracking4_receipt_sha256'], 'RETAINED_TRACKING4_RECEIPT')
    live = api('git/ref/heads/work/infinity-2103460-nine-corrections-20261106')
    require(live['object']['sha'] == AUTHORITY, 'LIVE_VERSION_AUTHORITY_ADVANCED')
    lock = api('git/ref/heads/locks/infinity-2103469-protected-recovery-20261108')
    require(lock['object']['sha'] == AUTHORITY, 'PROTECTED69_LOCK_CHANGED')
    live_authority = api('contents/repairs/dual-experience-isolation-2103420/release-authority.json?ref=' + AUTHORITY)
    require(live_authority['sha'] == '4905f8d31c9996bd1f8a93a4bf8a4347da71bd8d', 'UNCHANGED_LIVE_AUTHORITY_BLOB')
    runs = api('actions/workflows/397702717/runs?per_page=10')['workflow_runs']
    check_fresh_runs(runs, int(os.environ['GITHUB_RUN_ID']))
    prior = git('show', AUTHORITY + ':' + WORKFLOW).decode()
    actual = (ROOT / WORKFLOW).read_text()
    expected = prior.replace('publish-watchlist]', 'publish-watchlist, prepare-tracking-modules]', 1)
    expected = expected.replace('branches: [work/infinity-final-release-462-20261107]',
        'branches: [work/infinity-final-release-462-20261107, ' + BRANCH + ']', 1)
    expected = expected.replace('paths: [repairs/infinity-final-release-462-20261107/REQUEST.json]',
        'paths: [repairs/infinity-final-release-462-20261107/REQUEST.json, ' + REQUEST.relative_to(ROOT).as_posix() + ']', 1)
    require(actual.startswith(expected.rstrip() + '\n') and
            re.findall(r'^  ([A-Za-z0-9_-]+):', actual[len(expected.rstrip()):], re.M) == ['prepare-tracking-modules'],
            'ALL_ORIGINAL_WORKFLOW_JOBS_UNCHANGED')
    baseline = api('actions/runs/42542862696')
    require(baseline['workflow_id'] == 393886994 and baseline['head_sha'] == '3d32dfa90510011701c11c49a763774ce3428200' and
            baseline['conclusion'] == 'success' and baseline['status'] == 'completed', 'ACTUAL_UNCHANGED69_API36_STARTUP_PASS')
    proof = load(HERE / 'evidence/api36-startup-pass-42542862696/EVIDENCE.json')
    require(proof['status'] == 'PASS_UNCHANGED69_STOCK_API36_THREE_STARTS_ONLY' and len(proof['starts']) == 3,
            'BASELINE_PASS_RECEIPT')
    return request, head


def prep_module():
    # check_sources hashes this file and the preparation module before import.
    path = HERE / 'prepare_tracking_release.py'
    spec = importlib.util.spec_from_file_location('tracking_fixture_preparation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.load_tools()
    return module


def download(row, directory):
    run = api('actions/runs/' + str(row['run']))
    require(run['workflow_id'] == 397702717 and run['path'] == WORKFLOW and run['head_sha'] == row['source'] and
            run['status'] == 'completed' and run['conclusion'] == 'success', 'EXACT_ORIGINAL69_INPUT_PRODUCER')
    meta = api('actions/artifacts/' + str(row['id']))
    require(not meta['expired'] and meta['workflow_run']['id'] == row['run'] and
            all(meta[k] == row[k] for k in ('id', 'name', 'digest', 'size_in_bytes')), 'EXACT_LIVE_INPUT_ARTIFACT')
    directory.mkdir(parents=True)
    archive = directory / 'artifact.zip'
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/' + REPO + '/actions/artifacts/' + str(row['id']) + '/zip'],
                       stdout=stream, check=True, timeout=600)
    require(archive.stat().st_size == row['size_in_bytes'] and 'sha256:' + sha(archive) == row['digest'],
            'WHOLE_INPUT_ARCHIVE_DIGEST')
    t = prep_module().load_tools()
    with ZipFile(archive) as z:
        names = t.validate_names(z)
        require(len(names) < 100000 and sum(i.file_size for i in z.infolist()) < 8 * 1024**3, 'BOUNDED_INPUT_ZIP')
        require(all(not stat.S_ISLNK(i.external_attr >> 16) and not i.flag_bits & 1 for i in z.infolist()), 'REGULAR_UNENCRYPTED_ZIP')
        z.extractall(directory / 'files')
    return directory / 'files'


def preflight(out, sdk):
    request, source = check_sources()
    require(not out.exists(), 'FRESH_INTERNAL_FIXTURE_PREPARATION')
    out.mkdir(parents=True)
    signed = download(SIGNED, out / 'signed69-input')
    prepared = download(PREPARED, out / 'prepared69-input')
    apk = signed / 'Infinity-2103469-Combined-Original-Signer.apk'
    signature = subprocess.check_output([str(sdk / 'apksigner'), 'verify', '--verbose', '--print-certs', str(apk)], text=True, timeout=60)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) ==
            ['d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'], 'ORIGINAL69_APK_CERTIFICATE')
    (out / 'ORIGINAL69-SIGNATURE.txt').write_text(signature)
    p = prep_module()
    p.inputs(apk, prepared, HERE / 'VERSION-ADMISSION.json', out / 'pair')
    check_sources()
    save(out / 'PREFLIGHT.json', dict(status='PASS_INTERNAL80_FIXTURE_ADMISSION_BEFORE_KEYS', source=source,
         request_sha256=sha(REQUEST), source_pins_sha256=sha(out / 'pair/SOURCE-PINS.json'),
         APK_build=False, publication=False, registry_mutated=False, original_workflow=397702717))


def frozen(out, signed=False):
    _, source = check_sources()
    p = prep_module()
    proof = load(out / 'PREFLIGHT.json')
    pair = out / 'pair'
    pins = load(pair / 'SOURCE-PINS.json')
    require(proof['source'] == pins['source'] == source and sha(REQUEST) == proof['request_sha256'] and
            sha(pair / 'SOURCE-PINS.json') == proof['source_pins_sha256'] and p.load_tools().pins == pins['original_tools'],
            'EXACT_PREFLIGHT_SOURCE_AND_ORIGINAL_TOOLS')
    require(p.source_inputs()[1] == pins['overlay_sha256'] and sha(pair / 'VERSION-ADMISSION.json') == pins['version_admission_sha256'],
            'FROZEN_RUNTIME_AND_UNUSED_VERSION_ADMISSION')
    require(pins['production_source'] == load(HERE / 'SERVICE-SURVIVAL-SOURCE-PROOF.json')['production_source'] and
            pins['installer_selection_sha256'] == sha(HERE / 'CURRENT-INPUT-FIXTURE.json'), 'FROZEN_SELECTED_CURRENT_GENERATION')
    roots = []
    for version, cc in p.admission(pair / 'VERSION-ADMISSION.json'):
        work = pair / str(version)
        require(sha(work / 'INPUTS.json') == pins['input_metadata_sha256'][str(version)], 'FROZEN_FULL_INPUTS')
        meta = load(work / 'INPUTS.json')
        root = work / 'modules'
        now = p.hashes(root)
        sig = CC + '/' + p.MANIFEST + '.sig'
        require({n: h for n, h in now.items() if n != sig} == meta['modules'] and (sig in now) is signed,
                'NO_STAGED_SOURCE_OR_SIGNATURE_CHANGE')
        payload, files = p.load_tools().module_bundle.build(root)
        require(len(files) == 80 and hashlib.sha256(payload).hexdigest() == meta['module_manifest_sha256'] and
                payload == (root / CC / p.MANIFEST).read_bytes(), 'COMPLETE_FROZEN80_MANIFEST')
        if signed:
            p.verify_signature(root)
        roots.append(root)
    return p, roots


def archive(out):
    p, roots = frozen(out, signed=True)
    audit = load(out / 'module-audit/MODULE-UPGRADE-RECOVERY.json')
    require(audit['status'] == 'PASS_FOUR_REAL_JAVA_CURRENT80_GENERATION_CASES' and
            audit['complete80_signatures_verified'] and tuple(r['case'] for r in audit['cases']) == SELECTION and
            audit['selected_tests_sha256'] == sha(HERE / 'CURRENT-INPUT-FIXTURE.json') and
            audit['verifier_sha256'] == sha(HERE / 'verify_tracking_modules.py') and
            audit['source_pins_sha256'] == sha(out / 'pair/SOURCE-PINS.json'), 'ACTUAL_SELECTED_INSTALLER_CASES_REQUIRED')
    dest = out / 'publish'
    dest.mkdir(exist_ok=False)
    shutil.copytree(out / 'pair', dest / 'pair')
    shutil.copytree(out / 'module-audit', dest / 'module-audit')
    reports = []
    for root in roots:
        metadata = load(root.parent / 'INPUTS.json')
        target = dest / (CC + '-' + metadata['CC'] + '-INTERNAL-ANDROID-FIXTURE.zip')
        with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=9) as z:
            for path in sorted((root / CC).rglob('*')):
                if path.is_file():
                    info = ZipInfo(path.relative_to(root).as_posix(), date_time=(2026,11,9,0,0,0))
                    info.compress_type = ZIP_DEFLATED
                    z.writestr(info, path.read_bytes())
        reports.append(dict(CC=metadata['CC'], archive=target.name, sha256=sha(target), recovery=metadata['recovery'],
                            versionCode=metadata['versionCode'],
                            modules_path='pair/' + str(metadata['versionCode']) + '/modules'))
    save(dest / 'MODULE-FIXTURE.json', dict(status='ORIGINAL_KEY_SIGNED_INTERNAL_MODULE_FIXTURE_NOT_RELEASE_ACCEPTANCE',
         source=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']), fixture_packages=reports,
         production_source=load(HERE / 'SERVICE-SURVIVAL-SOURCE-PROOF.json')['production_source'], installed_target_versionCode=2103469,
         source_pins_sha256=sha(out / 'pair/SOURCE-PINS.json'), original80_source_signatures=True,
         APK_build=False, APK_present=False, APK_signing=False, registry_mutated=False, publication=False,
         Android='NOT_RUN', Fold='NOT_RUN', release_acceptance=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for mode in ('preflight', 'archive'):
        p = sub.add_parser(mode)
        p.add_argument('--out', type=Path, required=True)
        if mode == 'preflight':
            p.add_argument('--sdk', type=Path, required=True)
    args = vars(parser.parse_args())
    globals()[args.pop('command')](**args)
