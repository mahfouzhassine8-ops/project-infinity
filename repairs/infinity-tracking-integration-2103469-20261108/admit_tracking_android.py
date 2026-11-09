"""Source-bound selected Android tracking intake; no signing or app execution."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUEST = HERE / 'TRACKING-ANDROID-REQUEST.json'
WORKFLOW = '.github/workflows/infinity-saved-navigation-android.yml'
BRANCH = 'work/infinity-tracking-integration-20261108'
REVIEWED = 'e410f30ba9e38182e4e77810e5237e5442cbd31a'
WORKFLOW_SHAPE_BASE = '9d64ffb84404036ce6e02d6cb160fb004a029b33'
RETAINED_RUN = 42567028842
RETAINED_SOURCE = '9b05d1b4bf2283b7adc92f7ef6db0aff3b9fede3'
RETAINED_ARTIFACT = 13652516052
RETAINED_DIGEST = '20a7c899f2abdc556e1843fc828d53f8f80d774f18642f7bb512581191c5b240'
RETAINED_SIZE = 2324287
RETAINED_DIR = 'evidence/native-av-identity-fail-42567028842/'


def require(value, label):
    if not value:
        raise RuntimeError(label)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=30)


def checked_focus(selected):
    require(selected.get('execution_focus') == 'infinity-origin-acceptance', 'EXACT_INFINITY_ORIGIN_FOCUS_ONLY')
    require(selected.get('direct_provider_acceptance') is False and
            selected.get('direct_provider_fallback') is False, 'NO_PROVIDER_BYPASS_AS_INFINITY_ACCEPTANCE')
    require(selected.get('maximum_new_attempts') == 1 and selected.get('automatic_retries') == 0,
            'ONE_NEW_ORIGIN_ATTEMPT_NO_RETRIES')
    require(selected.get('protected_source_checkpoint') == REVIEWED and
            selected.get('retained_environment_failure_run') == 42570831467,
            'FROZEN_E410_AND_RETAINED_STARTUP_FAILURE_REQUIRED')
    contract = load(HERE / 'INFINITY-ORIGIN-ACCEPTANCE.json')
    require(contract['operation'] == 'accept-existing-infinity-origin-playback-tracking' and
            contract['protected_source_checkpoint'] == REVIEWED and contract['protected_recovery'] == 2103469,
            'EXACT_OWNER_ORIGIN_ACCEPTANCE_CONTRACT')
    require(contract['owner_confirmed_navigation']['status'] == 'PASS_OWNER_REPORTED_GALAXY_FOLD_NAVIGATION_ONLY' and
            contract['owner_confirmed_navigation']['tracking_acceptance'] is False,
            'PRESERVE_OWNER_NAVIGATION_CONFIRMATION_WITHOUT_TRACKING_PASS')
    for name, wanted in contract['production_source_sha256'].items():
        require(name in ('plugin.py', 'resume_hub.py', 'service.py') and
                sha(HERE / 'overlay/script.infinity.commandcenter' / name) == wanted,
                'UNCHANGED_E410_SOURCE_FROM_OWNER_CONTRACT:' + name)
    require(set(contract['production_source_sha256']) == {'plugin.py', 'resume_hub.py', 'service.py'},
            'EXACT_THREE_FROZEN_PRODUCTION_SOURCES')


def checked_module_pin():
    module = load(HERE / 'TRACKING-MODULE-FIXTURE-PIN.json')
    require(module.get('production_source_checkpoint') == REVIEWED and
            module.get('workflow_id') == 397702717 and
            module.get('workflow_path') == '.github/workflows/infinity-combined-release.yml' and
            module.get('APK_build') is False and module.get('publication') is False,
            'MATCHING_ORIGINAL_KEY_E410_MODULE_FIXTURE_REQUIRED')
    require(re.fullmatch(r'[0-9a-f]{40}', module.get('source', '')) and
            type(module.get('run')) is int and type(module.get('id')) is int,
            'EXACT_SIGNED_FIXTURE_PRODUCER_REFERENCE')
    return module


def checked_request():
    selected = load(REQUEST)
    require(selected['operation'] == 'verify-infinity-movies-tv-existing-tracking' and
            selected['application_tests'] is True and selected['shutdown_tests'] is False and
            selected['APK_build'] is False and selected['publication'] is False, 'EXACT_SELECTED_TRACKING_TESTS_ONLY')
    require(selected['qualified_startup_run_reused'] == 42542862696 and selected['startup_qualification_repeated'] is False,
            'REUSE_VALID_UNCHANGED69_STARTUP_PASS')
    require(selected['image'] == 'system-images;android-36;google_apis;x86_64' and selected['image_revision'] == 7 and
            selected['avd_name'] == 'infinity-tracking-baseline-api36', 'REUSE_EXACT_QUALIFIED_STOCK_RUNTIME')
    require(set(selected['mandatory_checks']) == {r['id'] for r in load(HERE / 'SCOPE.json')['selected_checks']},
            'ALL_MANDATORY_GATES_REMAIN_VISIBLE')
    expected = {'admit_tracking_android.py', 'stage_tracking_android.py', 'tracking_android_observer.py',
        'verify_tracking_android.py', 'TRACKING-ANDROID-PLAN.md', 'TRACKING-DEPENDENCY-PINS.json',
        'TRACKING-MODULE-FIXTURE-PIN.json', 'qualify_android_baseline.py', 'ANDROID-BASELINE-HOST-GUARDS.json',
        'dependency-evidence/PUBLIC-MOVIE-INPUT.json',
        'SCOPE.json', 'INTEGRATION-SOURCE-PROOF.json', 'PROJECTION-HOST-RESULT.json', 'ACTUAL-SOURCE-HOST-RESULT.json',
        'CURRENT-SOURCE-PROOF.json', 'TV-IDENTITY-SAFETY-BRIDGE-HOST-RESULT.json',
        'TV-IDENTITY-SAFETY-BRIDGE-REVIEW.json', 'INFINITY-ORIGIN-ACCEPTANCE.json',
        'CURRENT-INPUT-FIXTURE.json', 'evidence/baseline-constructor-fail-42570831467/EVIDENCE.json',
        'evidence/signed-e410-origin-fixture-42588102830/REVIEW.json',
        'evidence/signed-e410-origin-fixture-42588102830/MODULE-UPGRADE-RECOVERY.json',
        'evidence/api36-startup-pass-42542862696/EVIDENCE.json',
        RETAINED_DIR + 'EVIDENCE.json', RETAINED_DIR + 'queens-blade-e4-actual-av.json',
        'evidence/signed-tracking80-42555855742/MODULE-UPGRADE-RECOVERY.json'}
    expected |= {'overlay/script.infinity.commandcenter/' + n for n in ('plugin.py', 'resume_hub.py', 'service.py')}
    prefix = HERE.relative_to(ROOT).as_posix() + '/'
    require(set(selected['source_bindings']) == {prefix + n for n in expected}, 'EXACT_SELECTED_INPUT_BINDING_SET')
    for name, wanted in selected['source_bindings'].items():
        require(sha(ROOT / name) == wanted, 'FROZEN_ANDROID_INPUT:' + name)
    require(sha(ROOT / WORKFLOW) == selected['workflow_sha256'], 'EXACT_ANDROID_WORKFLOW_SOURCE')
    checked_focus(selected)
    for name in ['overlay/script.infinity.commandcenter/' + n for n in ('plugin.py', 'resume_hub.py', 'service.py')] + [
            'SCOPE.json', 'INTEGRATION-SOURCE-PROOF.json', 'PROJECTION-HOST-RESULT.json', 'ACTUAL-SOURCE-HOST-RESULT.json',
            'CURRENT-SOURCE-PROOF.json', 'TV-IDENTITY-SAFETY-BRIDGE-HOST-RESULT.json',
            'TV-IDENTITY-SAFETY-BRIDGE-REVIEW.json']:
        path = HERE / name
        require(path.read_bytes() == git('show', REVIEWED + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_REVIEWED_PRODUCTION_OR40_CASE_EVIDENCE:' + name)
    module = checked_module_pin()
    for name in ('tracking_module_fixture.py', 'prepare_tracking_release.py', 'verify_tracking_modules.py'):
        path = HERE / name
        require(path.read_bytes() == git('show', module['source'] + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_ORIGINAL_MODULE_FIXTURE_TOOL:' + name)
    return selected


def workflow_shape():
    prior = git('show', WORKFLOW_SHAPE_BASE + ':' + WORKFLOW).decode()
    expected = prior.replace('tracking-baseline-android]', 'tracking-baseline-android, tracking-integration-android]', 1)
    anchor = "'repairs/infinity-tracking-integration-2103469-20261108/ANDROID-BASELINE-REQUEST.json']"
    expected = expected.replace(anchor, anchor[:-1] + ", 'repairs/infinity-tracking-integration-2103469-20261108/TRACKING-ANDROID-REQUEST.json']", 1)
    exclude = "&& inputs.feature != 'tracking-baseline-android'"
    expected = expected.replace(exclude, exclude + " && inputs.feature != 'tracking-integration-android'", 1)
    actual = (ROOT / WORKFLOW).read_text()
    require(actual.startswith(expected.rstrip() + '\n') and
            re.findall(r'^  ([A-Za-z0-9_-]+):', actual[len(expected.rstrip()):], re.M) == ['tracking_integration_android'],
            'ALL_EXISTING_FEATURE_JOBS_UNCHANGED')


def admit(out):
    selected = checked_request()
    workflow_shape()
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'EXACT_DISPOSABLE_CI_SELECTION')
    source = git('rev-parse', 'HEAD').decode().strip()
    require(source == os.environ['GITHUB_SHA'] and not git('status', '--porcelain', '--untracked-files=no').strip(),
            'CLEAN_EXACT_TEST_COMMIT')
    if os.environ['GITHUB_EVENT_NAME'] == 'push':
        require(load(os.environ['GITHUB_EVENT_PATH'])['head_commit']['message'].startswith('Verify tracking integration:'),
                'EXPLICIT_SELECTED_TRACKING_PUSH')
    require(not out.exists(), 'FRESH_ANDROID_ADMISSION_DIRECTORY')
    path = HERE / 'tracking_module_fixture.py'
    spec = importlib.util.spec_from_file_location('original_tracking_fixture_download', path)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    this = original.api('actions/runs/' + os.environ['GITHUB_RUN_ID'])
    require(this['head_sha'] == source and this['workflow_id'] == 393886994 and this['path'] == WORKFLOW,
            'EXISTING_SELECTED_FEATURE_WORKFLOW')
    baseline = original.api('actions/runs/42542862696')
    require(baseline['status'] == 'completed' and baseline['conclusion'] == 'success' and
            baseline['head_sha'] == '3d32dfa90510011701c11c49a763774ce3428200', 'QUALIFIED_BASELINE_PASS_NOT_CHANGED')
    lock = original.api('git/ref/heads/locks/infinity-2103469-protected-recovery-20261108')
    require(lock['object']['sha'] == original.AUTHORITY, 'PROTECTED_RECOVERY69_UNCHANGED')
    module = checked_module_pin()
    module_run = original.api('actions/runs/' + str(module['run']))
    require(module_run['status'] == 'completed' and module_run['conclusion'] == 'success' and
            module_run['workflow_id'] == module['workflow_id'] and module_run['path'] == module['workflow_path'] and
            module_run['head_sha'] == module['source'], 'EXACT_ORIGINAL_SIGNED_E410_MODULE_PRODUCER')
    e410 = original.api('git/ref/heads/locks/infinity-tracking-e410f30b-20261109')
    require(e410['object']['sha'] == REVIEWED, 'PROTECTED_E410_CHECKPOINT_UNCHANGED')
    retained = original.api('actions/runs/' + str(RETAINED_RUN))
    require(retained['status'] == 'completed' and retained['conclusion'] == 'failure' and
            retained['head_sha'] == RETAINED_SOURCE and retained['workflow_id'] == 393886994 and
            retained['path'] == WORKFLOW, 'ORIGINAL_FAILED_EPISODE_PRODUCER_PROVENANCE')
    artifact = original.api('actions/artifacts/' + str(RETAINED_ARTIFACT))
    require(artifact['workflow_run']['id'] == RETAINED_RUN and
            artifact['workflow_run']['head_sha'] == RETAINED_SOURCE and
            artifact['digest'] == 'sha256:' + RETAINED_DIGEST and artifact['size_in_bytes'] == RETAINED_SIZE,
            'ORIGINAL_FAILED_EPISODE_ARTIFACT_PROVENANCE')
    signed = original.download(original.SIGNED, out / 'original69')
    fixtures = original.download(module, out / 'signed-modules')
    require(sha(fixtures / 'pair/SOURCE-PINS.json') == module['source_pins_sha256'], 'FROZEN_MODULE_SOURCE_PINS')
    metadata = load(fixtures / 'MODULE-FIXTURE.json')
    require(metadata['production_source'] == module['production_source_checkpoint'] == REVIEWED and
            metadata['source'] == module['source'] and metadata['run_id'] == module['run'] and
            metadata['APK_build'] is False and metadata['APK_present'] is False and
            metadata['fixture_packages'] == module['fixture_packages'],
            'SIGNED_ARTIFACT_METADATA_MATCHES_APPROVED_E410_PIN')
    proof = dict(status='PASS_SELECTED_TRACKING_ANDROID_INPUT_ADMISSION_ONLY', source=source,
        APK=str((signed / 'Infinity-2103469-Combined-Original-Signer.apk').resolve()),
        module_fixture=str(fixtures.resolve()), selected_request_sha256=sha(REQUEST),
        qualified_startup_run_reused=42542862696, startup_qualification_repeated=False,
        execution_focus=selected['execution_focus'], direct_provider_acceptance=False,
        maximum_new_attempts=1, automatic_retries=0, retained_environment_failure_run=42570831467,
        application_execution=False, module_producer=module, APK_build=False, publication=False)
    (out / 'ADMISSION.json').write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n')
    print(proof['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    admit(parser.parse_args().out)
