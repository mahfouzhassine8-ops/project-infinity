"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 critical local-first Continue verification on signed414. Prior run40346077812 failed adbroot transport before APK installation; retry only after exact bounded fresh-noapp API37 daemon recovery, preserving failure. Original movie/TV identity/native60of180/watched/noautoplay/removal/progress/alias/rewind assertions and45/15sec deadlines, valid24fps seekable generated clip, actual state/player/Favorites readback. No app retry/permission bypass/firstparty writer grant/Search repeat/Close or physical acceptance.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-continue', 'candidate_build': 40345149803, 'candidate_source_commit': 'f5dbd03fb3a5df6b2f0f209bc36768d6ebd16c71', 'candidate_apk_sha256': 'a13bd3a5fc10752fc06621e2b49d050b5fd3ba0a8a86ad9e675420335b0313d3', 'candidate_artifact': 'Infinity-2103414-Refresh-Corrective-Verification-40345149803', 'authorization': 'UserOct26 critical local-first Continue verification on signed414. Prior run40346077812 failed adbroot transport before APK installation; retry only after exact bounded fresh-noapp API37 daemon recovery, preserving failure. Original movie/TV identity/native60of180/watched/noautoplay/removal/progress/alias/rewind assertions and45/15sec deadlines, valid24fps seekable generated clip, actual state/player/Favorites readback. No app retry/permission bypass/firstparty writer grant/Search repeat/Close or physical acceptance.', 'request_id': 'integrated414-local-continue-bootstrap-transport-02'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
