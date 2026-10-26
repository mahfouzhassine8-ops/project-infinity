"""One exact integrated candidate feature; baseline-reference requests stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION=('UserOct26 authorized continuation after focused Search PASS40306535463: actual signed411 API37 '
    'original SearchAll Enter/results/history/Home, then 50 Search, 30 generated native-clip playback-to-Home '
    'and 20 OS rotations. Retain original assertions and deadlines; stop first failure and keep partial counts. '
    'Actual system IME prepared through normal Settings Search before first Infinity launch, without typing or preference writes. '
    'No Close, shutdown, reset, text repair, APK rebuild or physical Fold acceptance.')
EXPECTED=dict(schema=1,kind='integrated-candidate',selected_case='final-search-all-enter',
    candidate_build=40316348289,candidate_source_commit='26753a8e863f1e02c9993d2a1f5cd4940c5c305a',
    candidate_apk_sha256='0729e8403b842568665567db118902d5b15b6e554b9f96a23cc9a94e24779c80',
    candidate_artifact='Infinity-2103411-Corrective-INTERNAL-NOT-FINAL-40316348289',
    authorization=AUTHORIZATION,request_id='integrated411-search50-playback30-rotation20-04-prepared-ime',
    post_feature={'search':50,'playback_home':30,'rotation':20})


def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
