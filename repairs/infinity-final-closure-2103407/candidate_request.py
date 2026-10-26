"""One exact integrated candidate feature; baseline-reference requests stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION=('UserOct26 GitHubfailure correction: actualsigned410 originalAPI37 SearchAll Enter/results/history/Home withactual '
    'IMEbody-ready proof insideunchanged45secondkeyboarddeadline. ReadonlyPATH/defaultVersionChecksource metadata; '
    'nochildexecution, Close, textrepair, stressrepetition orproductionAPKchange.')
EXPECTED=dict(schema=1,kind='integrated-candidate',selected_case='final-search-all-enter',
    candidate_build=40305746524,candidate_source_commit='925b475f4e4c1c1862817c13167285ebec06894a',
    candidate_apk_sha256='7de8ada4774d39c80c3251e21b1750874fbbfdbdfb08b7468dd25151d92a7a34',
    candidate_artifact='Infinity-2103410-Corrective-INTERNAL-NOT-FINAL-40305746524',
    authorization=AUTHORIZATION,request_id='integrated410-search-ime-ready-01')


def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
