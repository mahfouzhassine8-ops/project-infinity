"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 original Search and whole-app50/30/20 scope on signed414. Prior413/414Search setup failed unrelated GoogleSettings utility BEFORE APK install, not app behavior. Correct contract: skip that optional utility; require actual Infinity first native keyboard strict currentPID/BODY/shown proof and ORIGINAL45sec deadline, no app input retry or waiver. ExactEnter/query/provider/result/history/duplicate/cancel50, actual identity/source/native position/watched/noautoplay after30Home and20OSrotations, real PSS/RSS/native frames. Source/signer/installover/data guards retained. No Close, synthetic pass, physical Fold or release acceptance.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-search-all-enter', 'candidate_build': 40345149803, 'candidate_source_commit': 'f5dbd03fb3a5df6b2f0f209bc36768d6ebd16c71', 'candidate_apk_sha256': 'a13bd3a5fc10752fc06621e2b49d050b5fd3ba0a8a86ad9e675420335b0313d3', 'candidate_artifact': 'Infinity-2103414-Refresh-Corrective-Verification-40345149803', 'authorization': 'UserOct26 original Search and whole-app50/30/20 scope on signed414. Prior413/414Search setup failed unrelated GoogleSettings utility BEFORE APK install, not app behavior. Correct contract: skip that optional utility; require actual Infinity first native keyboard strict currentPID/BODY/shown proof and ORIGINAL45sec deadline, no app input retry or waiver. ExactEnter/query/provider/result/history/duplicate/cancel50, actual identity/source/native position/watched/noautoplay after30Home and20OSrotations, real PSS/RSS/native frames. Source/signer/installover/data guards retained. No Close, synthetic pass, physical Fold or release acceptance.', 'request_id': 'integrated414-actual-search-ime50-real-home30-rotation20-02', 'post_feature': {'search': 50, 'playback_home': 30, 'rotation': 20}}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
