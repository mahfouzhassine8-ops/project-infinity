"""Select one immutable signed407 reference case in the existing API37 runner."""
import json
import os
from pathlib import Path
import subprocess

BRANCH = 'refs/heads/work/infinity-final-corrective-from-2103407-20261025'
REQUEST = 'repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json'
BASELINE = '0e8739d2d0e1be0ab8f127519b526556426fb160'
APK = '3616c4e69c976bd63b36170d4dbbd9b190a7ec2eace4bc0c34c3c72f7f9e8578'
AUTHORIZATION = ('Authorized final Infinity scope: actual Android17 baseline407 Search All Enter, '
                 'results/provider identity, history persistence and Back/Home response through the '
                 'existing feature-only runner. No shutdown, new APK, user installation or physical acceptance.')
EXPECTED = dict(schema=1, selected_case='final-search-all-enter', candidate_build=40230842944,
                baseline_commit=BASELINE, baseline_apk_sha256=APK,
                authorization=AUTHORIZATION, request_id='final407-search-reference-03-owned-fixture')


def validate(request, event, head, changed):
    if event.get('ref') != BRANCH or event.get('deleted') or event.get('after') != head:
        raise ValueError('Wrong branch/event/source for explicit Android17 reference request')
    if event.get('repository', {}).get('full_name') != 'mahfouzhassine8-ops/project-infinity':
        raise ValueError('Wrong repository')
    if request != EXPECTED or REQUEST not in changed:
        raise ValueError('An exact new reviewed reference request is required')
    allowed_workflows = {'.github/workflows/infinity-2103407-search-pressure-host-gate.yml',
                         '.github/workflows/infinity-saved-navigation-android.yml',
                         '.github/workflows/infinity-2103402-native-owner-build.yml'}
    if not all(name.startswith('repairs/infinity-final-closure-2103407/') or name in allowed_workflows
               for name in changed):
        raise ValueError('Unrelated source changed with this request')
    return dict(CANDIDATE_BUILD='40230842944', SELECTED_CASE='final-search-all-enter',
                CANDIDATE_ARTIFACT='Infinity-2103407-SEARCH-SINGLE-FLIGHT-ORIGINAL-SIGNER-QA',
                BASELINE_REQUEST_PATH=REQUEST, AUTHORIZED_SCOPE=AUTHORIZATION,
                FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_reference_observation.py')


def main():
    if os.environ['GITHUB_EVENT_NAME'] != 'push':
        raise ValueError('Explicit branch push required')
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    before = event.get('before', '')
    if len(before) != 40 or before == '0' * 40:
        raise ValueError('Existing final corrective checkpoint required')
    for commit in (BASELINE, before):
        subprocess.run(['git', 'merge-base', '--is-ancestor', commit, head], check=True)
    changed = subprocess.check_output(['git', 'diff', '--name-only', before, head], text=True).splitlines()
    output = validate(json.loads(Path(REQUEST).read_text()), event, head, changed)
    with Path(os.environ['GITHUB_ENV']).open('a') as stream:
        for key, value in output.items():
            if '\n' in value or '\r' in value:
                raise ValueError('Invalid environment value')
            stream.write(key + '=' + value + '\n')
    Path('android17-request-evidence.json').write_text(json.dumps(
        dict(output, test_source_commit=head, baseline_source_commit=BASELINE,
             android17='SELECTED', physical_fold='NOT RUN', release_accepted=False), indent=2)+'\n')


if __name__ == '__main__':
    main()
