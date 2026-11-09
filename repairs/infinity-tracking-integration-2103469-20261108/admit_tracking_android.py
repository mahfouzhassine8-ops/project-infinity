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
REVIEWED = '2e52b7befd0228a09449f79eaf9774a3946dfa1c'
MODULE_SOURCE = '9d64ffb84404036ce6e02d6cb160fb004a029b33'
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
    require(selected.get('execution_focus') == 'independent-movie', 'EXACT_MISSING_MOVIE_FOCUS_ONLY')
    require(selected.get('retained_actual_evidence') == dict(run=RETAINED_RUN, source=RETAINED_SOURCE,
        artifact=RETAINED_ARTIFACT, artifact_sha256=RETAINED_DIGEST, artifact_size=RETAINED_SIZE,
        queens_blade_status='FAIL_ACTUAL_SDK_MOVIE_UNKNOWN_EPISODE',
        cross_entry_rezero_status='BLOCKED_UNVERIFIED_METADATA', replay_known_wrong_typed_tv=False),
        'RETAIN_ACTUAL_EPISODE_FAILURE_WITHOUT_REPLAY_OR_PASS')
    actual = load(HERE / RETAINED_DIR / 'queens-blade-e4-actual-av.json')
    item = actual['item']
    require(actual['playing'] is True and item['media_type'] == 'movie' and
            item['season'] == item['episode'] == -1 and not any(item['ids'].values()) and
            any(event['event'] == 'AVStarted' for event in actual['events']),
            'ACTUAL_RETAINED_AV_IS_PLAYABLE_BUT_NOT_VERIFIED_EPISODE')


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
            'SCOPE.json', 'INTEGRATION-SOURCE-PROOF.json', 'PROJECTION-HOST-RESULT.json', 'ACTUAL-SOURCE-HOST-RESULT.json']:
        path = HERE / name
        require(path.read_bytes() == git('show', REVIEWED + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_REVIEWED_PRODUCTION_OR40_CASE_EVIDENCE:' + name)
    for name in ('tracking_module_fixture.py', 'prepare_tracking_release.py', 'verify_tracking_modules.py'):
        path = HERE / name
        require(path.read_bytes() == git('show', MODULE_SOURCE + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_ORIGINAL_MODULE_FIXTURE_TOOL:' + name)
    return selected


def workflow_shape():
    prior = git('show', MODULE_SOURCE + ':' + WORKFLOW).decode()
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
    module = load(HERE / 'TRACKING-MODULE-FIXTURE-PIN.json')
    require(module['run'] == 42555855742 and module['source'] == MODULE_SOURCE and module['workflow_id'] == 397702717 and
            module['APK_build'] is False and module['publication'] is False, 'EXACT_INTERNAL_SIGNED_MODULE_PRODUCER')
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
    proof = dict(status='PASS_SELECTED_TRACKING_ANDROID_INPUT_ADMISSION_ONLY', source=source,
        APK=str((signed / 'Infinity-2103469-Combined-Original-Signer.apk').resolve()),
        module_fixture=str(fixtures.resolve()), selected_request_sha256=sha(REQUEST),
        qualified_startup_run_reused=42542862696, startup_qualification_repeated=False,
        execution_focus=selected['execution_focus'], retained_actual_evidence=selected['retained_actual_evidence'],
        application_execution=False, module_producer=module, APK_build=False, publication=False)
    (out / 'ADMISSION.json').write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n')
    print(proof['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    admit(parser.parse_args().out)
