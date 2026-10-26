"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 final corrective scope after production Home-entry correction413: exact signed413 API37 original SearchAll actual Enter/results/attribution/history/Home,50 repeated Search/provider/history/duplicate/cancel interactions,30 actual native generated-clip playback/Home cycles requiring a real correct saved card,20 observed OS rotations with real saved cards. Keep45second keyboard deadline and all original predicates. Fresh disposable profile only; exact declared180sec resume clip exists with verified readback. No Close, reset, provider-code change or physical Fold acceptance in this feature lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-search-all-enter', 'candidate_build': 40336380247, 'candidate_source_commit': '282a12a5e538a3ba05d5544d94a318b1c5de5ad4', 'candidate_apk_sha256': 'b3af984c5f035f6c0e51f70f71726b317ddbb503764eb5306505b583c0643ec4', 'candidate_artifact': 'Infinity-2103413-Home-Corrective-Verification-40336380247', 'authorization': 'UserOct26 final corrective scope after production Home-entry correction413: exact signed413 API37 original SearchAll actual Enter/results/attribution/history/Home,50 repeated Search/provider/history/duplicate/cancel interactions,30 actual native generated-clip playback/Home cycles requiring a real correct saved card,20 observed OS rotations with real saved cards. Keep45second keyboard deadline and all original predicates. Fresh disposable profile only; exact declared180sec resume clip exists with verified readback. No Close, reset, provider-code change or physical Fold acceptance in this feature lane.', 'request_id': 'integrated413-search50-real-resume-home30-rotation20-01', 'post_feature': {'search': 50, 'playback_home': 30, 'rotation': 20}}


def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
