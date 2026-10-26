"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 unchanged seven-workstream corrections: verify signed413 original real item-menu Watchlist, Collection, watched/unwatched and Favorites toggles with unrelated local records preserved. Existing final-actions assertions, actual production RunPlugin mutations, pure read-only persisted-state observer only; no test writer grant, API bypass, Search repeat, Close or physical gesture acceptance in this lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-actions', 'candidate_build': 40336380247, 'candidate_source_commit': '282a12a5e538a3ba05d5544d94a318b1c5de5ad4', 'candidate_apk_sha256': 'b3af984c5f035f6c0e51f70f71726b317ddbb503764eb5306505b583c0643ec4', 'candidate_artifact': 'Infinity-2103413-Home-Corrective-Verification-40336380247', 'authorization': 'UserOct26 unchanged seven-workstream corrections: verify signed413 original real item-menu Watchlist, Collection, watched/unwatched and Favorites toggles with unrelated local records preserved. Existing final-actions assertions, actual production RunPlugin mutations, pure read-only persisted-state observer only; no test writer grant, API bypass, Search repeat, Close or physical gesture acceptance in this lane.', 'request_id': 'integrated413-real-saved-actions-favourites-watched-01'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
