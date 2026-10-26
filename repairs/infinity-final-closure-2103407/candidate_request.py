"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 critical Search/performance/stability50/30/20 on latest signed414 after actual disabled-refresh-loop correction. Original real Enter/provider/query/results/history/duplicate/cancel assertions and45sec app keyboard deadline retained. Strict actual saved-card native positions/source/episode/noautoplay after30Home and20OSrotations; measure PSS/RSS/native frames without physical Fold claims. Prior413run40339101147 failed before APK install when Android naturally replaced Settings Intelligence; allow one observed utility UI re-entry within original preparation budget. No app input retry, timeout waiver, writer grant, Close or release acceptance.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-search-all-enter', 'candidate_build': 40345149803, 'candidate_source_commit': 'f5dbd03fb3a5df6b2f0f209bc36768d6ebd16c71', 'candidate_apk_sha256': 'a13bd3a5fc10752fc06621e2b49d050b5fd3ba0a8a86ad9e675420335b0313d3', 'candidate_artifact': 'Infinity-2103414-Refresh-Corrective-Verification-40345149803', 'authorization': 'UserOct26 critical Search/performance/stability50/30/20 on latest signed414 after actual disabled-refresh-loop correction. Original real Enter/provider/query/results/history/duplicate/cancel assertions and45sec app keyboard deadline retained. Strict actual saved-card native positions/source/episode/noautoplay after30Home and20OSrotations; measure PSS/RSS/native frames without physical Fold claims. Prior413run40339101147 failed before APK install when Android naturally replaced Settings Intelligence; allow one observed utility UI re-entry within original preparation budget. No app input retry, timeout waiver, writer grant, Close or release acceptance.', 'request_id': 'integrated414-search50-real-home30-rotation20-01', 'post_feature': {'search': 50, 'playback_home': 30, 'rotation': 20}}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
