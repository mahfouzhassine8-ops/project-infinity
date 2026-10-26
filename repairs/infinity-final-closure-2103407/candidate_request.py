"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 critical local-first Continue requirement, latest signed414 corrects actual disabled refresh exception loop. Verify original final-continue exact real movie/TV card identity/source/native60of180 position/watched/noautoplay, retained removal data, actual playback alias progress and deliberate rewind. Replace only unsuitable1fps generated test clip with24fps1sec keyframes; original45/15sec predicates and deadlines unchanged. Read actual playback/state/Favorites observations on failure. Preserve signed413 partial passes and failures. No test writer grant, Search repetitions, Close or physical Fold pass in this lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-continue', 'candidate_build': 40345149803, 'candidate_source_commit': 'f5dbd03fb3a5df6b2f0f209bc36768d6ebd16c71', 'candidate_apk_sha256': 'a13bd3a5fc10752fc06621e2b49d050b5fd3ba0a8a86ad9e675420335b0313d3', 'candidate_artifact': 'Infinity-2103414-Refresh-Corrective-Verification-40345149803', 'authorization': 'UserOct26 critical local-first Continue requirement, latest signed414 corrects actual disabled refresh exception loop. Verify original final-continue exact real movie/TV card identity/source/native60of180 position/watched/noautoplay, retained removal data, actual playback alias progress and deliberate rewind. Replace only unsuitable1fps generated test clip with24fps1sec keyframes; original45/15sec predicates and deadlines unchanged. Read actual playback/state/Favorites observations on failure. Preserve signed413 partial passes and failures. No test writer grant, Search repetitions, Close or physical Fold pass in this lane.', 'request_id': 'integrated414-local-continue-seekable-clip-and-readback-01'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
