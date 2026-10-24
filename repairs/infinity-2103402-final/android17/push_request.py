"""Validate one explicitly requested existing Android17 case; no APK mutation."""
import json
import os
from pathlib import Path
import subprocess

BRANCH = 'refs/heads/work/infinity-2103402-final-stabilization-20261024'
REQUEST = 'repairs/infinity-2103402-final/android17/REQUEST.json'
BASELINE = '1738478709cd8881f7ad4a524e7abbbc82b5d79c'
APK = 'a7abd878768cd09cac0c0caeadd5afc691a842cf97c9ff14b0d913677117a742'
AUTHORIZATION = ('User-authorized 2103402 Android17 verification: reuse existing signed 2103401 '
                 'baseline for Search All Enter, result identity, history persistence, Back and Home '
                 'responsiveness. No shutdown test, APK rebuild, user installation or release acceptance.')


def validate(request, event, head, changed, event_name='push'):
    if event_name != 'push' or event.get('ref') != BRANCH or event.get('deleted'):
        raise ValueError('Only the authorized development branch push is eligible')
    if event.get('after') != head or event.get('repository', {}).get('full_name') != 'mahfouzhassine8-ops/project-infinity':
        raise ValueError('Event/source/repository binding differs')
    if REQUEST not in changed:
        raise ValueError('No explicit new verification request')
    expected = {'schema': 1, 'case': 'final-search-all-enter', 'candidate_build': 40089463702,
                'baseline_commit': BASELINE, 'baseline_apk_sha256': APK,
                'authorization': AUTHORIZATION, 'request_id': 'search-baseline-01'}
    if request != expected:
        raise ValueError('Verification request differs from the reviewed baseline scope')
    for name in changed:
        if not (name.startswith('repairs/infinity-2103402-final/') or
                name in ('.github/workflows/infinity-saved-navigation-android.yml',
                         '.github/workflows/infinity-2103402-scoped-tests.yml')):
            raise ValueError('Unrelated file changed with this request: ' + name)
    return {'CANDIDATE_BUILD': str(request['candidate_build']), 'SELECTED_CASE': request['case'],
            'AUTHORIZED_SCOPE': request['authorization']}


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    before = event.get('before', '')
    if len(before) != 40 or before == '0' * 40:
        raise ValueError('An existing reviewed branch checkpoint is required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, head], check=True)
    subprocess.run(['git', 'merge-base', '--is-ancestor', before, head], check=True)
    changed = subprocess.check_output(['git', 'diff', '--name-only', before, head], text=True).splitlines()
    values = validate(json.loads(Path(REQUEST).read_text()), event, head, changed,
                      os.environ['GITHUB_EVENT_NAME'])
    with Path(os.environ['GITHUB_ENV']).open('a') as output:
        for key, value in values.items():
            if '\n' in value or '\r' in value:
                raise ValueError('Invalid environment output')
            output.write(key + '=' + value + '\n')
    Path('android17-request-evidence.json').write_text(json.dumps(
        dict(values, test_source_commit=head, baseline_commit=BASELINE,
             baseline_apk_sha256=APK, release_accepted=False), indent=2) + '\n')


if __name__ == '__main__':
    main()
